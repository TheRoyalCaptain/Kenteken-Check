"""Public European model reports and local, user supplied PDF documents."""
import hashlib
import html
import json
import re
import threading
import time
import uuid
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

class ReportError(Exception):pass

PROVIDERS={
 'eu_euroncap':{'label':'Euro NCAP · veiligheidsrapport','provider':'Euro NCAP','url':'https://www.euroncap.com/assessments/','host':'www.euroncap.com','prefix':'/assessments/'},
 'eu_greenncap':{'label':'Green NCAP · milieurapport','provider':'Green NCAP','url':'https://www.greenncap.com/assessments/','host':'www.greenncap.com','prefix':'/assessments/'},
 'eu_adac':{'label':'ADAC · modeltest','provider':'ADAC','url':'https://www.adac.de/rund-ums-fahrzeug/autokatalog/autotest/','host':'www.adac.de','prefix':'/rund-ums-fahrzeug/autokatalog/marken-modelle/'},
}
def metadata():
 return {key:{**{k:v for k,v in row.items() if k in ('label','provider','url')},'scope':'extern','fields':{},'note':'Door jou gekoppeld modelrapport. Controleer generatie, motor en uitrusting in het originele rapport. Geen historie of bewezen eigenschappen van dit kenteken. Bron behoudt auteursrechten; originele rapporten worden niet gekopieerd.'} for key,row in PROVIDERS.items()}

def valid_url(key,url):
 try:
  p=urlparse(url);row=PROVIDERS[key]
  return len(url)<1000 and p.scheme=='https' and p.hostname==row['host'] and p.port in (None,443) and not p.username and not p.password and p.path.startswith(row['prefix']) and p.path.rstrip('/')!=row['prefix'].rstrip('/') and not p.query and not p.fragment and not any(x in p.path for x in ('..','%','\\'))
 except (ValueError,KeyError,TypeError):return False

def validate_selection(value):
 if not isinstance(value,dict) or len(value)>3 or any(not valid_url(key,url) for key,url in value.items()):raise ValueError('Gebruik een directe HTTPS-modelrapportlink van Euro NCAP, Green NCAP of ADAC.')
 return value

class Page(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.title='';self.in_title=False;self.links=[];self.anchor=None;self.meta={};self.headings=[];self.heading=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='title':self.in_title=True
  if tag=='meta' and a.get('content'):self.meta[a.get('property',a.get('name',''))]=a['content']
  if tag=='a':self.anchor={'url':a.get('href',''),'parts':[]}
  if tag=='h1':self.heading=[]
 def handle_data(self,data):
  if self.in_title:self.title+=data
  if self.anchor is not None:self.anchor['parts'].append(data)
  if self.heading is not None:self.heading.append(data)
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
  if tag=='a' and self.anchor is not None:
   self.links.append({'url':self.anchor['url'],'title':clean(' '.join(self.anchor['parts']))});self.anchor=None
  if tag=='h1' and self.heading is not None:self.headings.append(clean(' '.join(self.heading)));self.heading=None

def clean(value):return ' '.join(html.unescape(value).split())
def tokens(value):return re.findall(r'\w+',clean(value).casefold())
def contains(value,phrase):
 a,b=tokens(value),tokens(phrase)
 return bool(b) and any(a[i:i+len(b)]==b for i in range(len(a)-len(b)+1))
def identity_matches(title,make,model):
 value=tokens(title)
 for prefix in (['green','ncap','assessment','of','the'],['euro','ncap'],['adac','autotest'],['autotest']):
  if value[:len(prefix)]==prefix:value=value[len(prefix):];break
 base=tokens(model)
 return bool(base) and any(value[:len(tokens(name))+1]==tokens(name)+base[:1] for name in names(make))

def euro_facts(raw):
 # Read only factual summary fields from the page's public Next.js data.
 for script in re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")',raw):
  try:decoded=json.loads(script)
  except ValueError:continue
  marker='"safetyPerformance":';start=decoded.find(marker)
  if start<0:continue
  try:record,_=json.JSONDecoder().raw_decode(decoded[start+len(marker):].lstrip())
  except ValueError:continue
  result={key:record[key] for key in ('testedModel','ratingYear','nicePublicationDate','starRating') if key in record}
  for key in ('adultOccupant','childOccupant','vulnerableRoadUsers','safetyAssist'):
   if isinstance(record.get(key),dict) and 'normalisedScore' in record[key]:result[key+'_percent']=record[key]['normalisedScore']
  return result
 return {}

def names(make):return [make,'VW'] if make.casefold()=='volkswagen' else [make]

def read(url):
 try:
  with urlopen(Request(url,headers={'User-Agent':'KentekenCheck/0.7.0 (+https://github.com/TheRoyalCaptain/Kenteken-Check)','Accept':'text/html,application/xml'}),timeout=12) as response:
   # Do not follow a provider redirect to an unrelated host.
   if urlparse(response.url).hostname!=urlparse(url).hostname:raise ValueError('External redirect')
   raw=response.read(8_000_001)
  if len(raw)>8_000_000:raise ValueError('Too large')
  return raw.decode('utf-8')
 except (HTTPError,URLError,OSError,TimeoutError,ValueError) as exc:raise ReportError('Rapportbron kon niet worden opgehaald. Probeer later opnieuw.') from exc

_cache={};_lock=threading.Lock()
def cached(url):
 with _lock:
  entry=_cache.get(url)
  if entry and time.time()-entry[0]<86400:return entry[1]
 result=read(url)
 with _lock:_cache[url]=(time.time(),result)
 return result

def catalog(key,make,model):
 row=PROVIDERS[key]
 if key=='eu_euroncap':
  data=cached('https://www.euroncap.com/sitemap.xml')
  urls=re.findall(r'<loc>([^<]+)</loc>',data)
  # The public sitemap may be an index. Only follow official sitemap children.
  children=[u for u in urls if urlparse(u).hostname==row['host'] and urlparse(u).path.endswith('.xml')]
  if children:
   urls=[]
   for child in children:urls.extend(re.findall(r'<loc>([^<]+)</loc>',cached(child)))
  entries=[{'url':u,'title':' · '.join(urlparse(u).path.strip('/').split('/')[1:])} for u in urls if valid_url(key,u)]
 else:
  page=Page();page.feed(cached(row['url']))
  entries=[{**link,'url':urljoin(row['url'],link['url'])} for link in page.links]
 base=tokens(model)
 if not base:return []
 # Candidate list only; the user checks generation/engine before attaching a report.
 result={}
 for item in entries:
  if valid_url(key,item['url']) and item['title'] and identity_matches(item['title'],make,model):result[item['url']]=item
 return sorted(result.values(),key=lambda item:item['title'].casefold())

def fetch(key,url,vehicle):
 if not url:return [],'Geen modelrapport gekozen. Kies een kandidaat of plak een directe rapportlink bij Rapporten.'
 if not valid_url(key,url):raise ReportError('Ongeldige rapportlink.')
 raw=cached(url);page=Page();page.feed(raw);title=clean(page.meta.get('og:title') or page.title)
 make,model=vehicle.get('merk',''),vehicle.get('handelsbenaming','')
 base=tokens(model)
 if not make or not base:return [],'RDW-merk of model ontbreekt; rapport kan niet worden gecontroleerd.'
 if not identity_matches(title,make,model):return [],'Rapporttitel komt niet overeen met het RDW-merk en de modelfamilie. Kies een ander rapport.'
 pdfs=[]
 for link in page.links:
  target=urljoin(url,link['url']);p=urlparse(target)
  if p.scheme=='https' and p.hostname in (PROVIDERS[key]['host'],'cdn.euroncap.com','assets.adac.de') and p.path.lower().endswith('.pdf') and not p.username and not p.password:
   pdfs.append({'title':link['title'][:150] or 'Origineel PDF-rapport','url':target})
 return [{'title':title,'url':url,'provider':PROVIDERS[key]['provider'],'description':clean(page.meta.get('description',''))[:500],'test_summary':euro_facts(raw) if key=='eu_euroncap' else {}, 'pdf_reports':list({p['url']:p for p in pdfs}.values()),'applicability':'Door gebruiker gekoppeld op modelfamilie; generatie, motor en veiligheidsuitrusting moeten in het originele rapport gecontroleerd worden. Geen individuele voertuighistorie.'}], 'Gekozen openbaar modelrapport opgehaald; toepassing op de exacte uitvoering blijft door jou te controleren.'

MAX_PDF=6*1024*1024

def folder(directory,plate):
 if not re.fullmatch(r'(?:[A-Z0-9]{6}|[A-HJ-NPR-Z0-9]{17})',plate):raise ValueError('Ongeldig kenteken.')
 return Path(directory)/'reports'/plate

def documents(directory,plate):
 root=folder(directory,plate)
 if not root.exists():return []
 return sorted([json.loads(p.read_text()) for p in root.glob('*.json')],key=lambda row:row['uploaded_at'],reverse=True)

def save_document(directory,plate,name,data):
 if not isinstance(name,str) or not name.lower().endswith('.pdf') or len(name)>180:raise ValueError('Selecteer een PDF met een geldige bestandsnaam.')
 if not data.startswith(b'%PDF-') or len(data)>MAX_PDF:raise ValueError('Gebruik een PDF van maximaal 6 MB.')
 root=folder(directory,plate);root.mkdir(parents=True,exist_ok=True)
 if len(list(root.glob('*.json')))>=30:raise ValueError('Maximaal 30 rapporten per kenteken. Verwijder eerst een rapport.')
 ident=uuid.uuid4().hex;name=Path(name.replace('\\','/')).name
 row={'id':ident,'name':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'uploaded_at':int(time.time()),'url':f'/api/report-file/{plate}/{ident}','provenance':'Door gebruiker toegevoegd; inhoud niet als geverifieerde voertuighistorie geïnterpreteerd.'}
 (root/(ident+'.pdf')).write_bytes(data);(root/(ident+'.json')).write_text(json.dumps(row,ensure_ascii=False));return row

def document(directory,plate,ident,delete=False):
 if not re.fullmatch(r'[a-f0-9]{32}',ident):raise FileNotFoundError('Rapport niet gevonden.')
 root=folder(directory,plate);meta=root/(ident+'.json');pdf=root/(ident+'.pdf')
 if not meta.exists() or not pdf.exists():raise FileNotFoundError('Rapport niet gevonden.')
 row=json.loads(meta.read_text())
 if delete:meta.unlink();pdf.unlink();return row
 return row,pdf.read_bytes()
