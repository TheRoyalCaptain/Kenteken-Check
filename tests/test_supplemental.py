import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs,urlparse
import app
import supplemental as extra

class SupplementalTests(unittest.TestCase):
    def test_default_missing_sources_make_no_calls(self):
        with patch.object(extra,'get') as remote:
            sections,reasons,warnings=extra.fetch_all({}, {'voertuig':[],'terugroepstatus':[]})
        remote.assert_not_called()
        self.assertEqual(set(sections),set(extra.SOURCES))
        self.assertTrue(all(value==[] for value in sections.values()))
        self.assertEqual(warnings,[])
        self.assertIn('Niet ingeschakeld',reasons['eu_registraties'])

    def test_selection_validation(self):
        self.assertEqual(extra.context({'model_slug':'vw-golf','eea_enabled':True}),{'model_slug':'vw-golf','eea_enabled':True})
        for value in [{'vin':'ABC'},{'model_slug':'../bad'},{'eea_enabled':'true'},{'model_slug':None}]:
            with self.assertRaises(ValueError): extra.context(value)

    def test_eea_disabled_makes_no_transfer(self):
        vehicle={'typegoedkeuringsnummer':'e1*1*1*01','variant':'TEST','uitvoering':'TEST'}
        with patch.object(extra,'fetch_eu') as remote:
            extra.fetch_all({}, {'voertuig':[vehicle],'terugroepstatus':[]})
        remote.assert_not_called()

    def test_eea_exact_codes_and_pagination(self):
        vehicle={'typegoedkeuringsnummer':"e1*'x",'variant':'VAR','uitvoering':'VERSION'}
        record={'TAN':"e1*'x",'Va':'VAR','Ve':'VERSION','Year':2021,'MS':'NL','unknown':None}
        nonmatch={**record,'Ve':'OTHER'}
        with patch.object(extra,'get',side_effect=[{'results':[record]*1000},{'results':[record,nonmatch]}]) as remote:
            rows,reason=extra.fetch_eu(vehicle)
        self.assertEqual(len(rows),1001)
        query=parse_qs(urlparse(remote.call_args_list[0].args[0]).query)
        self.assertIn("[TAN] = 'e1*''x'",query['query'][0])
        self.assertNotIn('kenteken',query['query'][0])
        self.assertEqual(parse_qs(urlparse(remote.call_args_list[1].args[0]).query)['p'],['2'])
        self.assertIsNone(rows[0]['unknown'])

    def test_eea_no_approximate_approval(self):
        vehicle={'typegoedkeuringsnummer':'e1*1*1*01','variant':'A','uitvoering':'B'}
        with patch.object(extra,'get',return_value={'results':[{'TAN':'e1*1*1','Va':'A','Ve':'B'}]}):
            self.assertEqual(extra.fetch_eu(vehicle)[0],[])
        with patch.object(extra,'get') as remote:
            self.assertEqual(extra.fetch_eu({'typegoedkeuringsnummer':'e1*1*1*01'})[0],[])
        remote.assert_not_called()

    def test_eea_sql_error_is_failure(self):
        with patch.object(extra,'get',return_value={'errors':[{'error':'missing dataset'}]}):
            with self.assertRaises(extra.SourceError):extra.fetch_eu({'typegoedkeuringsnummer':'X','variant':'Y','uitvoering':'Z'})

    def test_recall_reference_and_complete_nested_data(self):
        record={'referentiecode':'MGP123','bron':'Teruggeroepen.nl','licentie':'credit','modellen':[{'type':'TEST'}]}
        with patch.object(extra,'get',return_value=record) as remote:
            rows,reason=extra.fetch_recalls({'terugroepstatus':[{'referentiecode_rdw':'MGP123'}]})
        self.assertEqual(rows,[record])
        self.assertTrue(remote.call_args.args[0].endswith('/auto/MGP123'))
        with patch.object(extra,'get',return_value={'referentiecode':'OTHER'}):
            with self.assertRaises(extra.SourceError):extra.fetch_recalls({'terugroepstatus':[{'referentiecode_rdw':'MGP123'}]})

    def test_recall_404_and_outage_distinct(self):
        error=extra.SourceError('missing');error.__cause__=HTTPError('https://www.teruggeroepen.nl',404,'missing',None,None)
        with patch.object(extra,'get',side_effect=error):
            self.assertEqual(extra.fetch_recalls({'terugroepstatus':[{'referentiecode_rdw':'MGP123'}]})[0],[])
        with self.assertRaises(extra.SourceError):extra.fetch_recalls({'terugroepstatus':None})

    def test_model_brand_validation_and_meta(self):
        dataset={'meta':{'license':'CC BY 4.0','generated':'2026-07-18'},'models':[{'slug':'test','merk':'Volkswagen','model':'Golf','generatie':'VII','specs':{'power':123}}]}
        with patch.object(extra,'catalog',return_value=dataset):
            rows,reason=extra.fetch_model({'model_slug':'test'},{'merk':'VOLKSWAGEN'})
            self.assertEqual(rows[0]['catalogus_meta'],dataset['meta'])
            self.assertEqual(extra.model_options('VOLKSWAGEN')[0]['value'],'test')
            self.assertEqual(extra.fetch_model({'model_slug':'test'},{'merk':'FORD'})[0],[])
            self.assertEqual(extra.fetch_model({'model_slug':'deleted'},{'merk':'VOLKSWAGEN'})[0],[])

    def test_context_sources_are_not_individual_history(self):
        before={'eu_registraties':[{'id':1}],'voertuig':[{'apk':'old'}]}
        after={'eu_registraties':[{'id':2}],'voertuig':[{'apk':'new'}]}
        self.assertEqual([row['source'] for row in app.changes_between(before,after)],['voertuig'])

    def test_remote_timeout(self):
        with patch.object(extra,'urlopen',side_effect=URLError('timeout')):
            with self.assertRaises(extra.SourceError):extra.get('https://www.teruggeroepen.nl/api/v1/bronnen')

    def test_selection_persistence_cache_and_clear(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(app,'DATA',Path(directory)),patch.dict(app.os.environ,{'KENTEKEN_API_KEY':''}),patch.object(app,'fetch_dataset',return_value=[]),patch.object(extra,'fetch_all',return_value=({}, {}, [])) as remote:
            selection={'model_slug':'test'}
            self.assertEqual(app.lookup('AB123C',selection=selection)['selection'],selection)
            self.assertTrue(app.lookup('AB123C')['cached'])
            self.assertEqual(remote.call_count,1)
            self.assertEqual(app.lookup('AB123C',selection={})['selection'],{})
            self.assertEqual(remote.call_count,2)
            self.assertEqual(app.history('AB123C',True)['observations'][0]['data']['selection'],selection)

    def test_metadata_only_dutch_european(self):
        self.assertEqual({row['provider'] for row in extra.metadata().values()},{'European Environment Agency (EEA)','Teruggeroepen.nl','autoseeker.eu'})
