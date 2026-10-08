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
            self.assertEqual(mock.call_count,10)
            self.assertTrue(app.lookup('AB123C')['cached'])
            self.assertEqual(mock.call_count,10)
            self.assertFalse(app.lookup('AB123C',True)['cached'])
            self.assertEqual(mock.call_count,20)
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
            self.assertEqual(mock.call_count,20)
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

    def test_old_cache_is_refetched(self):
        with app.database() as db:
            db.execute('INSERT INTO cache VALUES (?, ?, ?)', ('AB123C', app.time.time(), json.dumps({'sections': {'voertuig': []}})))
        with patch.object(app, 'fetch_dataset', side_effect=lambda key, plate: [{'kenteken': plate}] if key == 'voertuig' else []) as mock:
            result = app.lookup('AB123C')
        self.assertEqual(result['schema_version'], 2)
        self.assertEqual(mock.call_count, 10)

    def test_missing_parent_does_not_claim_related_data_is_empty(self):
        sections = {'gebreken': None, 'terugroepstatus': None}
        with patch.object(app, 'fetch_related') as mock: app.enrich(sections, [])
        self.assertIsNone(sections['gebrekbeschrijvingen'])
        self.assertIsNone(sections['terugroepdetails'])
        mock.assert_not_called()

    def test_description_matches_historical_version(self):
        sections = {'gebreken': [{'gebrek_identificatie':'RA1', 'meld_datum_door_keuringsinstantie':'20200101'}], 'terugroepstatus': []}
        descriptions = [
            {'gebrek_identificatie':'RA1','ingangsdatum_gebrek':'20170101','einddatum_gebrek':'20210101','gebrek_omschrijving':'Historical'},
            {'gebrek_identificatie':'RA1','ingangsdatum_gebrek':'20210101','gebrek_omschrijving':'Current'}]
        with patch.object(app, 'fetch_related', side_effect=lambda key,field,codes: descriptions if key == 'gebrekbeschrijvingen' else []):
            app.enrich(sections, [])
        self.assertEqual(sections['gebreken'][0]['gebrek_omschrijving'], 'Historical')

    def test_recall_details_filtered_by_reference(self):
        sections = {'gebreken': [], 'terugroepstatus': [{'referentiecode_rdw':'MGP123'}]}
        with patch.object(app, 'fetch_related', return_value=[]) as mock:
            app.enrich(sections, [])
        self.assertIn(unittest.mock.call('terugroepdetails','referentiecode_rdw',['MGP123']), mock.call_args_list)

    def test_description_outage_preserves_defect_code(self):
        sections = {'gebreken': [{'gebrek_identificatie':'RA1'}], 'terugroepstatus': []}
        warnings = []
        def fetch(key,field,codes):
            if key == 'gebrekbeschrijvingen': raise app.LookupError('Unavailable descriptions')
            return []
        with patch.object(app, 'fetch_related', side_effect=fetch): app.enrich(sections,warnings)
        self.assertEqual(sections['gebreken'][0]['gebrek_identificatie'],'RA1')
        self.assertIsNone(sections['gebrekbeschrijvingen'])
        self.assertEqual(len(warnings),1)

    def test_pagination(self):
        import io
        first = [{'kenteken':'AB123C'}]*1000
        second = [{'kenteken':'AB123C'}]
        with patch.object(app,'urlopen',side_effect=[io.BytesIO(json.dumps(first).encode()),io.BytesIO(json.dumps(second).encode())]) as mock:
            rows = app.fetch_dataset('keuringen','AB123C')
        self.assertEqual(len(rows),1001)
        self.assertIn('%24offset=1000',mock.call_args_list[1][0][0].full_url)

    def test_no_silent_truncation(self):
        import io
        with patch.object(app,'urlopen',side_effect=lambda *a,**k:io.BytesIO(json.dumps([{}]*1000).encode())):
            with self.assertRaises(app.LookupError): app.fetch_dataset('keuringen','AB123C')

    def test_related_empty_codes_skip_network(self):
        with patch.object(app,'fetch_rows') as mock:
            self.assertEqual(app.fetch_related('terugroepdetails','referentiecode_rdw',[]),[])
        mock.assert_not_called()

    def test_query_literals_are_escaped(self):
        with patch.object(app,'fetch_rows',return_value=[]) as mock:
            app.fetch_related('terugroepdetails','referentiecode_rdw',["code'x"])
        self.assertEqual(mock.call_args[0][2]['$where'], "referentiecode_rdw in ('code''x')")

if __name__=='__main__':unittest.main()
