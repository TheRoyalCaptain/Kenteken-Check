'use strict';
const $ = id => document.getElementById(id);
function element(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (cls) n.className = cls;
  return n;
}
const LABELS = {
  vervaldatum_apk:'APK geldig tot', datum_eerste_toelating:'Eerste toelating', datum_eerste_tenaamstelling_in_nederland:'Eerste registratie Nederland', datum_tenaamstelling:'Laatste tenaamstelling',
  wam_verzekerd:'WAM-verzekerd', openstaande_terugroepactie_indicator:'Openstaande terugroepactie', export_indicator:'Export geregistreerd', taxi_indicator:'Taxi geregistreerd',
  tellerstandoordeel:'Tellerstandoordeel', jaar_laatste_registratie_tellerstand:'Laatste jaar tellerregistratie', code_toelichting_tellerstandoordeel:'Toelichtingscode tellerstandoordeel',
  bruto_bpm:'Bruto BPM', handelsbenaming:'Model', eerste_kleur:'Kleur', tweede_kleur:'Tweede kleur', massa_rijklaar:'Rijklaargewicht', massa_ledig_voertuig:'Ledig gewicht',
  toegestane_maximum_massa_voertuig:'Maximale toegestane massa', technische_max_massa_voertuig:'Technische maximale massa', maximum_trekken_massa_geremd:'Trekgewicht geremd',
  maximum_massa_trekken_ongeremd:'Trekgewicht ongeremd', maximum_massa_samenstelling:'Maximale massa combinatie', vermogen_massarijklaar:'Vermogen / rijklaargewicht',
  cilinderinhoud:'Cilinderinhoud', nettomaximumvermogen:'Maximumvermogen (RDW)', brandstof_omschrijving:'Brandstof', emissiecode_omschrijving:'Emissieklasse',
  co2_uitstoot_gecombineerd:'CO₂ gecombineerd (NEDC)', co2_uitstoot_gewogen:'CO₂ gewogen (NEDC)', co2_uitstoot_gewogen_wltp:'CO₂ gewogen (WLTP)', co2_uitstoot_gecombineerd_wltp:'CO₂ gecombineerd (WLTP)',
  brandstofverbruik_gecombineerd:'Verbruik gecombineerd (NEDC)', brandstofverbruik_buiten:'Verbruik buitenweg (NEDC)', brandstofverbruik_stad:'Verbruik stadsverkeer (NEDC)',
  brandstofverbruik_gecombineerd_wltp:'Verbruik gecombineerd (WLTP)', brandstofverbruik_gewogen_gecombineerd_wltp:'Verbruik gewogen (WLTP)',
  elektrisch_verbruik_enkel_elektrisch_wltp:'Elektrisch verbruik (WLTP)', elektrisch_verbruik_extern_opladen_wltp:'Elektrisch verbruik, extern opladen (WLTP)',
  actie_radius_enkel_elektrisch_wltp:'Elektrische actieradius (WLTP)', actie_radius_extern_opladen_wltp:'Actieradius, extern opladen (WLTP)',
  emissie_deeltjes_type1_wltp:'Deeltjesemissie type 1 (WLTP)', klasse_hybride_elektrisch_voertuig:'Hybrideklasse', uitlaatemissieniveau:'Emissieniveau',
  geluidsniveau_stationair:'Geluidsniveau stationair', geluidsniveau_rijdend:'Geluidsniveau rijdend', toerental_geluidsniveau:'Toerental geluidsmeting',
  roetfilter:'Roetfilter', hoogte_voertuig:'Hoogte', europese_voertuigcategorie:'Europese voertuigcategorie',
  meld_datum_door_keuringsinstantie:'Melddatum', meld_tijd_door_keuringsinstantie:'Meldtijd', soort_erkenning_omschrijving:'Soort keuring',
  soort_melding_ki_omschrijving:'Soort melding', vervaldatum_keuring:'Keuring geldig tot', gebrek_identificatie:'Gebrekcode', gebrek_omschrijving:'Omschrijving gebrek',
  aantal_gebreken_geconstateerd:'Aantal constateringen', gebrek_artikel_nummer:'Artikel', gebrek_paragraaf_nummer:'Paragraaf',
  referentiecode_rdw:'RDW-referentie', referentiecode_producent:'Referentie fabrikant', publicatiedatum_rdw:'Publicatiedatum', code_status:'Statuscode',
  omschrijving_defect:'Defect', categorie_defect:'Categorie', materi_le_gevolgen:'Mogelijke gevolgen', beschrijving_van_het_herstel:'Herstelmaatregel',
  meldende_producent_distributeur:'Producent / distributeur', risicobeoordeling_rdw:'RDW-risicocode',
  soort_toe_te_voegen_object_omschrijving:'Ingebouwd object', merk_object_toegevoegd:'Merk object', gasinstallatie_tank_inhoud:'Tankinhoud gasinstallatie',
  classificatie_toegevoegd_obj:'Objectclassificatie', uitvoerings_volgnr_toegev_obj:'Uitvoeringsnummer object', aantal_assen:'Aantal assen',
  as_nummer:'Asnummer', aantal_wielen_as:'Wielen op as', spoorbreedte:'Spoorbreedte', technisch_toegestane_maximum_aslast:'Technische maximale aslast',
  wettelijk_toegestane_maximum_aslast:'Wettelijke maximale aslast', aangedreven_as:'Aangedreven as', geremde_as:'Geremde as', liftbare_as:'Liftbare as'
};
const UNITS = {
  cilinderinhoud:'cm³', lengte:'cm', breedte:'cm', wielbasis:'cm', spoorbreedte:'cm', hoogte_voertuig:'cm',
  geluidsniveau_stationair:'dB(A)', geluidsniveau_rijdend:'dB(A)', toerental_geluidsniveau:'rpm', gasinstallatie_tank_inhoud:'liter',
  co2_uitstoot_gecombineerd:'g/km', co2_uitstoot_gewogen:'g/km', co2_uitstoot_gecombineerd_wltp:'g/km', co2_uitstoot_gewogen_wltp:'g/km',
  brandstofverbruik_gecombineerd:'l/100 km', brandstofverbruik_buiten:'l/100 km', brandstofverbruik_stad:'l/100 km',
  brandstofverbruik_gecombineerd_wltp:'l/100 km', brandstofverbruik_gewogen_gecombineerd_wltp:'l/100 km',
  elektrisch_verbruik_enkel_elektrisch_wltp:'Wh/km', elektrisch_verbruik_extern_opladen_wltp:'Wh/km',
  actie_radius_enkel_elektrisch_wltp:'km', actie_radius_extern_opladen_wltp:'km', vermogen_massarijklaar:'kW/kg'
};
const GROUPS = {
  'Identiteit & registratie':['merk','handelsbenaming','voertuigsoort','inrichting','eerste_kleur','tweede_kleur','datum_eerste_toelating','datum_eerste_tenaamstelling_in_nederland','datum_tenaamstelling','catalogusprijs','bruto_bpm'],
  'APK & status':['vervaldatum_apk','wam_verzekerd','openstaande_terugroepactie_indicator','tellerstandoordeel','jaar_laatste_registratie_tellerstand','export_indicator','taxi_indicator','tenaamstellen_mogelijk'],
  'Motor & uitvoering':['aantal_cilinders','cilinderinhoud','type','variant','uitvoering','typegoedkeuringsnummer','europese_voertuigcategorie','zuinigheidsclassificatie'],
  'Gewichten & trekvermogen':['massa_ledig_voertuig','massa_rijklaar','toegestane_maximum_massa_voertuig','technische_max_massa_voertuig','maximum_massa_trekken_ongeremd','maximum_trekken_massa_geremd','maximum_massa_samenstelling'],
  'Afmetingen & indeling':['lengte','breedte','hoogte_voertuig','wielbasis','aantal_deuren','aantal_wielen','aantal_zitplaatsen','aantal_rolstoelplaatsen']
};
const TABS = [['overzicht','Overzicht'],['techniek','Techniek'],['energie','Motor & energie'],['keuringen','Keuringen'],['recalls','Terugroepacties'],['extra','Extra'],['alle','Alle gegevens']];
let current = null, activeTab = 'overzicht', requestId = 0, comparisons = [];
function readList(key) {
  try {const v=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(v)?v.filter(x=>typeof x==='string'&&/^[A-Z0-9]{6}$/.test(x)).slice(0,30):[];} catch {return [];}
}
let favorites=readList('kc-favorites'), recent=readList('kc-recent');
function message(text, cls='') {$('message').textContent=text;$('message').className=cls;}
function saveList(key, list) {try{localStorage.setItem(key,JSON.stringify(list));}catch{message('Je browser kon dit niet bewaren.','warning');}}
function label(key) {return LABELS[key]||key.replace(/_dt$/,'').replace(/_/g,' ').replace(/^./,c=>c.toUpperCase());}
function present(value) {return value!==undefined && value!==null && value!=='';}
function dateValue(value) {
  if (!value || value==='0') return null;
  const s=String(value);
  if (/^\d{8}$/.test(s)) return new Date(Number(s.slice(0,4)),Number(s.slice(4,6))-1,Number(s.slice(6,8)));
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return new Date(s);
  return null;
}
function format(key, value) {
  if (!present(value)) return '—';
  const v=String(value);
  if (key==='meld_tijd_door_keuringsinstantie') {const t=v.padStart(4,'0');return t.slice(0,2)+':'+t.slice(2);}
  if (key.endsWith('_dt') || /datum/.test(key)) {
    const d=dateValue(v);
    return d&&!Number.isNaN(d.getTime())?d.toLocaleDateString('nl-NL'):v==='0'?'Niet geregistreerd':v;
  }
  if (['catalogusprijs','bruto_bpm'].includes(key)&&Number.isFinite(Number(v))) return new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(Number(v));
  if (key==='nettomaximumvermogen'&&Number.isFinite(Number(v))) return v+' kW · ca. '+Math.round(Number(v)*1.35962)+' pk';
  if (UNITS[key]) return v+' '+UNITS[key];
  if ((/massa|aslast|maximum_last/.test(key))&&!/vermogen|verhouding/.test(key)) return v+' kg';
  return v;
}
function fields(row) {
  return Object.keys(row).filter(key=>key!=='kenteken'&&!key.startsWith('api_')&&!(key.endsWith('_dt')&&present(row[key.slice(0,-3)]))&&present(row[key]));
}
function rowList(row, keys) {
  const dl=element('dl');
  for (const key of (keys||fields(row)).filter(k=>present(row[k]))) {
    const r=element('div',undefined,'row');r.append(element('dt',label(key)),element('dd',format(key,row[key])));dl.append(r);
  }
  return dl;
}
function panel(title, count) {
  const box=element('section',undefined,'panel'), head=element('div',undefined,'panel-head');
  head.append(element('h2',title));if(count!==undefined)head.append(element('span',String(count),'count'));
  box.append(head);return box;
}
function note(box, text) {box.append(element('p',text,'panel-note'));}
function dataPanel(title, rows, keys) {
  const box=panel(title);
  if (rows===null) {note(box,'Deze bron kon niet worden opgehaald. Vernieuw de gegevens om het opnieuw te proberen.');return box;}
  if (!rows?.length) {note(box,'Geen openbare gegevens gevonden in deze dataset.');return box;}
  for(const row of rows) {
    const body=element('div',undefined,'panel-body');body.append(rowList(row,keys));box.append(body);
  }
  return box;
}
function garage() {
  $('garage-count').textContent=favorites.length?`· ${favorites.length} favoriet${favorites.length===1?'':'en'}`:'';
  for(const [id,list,isFav] of [['favorites',favorites,true],['recent',recent,false]]) {
    const box=$(id);box.replaceChildren();
    if(!list.length){box.append(element('span',isFav?'Nog geen favorieten.':'Nog geen recente zoekopdrachten.','empty'));continue;}
    box.append(element('span',isFav?'Favorieten':'Recent','empty'));
    for(const plate of list){const chip=element('span',undefined,'chip'),open=element('button',plate);open.type='button';open.addEventListener('click',()=>search(plate));chip.append(open);
      if(isFav){const remove=element('button','×','remove');remove.setAttribute('aria-label',`Verwijder ${plate} uit favorieten`);remove.addEventListener('click',()=>{favorites=favorites.filter(x=>x!==plate);saveList('kc-favorites',favorites);garage();favoriteButton();});chip.append(remove);}box.append(chip);
    }
  }
}
function favoriteButton(){if(current){const saved=favorites.includes(current.plate);$('favorite').textContent=saved?'★ Bewaard':'☆ Bewaren';$('favorite').setAttribute('aria-pressed',String(saved));}}
function vehicle(){return current.sections.voertuig[0];}
function fuelText(){return current.sections.brandstof?.map(x=>x.brandstof_omschrijving).filter(Boolean).join(' + ')||'—';}
function importText(v){const a=dateValue(v.datum_eerste_toelating),b=dateValue(v.datum_eerste_tenaamstelling_in_nederland);return a&&b?(b>a?'Ja':'Nee'):'—';}
function apkDays(v){const d=dateValue(v.vervaldatum_apk);if(!d||Number.isNaN(d.getTime()))return null;const today=new Date();today.setHours(0,0,0,0);return Math.round((d-today)/86400000);}
function overview(){
  const grid=element('div',undefined,'panel-grid'),v=vehicle();
  for(const title of ['Identiteit & registratie','APK & status','Gewichten & trekvermogen','Afmetingen & indeling'])grid.append(dataPanel(title,[v],GROUPS[title]));
  const history=panel('Laatste keuringsmeldingen',current.sections.keuringen?.length??'Niet opgehaald');
  if(current.sections.keuringen===null)note(history,'Keuringsmeldingen zijn niet bereikbaar.');
  else if(!current.sections.keuringen?.length)note(history,'Geen openbare keuringsmeldingen gevonden.');
  else history.append(inspectionTable(current.sections.keuringen.slice(0,3)));
  grid.append(history);
  const recall=panel('Terugroepacties',current.sections.terugroepstatus?.length??'Niet opgehaald');
  if(current.sections.terugroepstatus===null)note(recall,'Terugroepstatussen zijn niet bereikbaar.');
  else if(!current.sections.terugroepstatus?.length)note(recall,'Geen terugroepstatussen gevonden in de openbare dataset.');
  else for(const r of current.sections.terugroepstatus.slice(0,3)){const b=element('div',undefined,'panel-body');b.append(rowList(r,['referentiecode_rdw','status']));recall.append(b);}
  grid.append(recall);return grid;
}
function table(columns, rows){
  const wrap=element('div',undefined,'table-wrap'),t=element('table'),thead=element('thead'),tr=element('tr');
  for(const [,title]of columns)tr.append(element('th',title));thead.append(tr);t.append(thead);const body=element('tbody');
  for(const record of rows){const r=element('tr');for(const [key]of columns){const td=element('td',format(key,record[key]));if(/omschrijving/.test(key))td.className='long';r.append(td);}body.append(r);}t.append(body);wrap.append(t);return wrap;
}
function inspectionTable(rows){return table([['meld_datum_door_keuringsinstantie','Datum'],['soort_erkenning_omschrijving','Keuring'],['soort_melding_ki_omschrijving','Melding'],['vervaldatum_keuring','Geldig tot']],rows);}
function inspectionView(){
  const box=element('div'),inspections=current.sections.keuringen,defects=current.sections.gebreken,p=panel('Keuringsmeldingen',inspections?.length??'Niet opgehaald');
  if(inspections===null)note(p,'Keuringsmeldingen zijn tijdelijk niet bereikbaar.');else if(!inspections.length)note(p,'Geen openbare keuringsmeldingen gevonden.');else p.append(inspectionTable(inspections));
  note(p,'Dit zijn de beschikbare RDW-meldingen, geen volledige onderhoudshistorie.');box.append(p);
  const d=panel('Geconstateerde gebreken',defects?.length??'Niet opgehaald');
  if(defects===null)note(d,'Gebreken zijn tijdelijk niet bereikbaar.');else if(!defects.length)note(d,'Geen geconstateerde gebreken gevonden in deze openbare dataset.');
  else d.append(table([['meld_datum_door_keuringsinstantie','Datum'],['gebrek_identificatie','Code'],['gebrek_omschrijving','Omschrijving'],['aantal_gebreken_geconstateerd','Aantal']],defects));
  if(current.sections.gebrekbeschrijvingen===null)note(d,'De omschrijvingen konden niet worden opgehaald. De gebrekcodes blijven zichtbaar.');
  note(d,'Een constatering hoort bij de genoemde keuring en bewijst niet dat het gebrek nu nog aanwezig is. Geen resultaat bewijst niet dat het voertuig vrij van gebreken is.');box.append(d);return box;
}
function recallView(){
  const box=panel('Terugroepacties bij dit kenteken',current.sections.terugroepstatus?.length??'Niet opgehaald');
  if(current.sections.terugroepstatus===null){note(box,'De terugroepstatus kon niet worden opgehaald.');return box;}
  if(!current.sections.terugroepstatus.length){note(box,'Geen terugroepstatussen gevonden in de openbare dataset.');return box;}
  for(const status of current.sections.terugroepstatus){
    const detail=current.sections.terugroepdetails?.find(r=>r.referentiecode_rdw===status.referentiecode_rdw),record=element('details',undefined,'record'),s=element('summary');
    s.append(element('span',status.referentiecode_rdw||'Terugroepactie'),element('span',status.status||'Status onbekend','record-meta'));record.append(s);const body=element('div',undefined,'panel-body');
    body.append(rowList({...detail,...status},['status','publicatiedatum_rdw','meldende_producent_distributeur','referentiecode_producent','omschrijving_defect','categorie_defect','materi_le_gevolgen','beschrijving_van_het_herstel','risicobeoordeling_rdw','meer_informatie_via_telefoonnummer','opmerkingen_rdw']));
    if(!detail)body.append(element('p','Details van deze terugroepactie zijn niet beschikbaar.','empty'));record.append(body);box.append(record);
  }
  note(box,'De geregistreerde status geldt voor dit kenteken. De beschrijving en herstelmaatregel horen bij de terugroepactie.');return box;
}
function energyView(){
  const rows=current.sections.brandstof,box=element('div');
  if(!rows?.length){box.append(dataPanel('Motor & energie',rows));return box;}
  const grid=element('div',undefined,'panel-grid');
  for(const row of rows)grid.append(dataPanel(row.brandstof_omschrijving||'Brandstofregistratie',[row]));
  box.append(grid,element('p','Vermogen wordt per brandstofregistratie getoond. Bij hybride voertuigen is dit geen opgeteld systeemvermogen. WLTP-waarden zijn testwaarden, geen gemeten praktijkverbruik.','notice'));return box;
}
function allView(query=''){
  const grid=element('div',undefined,'panel-grid');let matches=0;
  for(const [key,source]of Object.entries(current.sources)){
    const rows=current.sections[key];
    if(query){
      if(!rows?.length)continue;
      const filtered=rows.map(row=>Object.fromEntries(fields(row).filter(k=>(label(k)+' '+format(k,row[k])+' '+source.label).toLowerCase().includes(query)).map(k=>[k,row[k]]))).filter(row=>Object.keys(row).length);
      if(filtered.length){grid.append(dataPanel(source.label,filtered));matches+=filtered.reduce((n,r)=>n+Object.keys(r).length,0);}
    }else if(rows===null||rows?.length)grid.append(dataPanel(source.label,rows));
  }
  if(query&&!matches)grid.append(element('p','Geen gegevens gevonden die overeenkomen met je zoekopdracht.','empty'));
  if(!query){const p=panel('Databronnen'),list=element('div',undefined,'source-list');for(const [key,source]of Object.entries(current.sources)){const a=element('a',source.label);a.href=source.url;a.target='_blank';a.rel='noopener';a.append(element('span',current.sections[key]===null?'Niet opgehaald':`${current.sections[key]?.length||0} regels`,'source-status'));list.append(a);}p.append(list);grid.append(p);}return grid;
}
function renderDetails(){
  if(!current)return;
  const query=$('field-query').value.trim().toLowerCase(),out=$('details');out.replaceChildren();
  if(query)out.append(allView(query));
  else if(activeTab==='overzicht')out.append(overview());
  else if(activeTab==='energie')out.append(energyView());
  else if(activeTab==='keuringen')out.append(inspectionView());
  else if(activeTab==='recalls')out.append(recallView());
  else if(activeTab==='alle')out.append(allView());
  else {const grid=element('div',undefined,'panel-grid');if(activeTab==='techniek'){grid.append(dataPanel('Motor & uitvoering',[vehicle()],GROUPS['Motor & uitvoering']),dataPanel('Assen',current.sections.assen),dataPanel('Carrosserie',current.sections.carrosserie),dataPanel('Specifieke carrosserie',current.sections.carrosserie_specifiek));}else{grid.append(dataPanel('Ingebouwde objecten',current.sections.objecten),dataPanel('Voertuigklasse',current.sections.voertuigklasse));}out.append(grid);}
  for(const b of $('tabs').children){b.classList.toggle('active',!query&&b.dataset.key===activeTab);b.setAttribute('aria-selected',String(!query&&b.dataset.key===activeTab));}
}
function render(){
  const v=vehicle(),days=apkDays(v);$('welcome').hidden=true;$('result').hidden=false;$('result-plate').textContent=current.plate;
  $('vehicle-title').textContent=[v.merk,v.handelsbenaming].filter(Boolean).join(' ');
  $('vehicle-subtitle').textContent=[v.inrichting,v.eerste_kleur,v.datum_eerste_toelating?.slice(0,4)].filter(Boolean).join(' · ');
  $('timestamp').textContent='Opgehaald '+new Date(current.fetched_at*1000).toLocaleString('nl-NL')+(current.cached?' · cache':' · bijgewerkt');
  const loaded=Object.values(current.sections).filter(x=>x!==null).length,total=Object.keys(current.sources).length;
  $('coverage').textContent=`${loaded}/${total} bronnen verwerkt · ${Object.values(current.sections).reduce((n,rows)=>n+(rows?.length||0),0)} gegevensregels`;
  const alerts=$('alerts');alerts.replaceChildren();for(const warning of current.warnings)alerts.append(element('p',warning,'warning'));
  if(v.openstaande_terugroepactie_indicator==='Ja')alerts.append(element('p','Openstaande terugroepactie gemeld. Bekijk het tabblad Terugroepacties.','warning'));
  if(v.tellerstandoordeel==='Onlogisch')alerts.append(element('p','Het RDW-tellerstandoordeel is onlogisch.','warning'));
  if(days!==null&&days<0)alerts.append(element('p','De geregistreerde APK-vervaldatum is verstreken.','warning'));
  else if(days!==null&&days<=30)alerts.append(element('p',days===0?'De APK-vervaldatum is vandaag.':`De APK-vervaldatum is over ${days} dagen.`,'warning'));
  const stats=[['APK geldig tot',format('vervaldatum_apk',v.vervaldatum_apk),days===null?'':days<0?'tone-bad':days<=30?'tone-warn':''],['Brandstof',fuelText(),''],['Tellerstandoordeel',v.tellerstandoordeel||'—',v.tellerstandoordeel==='Onlogisch'?'tone-bad':''],['WAM-verzekerd',v.wam_verzekerd||'—',''],['Terugroepactie',v.openstaande_terugroepactie_indicator||'—',v.openstaande_terugroepactie_indicator==='Ja'?'tone-warn':''],['Import',importText(v),''],['Rijklaargewicht',format('massa_rijklaar',v.massa_rijklaar),''],['Trekgewicht geremd',format('maximum_trekken_massa_geremd',v.maximum_trekken_massa_geremd),'']];
  const summary=$('summary');summary.replaceChildren();for(const [title,value,tone]of stats){const s=element('div',undefined,'stat');s.append(element('small',title),element('strong',value,tone));if(title==='Import')s.title='Afgeleid: eerste registratie Nederland is later dan eerste toelating.';summary.append(s);}
  $('tabs').replaceChildren();for(const [key,title]of TABS){const b=element('button',title);b.dataset.key=key;b.setAttribute('role','tab');b.id='tab-'+key;b.setAttribute('aria-controls','details');b.addEventListener('click',()=>{activeTab=key;$('field-query').value='';$('details').setAttribute('aria-labelledby',b.id);renderDetails();b.scrollIntoView({block:'nearest',inline:'nearest'});});$('tabs').append(b);}
  activeTab='overzicht';$('field-query').value='';$('details').setAttribute('aria-labelledby','tab-overzicht');renderDetails();favoriteButton();
}
async function search(plate,refresh=false){
  const id=++requestId;$('submit').disabled=true;$('refresh').disabled=true;$('result').hidden=true;$('welcome').hidden=true;current=null;message('Voertuiggegevens ophalen…');$('plate').value=plate;
  try{const response=await fetch('/api/vehicle/'+encodeURIComponent(plate)+(refresh?'?refresh=1':''));const data=await response.json();if(id!==requestId)return;if(!response.ok)throw new Error(data.error||'De gegevens konden niet worden opgehaald.');
    current=data;recent=[data.plate,...recent.filter(x=>x!==data.plate)].slice(0,8);saveList('kc-recent',recent);garage();render();message('');
  }catch(e){if(id===requestId){message(e.message||'Geen verbinding met de app.','error');$('welcome').hidden=false;}}
  finally{if(id===requestId){$('submit').disabled=false;$('refresh').disabled=false;}}
}
function compareValue(data,key){const v=data.sections.voertuig[0];if(key==='brandstof')return data.sections.brandstof?.map(x=>x.brandstof_omschrijving).filter(Boolean).join(' + ')||'—';if(key==='import')return importText(v);return format(key,v[key]);}
function renderComparison(){
  $('comparison').hidden=false;$('comparison-hint').hidden=comparisons.length===2;const wrap=$('comparison-content');wrap.replaceChildren();
  const t=element('table'),head=element('tr');head.append(element('th','Gegeven'));comparisons.forEach(x=>head.append(element('th',x.plate)));t.append(head);
  for(const key of ['merk','handelsbenaming','datum_eerste_toelating','brandstof','vervaldatum_apk','import','massa_rijklaar','maximum_trekken_massa_geremd','catalogusprijs','tellerstandoordeel']){const row=element('tr');row.append(element('th',label(key)));comparisons.forEach(x=>row.append(element('td',compareValue(x,key))));t.append(row);}wrap.append(t);
}
$('search').addEventListener('submit',e=>{e.preventDefault();search($('plate').value);});
$('refresh').addEventListener('click',()=>{if(current)search(current.plate,true);});
$('field-query').addEventListener('input',renderDetails);
$('tabs').addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;const tabs=[...$('tabs').children],i=tabs.indexOf(document.activeElement);if(i<0)return;e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[next].focus();tabs[next].click();});
$('favorite').addEventListener('click',()=>{if(!current)return;const p=current.plate;favorites=favorites.includes(p)?favorites.filter(x=>x!==p):[p,...favorites].slice(0,30);saveList('kc-favorites',favorites);garage();favoriteButton();});
$('export').addEventListener('click',()=>{if(!current)return;const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:'application/json'})),a=element('a');a.href=url;a.download=`kenteken-${current.plate}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('print').addEventListener('click',()=>{if(!current)return;const previous=activeTab,query=$('field-query').value;activeTab='overzicht';$('field-query').value='';renderDetails();window.print();activeTab=previous;$('field-query').value=query;renderDetails();});
$('compare').addEventListener('click',()=>{if(!current)return;comparisons=[...comparisons.filter(x=>x.plate!==current.plate),current].slice(-2);renderComparison();$('comparison').scrollIntoView({behavior:'smooth'});});
$('close-comparison').addEventListener('click',()=>{$('comparison').hidden=true;comparisons=[];});
garage();
