"""Licensed Commons example photos, matched by source metadata, never by plate."""
import hashlib
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

class PhotoError(Exception):
    pass

COLORS = {'BLAUW':('blue','blauw','blau','bleu'), 'ROOD':('red','rood','rot','rouge'),
          'WIT':('white','wit','weiß','weiss','blanc'), 'ZWART':('black','zwart','schwarz','noir'),
          'GRIJS':('grey','gray','grijs','grau','gris'), 'GROEN':('green','groen','grün','gruen','vert'),
          'GEEL':('yellow','geel','gelb','jaune'), 'ORANJE':('orange','oranje'),
          'BRUIN':('brown','bruin','braun','marron'), 'BEIGE':('beige',), 'PAARS':('purple','paars','violet'),
          'ROSE':('pink','rose','roze'), 'ROZE':('pink','rose','roze')}
MATCH_VERSION = 2
GENERATION_PATTERN = r'\b(?:VIII|VII|VI|IV|III|II|IX|V|I|X|[A-Z][0-9]{2,3})\b'

SOURCE = {'label':'Voorbeeldfoto’s · model en kleur','provider':'Wikimedia Commons','url':'https://commons.wikimedia.org',
          'scope':'extern','fields':{},'note':'Voorbeeldauto, geen foto van dit kenteken. Model en kleur zijn gematcht op bronmetadata; Generatie moet expliciet gekozen zijn en in de fotometadata overeenkomen; exacte lak en overige details blijven onbevestigd. Auteur en licentie staan bij elke foto.'}

def text(value):
    return html.unescape(re.sub(r'<[^>]*>', '', str(value))).strip()

def words(value):
    return re.findall(r'\w+', text(value).casefold())

def contains(value, phrase):
    haystack, needle = words(value), words(phrase)
    return any(haystack[i:i+len(needle)] == needle for i in range(len(haystack)-len(needle)+1)) if needle else False

def safe_url(value, hosts):
    if not isinstance(value,str): return False
    try:
        parsed=urlparse(value); port=parsed.port
    except ValueError:return False
    return parsed.scheme=='https' and parsed.hostname in hosts and not parsed.username and not parsed.password and port in (None,443)

def request(url, limit):
    try:
        with urlopen(Request(url,headers={'User-Agent':'KentekenCheck/0.7.0 (https://github.com/TheRoyalCaptain/Kenteken-Check)','Accept':'application/json, image/jpeg, image/png, image/webp'}),timeout=12) as response:
            data=response.read(limit+1);mime=response.headers.get_content_type()
        if len(data)>limit: raise ValueError('Response too large')
        return data,mime
    except (HTTPError,URLError,OSError,TimeoutError,ValueError) as exc:
        raise PhotoError('De fotobron kon niet worden opgehaald. Probeer later opnieuw.') from exc

def read_json(url):
    raw,_=request(url,4_000_000)
    try:return json.loads(raw)
    except ValueError as exc:raise PhotoError('De fotobron leverde een ongeldig antwoord.') from exc

def match(page, make, model, color, generation=''):
    info=(page.get('imageinfo') or [{}])[0];meta=info.get('extmetadata',{})
    values=lambda key:text(meta.get(key,{}).get('value',''))
    # Match individual labels, never assemble a vehicle identity from unrelated categories.
    labels=[page.get('title',''),values('ImageDescription'),values('ObjectName')]
    labels += [row.get('title','') for row in page.get('categories',[])]
    labels += values('Categories').split('|')
    identity=' '.join(labels[:3])
    make_names=[make]
    if make.upper()=='VOLKSWAGEN':make_names.append('VW')
    if not generation:return None
    requested=re.search(GENERATION_PATTERN,generation)
    if not requested:return None
    code=requested.group(0)
    candidates=[]
    for label in labels:
        if not any(contains(label,name) for name in make_names):continue
        stripped=re.sub(GENERATION_PATTERN,' ',text(label))
        if not contains(stripped,model):continue
        codes=set(re.findall(GENERATION_PATTERN,text(label)))
        # A comparison or contradictory metadata must not confirm a generation.
        if codes and codes != {code}:return None
        if codes=={code}:candidates.append(label)
    if not candidates:return None
    if contains(generation,'facelift') and not any(contains(label,'facelift') for label in candidates):return None
    if any(contains(label,'facelift') for label in candidates) and not contains(generation,'facelift'):return None
    if not any(contains(label,term) for label in labels for term in COLORS[color]):return None
    if any(contains(identity,term) for term in ('interior','dashboard','engine','wheel','interieur','motorraum')):return None
    licence=values('LicenseShortName');licence_url=meta.get('LicenseUrl',{}).get('value','')
    accepted=licence in ('CC0','Public domain','Public Domain','CC0 1.0') or bool(re.fullmatch(r'CC BY(?:-SA)? [1-4]\.0',licence))
    if not accepted or values('Restrictions'):return None
    if licence_url and not safe_url(licence_url,{'creativecommons.org'}):return None
    artist=values('Artist')
    if not artist:return None
    thumbnail=info.get('thumburl') or info.get('url')
    file_url=info.get('descriptionurl')
    if info.get('mime') not in ('image/jpeg','image/png','image/webp'):return None
    if not safe_url(thumbnail,{'upload.wikimedia.org','thumb.wikimedia.org'}) or not safe_url(file_url,{'commons.wikimedia.org'}):return None
    ident=hashlib.sha256(thumbnail.encode()).hexdigest()
    return {'id':ident,'image_url':'/api/photo/'+ident,'thumbnail_source_url':thumbnail,'file_url':file_url,
            'title':text(page.get('title','')).removeprefix('File:'),'description':values('ImageDescription'),
            'artist':artist,'credit':values('Credit'),'licence':licence,'licence_url':licence_url,
            'make':make,'model':model,'color':color,'generation_match':generation,'match_version':MATCH_VERSION,
            'match_basis':'Merk, volledig model, gekozen generatie en kleur in bronmetadata; geen visuele verificatie of individuele voertuigidentificatie.',
            'original_metadata':meta,'source_categories':page.get('categories',[])}

def find(vehicle, model_rows, directory):
    make,model,color=(str(vehicle.get(key,'')).strip() for key in ('merk','handelsbenaming','eerste_kleur'))
    if not make or not model or color not in COLORS:return [],'Merk, model of een bruikbare RDW-kleur ontbreekt; geen passende foto beschikbaar.'
    if len(make)>100 or len(model)>100:return [],'Modelnaam is niet bruikbaar voor fotozoeken.'
    if not model_rows:return [],'Foto niet beschikbaar: kies eerst het juiste model en de generatie bij Aanvullende bronnen.'
    selected=model_rows[0].get('model',{})
    if str(selected.get('merk','')).strip().casefold()!=make.casefold() or not contains(model,selected.get('model','')):
        return [],'Foto niet beschikbaar: het gekozen model komt niet overeen met het RDW-model.'
    generation=str(selected.get('generatie','')).strip()
    if not re.search(GENERATION_PATTERN,generation):
        return [],'Foto niet beschikbaar: de gekozen generatie heeft geen ondersteunde generatiecode voor een betrouwbare fotomatch.'
    terms=(MATCH_VERSION,make,model,color,generation)
    folder=Path(directory)/'photos';folder.mkdir(parents=True,exist_ok=True)
    cache=folder/('query-'+hashlib.sha256(json.dumps(terms).encode()).hexdigest()+'.json')
    if cache.exists():
        saved=json.loads(cache.read_text())
        if time.time()-saved['fetched_at']<86400:return saved['rows'],saved['reason']
    search=' '.join([make,model,generation,COLORS[color][0]])
    params={'action':'query','generator':'search','gsrsearch':search,'gsrnamespace':6,'gsrlimit':8,
            'prop':'imageinfo|categories','cllimit':'max','iiprop':'url|extmetadata|mime','iiurlwidth':960,'format':'json'}
    data=read_json('https://commons.wikimedia.org/w/api.php?'+urlencode(params))
    if not isinstance(data,dict) or 'error' in data:raise PhotoError('De fotobron leverde een foutantwoord.')
    pages=data.get('query',{}).get('pages',{})
    if not isinstance(pages,dict):raise PhotoError('De fotobron leverde een onverwacht antwoord.')
    rows=[]
    for page in sorted(pages.values(),key=lambda row:row.get('index',999)):
        row=match(page,make,model,color,generation)
        if row and row['id'] not in {r['id'] for r in rows}:
            rows.append(row)
            target=folder/(row['id']+'.json');target.write_text(json.dumps(row,ensure_ascii=False))
        if len(rows)==4:break
    reason='Voorbeeldfoto’s met overeenkomend model, gekozen generatie en kleur in de bronmetadata gevonden.' if rows else 'Geen herbruikbare foto met dit model, de gekozen generatie en deze kleur in de gecontroleerde zoekresultaten gevonden. Er wordt geen andere kleur ingevuld.'
    temp=cache.with_name(cache.stem+'-'+str(time.time_ns())+'.tmp');temp.write_text(json.dumps({'fetched_at':time.time(),'rows':rows,'reason':reason},ensure_ascii=False));temp.replace(cache)
    return rows,reason

def media(ident,directory):
    if not re.fullmatch(r'[a-f0-9]{64}',ident):raise FileNotFoundError('Ongeldige foto.')
    folder=Path(directory)/'photos';metadata=folder/(ident+'.json')
    if not metadata.is_file():raise FileNotFoundError('Foto niet gevonden.')
    image=folder/(ident+'.bin');mime_file=folder/(ident+'.mime')
    if image.is_file() and mime_file.is_file():return image.read_bytes(),mime_file.read_text()
    row=json.loads(metadata.read_text());url=row.get('thumbnail_source_url')
    if not safe_url(url,{'upload.wikimedia.org','thumb.wikimedia.org'}):raise PhotoError('Ongeldige fotobron.')
    data,mime=request(url,8_000_000)
    if mime not in ('image/jpeg','image/png','image/webp'):raise PhotoError('De bron leverde geen ondersteunde foto.')
    # Store only complete downloads. Shared-worker writes use unique temporary names.
    temporary=folder/(ident+'-'+str(time.time_ns())+'.tmp');temporary.write_bytes(data);temporary.replace(image)
    mime_file.write_text(mime)
    return data,mime
