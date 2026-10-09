"""Kenteken Check: WSGI application with no framework dependencies."""
import vin
import accounts
import contextvars
import shutil
from contextlib import contextmanager, closing
import photos
import reports
import base64
import supplemental
import itertools
import hashlib
import hmac
import json
import mimetypes
import os
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent
DATA = Path(os.environ.get('DATA_DIR', '/data'))
CURRENT_USER = contextvars.ContextVar('kenteken_user', default=None)

def storage_dir():
    ident = CURRENT_USER.get()
    return DATA / 'users' / str(ident) if ident is not None else DATA

def adopt_legacy(ident):
    target = DATA / 'users' / str(ident)
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (DATA / 'cache.sqlite').exists():
        with closing(sqlite3.connect(DATA / 'cache.sqlite')) as source, closing(sqlite3.connect(target / 'cache.sqlite')) as destination, destination:
            source.backup(destination)
            destination.execute('CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY, plate TEXT, observed REAL, last_seen REAL, hash TEXT, payload TEXT)')
            destination.execute('DELETE FROM observations WHERE id NOT IN (SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY plate ORDER BY observed DESC,id DESC) AS rank FROM observations) WHERE rank<=4)')
            if destination.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Migratiecontrole mislukt.')
    for name in ('reports','photos'):
        if (DATA / name).exists(): shutil.copytree(DATA/name,target/name,dirs_exist_ok=True)

def finish_legacy_migration():
    # Called only after the first account and its verified SQLite backup commit.
    for name in ('cache.sqlite','cache.sqlite-wal','cache.sqlite-shm'):
        (DATA/name).unlink(missing_ok=True)
DATASETS = {
    'voertuig': ('m9d7-ebf2', 'Voertuig'),
    'brandstof': ('8ys7-d773', 'Brandstof en emissies'),
    'assen': ('3huj-srit', 'Assen'),
    'carrosserie': ('vezc-m2t6', 'Carrosserie'),
    'carrosserie_specifiek': ('jhie-znh9', 'Specifieke carrosserie'),
    'voertuigklasse': ('kmfi-hrps', 'Voertuigklasse'),
    'keuringen': ('sgfe-77wx', 'Keuringsmeldingen'),
    'gebreken': ('a34c-vvps', 'Geconstateerde gebreken'),
    'objecten': ('sghb-dzxx', 'Ingebouwde objecten'),
    'terugroepstatus': ('t49b-isb7', 'Terugroepstatus'),
    'keuringsvervaldata': ('vkij-7mwc', 'Keuringsvervaldata'),
    'subcategorie': ('2ba7-embk', 'Voertuigsubcategorie'),
    'bijzonderheden': ('7ug8-2dtt', 'Voertuigbijzonderheden'),
    'rupsbanden': ('3xwf-ince', 'Rupsbanden'),
}
RELATED = {
    'gebrekbeschrijvingen': ('hx2c-gt7k', 'Gebrekbeschrijvingen'),
    'terugroepdetails': ('j9yg-7rg9', 'Terugroepacties'),
    'terugroeprisico': ('9ihi-jgpf', 'Terugroepgevaren'),
    'terugroepinformeren': ('mh8w-8cup', 'Informeren bij terugroepactie'),
    'terugroepmodellen': ('mu2x-mu5e', 'Modellen bij bevestigde terugroepactie'),
    'telleruitleg': ('jqs4-4kvw', 'Uitleg tellerstandoordeel'),
}
CACHE_SECONDS = 3600
SCHEMA_VERSION = 10
CATALOG = json.loads((ROOT / 'rdw_catalog.json').read_text())
TYPE_APPROVALS = {('tgk_' + row['id'].replace('-', '_')): (row['id'], row['name'].replace('Open Data RDW: TGK ', 'Typegoedkeuring: '))
                  for row in CATALOG['datasets'] if row['name'].startswith('Open Data RDW: TGK ')}
ALL_RDW = {**DATASETS, **RELATED, **TYPE_APPROVALS}
EXTERNALS = {
    'extern_voertuig': ('', 'Aanvullend voertuigrapport'),
    'extern_apk': ('/apk', 'Aanvullende APK-gegevens'),
    'extern_recalls': ('/terugroepacties', 'Aanvullende terugroepgegevens'),
    'extern_waarde': ('/waarde', 'Externe waarde-indicatie'),
}

class LookupError(Exception):
    def __init__(self, message, status=503):
        self.status = status
        super().__init__(message)

def normalize(value):
    plate = re.sub(r'[-\s]', '', value).upper()
    if not re.fullmatch(r'[A-Z0-9]{6}', plate) or not re.search('[A-Z]', plate) or not re.search('[0-9]', plate):
        raise LookupError('Vul een Nederlands kenteken in, bijvoorbeeld AB-123-C.', 400)
    return plate

def normalize_identifier(value):
    compact=re.sub(r'\s','',value).upper()
    if len(compact)==17:
        try:return vin.normalize(value)
        except ValueError as exc:raise LookupError(str(exc),400) from exc
    return normalize(value)

@contextmanager
def database():
    directory = storage_dir()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(directory / 'cache.sqlite', timeout=15)
    db.execute('PRAGMA journal_mode=WAL')
    os.chmod(directory / 'cache.sqlite', 0o600)
    db.execute('CREATE TABLE IF NOT EXISTS cache (plate TEXT PRIMARY KEY, fetched REAL, payload TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY, plate TEXT, observed REAL, last_seen REAL, hash TEXT, payload TEXT)')
    db.execute('CREATE INDEX IF NOT EXISTS observation_plate ON observations(plate, observed)')
    db.execute('CREATE TABLE IF NOT EXISTS selections (plate TEXT PRIMARY KEY, context TEXT)')
    try:
        with db: yield db
    finally: db.close()

def fetch_rows(dataset, label, filters):
    rows = []
    for offset in itertools.count(0, 1000):
        params = dict(filters, **{'$limit': 1000, '$offset': offset})
        url = f'https://opendata.rdw.nl/resource/{dataset}.json?' + urlencode(params)
        request = Request(url, headers={'User-Agent': 'KentekenCheck/0.7.0', 'Accept': 'application/json'})
        try:
            with urlopen(request, timeout=12) as response:
                raw = response.read(4_000_001)
                if len(raw) > 4_000_000:
                    raise ValueError('Response too large')
                page = json.loads(raw)
            if not isinstance(page, list) or not all(isinstance(row, dict) for row in page):
                raise ValueError('Invalid RDW response')
            rows.extend(page)
            if len(page) < 1000:
                return rows
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            raise LookupError(f'{label} kon niet worden opgehaald. Probeer het later opnieuw.') from exc

def fetch_dataset(key, plate):
    dataset, label = DATASETS[key]
    order = 'meld_datum_door_keuringsinstantie DESC, meld_tijd_door_keuringsinstantie DESC' if key in ('keuringen', 'gebreken') else 'kenteken'
    return fetch_rows(dataset, label, {'kenteken': plate, '$order': order})

def fetch_related(key, field, codes):
    if not codes:
        return []
    # Codes originate in RDW data; quote them as SoQL literals, never as URLs.
    values = ','.join("'" + str(code).replace("'", "''") + "'" for code in sorted(set(codes)))
    dataset, label = RELATED[key]
    return fetch_rows(dataset, label, {'$where': f'{field} in ({values})', '$order': field})

UNAVAILABLE_HISTORY = {
    'tellerhistorie': ('Kilometerstandhistorie', 'Niet beschikbaar via open data. Het RDW-voertuigrapport vereist toegang van de eigenaar/houder.', 'https://www.rdw.nl/uw-voertuig-en-uw-gegevens/informatie-over-uw-voertuig/rdw-voertuigrapport-aanvragen'),
    'eigenaarhistorie': ('Volledige eigenaarshistorie', 'Niet beschikbaar via de aangesloten openbare bronnen; een laatste tenaamstellingsdatum is geen volledige eigenaarshistorie.', 'https://www.rdw.nl/over-rdw/dienstverlening/open-data/algemene-informatie'),
    'schadehistorie': ('Volledige schadehistorie', 'Geen openbare bron aangesloten die een volledige schadehistorie op kenteken levert.', ''),
    'onderhoudshistorie': ('Volledige onderhoudshistorie', 'Geen openbare bron aangesloten die onderhoudsbeurten op kenteken levert.', ''),
    'advertentiehistorie': ('Advertentiehistorie', 'Geen geverifieerde openbare API voor historische advertenties aangesloten.', ''),
}

def source_metadata():
    catalog = {row['id']: row for row in CATALOG['datasets']}
    sources = {}
    for key, (dataset, label) in ALL_RDW.items():
        kind = 'typegoedkeuring' if key in TYPE_APPROVALS else 'kenteken' if key in DATASETS else 'referentie'
        sources[key] = {'label': label, 'url': f'https://opendata.rdw.nl/d/{dataset}', 'scope': kind,
                        'fields': catalog.get(dataset, {}).get('fields', {}), 'provider': 'RDW'}
    for key, (_, label) in EXTERNALS.items():
        sources[key] = {'label': label, 'url': 'https://123kentekencheck.nl/api/aanmelden', 'scope': 'extern', 'provider': '123kentekencheck.nl', 'fields': {}}
    for key, (label, reason, url) in UNAVAILABLE_HISTORY.items():
        sources[key] = {'label': label, 'url': url, 'scope': 'historie', 'provider': 'Beschikbaarheid historie', 'fields': {}}
    sources['modelfotos'] = photos.SOURCE
    sources.update(supplemental.metadata())
    sources.update(reports.metadata())
    return sources

def fetch_approval(key, vehicle):
    number = vehicle.get('typegoedkeuringsnummer')
    if not number:
        return [], 'Geen typegoedkeuringsnummer geregistreerd.'
    dataset, label = TYPE_APPROVALS[key]
    columns = next(row['fields'] for row in CATALOG['datasets'] if row['id'] == dataset)
    filters = {'typegoedkeuringsnummer': number}
    # Only exact matches. Do not substitute a nearby model or drop revision digits.
    if 'codevarianttgk' in columns or 'codevariantgk' in columns:
        if not vehicle.get('variant') or not vehicle.get('uitvoering'):
            return [], 'Variant of uitvoering ontbreekt; geen betrouwbare koppeling mogelijk.'
        filters['codevarianttgk' if 'codevarianttgk' in columns else 'codevariantgk'] = vehicle['variant']
        filters['codeuitvoeringtgk'] = vehicle['uitvoering']
    order = ','.join(k for k in ['typegoedkeuringsnummer', 'volgnummerrevisieuitvoering'] if k in columns)
    return fetch_rows(dataset, label, dict(filters, **{'$order': order})), None

def fetch_external(key, plate):
    token = os.environ.get('KENTEKEN_API_KEY')
    if not token:
        return [], 'Een persoonlijke API-sleutel ontbreekt; deze externe bron is niet aangesloten.'
    suffix, label = EXTERNALS[key]
    request = Request(f'https://123kentekencheck.nl/api/v1/kenteken/{plate}{suffix}',
                      headers={'X-API-Key': token, 'User-Agent': 'KentekenCheck/0.7.0', 'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=12) as response:
            raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise ValueError('Response too large')
            payload = json.loads(raw)
        if not isinstance(payload, (list, dict)):
            raise ValueError('Invalid provider response')
        if isinstance(payload, dict) and (payload.get('error') or payload.get('success') is False):
            raise ValueError('Provider returned error')
        rows = payload if isinstance(payload, list) and all(isinstance(r, dict) for r in payload) else [payload]
        if not payload:
            rows = []
        return rows, None
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise LookupError(f'{label} kon niet worden opgehaald. Controleer de API-sleutel of probeer later opnieuw.') from exc

def enrich(sections, warnings, reasons=None):
    reasons = reasons if reasons is not None else {}
    vehicle = sections['voertuig'][0] if sections.get('voertuig') else {}
    recalls = [r['referentiecode_rdw'] for r in sections.get('terugroepstatus') or [] if r.get('referentiecode_rdw')]
    jobs = {
        'gebrekbeschrijvingen': ('gebrek_identificatie', [r['gebrek_identificatie'] for r in sections.get('gebreken') or [] if r.get('gebrek_identificatie')]),
        'terugroepdetails': ('referentiecode_rdw', recalls),
        'terugroeprisico': ('referentiecode_rdw', recalls),
        'terugroepinformeren': ('referentiecode_rdw', recalls),
        'terugroepmodellen': ('referentiecode_rdw', recalls),
        'telleruitleg': ('code_toelichting_tellerstandoordeel', [vehicle['code_toelichting_tellerstandoordeel']] if vehicle.get('code_toelichting_tellerstandoordeel') else []),
    }
    parents = {'gebrekbeschrijvingen': 'gebreken', **{key: 'terugroepstatus' for key in jobs if key.startswith('terugroep')}}
    for key, parent in parents.items():
        if sections.get(parent) is None:
            sections[key] = None
            reasons[key] = 'De bron met de benodigde referentiecodes kon niet worden opgehaald.'
            jobs.pop(key, None)
    for key, (_, codes) in jobs.items():
        if not codes:
            reasons[key] = 'Geen bijbehorende referentiecode voor dit kenteken gevonden.'
    for key in list(jobs):
        if not jobs[key][1]:
            sections[key] = []
            jobs.pop(key)
    with ThreadPoolExecutor(max_workers=8) as pool:
        pending = {pool.submit(fetch_related, key, field, codes): (key, False) for key, (field, codes) in jobs.items()}
        pending.update({pool.submit(fetch_approval, key, vehicle): (key, True) for key in TYPE_APPROVALS})
        for job in as_completed(pending):
            key, approval = pending[job]
            try:
                value = job.result()
                if approval:
                    sections[key], reason = value
                    if reason:
                        reasons[key] = reason
                else:
                    sections[key] = value
            except LookupError as exc:
                sections[key] = None
                reasons[key] = str(exc)
                warnings.append(str(exc))
    descriptions = sections.get('gebrekbeschrijvingen')
    for defect in sections.get('gebreken') or []:
        date = defect.get('meld_datum_door_keuringsinstantie', '')
        matches = [r for r in descriptions or [] if r.get('gebrek_identificatie') == defect.get('gebrek_identificatie')
                   and (not r.get('ingangsdatum_gebrek') or r['ingangsdatum_gebrek'] <= date)
                   and (r.get('einddatum_gebrek') in (None, '', '0') or date < r['einddatum_gebrek'])]
        if matches:
            match = max(matches, key=lambda r: r.get('ingangsdatum_gebrek', ''))
            for field in ('gebrek_omschrijving', 'gebrek_artikel_nummer', 'gebrek_paragraaf_nummer'):
                if field in match:
                    defect[field] = match[field]
    return sections

def source_statuses(sections, reasons):
    return {key: {'status': 'error' if rows is None else 'available' if rows else 'unavailable',
                  'row_count': len(rows) if rows is not None else 0,
                  'field_count': len({field for row in rows or [] for field in row}),
                  'reason': reasons.get(key) or ('Er zijn gegevens gevonden.' if rows else 'Geen gegevens voor deze koppeling gevonden.' if rows is not None else 'Ophalen mislukt.')}
            for key, rows in sections.items()}

def remember(result):
    if CURRENT_USER.get() is not None and (result.get('warnings') or any(rows is None for rows in result['sections'].values())):
        return  # An outage is not a new retained vehicle version.
    plate = result['plate']
    payload = json.dumps({'sections': result['sections'], 'sources': result['sources'], 'selection': result.get('selection', {})}, sort_keys=True, ensure_ascii=False)
    canonical = {key: sorted((json.dumps(row, sort_keys=True, ensure_ascii=False) for row in rows)) if rows is not None else None for key, rows in result['sections'].items()}
    digest = hashlib.sha256(json.dumps({'sections': canonical, 'selection': result.get('selection', {})}, sort_keys=True).encode()).hexdigest()
    with database() as db:
        if db.execute('SELECT 1 FROM observations WHERE plate=? AND observed=? AND hash=?', (plate, result['fetched_at'], digest)).fetchone():
            return
        previous = db.execute('SELECT id, hash FROM observations WHERE plate=? ORDER BY observed DESC, id DESC LIMIT 1', (plate,)).fetchone()
        if previous and previous[1] == digest:
            db.execute('UPDATE observations SET last_seen=? WHERE id=?', (result['fetched_at'], previous[0]))
        else:
            db.execute('INSERT INTO observations (plate, observed, last_seen, hash, payload) VALUES (?,?,?,?,?)',
                       (plate, result['fetched_at'], result['fetched_at'], digest, payload))
        if CURRENT_USER.get() is not None:
            db.execute('DELETE FROM observations WHERE plate=? AND id NOT IN (SELECT id FROM observations WHERE plate=? ORDER BY observed DESC,id DESC LIMIT 4)', (plate,plate))

def changes_between(before, after):
    changes = []
    for key, rows in after.items():
        # Do not misreport source outages or newly enabled datasets as vehicle changes.
        if key in supplemental.SOURCES or key in reports.PROVIDERS or key == 'modelfotos':
            continue  # Context source changes do not prove an individual vehicle event.
        old = before.get(key)
        if old is None or rows is None:
            continue
        if sorted(json.dumps(row, sort_keys=True) for row in old) != sorted(json.dumps(row, sort_keys=True) for row in rows):
            changes.append({'source': key, 'before': old, 'after': rows})
    return changes

def history(plate, full=False):
    plate = normalize_identifier(plate)
    with database() as db:
        records = db.execute('SELECT id, observed, last_seen, payload FROM observations WHERE plate=? ORDER BY observed, id', (plate,)).fetchall()
    events, previous = [], {}
    for ident, observed, last_seen, raw in records:
        payload = json.loads(raw)
        event = {'id': ident, 'observed_at': observed, 'last_seen_at': last_seen, 'changes': changes_between(previous, payload['sections']) if events else [],
                 'kind': 'change' if events else 'first_observation'}
        if full:
            event['data'] = payload
        events.append(event)
        previous.update({key: rows for key, rows in payload['sections'].items() if rows is not None})
    return {'plate': plate, 'observations': events, 'note': 'Bewaarde eigen waarnemingen; geen gereconstrueerde historie. Per gebruiker: huidige versie plus maximaal drie oudere versies.'}

def archive_context(result):
    """Expose a saved positive snapshot separately; never fill live fields with it."""
    result['archive'] = None
    if result['sections'].get('voertuig'):
        return result
    plate = normalize(result['plate'])
    with database() as db:
        records = db.execute('SELECT observed, last_seen, payload FROM observations WHERE plate=? AND observed<=? ORDER BY observed DESC, id DESC', (plate, result['fetched_at']))
        for observed, last_seen, raw in records:
            payload = json.loads(raw)
            if not payload.get('sections', {}).get('voertuig'):
                continue
            result['archive'] = {'plate': plate, 'observed_at': observed, 'last_seen_at': last_seen,
                                 'provenance': 'Eerder door deze app opgehaalde en lokaal bewaarde gegevens. Geen actuele registratie of bewijs van export/sloop.',
                                 'sections': payload['sections'], 'sources': payload.get('sources', {}),
                                 'source_status': source_statuses(payload['sections'], {})}
            break
    return result

def lookup_vin(value, refresh=False, selection=None):
    try:value=vin.normalize(value)
    except ValueError as exc:raise LookupError(str(exc),400) from exc
    with database() as db:
        if selection is None:
            saved=db.execute('SELECT context FROM selections WHERE plate=?',(value,)).fetchone();selection=json.loads(saved[0]) if saved else {}
        if not isinstance(selection,dict) or set(selection)-{'vin_decode_enabled'} or not isinstance(selection.get('vin_decode_enabled',False),bool):raise LookupError('Ongeldige VIN-bronkeuze.',400)
        selection={'vin_decode_enabled':selection.get('vin_decode_enabled',False)}
        db.execute('INSERT OR REPLACE INTO selections VALUES (?,?)',(value,json.dumps(selection)))
        stored=db.execute('SELECT fetched,payload FROM cache WHERE plate=?',(value,)).fetchone()
    if stored and not refresh:
        cached=json.loads(stored[1])
        if time.time()-stored[0]<CACHE_SECONDS and cached.get('schema_version')==SCHEMA_VERSION and cached.get('selection')==selection and cached.get('vin_provider_enabled')==vin.configured():
            cached['cached']=True;cached['history']=history(value);return cached
    sections={'vin_structuur':[vin.structure(value)],'vin_rdw':[]};reasons={'vin_rdw':'RDW Open Data biedt in de aangesloten datasets geen zoeken op volledig VIN. Een kenteken moet afzonderlijk opgezocht worden.'};warnings=[]
    try:sections['vin_decoder'],reasons['vin_decoder']=vin.decode(value,selection['vin_decode_enabled'])
    except vin.VinError as exc:sections['vin_decoder']=None;reasons['vin_decoder']=str(exc);warnings.append(str(exc))
    for key,(_,reason) in vin.UNAVAILABLE.items():sections[key]=[];reasons[key]=reason
    sources=dict(vin.SOURCES)
    derived=vin.vehicle(sections.get('vin_decoder') or [])
    if derived:
        sections['voertuig']=derived;sources['voertuig']={'label':'Modelidentificatie uit VIN-provider','provider':'Vincario','scope':'vin','fields':{},'note':'Afgeleid uit ontvangen leveranciersvelden, geen RDW-registratie.','url':'https://vincario.com'}
    result={'plate':value,'vin':value,'lookup_type':'vin','schema_version':SCHEMA_VERSION,'selection':selection,'vin_provider_enabled':vin.configured(),'sections':sections,'sources':sources,'source_status':source_statuses(sections,reasons),'warnings':warnings,'fetched_at':time.time(),'cached':False}
    remember(result)
    if not warnings:
        with database() as db:db.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',(value,result['fetched_at'],json.dumps(result)))
    result['history']=history(value);return result

def lookup(plate, refresh=False, selection=None):
    plate = normalize(plate)
    if selection is not None:
        try: selection = supplemental.context(selection)
        except ValueError as exc: raise LookupError(str(exc), 400) from exc
        with database() as db:
            db.execute('INSERT OR REPLACE INTO selections VALUES (?, ?)', (plate, json.dumps(selection)))
    else:
        with database() as db:
            saved = db.execute('SELECT context FROM selections WHERE plate=?', (plate,)).fetchone()
        selection = json.loads(saved[0]) if saved else {}
    with database() as db:
        cached = db.execute('SELECT fetched, payload FROM cache WHERE plate=?', (plate,)).fetchone()
    if cached and not refresh and time.time() - cached[0] < CACHE_SECONDS and json.loads(cached[1]).get('schema_version') == SCHEMA_VERSION and json.loads(cached[1]).get('selection', {}) == selection and json.loads(cached[1]).get('external_enabled', False) == bool(os.environ.get('KENTEKEN_API_KEY')):
        result = json.loads(cached[1])
        result['cached'] = True
        result['history'] = history(plate)
        return archive_context(result)
    # Keep independent datasets and saved history usable even without a current base record.
    warnings = []
    reasons = {}
    try:
        vehicle = fetch_dataset('voertuig', plate)
        if not vehicle:
            reasons['voertuig'] = 'Geen voertuig in de actuele openbare basisregistratie gevonden.'
    except LookupError as exc:
        vehicle = None
        warnings.append(str(exc))
        reasons['voertuig'] = str(exc)
    if cached:
        old = json.loads(cached[1])
        if old.get('sections') and old.get('sources'):
            remember(old)
    sections = {'voertuig': vehicle}
    with ThreadPoolExecutor(max_workers=14) as pool:
        jobs = {pool.submit(fetch_dataset, key, plate): key for key in DATASETS if key != 'voertuig'}
        for job in as_completed(jobs):
            key = jobs[job]
            try:
                sections[key] = job.result()
            except LookupError as exc:
                sections[key] = None
                warnings.append(str(exc))
    enrich(sections, warnings, reasons)
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(fetch_external, key, plate): key for key in EXTERNALS}
        for job in as_completed(pending):
            key = pending[job]
            try:
                sections[key], reason = job.result()
                if reason:
                    reasons[key] = reason
            except LookupError as exc:
                sections[key] = None
                reasons[key] = str(exc)
                warnings.append(str(exc))
    for key, (_, reason, _) in UNAVAILABLE_HISTORY.items():
        sections[key] = []
        reasons[key] = reason
    extra, extra_reasons, extra_warnings = supplemental.fetch_all(selection, sections)
    sections.update(extra)
    reasons.update(extra_reasons)
    warnings.extend(extra_warnings)
    vehicle=(sections.get('voertuig') or [{}])[0]
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs={pool.submit(reports.fetch,key,selection.get('report_urls',{}).get(key,''),vehicle):key for key in reports.PROVIDERS}
        for job in as_completed(jobs):
            key=jobs[job]
            try:sections[key],reasons[key]=job.result()
            except reports.ReportError as exc:
                sections[key]=None;reasons[key]=str(exc);warnings.append(reports.PROVIDERS[key]['label']+': '+str(exc))
    try:
        sections['modelfotos'], reasons['modelfotos'] = photos.find((sections.get('voertuig') or [{}])[0], sections.get('eu_model') or [], storage_dir())
    except photos.PhotoError as exc:
        sections['modelfotos'] = None
        reasons['modelfotos'] = str(exc)
        warnings.append(str(exc))
    result = {'selection': selection, 'external_enabled': bool(os.environ.get('KENTEKEN_API_KEY')), 'schema_version': SCHEMA_VERSION, 'plate': plate, 'sections': sections, 'warnings': warnings, 'fetched_at': time.time(), 'cached': False,
              'sources': source_metadata(), 'source_status': source_statuses(sections, reasons)}
    remember(result)
    # Incomplete responses are not cached, so retry can recover missing sections.
    if not warnings:
        with database() as db:
            db.execute('INSERT OR REPLACE INTO cache VALUES (?, ?, ?)', (plate, result['fetched_at'], json.dumps(result)))
            db.execute('DELETE FROM cache WHERE fetched < ?', (time.time() - 7 * 86400,))
    result['history'] = history(plate)
    return archive_context(result)

def _application(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    status = 200
    headers = [('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'same-origin'),
               ('Content-Security-Policy', "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'")]
    content_type = 'application/json; charset=utf-8'
    try:
        if method not in ('GET','HEAD') and not (path.startswith('/api/reports/') and method in ('POST','DELETE')):
            raise LookupError('Methode niet toegestaan.', 405)
        if path == '/health':
            body = b'{"status":"ok","version":"0.10.0"}'
        elif path.startswith('/api/reports/'):
            parts=path.removeprefix('/api/reports/').split('/');plate=normalize_identifier(parts[0])
            if method in ('POST','DELETE'):
                if environ.get('HTTP_ORIGIN') and urlparse(environ['HTTP_ORIGIN']).netloc!=environ.get('HTTP_HOST'):raise LookupError('Ongeldige aanvraagherkomst.',400)
            try:
                if method=='POST':
                    if environ.get('CONTENT_TYPE','').split(';')[0]!='application/json':raise ValueError('Gebruik JSON voor een rapportupload.')
                    size=int(environ.get('CONTENT_LENGTH','0'))
                    if not 0<size<9_000_000:raise ValueError('Gebruik een PDF van maximaal 6 MB.')
                    value=json.loads(environ['wsgi.input'].read(size))
                    raw=base64.b64decode(value['data'],validate=True)
                    reports.save_document(storage_dir(),plate,value['name'],raw)
                elif method=='DELETE':
                    if len(parts)!=2:raise ValueError('Rapport-ID ontbreekt.')
                    reports.document(storage_dir(),plate,parts[1],delete=True)
                body=json.dumps(reports.documents(storage_dir(),plate),ensure_ascii=False).encode()
            except FileNotFoundError as exc:raise LookupError(str(exc),404) from exc
            except (ValueError,KeyError,TypeError) as exc:raise LookupError(str(exc),400) from exc
            headers.append(('Cache-Control','no-store'))
        elif path.startswith('/api/report-file/'):
            parts=path.removeprefix('/api/report-file/').split('/')
            if len(parts)!=2:raise LookupError('Rapport niet gevonden.',404)
            try:row,body=reports.document(storage_dir(),normalize_identifier(parts[0]),parts[1])
            except FileNotFoundError as exc:raise LookupError(str(exc),404) from exc
            content_type='application/pdf';headers.extend([('Content-Disposition',"attachment; filename=\"rapport.pdf\"; filename*=UTF-8''"+quote(row['name'],safe='')),('Cache-Control','no-store')])
        elif path=='/api/report-options':
            query=parse_qs(environ.get('QUERY_STRING',''));key=query.get('source',[''])[0];make=query.get('make',[''])[0];model=query.get('model',[''])[0]
            if key not in reports.PROVIDERS or not make or not model or len(make)>100 or len(model)>100:raise LookupError('Ongeldige rapportzoekopdracht.',400)
            try:body=json.dumps(reports.catalog(key,make,model),ensure_ascii=False).encode()
            except reports.ReportError as exc:raise LookupError(str(exc)) from exc
            headers.append(('Cache-Control','no-store'))
        elif path.startswith('/api/photo/'):
            try: body, content_type = photos.media(path.removeprefix('/api/photo/'), storage_dir())
            except FileNotFoundError as exc: raise LookupError(str(exc), 404) from exc
            except photos.PhotoError as exc: raise LookupError(str(exc)) from exc
            headers.append(('Cache-Control', 'private, max-age=86400'))
        elif path == '/api/eu-models':
            query = parse_qs(environ.get('QUERY_STRING', ''))
            try: body = json.dumps(supplemental.model_options(query.get('make', [''])[0]), ensure_ascii=False).encode()
            except ValueError as exc: raise LookupError(str(exc), 400) from exc
            except supplemental.SourceError as exc: raise LookupError(str(exc)) from exc
            headers.append(('Cache-Control', 'no-store'))
        elif path.startswith('/api/history/'):
            body = json.dumps(history(path.removeprefix('/api/history/'), full=True), ensure_ascii=False).encode()
            headers.append(('Cache-Control', 'no-store'))
        elif path.startswith('/api/vin/'):
            query=parse_qs(environ.get('QUERY_STRING',''));selection=None
            if 'selection' in query:
                try:selection=json.loads(query['selection'][0])
                except ValueError as exc:raise LookupError('Ongeldige VIN-bronkeuze.',400) from exc
            result=lookup_vin(path.removeprefix('/api/vin/'),query.get('refresh')==['1'],selection)
            add_lookup_count(result,environ,query)
            body=json.dumps(result,ensure_ascii=False).encode();headers.append(('Cache-Control','no-store'))
        elif path.startswith('/api/vehicle/'):
            query = parse_qs(environ.get('QUERY_STRING', ''))
            selection = None
            if 'selection' in query:
                try:
                    selection = json.loads(query['selection'][0])
                    if not isinstance(selection, dict): raise ValueError('Invalid selection')
                except ValueError as exc: raise LookupError('Ongeldige aanvullende zoekopties.', 400) from exc
            result = lookup(path.removeprefix('/api/vehicle/'), query.get('refresh') == ['1'], selection)
            add_lookup_count(result,environ,query)
            body = json.dumps(result, ensure_ascii=False).encode()
            headers.append(('Cache-Control', 'no-store'))
        else:
            relative = 'static/index.html' if path == '/' else path.lstrip('/')
            file = (ROOT / relative).resolve()
            if not file.is_relative_to((ROOT / 'static').resolve()) or not file.is_file():
                raise LookupError('Pagina niet gevonden.', 404)
            body = file.read_bytes()
            content_type = (mimetypes.guess_type(file)[0] or 'application/octet-stream') + '; charset=utf-8'
    except LookupError as exc:
        status = exc.status
        body = json.dumps({'error': str(exc)}).encode()
    except Exception:
        status = 500
        body = b'{"error":"Er ging iets mis. Probeer het opnieuw."}'
    headers.extend([('Content-Type', content_type), ('Content-Length', str(len(body)))])
    reason = {200:'OK',400:'Bad Request',404:'Not Found',405:'Method Not Allowed',500:'Internal Server Error',503:'Service Unavailable'}[status]
    start_response(f'{status} {reason}', headers)
    return [b'' if method == 'HEAD' else body]

def json_input(environ):
    if environ.get('CONTENT_TYPE','').split(';')[0] != 'application/json': raise accounts.AccountError('Gebruik JSON.')
    try:
        size = int(environ.get('CONTENT_LENGTH','0'))
        if not 0 < size <= 100_000: raise ValueError()
        data = json.loads(environ['wsgi.input'].read(size))
        if not isinstance(data,dict): raise ValueError()
        return data
    except (ValueError,TypeError,KeyError): raise accounts.AccountError('Ongeldige invoer.')

def account_routes(environ, user, token):
    path = environ.get('PATH_INFO','/'); method = environ.get('REQUEST_METHOD','GET'); issued = None
    if path == '/auth/state' and method == 'GET':
        with accounts.database(DATA) as db: setup = not db.execute('SELECT 1 FROM users LIMIT 1').fetchone()
        return {'setup':setup,'user':user,'csrf':accounts.csrf(token) if user else ''}, issued
    if path in ('/auth/setup','/auth/login') and method == 'POST':
        if environ.get('HTTP_X_KC_REQUEST') != '1': raise accounts.AccountError('Ongeldige aanvraag.',403)
        value=json_input(environ)
        if path.endswith('setup'):
            accounts.throttle(DATA,'setup:'+environ.get('REMOTE_ADDR','local'),10)
            user=accounts.create(DATA,value.get('username'),value.get('password'),role='admin',setup=True,adopt=adopt_legacy)
            finish_legacy_migration()
            issued=accounts.issue(DATA,user)
        else: user,issued=accounts.login(DATA,value.get('username'),value.get('password'),environ.get('REMOTE_ADDR','local'))
        return {'user':user,'csrf':accounts.csrf(issued)},issued
    if not user: raise accounts.AccountError('Log in om deze gegevens te bekijken.',401)
    if path == '/auth/logout' and method == 'POST':
        with accounts.database(DATA) as db: db.execute('DELETE FROM sessions WHERE hash=?',(accounts.token_hash(token),))
        return {'ok':True},''
    if path == '/auth/password' and method == 'POST':
        value=json_input(environ)
        if not isinstance(value.get('current_password'),str): raise accounts.AccountError('Vul je huidige wachtwoord in.')
        accounts.throttle(DATA,'password:'+str(user['id']),10)
        encoded=accounts.change_password(DATA,user['id'],value.get('password'),old=value['current_password'])
        issued=accounts.issue(DATA,user,encoded);return {'user':user,'csrf':accounts.csrf(issued)},issued
    if path.startswith('/auth/users'):
        if user['role'] != 'admin': raise accounts.AccountError('Alleen beheerders kunnen gebruikers beheren.',403)
        if path == '/auth/users' and method == 'POST':
            value=json_input(environ);accounts.create(DATA,value.get('username'),value.get('password'),value.get('role','user'))
        elif path != '/auth/users' and method == 'POST':
            try: ident=int(path.removeprefix('/auth/users/'))
            except ValueError: raise accounts.AccountError('Gebruiker niet gevonden.',404)
            if ident == user['id']: raise accounts.AccountError('Wijzig je eigen wachtwoord via Mijn account; je kunt jezelf niet uitschakelen.')
            value=json_input(environ)
            with accounts.database(DATA) as db:
                db.execute('BEGIN IMMEDIATE')
                target=db.execute('SELECT * FROM users WHERE id=?',(ident,)).fetchone()
                if not target: raise accounts.AccountError('Gebruiker niet gevonden.',404)
                if 'active' in value:
                    if not isinstance(value['active'],bool): raise accounts.AccountError('Ongeldige accountstatus.')
                    if not value['active'] and target['role']=='admin' and target['active'] and db.execute("SELECT count(*) FROM users WHERE role='admin' AND active=1").fetchone()[0]<=1:raise accounts.AccountError('De laatste actieve beheerder kan niet worden uitgeschakeld.')
                    db.execute('UPDATE users SET active=? WHERE id=?',(int(value['active']),ident));db.execute('DELETE FROM sessions WHERE user_id=?',(ident,))
            if 'password' in value: accounts.change_password(DATA,ident,value['password'])
        elif path != '/auth/users' or method != 'GET': raise accounts.AccountError('Methode niet toegestaan.',405)
        with accounts.database(DATA) as db: users=[accounts.public(row) for row in db.execute('SELECT * FROM users ORDER BY username')]
        return {'users':users},issued
    if path == '/api/garage' and method == 'GET':return {'favorites':accounts.favorites(DATA,user['id'])},issued
    if path.startswith('/api/garage/') and method in ('PUT','DELETE'):
        plate=normalize_identifier(path.removeprefix('/api/garage/'));value=json_input(environ) if method=='PUT' else {}
        watch=value.get('watch',len(plate)==6)
        if not isinstance(watch,bool) or (watch and len(plate)!=6):raise accounts.AccountError('Dagelijkse controles ondersteunen alleen Nederlandse kentekens, geen VIN-providertegoed.')
        return {'favorites':accounts.favorite(DATA,user['id'],plate,watch,delete=method=='DELETE')},issued
    if path == '/api/preferences' and method in ('GET','POST'):
        key=None;value=None
        if method=='POST':
            data=json_input(environ);key=data.get('key');value=data.get('value')
            if key=='recent':
                if not isinstance(value,list) or len(value)>30:raise accounts.AccountError('Ongeldige recente lijst.')
                value=[normalize_identifier(item) for item in value]
            elif isinstance(key,str) and key.startswith('costs:'):
                key='costs:'+normalize_identifier(key.removeprefix('costs:'))
                allowed={'km_year','litres_100','fuel_price','kwh_100','electric_price','insurance_month','tax_quarter','maintenance_year','tyres_year','other_year','purchase','resale','years'}
                if not isinstance(value,dict) or set(value)-allowed or any(not isinstance(v,(str,int,float)) or len(str(v))>64 for v in value.values()):raise accounts.AccountError('Ongeldige begroting.')
            else:raise accounts.AccountError('Ongeldige voorkeur.')
        return accounts.preferences(DATA,user['id'],key,value),issued
    raise accounts.AccountError('Pagina niet gevonden.',404)

def add_lookup_count(result, environ, query):
    user = CURRENT_USER.get()
    if user is not None:
        increment = (environ.get('REQUEST_METHOD','GET') == 'GET'
                     and environ.get('HTTP_X_LOOKUP_COUNT') == '1'
                     and 'refresh' not in query and 'selection' not in query)
        result['lookup_count'] = accounts.lookup_count(DATA,user,result['plate'],increment)

def application(environ, start_response):
    path=environ.get('PATH_INFO','/');method=environ.get('REQUEST_METHOD','GET')
    if path=='/' or path=='/health' or path.startswith('/static/'):
        return _application(environ,start_response)
    headers=[('Content-Type','application/json; charset=utf-8'),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','same-origin')]
    try:
        accounts.origin(environ)
        user,token=accounts.session(DATA,environ)
        public=path in ('/auth/state','/auth/login','/auth/setup')
        if not public and not user:raise accounts.AccountError('Log in om deze gegevens te bekijken.',401)
        query=parse_qs(environ.get('QUERY_STRING',''))
        mutable=method not in ('GET','HEAD') or (path.startswith(('/api/vehicle/','/api/vin/')) and ('selection' in query or 'refresh' in query or environ.get('HTTP_X_LOOKUP_COUNT')=='1'))
        if mutable and not public:
            if not hmac.compare_digest(environ.get('HTTP_X_CSRF_TOKEN',''),accounts.csrf(token)):raise accounts.AccountError('Sessiecontrole mislukt. Log opnieuw in.',403)
        if path.startswith('/auth/') or path.startswith('/api/garage') or path=='/api/preferences':
            data,issued=account_routes(environ,user,token)
            if issued is not None:headers.append(('Set-Cookie',accounts.cookie(issued,environ)))
            body=json.dumps(data,ensure_ascii=False).encode();status=200
        else:
            context=CURRENT_USER.set(user['id'])
            try:return _application(environ,start_response)
            finally:CURRENT_USER.reset(context)
    except (accounts.AccountError,LookupError) as exc:
        status=exc.status;body=json.dumps({'error':str(exc)},ensure_ascii=False).encode()
    except Exception:
        status=500;body=b'{"error":"Er ging iets mis. Probeer het opnieuw."}'
    headers.append(('Content-Length',str(len(body))))
    start_response(str(status)+' '+{200:'OK',400:'Bad Request',401:'Unauthorized',403:'Forbidden',404:'Not Found',405:'Method Not Allowed',409:'Conflict',429:'Too Many Requests',500:'Internal Server Error'}[status],headers)
    return [b'' if method=='HEAD' else body]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    make_server('127.0.0.1', 8080, application).serve_forever()
