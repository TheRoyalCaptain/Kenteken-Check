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
        self.env_patcher = patch.dict(app.os.environ, {'KENTEKEN_API_KEY': ''})
        self.env_patcher.start()
    def tearDown(self):
        self.env_patcher.stop()
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
    def test_missing_base_still_shows_other_sources(self):
        def fetch(key,plate):return [{'kenteken':plate,'referentiecode_rdw':'TEST'}] if key=='keuringen' else []
        with patch.object(app,'fetch_dataset',side_effect=fetch):
            result=app.lookup('AB123C')
        self.assertEqual(result['source_status']['voertuig']['status'],'unavailable')
        self.assertEqual(result['source_status']['keuringen']['status'],'available')

    def test_cache_and_refresh(self):
        def fetch(key,plate):return [{'kenteken':plate,'merk':'TEST'}] if key=='voertuig' else []
        with patch.object(app,'fetch_dataset',side_effect=fetch) as mock:
            self.assertFalse(app.lookup('AB123C')['cached'])
            self.assertEqual(mock.call_count,14)
            self.assertTrue(app.lookup('AB123C')['cached'])
            self.assertEqual(mock.call_count,14)
            self.assertFalse(app.lookup('AB123C',True)['cached'])
            self.assertEqual(mock.call_count,28)
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
            self.assertEqual(mock.call_count,28)
    def test_outage_status_visible(self):
        with patch.object(app,'fetch_dataset',side_effect=app.LookupError('RDW niet bereikbaar')):
            (status,headers),body=self.request('/api/vehicle/AB123C')
        self.assertTrue(status.startswith('200'))
        self.assertEqual(json.loads(body)['source_status']['voertuig']['status'],'error')
        self.assertIn('RDW',json.loads(body)['warnings'][0])

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
        self.assertEqual(result['schema_version'], 3)
        self.assertEqual(mock.call_count, 14)

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

    def test_pagination_continues_beyond_5000(self):
        import io
        pages = [io.BytesIO(json.dumps([{}]*1000).encode()) for _ in range(6)] + [io.BytesIO(b'[]')]
        with patch.object(app,'urlopen',side_effect=pages):
            rows = app.fetch_dataset('keuringen','AB123C')
        self.assertEqual(len(rows),6000)

    def test_related_empty_codes_skip_network(self):
        with patch.object(app,'fetch_rows') as mock:
            self.assertEqual(app.fetch_related('terugroepdetails','referentiecode_rdw',[]),[])
        mock.assert_not_called()

    def test_query_literals_are_escaped(self):
        with patch.object(app,'fetch_rows',return_value=[]) as mock:
            app.fetch_related('terugroepdetails','referentiecode_rdw',["code'x"])
        self.assertEqual(mock.call_args[0][2]['$where'], "referentiecode_rdw in ('code''x')")

    def test_source_status_distinguishes_empty_and_outage(self):
        statuses = app.source_statuses({'empty': [], 'failed': None, 'present': [{'value': 0}]}, {})
        self.assertEqual(statuses['empty']['status'],'unavailable')
        self.assertEqual(statuses['failed']['status'],'error')
        self.assertEqual(statuses['present']['status'],'available')

    def test_no_key_external_does_not_call_network(self):
        with patch.object(app,'urlopen') as mock:
            rows,reason=app.fetch_external('extern_voertuig','AB123C')
        self.assertEqual(rows,[])
        self.assertIn('API-sleutel',reason)
        mock.assert_not_called()

    def test_external_preserves_nested_payload(self):
        import io
        payload={'kenteken':'AB123C','historie':[{'date':'2020-01-01','nested':{'value':None}}]}
        with patch.dict(app.os.environ,{'KENTEKEN_API_KEY':'test_key'}), patch.object(app,'urlopen',return_value=io.BytesIO(json.dumps(payload).encode())):
            rows,reason=app.fetch_external('extern_voertuig','AB123C')
        self.assertEqual(rows,[payload])
        self.assertIsNone(reason)

    def test_approval_exact_variant_and_execution(self):
        with patch.object(app,'fetch_rows',return_value=[]) as mock:
            app.fetch_approval('tgk_4by9_ammk', {'typegoedkeuringsnummer':'e1*test*00','variant':'VAR','uitvoering':'EXEC'})
        params=mock.call_args[0][2]
        self.assertEqual(params['typegoedkeuringsnummer'],'e1*test*00')
        self.assertEqual(params['codevarianttgk'],'VAR')
        self.assertEqual(params['codeuitvoeringtgk'],'EXEC')

    def test_approval_does_not_guess_when_variant_missing(self):
        with patch.object(app,'fetch_rows') as mock:
            rows,reason=app.fetch_approval('tgk_4by9_ammk', {'typegoedkeuringsnummer':'e1*test*00'})
        self.assertEqual(rows,[])
        self.assertIn('ontbreekt',reason)
        mock.assert_not_called()

    def test_history_preserves_changes_and_deduplicates(self):
        result={'plate':'AB123C','fetched_at':1000,'sections':{'voertuig':[{'apk':'20260101'}]},'sources':{}}
        app.remember(result)
        result['fetched_at']=1100
        app.remember(result)
        self.assertEqual(len(app.history('AB123C')['observations']),1)
        result['sections']['voertuig'][0]['apk']='20270101'
        result['fetched_at']=1200
        app.remember(result)
        history=app.history('AB123C',True)
        self.assertEqual(len(history['observations']),2)
        self.assertEqual(history['observations'][1]['changes'][0]['before'][0]['apk'],'20260101')
        self.assertEqual(history['observations'][1]['data']['sections']['voertuig'][0]['apk'],'20270101')

    def test_history_outages_are_not_vehicle_changes(self):
        self.assertEqual(app.changes_between({'brandstof':[{'vermogen':100}]},{'brandstof':None}),[])
        self.assertEqual(app.changes_between({'brandstof':None},{'brandstof':[{'vermogen':100}]}),[])

    def test_legacy_snapshot_is_not_imported_twice(self):
        old={'plate':'AB123C','fetched_at':1000,'sections':{'voertuig':[{'a':1}]},'sources':{}}
        newer={'plate':'AB123C','fetched_at':1200,'sections':{'voertuig':[{'a':2}]},'sources':{}}
        app.remember(old)
        app.remember(newer)
        app.remember(old)
        self.assertEqual(len(app.history('AB123C')['observations']),2)

    def test_history_row_reordering_is_not_a_change(self):
        self.assertEqual(app.changes_between({'data':[{'a':1},{'a':2}]},{'data':[{'a':2},{'a':1}]}),[])

    def test_metadata_covers_all_32_official_datasets(self):
        self.assertEqual(len(app.ALL_RDW),32)
        expected={r['id'] for r in app.CATALOG['datasets']}
        self.assertEqual({r[0] for r in app.ALL_RDW.values()},expected)

    def test_snapshot_keeps_original_dates_urls_and_empty_values(self):
        original={'datum_dt':'2026-01-01T12:34:56.000','api_link':'https://example.test','empty':'','null':None}
        app.remember({'plate':'AB123C','fetched_at':1000,'sections':{'voertuig':[original]},'sources':{}})
        stored=app.history('AB123C',True)['observations'][0]['data']['sections']['voertuig'][0]
        self.assertEqual(stored,original)

if __name__=='__main__':unittest.main()
