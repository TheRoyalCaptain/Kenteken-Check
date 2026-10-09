"""Persistent daily monitor; one leased job at a time, safe across restarts."""
import time
import accounts
import app

def run_once(now=None):
    job = accounts.claim(app.DATA, now)
    if not job: return False
    token = app.CURRENT_USER.set(job['user_id'])
    try:
        # Only Dutch plates can be monitored. VIN providers may charge per request.
        plate = app.normalize(job['plate'])
        result = app.lookup(plate, refresh=True)
        error = 'Een of meer bronnen waren onbereikbaar. De laatste goede versie is behouden.' if result['warnings'] else ''
    except Exception:
        error = 'Controle mislukt. De laatste goede versie is behouden; er volgt een nieuwe poging.'
    finally:
        app.CURRENT_USER.reset(token)
    accounts.finish(app.DATA, job, error, now)
    return True

if __name__ == '__main__':
    while True:
        try:
            for _ in range(20):
                if not run_once(): break
        except Exception:
            pass  # No credentials, URLs or user payloads in worker logs.
        time.sleep(60)
