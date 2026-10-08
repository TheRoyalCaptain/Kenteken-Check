"""Kenteken Check: WSGI application with no framework dependencies."""
import json
import mimetypes
import os
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode
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
}
CACHE_SECONDS = 3600

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
    return db

def fetch_dataset(key, plate):
    dataset, label = DATASETS[key]
    url = f'https://opendata.rdw.nl/resource/{dataset}.json?' + urlencode({'kenteken': plate, '$limit': 100})
    request = Request(url, headers={'User-Agent': 'KentekenCheck/0.1.0', 'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=12) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError('Response too large')
            rows = json.loads(raw)
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError('Invalid RDW response')
        return rows
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise LookupError(f'{label} kon niet worden opgehaald. Probeer het later opnieuw.') from exc

def lookup(plate, refresh=False):
    plate = normalize(plate)
    with database() as db:
        cached = db.execute('SELECT fetched, payload FROM cache WHERE plate=?', (plate,)).fetchone()
    if cached and not refresh and time.time() - cached[0] < CACHE_SECONDS:
        result = json.loads(cached[1])
        result['cached'] = True
        return result
    # A missing vehicle must not be confused with an unavailable data source.
    vehicle = fetch_dataset('voertuig', plate)
    if not vehicle:
        raise LookupError('Dit kenteken is niet gevonden in de openbare RDW-registratie.', 404)
    sections = {'voertuig': vehicle}
    warnings = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs = {pool.submit(fetch_dataset, key, plate): key for key in DATASETS if key != 'voertuig'}
        for job in as_completed(jobs):
            key = jobs[job]
            try:
                sections[key] = job.result()
            except LookupError as exc:
                sections[key] = None
                warnings.append(str(exc))
    result = {'plate': plate, 'sections': sections, 'warnings': warnings, 'fetched_at': time.time(), 'cached': False,
              'sources': {key: {'label': label, 'url': f'https://opendata.rdw.nl/d/{dataset}'} for key, (dataset, label) in DATASETS.items()}}
    # Incomplete responses are not cached, so retry can recover missing sections.
    if not warnings:
        with database() as db:
            db.execute('INSERT OR REPLACE INTO cache VALUES (?, ?, ?)', (plate, result['fetched_at'], json.dumps(result)))
            db.execute('DELETE FROM cache WHERE fetched < ?', (time.time() - 7 * 86400,))
    return result

def application(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    status = 200
    headers = [('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'same-origin'),
               ('Content-Security-Policy', "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'")]
    content_type = 'application/json; charset=utf-8'
    try:
        if method not in ('GET', 'HEAD'):
            raise LookupError('Methode niet toegestaan.', 405)
        if path == '/health':
            body = b'{"status":"ok","version":"0.1.0"}'
        elif path.startswith('/api/vehicle/'):
            query = parse_qs(environ.get('QUERY_STRING', ''))
            result = lookup(path.removeprefix('/api/vehicle/'), query.get('refresh') == ['1'])
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
