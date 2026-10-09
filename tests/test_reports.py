import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import app
import reports
import supplemental

GREEN='https://www.greenncap.com/assessments/vw-golf-2021-0081/'
PAGE='<title>Green NCAP assessment of the VW Golf GTE 180 kW, 2021</title><meta name="description" content="Model test"><a href="https://www.greenncap.com/report.pdf">PDF report</a>'
class ReportTests(unittest.TestCase):
 def test_selection_allowlist(self):
  self.assertEqual(supplemental.context({'report_urls':{'eu_greenncap':GREEN}})['report_urls']['eu_greenncap'],GREEN)
  for url in ['http://www.greenncap.com/assessments/test/','https://example.com/assessments/test/','https://www.greenncap.com/assessments/','https://www.greenncap.com/assessments/../secret','https://www.greenncap.com/assessments/test/?next=https://example.com']:
   with self.assertRaises(ValueError):reports.validate_selection({'eu_greenncap':url})
 def test_unselected_makes_no_external_request(self):
  with patch('reports.read') as remote:
   self.assertEqual(reports.fetch('eu_greenncap','',{})[0],[]);remote.assert_not_called()
 def test_selected_report_preserves_pdf_and_provenance(self):
  with patch('reports.cached',return_value=PAGE):rows,_=reports.fetch('eu_greenncap',GREEN,{'merk':'VOLKSWAGEN','handelsbenaming':'GOLF GTE'})
  self.assertEqual(len(rows),1);self.assertEqual(len(rows[0]['pdf_reports']),1);self.assertIn('Door gebruiker',rows[0]['applicability'])
 def test_wrong_model_and_comparison_mentions_rejected(self):
  for title in ('Green NCAP assessment of the VW Polo 2021','Autotest Škoda Scala: Alternative zum VW Golf'):
   with patch('reports.cached',return_value='<title>'+title+'</title>'):
    self.assertEqual(reports.fetch('eu_greenncap',GREEN,{'merk':'VOLKSWAGEN','handelsbenaming':'GOLF GTE'})[0],[])
 def test_catalog_dedup_and_brand(self):
  source=f'<a href="{GREEN}">VW Golf GTE</a><a href="{GREEN}">VW Golf GTE</a><a href="https://www.greenncap.com/assessments/vw-polo-test/">VW Polo</a>'
  with patch('reports.cached',return_value=source):self.assertEqual(reports.catalog('eu_greenncap','VOLKSWAGEN','GOLF GTE'),[{'url':GREEN,'title':'VW Golf GTE'}])
 def test_euro_summary_is_test_scope(self):
  data={'safetyPerformance':{'testedModel':'VW Golf 1.5','ratingYear':2019,'starRating':5,'adultOccupant':{'normalisedScore':95}}}
  raw='self.__next_f.push([1,'+json.dumps(json.dumps(data))+'])'
  self.assertEqual(reports.euro_facts(raw)['adultOccupant_percent'],95)
 def test_context_report_not_individual_history(self):
  self.assertEqual(app.changes_between({'eu_euroncap':[{'x':1}]},{'eu_euroncap':[{'x':2}]}),[])
 def test_upload_download_delete_and_plate_isolation(self):
  with tempfile.TemporaryDirectory() as root:
   row=reports.save_document(root,'AB123C','report.pdf',b'%PDF-1.7 test')
   self.assertEqual(reports.documents(root,'CD456E'),[]);self.assertEqual(reports.document(root,'AB123C',row['id'])[1],b'%PDF-1.7 test')
   reports.document(root,'AB123C',row['id'],delete=True);self.assertEqual(reports.documents(root,'AB123C'),[])
 def test_invalid_upload_and_paths(self):
  with tempfile.TemporaryDirectory() as root:
   for name,data in [('x.html',b'%PDF-1.7'),('x.pdf',b'<html>'),('x.pdf',b'%PDF-'+b'x'*reports.MAX_PDF)]:
    with self.assertRaises(ValueError):reports.save_document(root,'AB123C',name,data)
   with self.assertRaises(FileNotFoundError):reports.document(root,'AB123C','../../secret')
 def test_wsgi_document_flow_and_cross_origin_rejection(self):
  def call(path,method='GET',body=None,origin=None):
   raw=json.dumps(body).encode() if body else b'';statuses=[]
   env={'PATH_INFO':path,'REQUEST_METHOD':method,'QUERY_STRING':'','CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(raw)),'wsgi.input':io.BytesIO(raw),'HTTP_HOST':'localhost'}
   if origin:env['HTTP_ORIGIN']=origin
   result=b''.join(app.application(env,lambda s,h:statuses.append((s,h))))
   return statuses[0],result
  with tempfile.TemporaryDirectory() as root,patch.object(app,'DATA',Path(root)):
   (status,_),body=call('/api/reports/AB123C','POST',{'name':'test.pdf','data':base64.b64encode(b'%PDF-1.7 test').decode()});self.assertEqual(status,'200 OK');row=json.loads(body)[0]
   (status,headers),body=call(row['url']);self.assertEqual(status,'200 OK');self.assertEqual(dict(headers)['Content-Type'],'application/pdf');self.assertEqual(body,b'%PDF-1.7 test')
   (status,_),_=call('/api/reports/AB123C','POST',{'name':'test.pdf','data':'abcd'},'https://foreign.example');self.assertEqual(status,'400 Bad Request')
   (status,_),body=call('/api/reports/AB123C/'+row['id'],'DELETE');self.assertEqual(status,'200 OK');self.assertEqual(json.loads(body),[])
