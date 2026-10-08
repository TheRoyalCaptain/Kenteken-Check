import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
import app

class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patcher = patch.object(app, 'DATA', Path(self.temp.name))
        self.patcher.start()
    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()
    def request(self, path, method='GET'):
        statuses=[]
        body=b''.join(app.application({'PATH_INFO':path,'REQUEST_METHOD':method,'QUERY_STRING':''},lambda s,h:statuses.append((s,h))))
        return statuses[0], body
    def test_normalize_and_reject_injection(self):
        self.assertEqual(app.normalize(' ab-123-c '),'AB123C')
        for invalid in ['ABCDEF','123456',"AB123C'",'../../app.py','AB123C?x=1','']:
            with self.assertRaises(app.LookupError):app.normalize(invalid)
    def test_missing_not_cached(self):
        with patch.object(app,'fetch_dataset',return_value=[]):
            with self.assertRaises(app.LookupError) as exc:app.lookup('AB123C')
        self.assertEqual(exc.exception.status,404)
    def test_cache_and_refresh(self):
        def fetch(key,plate):return [{'kenteken':plate,'merk':'TEST'}] if key=='voertuig' else []
        with patch.object(app,'fetch_dataset',side_effect=fetch) as mock:
            self.assertFalse(app.lookup('AB123C')['cached'])
            self.assertEqual(mock.call_count,6)
            self.assertTrue(app.lookup('AB123C')['cached'])
            self.assertEqual(mock.call_count,6)
            self.assertFalse(app.lookup('AB123C',True)['cached'])
            self.assertEqual(mock.call_count,12)
    def test_partial_failure_explicit_and_retryable(self):
        def fetch(key,plate):
            if key=='brandstof':raise app.LookupError('Brandstof niet bereikbaar')
            return [{'kenteken':plate}] if key=='voertuig' else []
        with patch.object(app,'fetch_dataset',side_effect=fetch) as mock:
            result=app.lookup('AB123C')
            self.assertIsNone(result['sections']['brandstof'])
            self.assertEqual(result['sections']['assen'],[])
            self.assertTrue(result['warnings'])
            app.lookup('AB123C')
            self.assertEqual(mock.call_count,12)
    def test_outage_not_reported_as_not_found(self):
        with patch.object(app,'fetch_dataset',side_effect=app.LookupError('RDW niet bereikbaar')):
            (status,headers),body=self.request('/api/vehicle/AB123C')
        self.assertTrue(status.startswith('503'))
        self.assertIn('RDW',json.loads(body)['error'])
    def test_remote_timeout(self):
        with patch.object(app,'urlopen',side_effect=URLError('timeout')):
            with self.assertRaises(app.LookupError):app.fetch_dataset('voertuig','AB123C')
    def test_static_traversal_and_methods(self):
        for path in ['/app.py','/static/../app.py','/static/../../etc/passwd']:
            self.assertTrue(self.request(path)[0][0].startswith('404'))
        self.assertTrue(self.request('/health','POST')[0][0].startswith('405'))
    def test_static_and_health(self):
        self.assertTrue(self.request('/')[0][0].startswith('200'))
        self.assertIn(b'Kenteken Check',self.request('/')[1])
        self.assertEqual(json.loads(self.request('/health')[1])['status'],'ok')
        self.assertEqual(self.request('/','HEAD')[1],b'')

if __name__=='__main__':unittest.main()
