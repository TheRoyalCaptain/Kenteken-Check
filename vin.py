"""VIN structure checks and an explicitly enabled European decoder adapter."""
import hashlib
import json
import os
import re
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

class VinError(Exception):pass
SOURCES={
 'vin_structuur':{'label':'VIN · structuurcontrole','provider':'Lokale controle','scope':'vin','fields':{},'url':'https://eur-lex.europa.eu/eli/reg_impl/2021/535/oj','note':'Controle van invoer en posities; geen bewijs dat het voertuig bestaat of dat fabrikant/model zijn bevestigd.'},
 'vin_decoder':{'label':'VIN · Europese decoder','provider':'Vincario / vindecoder.eu','scope':'vin','fields':{},'url':'https://vincario.com/api-docs/3.2/','note':'Optionele leveranciersgegevens. Eigen API-sleutels en expliciet inschakelen vereist. Proefquota of betaald tegoed, geen onbeperkte gratis bron.'},
 'vin_rdw':{'label':'VIN · Nederlandse registratie','provider':'RDW Open Data','scope':'vin','fields':{},'url':'https://opendata.rdw.nl','note':'Geen openbare VIN-naar-kentekenkoppeling aangesloten. VIN en kenteken worden niet op een vergelijkbaar model gekoppeld.'},
}
UNAVAILABLE={
 'vin_schade':('Schadehistorie','Geen geautoriseerde schadehistoriebron op VIN aangesloten.'),
 'vin_onderhoud':('Onderhoudshistorie','Geen openbare onderhoudshistoriebron op VIN aangesloten. Eigen dealeruitdraai kan bij Rapporten worden bewaard.'),
 'vin_kilometers':('Kilometerhistorie','Geen openbare kilometerhistoriebron op VIN aangesloten.'),
 'vin_diefstal':('Diefstalcontrole','Geen geautoriseerde diefstalregistercontrole aangesloten; dit resultaat zegt niet dat de auto niet gestolen is.'),
 'vin_eigenaren':('Eigenaarshistorie','Geen openbare volledige eigenaarshistoriebron op VIN aangesloten.'),
 'vin_recalls':('Individuele terugroepstatus','Geen VIN-specifieke fabrikantcontrole aangesloten; modelacties zijn geen individuele herstelstatus.'),
}
for key,(title,reason) in UNAVAILABLE.items():SOURCES[key]={'label':title,'provider':'Beschikbaarheid VIN-historie','scope':'historie','fields':{},'url':'','note':reason}

def normalize(value):
 if not isinstance(value,str):raise ValueError('Vul een VIN/chassisnummer van 17 tekens in.')
 value=re.sub(r'\s','',value).upper()
 if not re.fullmatch(r'[A-HJ-NPR-Z0-9]{17}',value):raise ValueError('Een modern VIN heeft 17 letters/cijfers, zonder I, O of Q. Oude kortere chassisnummers worden nog niet ondersteund.')
 return value

def structure(value):
 value=normalize(value)
 return {'vin':value,'formaat':'17 toegestane letters/cijfers','wmi':value[:3],'posities_4_8':value[3:8],'positie_9':value[8],'vis_posities_10_17':value[9:],'positie_10':value[9],'positie_11':value[10],'laatste_vier_numeriek':value[-4:].isdigit(),'interpretatie':'Positie 10/11 en controlecijfer worden niet universeel als modeljaar/fabriek/geldigheid uitgelegd. Dit vereist fabrikant- en bouwjaarcontext. De WMI-code is niet in een fabrikantregister geverifieerd.'}

def configured():return bool(os.environ.get('VINCARIO_API_KEY') and os.environ.get('VINCARIO_SECRET_KEY'))

def decode(value,enabled=False):
 value=normalize(value)
 if not enabled:return [],'Niet ingeschakeld. Uitgebreide VIN-decodering vereist eigen sleutels en kan leveranciersquota of betaald tegoed gebruiken.'
 if not configured():return [],'Niet beschikbaar: VINCARIO_API_KEY en VINCARIO_SECRET_KEY ontbreken op de server.'
 key=os.environ['VINCARIO_API_KEY'];secret=os.environ['VINCARIO_SECRET_KEY']
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',key):raise VinError('De VIN-providerconfiguratie is ongeldig.')
 control=hashlib.sha1(f'{value}|decode|{key}|{secret}'.encode()).hexdigest()[:10]
 url=f'https://api.vindecoder.eu/3.2/{key}/{control}/decode/{value}.json'
 try:
  with urlopen(Request(url,headers={'Accept':'application/json','User-Agent':'KentekenCheck/0.7.0'}),timeout=12) as response:
   if response.url!=url:raise ValueError('Unexpected redirect')
   raw=response.read(4_000_001)
  if len(raw)>4_000_000:raise ValueError('Too large')
  data=json.loads(raw)
  if not isinstance(data,dict) or data.get('error'):raise ValueError('Provider error')
  if data.get('vin')!=value:raise ValueError('VIN mismatch')
  if not isinstance(data.get('decode'),list) or not all(isinstance(row,dict) for row in data['decode']):raise ValueError('Unexpected decoder response')
  return ([data],'Alle ontvangen leveranciersvelden; geen gegarandeerde volledige historie.') if data['decode'] else ([], 'De leverancier leverde geen decodeergegevens voor dit VIN.')
 except (HTTPError,URLError,OSError,TimeoutError,ValueError) as exc:raise VinError('VIN-provider kon geen geldig resultaat leveren. Controleer toegang/tegoed of probeer later opnieuw.') from exc

def vehicle(rows):
 if not rows:return []
 fields={row.get('label'):row.get('value') for row in rows[0].get('decode',[]) if isinstance(row.get('value'),(str,int,float))}
 record={target:fields[label] for label,target in [('Make','merk'),('Model','handelsbenaming'),('Body','inrichting')] if fields.get(label)}
 return [record] if record else []
