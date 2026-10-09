"""Kenteken Check: WSGI application with no framework dependencies."""
import photos
import reports
import base64
import supplemental
import itertools
import hashlib
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
SCHEMA_VERSION = 7
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

def database():
    DATA.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATA / 'cache.sqlite', timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS cache (plate TEXT PRIMARY KEY, fetched REAL, payload TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY, plate TEXT, observed REAL, last_seen REAL, hash TEXT, payload TEXT)')
    db.execute('CREATE INDEX IF NOT EXISTS observation_plate ON observations(plate, observed)')
    db.execute('CREATE TABLE IF NOT EXISTS selections (plate TEXT PRIMARY KEY, context TEXT)')
    return db

def fetch_rows(dataset, label, filters):
    rows = []
    for offset in itertools.count(0, 1000):
        params = dict(filters, **{'$limit': 1000, '$offset': offset})
        url = f'https://opendata.rdw.nl/resource/{dataset}.json?' + urlencode(params)
        request = Request(url, headers={'User-Agent': 'KentekenCheck/0.6.0', 'Accept': 'application/json'})
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
                      headers={'X-API-Key': token, 'User-Agent': 'KentekenCheck/0.6.0', 'Accept': 'application/json'})
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
    plate = normalize(plate)
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
    return {'plate': plate, 'observations': events, 'note': 'Eigen waarnemingen sinds het opzoeken in deze app; geen gereconstrueerde historie van vóór die tijd.'}

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
        return result
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
        sections['modelfotos'], reasons['modelfotos'] = photos.find((sections.get('voertuig') or [{}])[0], sections.get('eu_model') or [], DATA)
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
    return result

def application(environ, start_response):
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
            body = b'{"status":"ok","version":"0.6.0"}'
        elif path.startswith('/api/reports/'):
            parts=path.removeprefix('/api/reports/').split('/');plate=normalize(parts[0])
            if method in ('POST','DELETE'):
                if environ.get('HTTP_ORIGIN') and urlparse(environ['HTTP_ORIGIN']).netloc!=environ.get('HTTP_HOST'):raise LookupError('Ongeldige aanvraagherkomst.',400)
            try:
                if method=='POST':
                    if environ.get('CONTENT_TYPE','').split(';')[0]!='application/json':raise ValueError('Gebruik JSON voor een rapportupload.')
                    size=int(environ.get('CONTENT_LENGTH','0'))
                    if not 0<size<9_000_000:raise ValueError('Gebruik een PDF van maximaal 6 MB.')
                    value=json.loads(environ['wsgi.input'].read(size))
                    raw=base64.b64decode(value['data'],validate=True)
                    reports.save_document(DATA,plate,value['name'],raw)
                elif method=='DELETE':
                    if len(parts)!=2:raise ValueError('Rapport-ID ontbreekt.')
                    reports.document(DATA,plate,parts[1],delete=True)
                body=json.dumps(reports.documents(DATA,plate),ensure_ascii=False).encode()
            except FileNotFoundError as exc:raise LookupError(str(exc),404) from exc
            except (ValueError,KeyError,TypeError) as exc:raise LookupError(str(exc),400) from exc
            headers.append(('Cache-Control','no-store'))
        elif path.startswith('/api/report-file/'):
            parts=path.removeprefix('/api/report-file/').split('/')
            if len(parts)!=2:raise LookupError('Rapport niet gevonden.',404)
            try:row,body=reports.document(DATA,normalize(parts[0]),parts[1])
            except FileNotFoundError as exc:raise LookupError(str(exc),404) from exc
            content_type='application/pdf';headers.extend([('Content-Disposition',"attachment; filename=\"rapport.pdf\"; filename*=UTF-8''"+quote(row['name'],safe='')),('Cache-Control','no-store')])
        elif path=='/api/report-options':
            query=parse_qs(environ.get('QUERY_STRING',''));key=query.get('source',[''])[0];make=query.get('make',[''])[0];model=query.get('model',[''])[0]
            if key not in reports.PROVIDERS or not make or not model or len(make)>100 or len(model)>100:raise LookupError('Ongeldige rapportzoekopdracht.',400)
            try:body=json.dumps(reports.catalog(key,make,model),ensure_ascii=False).encode()
            except reports.ReportError as exc:raise LookupError(str(exc)) from exc
            headers.append(('Cache-Control','no-store'))
        elif path.startswith('/api/photo/'):
            try: body, content_type = photos.media(path.removeprefix('/api/photo/'), DATA)
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
        elif path.startswith('/api/vehicle/'):
            query = parse_qs(environ.get('QUERY_STRING', ''))
            selection = None
            if 'selection' in query:
                try:
                    selection = json.loads(query['selection'][0])
                    if not isinstance(selection, dict): raise ValueError('Invalid selection')
                except ValueError as exc: raise LookupError('Ongeldige aanvullende zoekopties.', 400) from exc
            result = lookup(path.removeprefix('/api/vehicle/'), query.get('refresh') == ['1'], selection)
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

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    make_server('127.0.0.1', 8080, application).serve_forever()
