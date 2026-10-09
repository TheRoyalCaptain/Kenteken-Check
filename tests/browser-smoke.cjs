// Browser-level checks of the user flows, using controlled RDW responses.
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');
const port = 8081;
const server = spawn(process.env.PYTHON || 'python', ['-c', `from wsgiref.simple_server import make_server; import app; make_server('127.0.0.1',${port},app.application).serve_forever()`], {cwd:path.join(__dirname,'..'),stdio:'ignore'});
const sources = Object.fromEntries(['voertuig','brandstof','assen','carrosserie','carrosserie_specifiek','voertuigklasse','keuringen','gebreken','objecten','terugroepstatus','gebrekbeschrijvingen','terugroepdetails'].map(key=>[key,{label:key,url:'https://opendata.rdw.nl'}]));
const selections=new Map();
const photoId='a'.repeat(64);
function fixture(plate) {return {plate,schema_version:3,fetched_at:Date.now()/1000,cached:false,warnings:[],sources,sections:{
  voertuig:[{kenteken:plate,merk:'VOLKSWAGEN',handelsbenaming:'GOLF GTE',inrichting:'hatchback',eerste_kleur:'BLAUW',datum_eerste_toelating:'20210611',datum_eerste_tenaamstelling_in_nederland:'20220611',vervaldatum_apk:'20270611',massa_rijklaar:'1624',maximum_trekken_massa_geremd:'1500',tellerstandoordeel:'Logisch',wam_verzekerd:'Ja',openstaande_terugroepactie_indicator:'Ja',aantal_zitplaatsen:'5',cilinderinhoud:'1395',catalogusprijs:'43000',datum_eerste_toelating_dt:'2021-06-11T12:34:56.000',api_gekentekende_voertuigen_brandstof:'https://opendata.rdw.nl/resource/8ys7-d773.json',lege_waarde:'',null_waarde:null}],
  brandstof:[{brandstof_omschrijving:'Benzine',nettomaximumvermogen:'110',brandstofverbruik_gecombineerd_wltp:'5.5'},{brandstof_omschrijving:'Elektriciteit',nettomaximumvermogen:'80',actie_radius_extern_opladen_wltp:'62'}],
  assen:[{as_nummer:'1',spoorbreedte:'153'}],carrosserie:[],carrosserie_specifiek:[],voertuigklasse:[],objecten:[],
  keuringen:[{meld_datum_door_keuringsinstantie:'20250611',soort_erkenning_omschrijving:'APK Lichte voertuigen',soort_melding_ki_omschrijving:'periodieke controle'}],
  gebreken:[{meld_datum_door_keuringsinstantie:'20250611',gebrek_identificatie:'RA1',gebrek_omschrijving:'Waarschuwingsinrichting airbag geeft defect',aantal_gebreken_geconstateerd:'1'}],
  gebrekbeschrijvingen:[],terugroepstatus:[{referentiecode_rdw:'MGP123',status:'Producent heeft herstel gemeld'}],terugroepdetails:[{referentiecode_rdw:'MGP123',omschrijving_defect:'Voorbeelddefect',beschrijving_van_het_herstel:'Vervang het onderdeel'}]
}};}
(async()=>{
 let browser;
 try {
  for(let i=0;i<50;i++){try{await fetch(`http://127.0.0.1:${port}/health`);break;}catch{await new Promise(r=>setTimeout(r,100));}}
  browser=await chromium.launch({headless:true,...(process.env.KC_CHROME?{executablePath:process.env.KC_CHROME,args:['--no-sandbox','--disable-dev-shm-usage']}:{} )});
  const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/vehicle/**',async route=>{
   const url=new URL(route.request().url()),plate=decodeURIComponent(url.pathname.split('/').at(-1)).replace(/[-\s]/g,'').toUpperCase();
   if(plate==='XXXXXX')return route.fulfill({status:404,contentType:'application/json',body:JSON.stringify({error:'Niet gevonden'})});
   const data=fixture(plate);
   if(url.searchParams.has('selection'))selections.set(plate,JSON.parse(url.searchParams.get('selection')));
   data.selection=selections.get(plate)||{};
   data.sources={...data.sources,eu_registraties:{label:'Europese registraties',scope:'extern',provider:'European Environment Agency (EEA)',note:'Europese context, geen individuele historie.',url:'https://www.eea.europa.eu'},nl_teruggeroepen:{label:'Nederlandse terugroepinformatie',scope:'extern',provider:'Teruggeroepen.nl',note:'Gekoppelde RDW-referentie',url:'https://www.teruggeroepen.nl'},eu_model:{label:'Europese modelspecificaties',scope:'extern',provider:'autoseeker.eu',licence:'CC BY 4.0',note:'Indicatieve Europese modelinformatie',url:'https://autoseeker.eu/data/'}};
   data.sources.modelfotos={label:'Voorbeeldfoto’s',scope:'extern',url:'https://commons.wikimedia.org'};
   data.sections.modelfotos=plate==='CD456E'?[]:[{id:photoId,image_url:'/api/photo/'+photoId,make:'VOLKSWAGEN',model:'GOLF GTE',color:'BLAUW',artist:'Voorbeeldauteur',licence:'CC BY-SA 4.0',licence_url:'https://creativecommons.org/licenses/by-sa/4.0/',file_url:'https://commons.wikimedia.org/wiki/File:Test.jpg'}];
   data.source_status={modelfotos:{status:data.sections.modelfotos.length?'available':'unavailable',row_count:data.sections.modelfotos.length,reason:data.sections.modelfotos.length?'Voorbeeldfoto gevonden.':'Geen passende foto beschikbaar.'}};
   data.sections.nl_teruggeroepen=[{referentiecode:'MGP123',defect:'Nederlands voorbeelddefect'}];
   data.sections.eu_model=data.selection.model_slug?[{catalogus_meta:{license:'CC BY 4.0'},model:{slug:data.selection.model_slug,generatie:'VII facelift',specs:{kofferbak_liter:272}}}]:[];
   data.sections.eu_registraties=data.selection.eea_enabled?Array.from({length:60},(_,i)=>({ID:i+1,MS:'NL',Year:2021,Ewltp:123})):[];
   if(plate==='CD456E'){data.sections.brandstof=null;data.sections.gebreken=[];data.sections.terugroepstatus=[];data.sections.terugroepdetails=[];data.warnings=['Brandstof kon niet worden opgehaald.'];}
   await route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
  });
  await page.route('**/api/eu-models?*',route=>route.fulfill({contentType:'application/json',body:JSON.stringify([{value:'volkswagen-golf7-gte-2018',text:'Volkswagen · Golf GTE · VII facelift'}])}));
  await page.route('**/api/photo/**',route=>route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aE1sAAAAASUVORK5CYII=','base64')}));
  await page.goto(`http://127.0.0.1:${port}`);
  await page.fill('#plate','AB-123-C');await page.click('#submit');await page.waitForSelector('#result:not([hidden])');
  assert.equal(await page.locator('#vehicle-title').textContent(),'VOLKSWAGEN GOLF GTE');
  assert.equal(await page.locator('.stat').count(),8);
  await page.locator('#vehicle-photos img').waitFor();await page.waitForFunction(()=>document.querySelector('#vehicle-photos img').naturalWidth>0);
  assert((await page.locator('#vehicle-photos').textContent()).includes('Voorbeeldauteur'));
  await page.click('#tab-fotos');assert((await page.locator('#details').textContent()).includes('CC BY-SA 4.0'));
  await page.route('**/api/photo/**',route=>route.fulfill({status:503,body:'unavailable'}));await page.click('#tab-overzicht');await page.click('#tab-fotos');await page.locator('#details .photo-card img').evaluate(img=>img.src+='?failure=1');await page.getByText('Foto tijdelijk niet beschikbaar.',{exact:true}).waitFor();await page.unroute('**/api/photo/**');await page.route('**/api/photo/**',route=>route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aE1sAAAAASUVORK5CYII=','base64')}));

  await page.click('#favorite');assert.equal(await page.locator('#favorite').textContent(),'★ Bewaard');
  await page.click('#tab-energie');assert((await page.locator('#details').textContent()).includes('62 km'));
  assert((await page.locator('#details').textContent()).includes('ca. 150 pk'));
  await page.click('#tab-keuringen');assert((await page.locator('#details').textContent()).includes('Waarschuwingsinrichting airbag'));
  await page.click('#tab-recalls');await page.locator('.record summary').click();assert(await page.getByText('Vervang het onderdeel',{exact:true}).isVisible());
  await page.fill('#field-query','airbag');assert((await page.locator('#details').textContent()).includes('Waarschuwingsinrichting'));
  await page.fill('#field-query','zzzznotfound');assert((await page.locator('#details').textContent()).includes('Geen gegevens gevonden'));
  await page.click('#tab-alle');assert((await page.locator('#details').textContent()).includes('2021-06-11T12:34:56.000'));assert((await page.locator('#details').textContent()).includes('https://opendata.rdw.nl/resource/8ys7-d773.json'));assert((await page.locator('#details').textContent()).includes('(lege waarde)'));assert((await page.locator('#details').textContent()).includes('null'));
  await page.click('#tab-bronnen');assert((await page.locator('#details').textContent()).includes('Niet beschikbaar'));
  await page.click('#tab-historie');assert((await page.locator('#details').textContent()).includes('Gebrek geconstateerd'));
  await page.click('#tab-aanvullend');await page.waitForFunction(()=>!document.querySelector('#eu-model').disabled);
  await page.selectOption('#eu-model','volkswagen-golf7-gte-2018');await page.getByRole('button',{name:'Modelgegevens ophalen',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#tab-aanvullend')?.getAttribute('aria-selected')==='true'&&document.querySelector('#details').textContent.includes('kofferbak_liter'));
  await page.waitForFunction(()=>document.querySelector('#eu-model')?.value==='volkswagen-golf7-gte-2018'&&!document.querySelector('#eu-model').disabled);
  assert.equal(await page.locator('#eea-enabled').isChecked(),false);
  await page.check('#eea-enabled');await page.getByRole('button',{name:'EEA-keuze opslaan',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#tab-aanvullend')?.getAttribute('aria-selected')==='true'&&document.querySelector('#details').textContent.includes('50/60 zichtbaar'));
  await page.getByRole('button',{name:'Toon volgende 10 records · 50/60 zichtbaar',exact:true}).click();
  assert((await page.locator('#details').textContent()).includes('Record 60'));
  if(process.env.KC_SCREENSHOTS){fs.mkdirSync(process.env.KC_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.KC_SCREENSHOTS,'eu-desktop.png'),fullPage:true});await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(process.env.KC_SCREENSHOTS,'eu-mobile.png'),fullPage:true});await page.setViewportSize({width:1280,height:900});}
  await page.getByRole('button',{name:'Modelselectie verwijderen',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#eu-model')?.value===''&&!document.querySelector('#eu-model').disabled&&document.querySelector('#tab-aanvullend')?.getAttribute('aria-selected')==='true'&&!document.querySelector('#details').textContent.includes('kofferbak_liter'));
  assert.equal(await page.locator('#eea-enabled').isChecked(),true);
  await page.click('#tab-overzicht');await page.click('#compare');
  const screenshots=process.env.KC_SCREENSHOTS;
  if(screenshots){fs.mkdirSync(screenshots,{recursive:true});await page.screenshot({path:path.join(screenshots,'desktop.png'),fullPage:true});}
  await page.fill('#plate','CD456E');await page.click('#submit');await page.waitForFunction(()=>document.querySelector('#result-plate').textContent==='CD456E');
  assert((await page.locator('#alerts').textContent()).includes('Brandstof kon niet'));assert((await page.locator('#vehicle-photos').textContent()).includes('Geen passende foto beschikbaar'));assert.equal(await page.locator('#vehicle-photos img').count(),0);
  await page.click('#tab-energie');assert((await page.locator('#details').textContent()).includes('Deze bron kon niet'));
  await page.click('#tab-recalls');assert((await page.locator('#details').textContent()).includes('Geen terugroepstatussen'));
  await page.click('#compare');assert((await page.locator('#comparison-content').textContent()).includes('AB123C'));
  assert((await page.locator('#comparison-content').textContent()).includes('CD456E'));
  await page.reload();await page.locator('#garage summary').click();assert((await page.locator('#favorites').textContent()).includes('AB123C'));
  await page.locator('#favorites button').first().click();await page.waitForSelector('#result:not([hidden])');
  for(const width of [390,320]){await page.setViewportSize({width,height:844});for(const [key]of [['overzicht'],['fotos'],['techniek'],['energie'],['keuringen'],['recalls'],['extra'],['aanvullend'],['historie'],['bronnen'],['alle']]){await page.click('#tab-'+key);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Overflow at ${width} in ${key}`);}}
  await page.click('#tab-overzicht');await page.setViewportSize({width:390,height:844});if(screenshots)await page.screenshot({path:path.join(screenshots,'mobile.png'),fullPage:true});
  await page.locator('.export-menu summary').click();const download=page.waitForEvent('download');await page.click('#export');assert.equal((await download).suggestedFilename(),'kenteken-AB123C.json');
  await page.fill('#plate','XXXXXX');await page.click('#submit');await page.waitForSelector('#message.error');assert.equal(await page.locator('#result').isVisible(),false);
  assert.deepEqual(errors,[]);console.log('Browser checks passed: European model selection, EEA opt-in and record pagination, tabs, data search, two fuels, recall details, empty/error states, favorites persistence, comparison, export, 320px/390px layout.');
 }finally{if(browser)await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
