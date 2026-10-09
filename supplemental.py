"""Dutch and European public sources. Context records never prove individual history."""
import itertools
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

class SourceError(Exception):
    pass

SOURCES = {
    'eu_registraties': ('Europese registraties · exacte uitvoering', 'https://www.eea.europa.eu/en/datahub/datahubitem-view/fa8b1229-3db6-495d-b18e-9c9b3267c02b', 'European Environment Agency (EEA)', 'Europese registratierecords van dezelfde typegoedkeuring, variant en uitvoering. Geen gebeurtenissen van dit individuele kenteken.'),
    'nl_teruggeroepen': ('Aanvullende Nederlandse terugroepinformatie', 'https://www.teruggeroepen.nl/api', 'Teruggeroepen.nl', 'Gekoppeld op terugroepreferenties die RDW voor dit kenteken heeft geleverd. Onderliggende bron is RDW; geen onafhankelijke bevestiging.'),
    'eu_model': ('Indicatieve Europese modelspecificaties', 'https://autoseeker.eu/data/', 'autoseeker.eu', 'Door jou gekozen Europese model/generatie. Indicatieve catalogusgegevens, geen bevestigde uitvoering of historie van dit kenteken. CC BY 4.0.'),
}

def metadata():
    return {key: {'label': label, 'url': url, 'provider': provider, 'scope': 'extern', 'fields': {}, 'note': note,
                  'licence': 'CC BY 4.0' if key == 'eu_model' else 'Zie bronvoorwaarden'}
            for key, (label, url, provider, note) in SOURCES.items()}

def context(values):
    if set(values) - {'model_slug', 'eea_enabled'}: raise ValueError('Onbekende aanvullende zoekoptie.')
    slug = values.get('model_slug', '')
    if not isinstance(slug, str) or not re.fullmatch(r'[a-z0-9-]{0,120}', slug):
        raise ValueError('Ongeldige Europese modelselectie.')
    enabled = values.get('eea_enabled', False)
    if not isinstance(enabled, bool): raise ValueError('Ongeldige keuze voor EEA.')
    return {**({'model_slug': slug} if slug else {}), **({'eea_enabled': True} if enabled else {})}

def get(url):
    try:
        with urlopen(Request(url, headers={'Accept': 'application/json', 'User-Agent': 'KentekenCheck/0.5.1'}), timeout=12) as response:
            raw = response.read(8_000_001)
        if len(raw) > 8_000_000: raise ValueError('Response too large')
        data = json.loads(raw)
        if not isinstance(data, (dict, list)): raise ValueError('Invalid response')
        return data
    except (HTTPError, URLError, OSError, TimeoutError, ValueError) as exc:
        raise SourceError('Bron kon niet worden opgehaald. Probeer later opnieuw.') from exc

_catalog_lock = threading.Lock()
_catalog = None
_catalog_at = 0

def catalog():
    global _catalog, _catalog_at
    with _catalog_lock:
        if _catalog is not None and time.time() - _catalog_at < 86400: return _catalog
        data = get('https://autoseeker.eu/data/models.json')
        if not isinstance(data, dict) or not isinstance(data.get('models'), list) or not all(isinstance(row, dict) and isinstance(row.get('slug'), str) for row in data['models']):
            raise SourceError('De bron leverde een onverwachte modelcatalogus.')
        _catalog, _catalog_at = data, time.time()
        return data

def model_options(make):
    if not isinstance(make, str) or not make.strip() or len(make) > 100:
        raise ValueError('Geen geldig voertuigmerk beschikbaar.')
    return [{'value': row['slug'], 'text': ' · '.join(str(row.get(key, '')) for key in ('merk','model','generatie'))}
            for row in catalog()['models'] if str(row.get('merk','')).casefold() == make.strip().casefold()]

def fetch_eu(vehicle):
    values = [vehicle.get(key) for key in ('typegoedkeuringsnummer', 'variant', 'uitvoering')]
    if not all(values): return [], 'Typegoedkeuringsnummer, variant of uitvoering ontbreekt; geen betrouwbare Europese koppeling mogelijk.'
    if not all(isinstance(value, str) and len(value) <= 200 for value in values):
        raise SourceError('Ongeldige koppelcodes in RDW-antwoord.')
    predicates = [f"[{column}] = '{value.replace(chr(39), chr(39)*2)}'" for column, value in zip(('TAN','Va','Ve'), values)]
    sql = 'SELECT * FROM [CO2Emission].[latest].[co2cars] WHERE ' + ' AND '.join(predicates) + ' ORDER BY [Year], [Status], [MS], [ID], [Version_file]'
    rows = []
    for page in itertools.count(1):
        data = get('https://discodata.eea.europa.eu/sql?' + urlencode({'query': sql, 'p': page, 'nrOfHits': 1000}))
        if not isinstance(data, dict) or data.get('errors') or not isinstance(data.get('results'), list):
            raise SourceError('EEA leverde een fout of onverwacht antwoord; geen volledig resultaat beschikbaar.')
        records = data['results']
        if not all(isinstance(row, dict) for row in records): raise SourceError('EEA leverde ongeldige records.')
        # SQL collation can ignore case/trailing spaces; retain only literal exact matches.
        rows.extend(row for row in records if all(row.get(column) == value for column, value in zip(('TAN','Va','Ve'),values)))
        if len(records) < 1000: break
    return rows, ('Europese registraties voor exact dezelfde goedkeuring, variant en uitvoering; geen individuele voertuighistorie.' if rows else 'Geen Europese registratierecords met deze exacte goedkeuring, variant en uitvoering gevonden.')

def fetch_recalls(sections):
    if sections.get('terugroepstatus') is None:
        raise SourceError('RDW-terugroepstatus kon niet worden opgehaald; benodigde referenties ontbreken.')
    codes = sorted({row['referentiecode_rdw'] for row in sections.get('terugroepstatus',[]) if row.get('referentiecode_rdw')})
    if not codes: return [], 'RDW heeft geen gekoppelde terugroepreferentie voor dit kenteken geleverd.'
    rows = []
    for code in codes:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', code): raise SourceError('Ongeldige terugroepreferentie in RDW-antwoord.')
        try: data = get('https://www.teruggeroepen.nl/api/v1/auto/' + quote(code, safe=''))
        except SourceError as exc:
            if isinstance(exc.__cause__, HTTPError) and exc.__cause__.code == 404: continue
            raise
        if not isinstance(data, dict) or data.get('referentiecode') != code:
            raise SourceError('De aanvullende terugroepbron leverde geen overeenkomende referentie.')
        rows.append(data)
    return rows, 'Aanvullend bronantwoord op bevestigde RDW-referenties.' if rows else 'Geen aanvullende melding op de gevonden RDW-referenties beschikbaar.'

def fetch_model(selection, vehicle):
    slug = selection.get('model_slug')
    if not slug: return [], 'Geen Europese model/generatie gekozen bij Aanvullende bronnen.'
    data = catalog()
    row = next((row for row in data['models'] if row['slug'] == slug), None)
    if row is None: return [], 'De geselecteerde generatie staat niet meer in de actuele Europese modelcatalogus.'
    if str(row.get('merk','')).casefold() != str(vehicle.get('merk','')).strip().casefold():
        return [], 'Modelmerk komt niet overeen met het RDW-merk; selecteer opnieuw.'
    return [{'catalogus_meta': data.get('meta', {}), 'model': row}], 'Door jou geselecteerde Europese generatie; specificaties zijn indicatief en kunnen afwijken van jouw uitvoering.'

def fetch_all(selection, sections):
    vehicle = (sections.get('voertuig') or [{}])[0]
    jobs = {'eu_registraties': lambda: fetch_eu(vehicle) if selection.get('eea_enabled') else ([], 'Niet ingeschakeld. Deze bron ontvangt de typegoedkeurings-, variant- en uitvoeringscodes. Schakel expliciet in bij Aanvullende bronnen.'), 'nl_teruggeroepen': lambda: fetch_recalls(sections), 'eu_model': lambda: fetch_model(selection, vehicle)}
    result, reasons, warnings = {}, {}, []
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(job): key for key, job in jobs.items()}
        for job in as_completed(pending):
            key = pending[job]
            try: result[key], reasons[key] = job.result()
            except SourceError as exc:
                result[key] = None
                reasons[key] = str(exc)
                warnings.append(SOURCES[key][0] + ': ' + str(exc))
    return result, reasons, warnings
