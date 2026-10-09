import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import app
import vin
import reports

VIN='WVWZZZCDZMW123456'
class VinTests(unittest.TestCase):
 def test_normalize_and_invalid_inputs(self):
  self.assertEqual(vin.normalize(' wvwzzzcdzmw123456 '),VIN)
  for value in ('123','I'+VIN[1:],'O'+VIN[1:],'Q'+VIN[1:],VIN+'X',VIN[:-1]+'-',None):
   with self.assertRaises(ValueError):vin.normalize(value)
 def test_structure_does_not_invent_year_or_manufacturer(self):
  row=vin.structure(VIN);self.assertEqual(row['wmi'],'WVW');self.assertEqual(row['vis_posities_10_17'],VIN[9:]);self.assertTrue(row['laatste_vier_numeriek']);self.assertNotIn('merk',row);self.assertNotIn('modeljaar',row)
 def test_disabled_or_missing_key_makes_no_request(self):
  with patch.dict(vin.os.environ,{'VINCARIO_API_KEY':'','VINCARIO_SECRET_KEY':''}),patch('vin.urlopen') as remote:
   self.assertEqual(vin.decode(VIN)[0],[]);self.assertEqual(vin.decode(VIN,True)[0],[]);remote.assert_not_called()
  with patch.dict(vin.os.environ,{'VINCARIO_API_KEY':'test','VINCARIO_SECRET_KEY':'secret'}),patch('vin.urlopen') as remote:
   vin.decode(VIN);remote.assert_not_called()
 def test_provider_signature_complete_data_and_exact_vin(self):
  import hashlib
  data={'vin':VIN,'decode':[{'label':'Make','value':'Volkswagen'},{'label':'Model','value':'Golf'},{'label':'unknown','value':{'nested':None}}],'remaining':4}
  url=f'https://api.vindecoder.eu/3.2/test/{hashlib.sha1((VIN+"|decode|test|secret").encode()).hexdigest()[:10]}/decode/{VIN}.json'
  response=io.BytesIO(json.dumps(data).encode());response.url=url
  with patch.dict(vin.os.environ,{'VINCARIO_API_KEY':'test','VINCARIO_SECRET_KEY':'secret'}),patch('vin.urlopen',return_value=response) as remote:
   rows,_=vin.decode(VIN,True);self.assertEqual(rows,[data]);self.assertEqual(remote.call_args.args[0].full_url,url);self.assertEqual(vin.vehicle(rows)[0]['merk'],'Volkswagen')
 def test_provider_error_and_mismatched_vin(self):
  import hashlib
  url=f'https://api.vindecoder.eu/3.2/test/{hashlib.sha1((VIN+"|decode|test|secret").encode()).hexdigest()[:10]}/decode/{VIN}.json'
  for data in ({'error':'no credit'},{'vin':'OTHER','decode':[]},{'vin':VIN,'decode':'bad'}):
   response=io.BytesIO(json.dumps(data).encode());response.url=url
   with patch.dict(vin.os.environ,{'VINCARIO_API_KEY':'test','VINCARIO_SECRET_KEY':'secret'}),patch('vin.urlopen',return_value=response):
    with self.assertRaises(vin.VinError):vin.decode(VIN,True)
 def test_lookup_cache_preferences_history_and_no_rdw_guess(self):
  with tempfile.TemporaryDirectory() as root,patch.object(app,'DATA',Path(root)),patch.dict(vin.os.environ,{'VINCARIO_API_KEY':'','VINCARIO_SECRET_KEY':''}),patch('app.fetch_dataset') as rdw,patch('vin.urlopen') as remote:
   first=app.lookup_vin(VIN);self.assertEqual(first['lookup_type'],'vin');self.assertEqual(first['source_status']['vin_decoder']['status'],'unavailable');self.assertEqual(first['source_status']['vin_structuur']['status'],'available');self.assertTrue(app.lookup_vin(VIN)['cached']);self.assertFalse(app.lookup_vin(VIN,True)['cached']);rdw.assert_not_called();remote.assert_not_called();self.assertEqual(len(app.history(VIN)['observations']),1)
   self.assertTrue(app.lookup_vin(VIN,selection={'vin_decode_enabled':True})['selection']['vin_decode_enabled']);self.assertTrue(app.lookup_vin(VIN)['selection']['vin_decode_enabled']);self.assertEqual(app.history(VIN,True)['observations'][0]['data']['sections']['vin_structuur'][0]['vin'],VIN)
 def test_provider_failure_retains_local_results_and_is_not_cached(self):
  with tempfile.TemporaryDirectory() as root,patch.object(app,'DATA',Path(root)),patch('vin.decode',side_effect=vin.VinError('provider error')):
   data=app.lookup_vin(VIN,selection={'vin_decode_enabled':True});self.assertEqual(data['source_status']['vin_decoder']['status'],'error');self.assertTrue(data['sections']['vin_structuur']);self.assertFalse(app.lookup_vin(VIN)['cached'])
 def test_pdf_documents_support_vin_without_plate_association(self):
  with tempfile.TemporaryDirectory() as root:
   row=reports.save_document(root,VIN,'vin.pdf',b'%PDF-1.7 test');self.assertEqual(len(reports.documents(root,VIN)),1);self.assertEqual(reports.documents(root,'AB123C'),[]);reports.document(root,VIN,row['id'],True)
 def test_vin_route_and_invalid_preferences(self):
  with tempfile.TemporaryDirectory() as root,patch.object(app,'DATA',Path(root)),patch.dict(vin.os.environ,{'VINCARIO_API_KEY':'','VINCARIO_SECRET_KEY':''}):
   statuses=[];raw=b''.join(app._application({'PATH_INFO':'/api/vin/'+VIN,'REQUEST_METHOD':'GET','QUERY_STRING':''},lambda s,h:statuses.append(s)));self.assertEqual(statuses,['200 OK']);self.assertEqual(json.loads(raw)['vin'],VIN)
   for selection in ({'vin_decode_enabled':'true'},{'eea_enabled':True},[],None):
    if selection is None:continue
    with self.assertRaises(app.LookupError):app.lookup_vin(VIN,selection=selection)
