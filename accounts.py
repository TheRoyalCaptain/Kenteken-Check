"""Account database, hashed passwords and revocable opaque sessions."""
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlparse

HASH_LOCK = threading.Lock()
SESSION_SECONDS = 12 * 3600
IDLE_SECONDS = 30 * 60

class AccountError(Exception):
    def __init__(self, message, status=400):
        self.status = status
        super().__init__(message)

@contextmanager
def database(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(root / 'platform.sqlite', timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires REAL NOT NULL, seen REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts (key TEXT PRIMARY KEY, start REAL NOT NULL, count INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS favorites (user_id INTEGER NOT NULL REFERENCES users(id), plate TEXT NOT NULL, watch INTEGER NOT NULL, next_due REAL NOT NULL, lease REAL NOT NULL DEFAULT 0, checked REAL, error TEXT NOT NULL DEFAULT '', PRIMARY KEY(user_id,plate));
        CREATE TABLE IF NOT EXISTS preferences (user_id INTEGER NOT NULL REFERENCES users(id), key TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(user_id,key));
    ''')
    os.chmod(root / 'platform.sqlite', 0o600)
    try:
        with db: yield db
    finally: db.close()

def username(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_.-]{3,40}', value):
        raise AccountError('Gebruik 3–40 letters, cijfers, punten, streepjes of underscores voor je gebruikersnaam.')
    return value.lower()

def password_hash(password):
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        raise AccountError('Gebruik een wachtwoord van 12 tot 128 tekens.')
    salt = secrets.token_bytes(16)
    with HASH_LOCK:
        digest = hashlib.scrypt(password.encode(), salt=salt, n=2**17, r=8, p=1, maxmem=192*1024*1024, dklen=64)
    return 'scrypt$131072$8$1$' + salt.hex() + '$' + digest.hex()

def verify(password, encoded):
    if not isinstance(password, str) or len(password) > 128: return False
    try:
        algorithm, n, r, p, salt, expected = encoded.split('$')
        if (algorithm,n,r,p) != ('scrypt','131072','8','1'): return False
        with HASH_LOCK:
            digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**17, r=8, p=1, maxmem=192*1024*1024, dklen=64)
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError): return False

DUMMY_HASH = password_hash(secrets.token_urlsafe(24))

def public(user):
    return {key:user[key] for key in ('id','username','role','active')}

def token_hash(token): return hashlib.sha256(token.encode()).hexdigest()
def csrf(token): return hmac.new(token.encode(), b'kenteken-check-csrf', hashlib.sha256).hexdigest()

def session(root, environ):
    cookie = SimpleCookie()
    try: cookie.load(environ.get('HTTP_COOKIE', '')); token = cookie['kc_session'].value
    except Exception: return None, ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', token): return None, ''
    now = time.time()
    with database(root) as db:
        user = db.execute('SELECT users.*, sessions.expires, sessions.seen FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.hash=?', (token_hash(token),)).fetchone()
        if not user or not user['active'] or user['expires'] <= now or user['seen'] + IDLE_SECONDS <= now:
            db.execute('DELETE FROM sessions WHERE hash=?', (token_hash(token),)); return None, ''
        db.execute('UPDATE sessions SET seen=? WHERE hash=?', (now, token_hash(token)))
    return public(user), token

def issue_in_db(db, user):
    token = secrets.token_urlsafe(32); now = time.time()
    db.execute('DELETE FROM sessions WHERE expires<? OR seen<?', (now, now-IDLE_SECONDS))
    db.execute('INSERT INTO sessions VALUES (?,?,?,?)', (token_hash(token), user['id'], now+SESSION_SECONDS, now))
    return token

def issue(root, user, expected_hash=None):
    with database(root) as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone()
        if not row or not row['active'] or (expected_hash is not None and row['password_hash']!=expected_hash):raise AccountError('Accountgegevens veranderd. Log opnieuw in.',401)
        return issue_in_db(db,user)

def cookie(token, environ):
    secure = os.environ.get('SESSION_COOKIE_SECURE', 'auto')
    use_secure = secure == 'true' or (secure == 'auto' and (environ.get('wsgi.url_scheme') == 'https' or environ.get('HTTP_X_FORWARDED_PROTO') == 'https'))
    return 'kc_session='+token+'; Path=/; HttpOnly; SameSite=Lax; Max-Age='+str(SESSION_SECONDS if token else 0)+('; Secure' if use_secure else '')

def origin(environ):
    if environ.get('HTTP_SEC_FETCH_SITE') == 'cross-site': raise AccountError('Ongeldige aanvraagherkomst.', 403)
    if environ.get('HTTP_ORIGIN') and urlparse(environ['HTTP_ORIGIN']).netloc != environ.get('HTTP_HOST'):
        raise AccountError('Ongeldige aanvraagherkomst.', 403)

def throttle(root, key, maximum):
    now = time.time()
    with database(root) as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM attempts WHERE start<?', (now-900,))
        row = db.execute('SELECT count FROM attempts WHERE key=?', (key,)).fetchone()
        if row and row[0] >= maximum: raise AccountError('Te veel pogingen. Probeer over 15 minuten opnieuw.', 429)
        db.execute('INSERT INTO attempts VALUES (?,?,1) ON CONFLICT(key) DO UPDATE SET count=count+1', (key,now))

def create(root, name, password, role='user', setup=False, adopt=None):
    name = username(name)
    if role not in ('user','admin'): raise AccountError('Ongeldige rol.')
    encoded = password_hash(password)
    try:
        with database(root) as db:
            db.execute('BEGIN IMMEDIATE')
            if setup and db.execute('SELECT 1 FROM users LIMIT 1').fetchone(): raise AccountError('De eerste beheerder is al ingesteld.', 409)
            ident = db.execute('INSERT INTO users (username,password_hash,role,created) VALUES (?,?,?,?)', (name,encoded,role,time.time())).lastrowid
            if setup and adopt: adopt(ident)
            user = db.execute('SELECT * FROM users WHERE id=?', (ident,)).fetchone()
        return public(user)
    except sqlite3.IntegrityError as exc: raise AccountError('Deze gebruikersnaam bestaat al.', 409) from exc

def login(root, name, password, remote):
    name = str(name).lower()[:40]
    throttle(root, 'ip:'+remote, 50); throttle(root, 'user:'+name, 10)
    with database(root) as db: user = db.execute('SELECT * FROM users WHERE username=?', (name,)).fetchone()
    ok = verify(password, user['password_hash'] if user else DUMMY_HASH)
    if not user or not user['active'] or not ok: raise AccountError('Gebruikersnaam of wachtwoord klopt niet.', 401)
    with database(root) as db:
        db.execute('BEGIN IMMEDIATE')
        current=db.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone()
        if not current or not current['active'] or current['password_hash']!=user['password_hash']:raise AccountError('Gebruikersnaam of wachtwoord klopt niet.',401)
        db.execute('DELETE FROM attempts WHERE key=?', ('user:'+name,))
        token=issue_in_db(db,current)
    return public(user),token

def change_password(root, ident, password, old=None):
    with database(root) as db: row = db.execute('SELECT * FROM users WHERE id=?', (ident,)).fetchone()
    if not row: raise AccountError('Gebruiker niet gevonden.', 404)
    if old is not None and not verify(old,row['password_hash']): raise AccountError('Huidig wachtwoord klopt niet.', 400)
    encoded = password_hash(password)
    with database(root) as db:
        db.execute('BEGIN IMMEDIATE')
        current=db.execute('SELECT password_hash FROM users WHERE id=?',(ident,)).fetchone()
        if old is not None and current['password_hash']!=row['password_hash']:raise AccountError('Accountgegevens veranderd. Probeer opnieuw.',409)
        db.execute('UPDATE users SET password_hash=? WHERE id=?', (encoded,ident)); db.execute('DELETE FROM sessions WHERE user_id=?', (ident,))
    return encoded

def favorites(root, ident):
    with database(root) as db:
        rows = db.execute('SELECT plate,watch,next_due,checked,error FROM favorites WHERE user_id=? ORDER BY plate', (ident,)).fetchall()
    return [dict(row) for row in rows]

def favorite(root, ident, plate, watch=None, delete=False):
    with database(root) as db:
        if delete: db.execute('DELETE FROM favorites WHERE user_id=? AND plate=?', (ident,plate))
        else:
            count = db.execute('SELECT count(*) FROM favorites WHERE user_id=?', (ident,)).fetchone()[0]
            if count >= 50 and not db.execute('SELECT 1 FROM favorites WHERE user_id=? AND plate=?',(ident,plate)).fetchone(): raise AccountError('Maximaal 50 opgeslagen voertuigen per gebruiker.')
            db.execute('INSERT INTO favorites (user_id,plate,watch,next_due) VALUES (?,?,?,?) ON CONFLICT(user_id,plate) DO UPDATE SET watch=excluded.watch', (ident,plate,int(bool(watch)),time.time()+86400))
    return favorites(root,ident)

def preferences(root, ident, key=None, value=None):
    with database(root) as db:
        if key is not None: db.execute('INSERT OR REPLACE INTO preferences VALUES (?,?,?)', (ident,key,json.dumps(value)))
        return {row['key']:json.loads(row['value']) for row in db.execute('SELECT key,value FROM preferences WHERE user_id=?', (ident,))}

def claim(root, now=None):
    now = time.time() if now is None else now
    with database(root) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT favorites.* FROM favorites JOIN users ON users.id=favorites.user_id WHERE users.active=1 AND watch=1 AND next_due<=? AND lease<=? ORDER BY next_due LIMIT 1', (now,now)).fetchone()
        if row: db.execute('UPDATE favorites SET lease=? WHERE user_id=? AND plate=?', (now+1800,row['user_id'],row['plate']))
    return dict(row) if row else None

def finish(root, job, error='', now=None):
    now = time.time() if now is None else now
    with database(root) as db:
        db.execute('UPDATE favorites SET next_due=?,lease=0,checked=?,error=? WHERE user_id=? AND plate=?', (now+(3600 if error else 86400),now,error[:500],job['user_id'],job['plate']))
