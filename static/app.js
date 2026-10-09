'use strict';
const $ = id => document.getElementById(id);
function element(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (cls) n.className = cls;
  return n;
}
const LABELS = {
  vin_wmi:'WMI',vin:'VIN / chassisnummer',wmi:'WMI · posities 1–3',posities_4_8:'Posities 4–8',positie_9:'Positie 9',vis_posities_10_17:'VIS · posities 10–17',positie_10:'Positie 10',positie_11:'Positie 11',laatste_vier_numeriek:'Laatste vier tekens numeriek',formaat:'Invoerformaat',interpretatie:'Wat deze controle betekent',
  testedModel:'Geteste uitvoering',ratingYear:'Testjaar',nicePublicationDate:'Publicatie',starRating:'Veiligheidssterren',adultOccupant_percent:'Volwassen inzittenden (%)',childOccupant_percent:'Kinderen (%)',vulnerableRoadUsers_percent:'Kwetsbare weggebruikers (%)',safetyAssist_percent:'Veiligheidsassistentie (%)',
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
const TABS = [['overzicht','Overzicht'],['fotos','Foto’s'],['rapporten','Rapporten'],['techniek','Techniek'],['energie','Motor & energie'],['keuringen','Keuringen'],['recalls','Terugroepacties'],['extra','Extra'],['aanvullend','Aanvullende bronnen'],['typegoedkeuring','Typegoedkeuring'],['historie','Historie'],['bronnen','Bronnen'],['alle','Alle ontvangen data']];
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
  const v=typeof value==='object'?JSON.stringify(value,null,2):String(value);
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
  return Object.keys(row);
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
function vehicle(){return current.sections.voertuig?.[0]||{};}
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
function sourceState(key) {
  const rows=current.sections[key];
  return current.source_status?.[key] || {status:rows===null?'error':rows?.length?'available':'unavailable',row_count:rows?.length||0,reason:rows===null?'Ophalen mislukt.':rows?.length?'Gegevens gevonden.':'Geen gegevens voor dit kenteken gevonden.'};
}
function statusPill(key) {
  const state=sourceState(key),n=element('span',state.status==='available'?'Beschikbaar':state.status==='error'?'Ophalen mislukt':'Niet beschikbaar','status-pill '+(state.status==='available'?'good':state.status==='error'?'warn':''));
  return n;
}
function rawValue(value) {
  if(value===null)return 'null';
  if(value===undefined)return 'Niet beschikbaar';
  if(value==='')return '(lege waarde)';
  return typeof value==='object'?JSON.stringify(value,null,2):String(value);
}
function rawPanel(key, query='') {
  const source=current.sources[key],rows=current.sections[key],box=panel(source.label,rows?.length??0);
  box.querySelector('.panel-head').append(statusPill(key));
  if(source.note){note(box,source.note);const credit=element('p',undefined,'panel-note'),link=element('a','Bron: '+source.provider+(source.licence?' · '+source.licence:''));link.href=source.url;link.target='_blank';link.rel='noopener';credit.append(link);box.append(credit);}
  if(!rows?.length){note(box,sourceState(key).reason);return box;}
  const records=rows.map((row,index)=>({row,index,keys:Object.keys(row).filter(k=>!query||(k+' '+(source.fields?.[k]||label(k))+' '+rawValue(row[k])+' '+source.label).toLowerCase().includes(query))})).filter(record=>record.keys.length);
  let cursor=0;const more=element('button','Toon volgende 50 records','secondary');more.type='button';
  const next=()=>{more.remove();const end=Math.min(cursor+50,records.length);for(;cursor<end;cursor++){
    const {row,index,keys}=records[cursor],record=element('details',undefined,'record raw-record');record.open=!!query||rows.length===1;
    record.append(element('summary',`Record ${index+1} · ${keys.length} velden`));const dl=element('dl');
    for(const field of keys){const r=element('div',undefined,'row'),dt=element('dt',source.fields?.[field]||label(field));dt.append(element('code',field,'field-code'));r.append(dt,element('dd',rawValue(row[field])));dl.append(r);}record.append(dl);box.append(record);
  }if(cursor<records.length){more.textContent=`Toon volgende ${Math.min(50,records.length-cursor)} records · ${cursor}/${records.length} zichtbaar`;box.append(more);}};
  more.addEventListener('click',next);next();if(records.length>50)note(box,'Alle records zijn opgehaald en staan in de JSON-export. Toon meer om verder te bladeren.');return box;
}
function allView(query=''){
  const grid=element('div',undefined,'panel-grid');let matches=0;
  for(const [key,source]of Object.entries(current.sources)){
    const rows=current.sections[key];
    if(query&&!rows?.some(row=>Object.keys(row).some(k=>(k+' '+(source.fields?.[k]||label(k))+' '+rawValue(row[k])+' '+source.label).toLowerCase().includes(query))))continue;
    grid.append(rawPanel(key,query));matches++;
  }
  if(query&&!matches)grid.append(element('p','Geen gegevens gevonden die overeenkomen met je zoekopdracht.','empty'));
  return grid;
}
function sourceView(){
  const box=element('div');box.append(element('p','Beschikbaar betekent dat deze bron gegevens heeft geleverd. Niet beschikbaar betekent geen resultaat of geen bruikbare koppeling/toegang. Een storing wordt apart gemeld.','notice'));
  const groups=new Map();
  for(const [key,source]of Object.entries(current.sources)){const title=source.scope==='typegoedkeuring'?'Typegoedkeuring · exacte koppeling':source.scope==='extern'?'Aanvullende externe bronnen':source.scope==='historie'?'Beschikbaarheid aanvullende historie':'RDW · voertuig en gerelateerde gegevens';if(!groups.has(title))groups.set(title,[]);groups.get(title).push([key,source]);}
  for(const [title,entries]of groups){const p=panel(title,entries.length);for(const [key,source]of entries){const r=element('details',undefined,'record'),head=element('summary');head.append(element('span',source.label),statusPill(key));r.append(head);const body=element('div',undefined,'panel-body');body.append(element('p',sourceState(key).reason,'empty'));body.append(rowList({records:sourceState(key).row_count,velden_in_catalogus:Object.keys(source.fields||{}).length,aanbieder:source.provider||'RDW'}));
    if(source.url){const a=element('a','Broninformatie');a.href=source.url;a.target='_blank';a.rel='noopener';body.append(a);}
    if(Object.keys(source.fields||{}).length){const fields=element('details'),sm=element('summary','Alle velden in deze dataset');fields.append(sm);const loaded=new Set((current.sections[key]||[]).flatMap(row=>Object.keys(row)));for(const [field,name]of Object.entries(source.fields)){fields.append(element('div',(name||field)+' · '+((current.sections[key]||[]).some(row=>present(row[field]))?'Beschikbaar':loaded.has(field)?'Leeg geleverd':'Niet beschikbaar voor dit kenteken'),'field-availability'));}body.append(fields);}
    r.append(body);p.append(r);}box.append(p);}return box;
}
function historyView(){
  const box=element('div'),events=[],v=vehicle();
  const add=(date,title,detail,source)=>{const d=dateValue(date);if(d&&!Number.isNaN(d.getTime()))events.push({time:d.getTime(),date:format('datum',date),title,detail,source});};
  for(const [key,title]of [['datum_eerste_toelating','Eerste toelating'],['datum_eerste_tenaamstelling_in_nederland','Eerste registratie Nederland'],['datum_tenaamstelling','Laatste tenaamstelling']])add(v[key],title,'Geregistreerde datum; geen volledige reeks eigenaarwisselingen.','Voertuigregistratie');
  for(const r of current.sections.keuringen||[])add(r.meld_datum_door_keuringsinstantie,'Keuringsmelding',r.soort_melding_ki_omschrijving||r.soort_erkenning_omschrijving||'','Keuringsmeldingen');
  for(const r of current.sections.gebreken||[])add(r.meld_datum_door_keuringsinstantie,'Gebrek geconstateerd',r.gebrek_omschrijving||r.gebrek_identificatie,'Geconstateerde gebreken');
  for(const r of current.sections.objecten||[]){add(r.montagedatum,'Object ingebouwd',r.soort_toe_te_voegen_object_omschrijving||'','Ingebouwde objecten');add(r.demontagedatum,'Object verwijderd',r.soort_toe_te_voegen_object_omschrijving||'','Ingebouwde objecten');}
  for(const r of current.sections.terugroepdetails||[])add(r.publicatiedatum_rdw,'Terugroepactie gepubliceerd',(r.referentiecode_rdw||'')+' · '+(r.omschrijving_defect||''),'Terugroepacties');
  events.sort((a,b)=>b.time-a.time);
  const p=panel('Beschikbare historische gebeurtenissen',events.length);
  if(!events.length)note(p,'Geen gedateerde gebeurtenissen gevonden.');
  for(const event of events){const r=element('div',undefined,'timeline-event');r.append(element('span',event.date,'timeline-date'),element('strong',event.title),element('p',event.detail),element('small',event.source));p.append(r);}box.append(p);
  const observations=current.history?.observations||[],o=panel('Eigen waarnemingen & wijzigingen',observations.length);note(o,'Deze historie ontstaat vanaf het opzoeken in deze app. Een waarnemingsdatum is geen bewezen datum van een voertuigwijziging. Storingen worden niet als voertuigwijzigingen weergegeven.');
  if(!observations.length)note(o,'Nog geen opgeslagen waarnemingen.');
  for(const r of [...observations].reverse()){const record=element('details',undefined,'record'),head=element('summary');head.append(element('span',new Date(r.observed_at*1000).toLocaleString('nl-NL')),element('span',r.kind==='first_observation'?'Eerste waarneming':r.changes.length?`${r.changes.length} gewijzigde datasets`:'Aanvullende broninformatie','record-meta'));record.append(head);
    for(const change of r.changes){const detail=element('details',undefined,'change-detail');detail.append(element('summary',current.sources[change.source]?.label||change.source),element('pre',JSON.stringify({voor:change.before,na:change.after},null,2)));record.append(detail);}o.append(record);}box.append(o);
  const unavailable=panel('Andere historische gegevens');for(const [key,source]of Object.entries(current.sources).filter(([,s])=>s.scope==='historie')){const r=element('div',undefined,'record');r.append(element('strong',source.label),element('p',sourceState(key).reason,'empty'));unavailable.append(r);}box.append(unavailable);return box;
}

const euModelMenus=new Map();
function supplementalView(){
  const box=element('div'),p=panel('Europese modelinformatie'),form=element('form',undefined,'source-form'),label=element('label','Model en generatie'),select=element('select'),status=element('p','Modellen ophalen…','empty');select.id='eu-model';select.disabled=true;
  const empty=element('option','Kies een passende Europese generatie');empty.value='';select.append(empty);label.append(select);form.append(label);
  const apply=element('button','Modelgegevens ophalen');apply.type='submit';apply.disabled=true;form.append(apply);
  const clear=element('button','Modelselectie verwijderen','secondary');clear.type='button';clear.addEventListener('click',()=>{const next={...current.selection};delete next.model_slug;applySupplemental(next);});form.append(clear);
  form.addEventListener('submit',e=>{e.preventDefault();if(select.value)applySupplemental({...current.selection,model_slug:select.value});});p.append(form,status);note(p,'De lijst bevat Europese modellen van hetzelfde merk. Kies de juiste generatie zelf. Specificaties zijn indicatief en kunnen afwijken van jouw uitvoering. De Nederlandse terugroepbron wordt automatisch gekoppeld waar exacte referenties beschikbaar zijn.');box.append(p);
  const make=vehicle().merk,selection=current.selection||{};
  (async()=>{await Promise.resolve();if(!make){status.textContent='RDW-merk ontbreekt; geen betrouwbare modelselectie mogelijk.';return;}
    try{let data=euModelMenus.get(make);if(!data){const response=await fetch('/api/eu-models?'+new URLSearchParams({make}));data=await response.json();if(!response.ok)throw new Error(data.error||'Modelcatalogus kon niet worden opgehaald.');euModelMenus.set(make,data);}
      if(!form.isConnected)return;for(const item of data){const option=element('option',item.text);option.value=item.value;select.append(option);}select.value=selection.model_slug||'';select.disabled=!data.length;apply.disabled=!data.length;status.textContent=data.length?'':'Geen Europese modelgeneraties voor dit merk in deze catalogus.';
    }catch(e){if(form.isConnected)status.textContent=e.message;}
  })();
  const eea=panel('Europese registraties · EEA'),eeaForm=element('form',undefined,'source-form'),eeaLabel=element('label','Europese registraties ophalen'),enabled=element('input');enabled.type='checkbox';enabled.id='eea-enabled';enabled.checked=!!selection.eea_enabled;eeaLabel.prepend(enabled);eeaForm.append(eeaLabel);const eeaApply=element('button','EEA-keuze opslaan');eeaApply.type='submit';eeaForm.append(eeaApply);eeaForm.addEventListener('submit',e=>{e.preventDefault();const next={...current.selection};if(enabled.checked)next.eea_enabled=true;else delete next.eea_enabled;applySupplemental(next);});eea.append(eeaForm);note(eea,'Bij inschakelen verstuurt de app onderstaande koppelcodes naar de European Environment Agency. Het kenteken wordt niet meegestuurd.');eea.append(rowList(vehicle(),['typegoedkeuringsnummer','variant','uitvoering']));box.append(eea);
  box.append(element('p','Deze bronnen gebruiken Nederlandse en Europese gegevens. EEA-registraties van vergelijkbare voertuigen en gekozen modelspecificaties zijn geen historie van dit individuele kenteken.','notice'));
  const grid=element('div',undefined,'panel-grid');for(const key of Object.keys(current.sources).filter(key=>/^(eu_|nl_|extern_)/.test(key)))grid.append(rawPanel(key));box.append(grid);return box;
}
async function applySupplemental(selection){
  const plate=current.plate;await search(plate,false,selection);if(current){activeTab='aanvullend';$('details').setAttribute('aria-labelledby','tab-aanvullend');renderDetails();}
}

const reportSources=[['eu_euroncap','Euro NCAP'],['eu_greenncap','Green NCAP'],['eu_adac','ADAC']];
const reportMenus=new Map();
function reportView(){
 const box=element('div');box.append(element('p','Modelrapporten beschrijven een geteste uitvoering. Controleer generatie, motor en uitrusting voordat je een rapport koppelt. Eigen PDF’s blijven lokaal bewaard.','notice'));
 const grid=element('div',undefined,'panel-grid');
 for(const [key,title]of (current.lookup_type==='vin'?[]:reportSources)){
  const p=panel(title),form=element('form',undefined,'source-form'),select=element('select'),input=element('input'),status=element('p','Kandidaten ophalen…','empty');select.setAttribute('aria-label',title+' rapportkandidaten');select.append(element('option','Kies een kandidaat of plak een directe link'));
  select.firstChild.value='';input.type='url';input.placeholder='Directe modelrapportlink (https://…)';input.setAttribute('aria-label',title+' rapportlink');input.value=current.selection?.report_urls?.[key]||'';select.addEventListener('change',()=>{if(select.value)input.value=select.value;});
  const confirm=element('input');confirm.type='checkbox';confirm.required=true;const label=element('label','Ik heb generatie, motor en uitrusting in het originele rapport gecontroleerd.');label.prepend(confirm);
  const save=element('button','Rapport koppelen');save.type='submit';const clear=element('button','Verwijderen','secondary');clear.type='button';clear.addEventListener('click',async()=>{const next={...current.selection,report_urls:{...current.selection?.report_urls}};delete next.report_urls[key];await applyReports(next);});
  form.append(select,input,label,save,clear);form.addEventListener('submit',async e=>{e.preventDefault();if(input.value&&confirm.checked)await applyReports({...current.selection,report_urls:{...current.selection?.report_urls,[key]:input.value}});});p.append(form,status);
  (async()=>{await Promise.resolve();const v=vehicle(),cacheKey=[key,v.merk,v.handelsbenaming].join('|');if(!v.merk||!v.handelsbenaming){status.textContent='RDW-merk of model ontbreekt.';return;}
   try{let data=reportMenus.get(cacheKey);if(!data){const response=await fetch('/api/report-options?'+new URLSearchParams({source:key,make:v.merk,model:v.handelsbenaming}));data=await response.json();if(!response.ok)throw new Error(data.error||'Kandidaten niet beschikbaar.');reportMenus.set(cacheKey,data);}if(!form.isConnected)return;for(const item of data){const option=element('option',item.title);option.value=item.url;select.append(option);}status.textContent=data.length?`${data.length} kandidaten uit de openbare index. Controleer zelf de exacte uitvoering.`:'Geen kandidaten in deze index. Je kunt een directe officiële modelrapportlink invoeren.';if(key==='eu_adac')status.textContent+=' ADAC-index: selectie van recente tests, geen volledige catalogus.';
   }catch(e){if(form.isConnected)status.textContent=e.message+' Een directe officiële rapportlink blijft mogelijk.';}
  })();
  const records=current.sections[key]||[];
  for(const report of records){const r=element('div',undefined,'record');r.append(element('strong',report.title),element('p',report.applicability,'empty'));if(report.test_summary&&Object.keys(report.test_summary).length)r.append(rowList(report.test_summary));const links=[{title:'Origineel modelrapport',url:report.url},...(report.pdf_reports||[])];for(const link of links){const a=element('a',link.title);a.href=link.url;a.target='_blank';a.rel='noopener noreferrer';r.append(a,element('br'));}p.append(r);}
  p.append(element('p',sourceState(key).reason,'empty'));grid.append(p);
 }
 box.append(grid);
 const local=panel('Eigen rapporten · PDF'),upload=element('form',undefined,'source-form'),file=element('input'),submit=element('button','PDF bewaren'),list=element('div'),message=element('p','Car-Pass, HistoVec, dealeruitdraai of een zelf verkregen historierapport. Maximaal 6 MB per PDF en 30 rapporten per kenteken.','empty');file.type='file';file.accept='.pdf,application/pdf';file.required=true;file.setAttribute('aria-label','Eigen PDF-rapport');submit.type='submit';upload.append(file,submit);local.append(upload,message,list);box.append(local);const plate=current.plate;
 const renderLocal=rows=>{if(current?.plate!==plate||!list.isConnected)return;current.local_reports=rows;list.replaceChildren();if(!rows.length)list.append(element('p','Nog geen eigen rapporten bewaard.','empty'));for(const row of rows){const item=element('div',undefined,'record'),a=element('a',row.name);a.href=row.url;a.download=row.name;const remove=element('button','PDF verwijderen','secondary');remove.type='button';remove.addEventListener('click',async()=>{remove.disabled=true;try{const response=await fetch('/api/reports/'+plate+'/'+row.id,{method:'DELETE'}),data=await response.json();if(!response.ok)throw new Error(data.error);renderLocal(data);}catch(e){message.textContent=e.message;remove.disabled=false;}});item.append(a,element('p',new Date(row.uploaded_at*1000).toLocaleString('nl-NL')+' · '+Math.ceil(row.size/1024)+' KB · Door jou toegevoegd','empty'),remove);list.append(item);}};
 (async()=>{await Promise.resolve();try{const response=await fetch('/api/reports/'+plate),rows=await response.json();if(!response.ok)throw new Error(rows.error);renderLocal(rows);}catch(e){message.textContent=e.message;}})();
 upload.addEventListener('submit',async e=>{e.preventDefault();const pdf=file.files[0];if(!pdf)return;if(pdf.size>6*1024*1024){message.textContent='Gebruik een PDF van maximaal 6 MB.';return;}submit.disabled=true;try{const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('PDF kon niet worden gelezen.'));reader.readAsDataURL(pdf);});const response=await fetch('/api/reports/'+plate,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:pdf.name,data})}),rows=await response.json();if(!response.ok)throw new Error(rows.error);renderLocal(rows);file.value='';message.textContent='PDF lokaal bewaard. De inhoud is niet als geverifieerde voertuighistorie verwerkt.';}catch(e){message.textContent=e.message;}finally{submit.disabled=false;}});
 return box;
}
async function applyReports(selection){const plate=current.plate;await search(plate,false,selection);if(current){activeTab='rapporten';$('details').setAttribute('aria-labelledby','tab-rapporten');renderDetails();}}

function photoView(compact=false){
  const box=element('section',undefined,compact?'photo-strip':'photo-section');
  box.append(element('h2','Voorbeeldfoto’s · model, generatie en kleur'));
  const choose=element('button','Model/generatie kiezen','secondary');choose.addEventListener('click',()=>{activeTab='aanvullend';$('field-query').value='';$('details').setAttribute('aria-labelledby','tab-aanvullend');renderDetails();$('details').scrollIntoView({block:'start'});});box.append(choose);
  const rows=(current.sections.modelfotos||[]).filter(photo=>photo.match_version===2&&photo.generation_match);
  if(!rows.length){box.append(element('p',sourceState('modelfotos').reason||'Geen passende foto beschikbaar.','empty'));return box;}
  box.append(element('p','Voorbeeldauto, niet dit kenteken. Gekozen generatie gematcht op bronmetadata; exacte lak en overige details zijn niet bevestigd.','photo-note'));
  const gallery=element('div',undefined,'photo-gallery');
  for(const photo of rows){
    if(!/^\/api\/photo\/[a-f0-9]{64}$/.test(photo.image_url||''))continue;
    const figure=element('figure',undefined,'photo-card'),img=element('img');img.src=photo.image_url;img.alt=[photo.make,photo.model,photo.color,'· voorbeeldauto'].filter(Boolean).join(' ');img.loading='lazy';img.decoding='async';
    img.addEventListener('error',()=>{img.hidden=true;figure.prepend(element('p','Foto tijdelijk niet beschikbaar.','empty'));},{once:true});
    const caption=element('figcaption');caption.append(element('strong',[photo.model,photo.generation_match,photo.color].join(' · ')),element('span','Foto: '+photo.artist));
    const links=element('span');
    for(const [label,url,host]of [[photo.licence,photo.licence_url,'creativecommons.org'],['Wikimedia Commons',photo.file_url,'commons.wikimedia.org']]){
      try{const parsed=new URL(url);if(parsed.protocol!=='https:'||parsed.hostname!==host)continue;const a=element('a',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';links.append(a,' · ');}catch{}
    }
    caption.append(links);figure.append(img,caption);gallery.append(figure);
  }
  box.append(gallery);if(!compact)box.append(rawPanel('modelfotos'));return box;
}

function vinOverview(){
 const box=element('div');box.append(element('p','De VIN-opbouw wordt lokaal gecontroleerd. Dit bewijst niet dat het voertuig bestaat en levert geen volledige historie. RDW Open Data kan hier geen Nederlands kenteken bij zoeken.','notice'));
 const grid=element('div',undefined,'panel-grid');grid.append(rawPanel('vin_structuur'),rawPanel('vin_decoder'));box.append(grid);
 const p=panel('Optionele Europese VIN-decodering'),form=element('form',undefined,'source-form'),check=element('input'),label=element('label','Ik wil dit VIN naar Vincario versturen voor decodering. Dit kan leveranciersquota of betaald tegoed gebruiken.');check.type='checkbox';check.id='vin-decode-enabled';check.checked=!!current.selection?.vin_decode_enabled;label.prepend(check);const submit=element('button','VIN-bronkeuze opslaan');submit.type='submit';form.append(label,submit);form.addEventListener('submit',e=>{e.preventDefault();search(current.vin,true,{vin_decode_enabled:check.checked});});p.append(form);note(p,current.vin_provider_enabled?'Provider ingesteld. Er wordt alleen na inschakelen een aanvraag verstuurd.':'Niet beschikbaar: de server heeft geen VINCARIO_API_KEY en VINCARIO_SECRET_KEY. De lokale VIN-check werkt zonder sleutel.');box.append(p);
 const unavailable=panel('Beschikbaarheid historie');for(const [key,source]of Object.entries(current.sources).filter(([,row])=>row.scope==='historie')){const row=element('div',undefined,'record');row.append(element('strong',source.label),element('p',sourceState(key).reason,'empty'));unavailable.append(row);}box.append(unavailable);return box;
}

function renderDetails(){
  if(!current)return;
  const query=$('field-query').value.trim().toLowerCase(),out=$('details');out.replaceChildren();
  if(query)out.append(allView(query));
  else if(activeTab==='overzicht')out.append(current.lookup_type==='vin'?vinOverview():overview());
  else if(activeTab==='rapporten')out.append(reportView());
  else if(activeTab==='fotos')out.append(photoView());
  else if(activeTab==='energie')out.append(energyView());
  else if(activeTab==='keuringen')out.append(inspectionView());
  else if(activeTab==='recalls')out.append(recallView());
  else if(activeTab==='aanvullend')out.append(supplementalView());
  else if(activeTab==='alle')out.append(allView());
  else if(activeTab==='bronnen')out.append(sourceView());
  else if(activeTab==='historie')out.append(historyView());
  else if(activeTab==='typegoedkeuring'){const grid=element('div',undefined,'panel-grid');out.append(element('p','Typegoedkeuringsgegevens zijn gekoppeld op exact goedkeuringsnummer en waar mogelijk variant en uitvoering. Revisies en grenswaarden horen bij de goedkeuring, niet bij een onderhouds- of wijzigingshistorie van deze auto.','notice'));for(const [key,source]of Object.entries(current.sources).filter(([,s])=>s.scope==='typegoedkeuring'))grid.append(rawPanel(key));out.append(grid);}
  else {const grid=element('div',undefined,'panel-grid');if(activeTab==='techniek'){grid.append(dataPanel('Motor & uitvoering',[vehicle()],GROUPS['Motor & uitvoering']),dataPanel('Assen',current.sections.assen),dataPanel('Carrosserie',current.sections.carrosserie),dataPanel('Specifieke carrosserie',current.sections.carrosserie_specifiek));}else{grid.append(dataPanel('Ingebouwde objecten',current.sections.objecten),dataPanel('Voertuigklasse',current.sections.voertuigklasse));for(const key of ['subcategorie','bijzonderheden','rupsbanden','keuringsvervaldata','telleruitleg'])if(current.sources[key])grid.append(dataPanel(current.sources[key].label,current.sections[key]));}out.append(grid);}
  for(const b of $('tabs').children){b.classList.toggle('active',!query&&b.dataset.key===activeTab);b.setAttribute('aria-selected',String(!query&&b.dataset.key===activeTab));}
}
function render(){
  const v=vehicle(),isVin=current.lookup_type==='vin',days=apkDays(v);$('welcome').hidden=true;$('result').hidden=false;$('result-plate').textContent=current.plate;
  $('result-plate').classList.toggle('vin-identifier',isVin);$('vehicle-title').textContent=isVin?['VIN-check',v.merk,v.handelsbenaming].filter(Boolean).join(' · '):[v.merk,v.handelsbenaming].filter(Boolean).join(' ')||'Geen actuele voertuigregistratie beschikbaar';
  $('vehicle-subtitle').textContent=[v.inrichting,v.eerste_kleur,v.datum_eerste_toelating?.slice(0,4)].filter(Boolean).join(' · ');
  $('timestamp').textContent='Opgehaald '+new Date(current.fetched_at*1000).toLocaleString('nl-NL')+(current.cached?' · cache':' · bijgewerkt');
  const states=Object.keys(current.sources).map(sourceState),available=states.filter(x=>x.status==='available').length,unavailable=states.filter(x=>x.status==='unavailable').length,errors=states.filter(x=>x.status==='error').length;
  $('coverage').textContent=`${available} beschikbaar · ${unavailable} niet beschikbaar · ${errors} mislukt`;
  const alerts=$('alerts');alerts.replaceChildren();if(!isVin&&!current.sections.voertuig?.length)alerts.append(element('p','De actuele basisregistratie is niet beschikbaar. Andere bronnen en opgeslagen historie blijven hieronder zichtbaar.','notice'));for(const warning of current.warnings)alerts.append(element('p',warning,'warning'));
  if(v.openstaande_terugroepactie_indicator==='Ja')alerts.append(element('p','Openstaande terugroepactie gemeld. Bekijk het tabblad Terugroepacties.','warning'));
  if(v.tellerstandoordeel==='Onlogisch')alerts.append(element('p','Het RDW-tellerstandoordeel is onlogisch.','warning'));
  if(days!==null&&days<0)alerts.append(element('p','De geregistreerde APK-vervaldatum is verstreken.','warning'));
  else if(days!==null&&days<=30)alerts.append(element('p',days===0?'De APK-vervaldatum is vandaag.':`De APK-vervaldatum is over ${days} dagen.`,'warning'));
  const stats=isVin?[['VIN-formaat','17 tekens',''],['WMI',current.sections.vin_structuur?.[0]?.wmi||'—',''],['Decoder',sourceState('vin_decoder').status==='available'?'Beschikbaar':'Niet beschikbaar',''],['Bronnen',String(available)+' beschikbaar','']]:[['APK geldig tot',format('vervaldatum_apk',v.vervaldatum_apk),days===null?'':days<0?'tone-bad':days<=30?'tone-warn':''],['Brandstof',fuelText(),''],['Tellerstandoordeel',v.tellerstandoordeel||'—',v.tellerstandoordeel==='Onlogisch'?'tone-bad':''],['WAM-verzekerd',v.wam_verzekerd||'—',''],['Terugroepactie',v.openstaande_terugroepactie_indicator||'—',v.openstaande_terugroepactie_indicator==='Ja'?'tone-warn':''],['Import',importText(v),''],['Rijklaargewicht',format('massa_rijklaar',v.massa_rijklaar),''],['Trekgewicht geremd',format('maximum_trekken_massa_geremd',v.maximum_trekken_massa_geremd),'']];
  const summary=$('summary');summary.replaceChildren();for(const [title,value,tone]of stats){const s=element('div',undefined,'stat');s.append(element('small',title),element('strong',value,tone));if(title==='Import')s.title='Afgeleid: eerste registratie Nederland is later dan eerste toelating.';summary.append(s);}
  $('vehicle-photos').replaceChildren(...(isVin?[]:[photoView(true)]));
  $('tabs').replaceChildren();for(const [key,title]of (isVin?[['overzicht','VIN-overzicht'],['rapporten','Eigen rapporten'],['historie','Waarnemingen'],['bronnen','Bronnen'],['alle','Alle ontvangen data']]:TABS)){const b=element('button',title);b.dataset.key=key;b.setAttribute('role','tab');b.id='tab-'+key;b.setAttribute('aria-controls','details');b.addEventListener('click',()=>{activeTab=key;$('field-query').value='';$('details').setAttribute('aria-labelledby',b.id);renderDetails();b.scrollIntoView({block:'nearest',inline:'nearest'});});$('tabs').append(b);}
  activeTab='overzicht';$('field-query').value='';$('details').setAttribute('aria-labelledby','tab-overzicht');renderDetails();favoriteButton();
}
async function search(plate,refresh=false,selection=undefined,mode=undefined){
  const useVin=mode==='vin'||(mode===undefined&&String(plate).replace(/\s/g,'').length===17);$('lookup-mode').value=useVin?'vin':'plate';updateSearchMode();
  const id=++requestId;$('submit').disabled=true;$('refresh').disabled=true;$('result').hidden=true;$('welcome').hidden=true;current=null;message('Voertuiggegevens ophalen…');$('plate').value=plate;
  const params=new URLSearchParams();if(refresh)params.set('refresh','1');if(selection!==undefined)params.set('selection',JSON.stringify(selection));
  try{const response=await fetch((useVin?'/api/vin/':'/api/vehicle/')+encodeURIComponent(plate)+(params.size?'?'+params.toString():''));const data=await response.json();if(id!==requestId)return;if(!response.ok)throw new Error(data.error||'De gegevens konden niet worden opgehaald.');
    current=data;recent=[data.plate,...recent.filter(x=>x!==data.plate)].slice(0,8);saveList('kc-recent',recent);garage();render();message('');
  }catch(e){if(id===requestId){message(e.message||'Geen verbinding met de app.','error');$('welcome').hidden=false;}}
  finally{if(id===requestId){$('submit').disabled=false;$('refresh').disabled=false;}}
}
function compareValue(data,key){if(key==='vin_wmi')return data.sections.vin_structuur?.[0]?.wmi||'—';const v=data.sections.voertuig?.[0]||{};if(key==='brandstof')return data.sections.brandstof?.map(x=>x.brandstof_omschrijving).filter(Boolean).join(' + ')||'—';if(key==='import')return importText(v);return format(key,v[key]);}
function renderComparison(){
  $('comparison').hidden=false;$('comparison-hint').hidden=comparisons.length===2;const wrap=$('comparison-content');wrap.replaceChildren();
  const t=element('table'),head=element('tr');head.append(element('th','Gegeven'));comparisons.forEach(x=>head.append(element('th',x.plate)));t.append(head);
  for(const key of [...(comparisons.some(x=>x.lookup_type==='vin')?['vin_wmi']:[]),'merk','handelsbenaming','datum_eerste_toelating','brandstof','vervaldatum_apk','import','massa_rijklaar','maximum_trekken_massa_geremd','catalogusprijs','tellerstandoordeel']){const row=element('tr');row.append(element('th',label(key)));comparisons.forEach(x=>row.append(element('td',compareValue(x,key))));t.append(row);}wrap.append(t);
}
function updateSearchMode(){const isVin=$('lookup-mode').value==='vin';document.querySelector('.plate-input .nl').textContent=isVin?'VIN':'★\nNL';$('plate').maxLength=isVin?24:12;$('plate').placeholder=isVin?'17 tekens · VIN':'AB-123-C';$('identifier-label').textContent=isVin?'VIN / chassisnummer':'Nederlands kenteken';$('plate').closest('.plate-input').classList.toggle('vin-input',isVin);$('lookup-meta').textContent=isVin?'VIN-opbouw · Bronstatus · Eigen rapporten':'Registratie · Techniek · Keuringen · Terugroepacties';}
$('lookup-mode').addEventListener('change',()=>{updateSearchMode();$('plate').value='';$('plate').focus();});
$('search').addEventListener('submit',e=>{e.preventDefault();search($('plate').value,false,undefined,$('lookup-mode').value);});
$('refresh').addEventListener('click',()=>{if(current)search(current.plate,true);});
$('field-query').addEventListener('input',renderDetails);
$('tabs').addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;const tabs=[...$('tabs').children],i=tabs.indexOf(document.activeElement);if(i<0)return;e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[next].focus();tabs[next].click();});
$('favorite').addEventListener('click',()=>{if(!current)return;const p=current.plate;favorites=favorites.includes(p)?favorites.filter(x=>x!==p):[p,...favorites].slice(0,30);saveList('kc-favorites',favorites);garage();favoriteButton();});
$('export').addEventListener('click',()=>{if(!current)return;const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:'application/json'})),a=element('a');a.href=url;a.download=`${current.lookup_type==='vin'?'vin':'kenteken'}-${current.plate}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('print').addEventListener('click',()=>{if(!current)return;const previous=activeTab,query=$('field-query').value;activeTab='overzicht';$('field-query').value='';renderDetails();window.print();activeTab=previous;$('field-query').value=query;renderDetails();});
$('compare').addEventListener('click',()=>{if(!current)return;comparisons=[...comparisons.filter(x=>x.plate!==current.plate),current].slice(-2);renderComparison();$('comparison').scrollIntoView({behavior:'smooth'});});
$('history-export').addEventListener('click',async()=>{if(!current)return;try{const response=await fetch('/api/history/'+current.plate);if(!response.ok)throw new Error('Historie kon niet worden opgehaald.');const data=await response.json(),url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),a=element('a');a.href=url;a.download=`historie-${current.plate}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){message(e.message,'error');}});
$('close-comparison').addEventListener('click',()=>{$('comparison').hidden=true;comparisons=[];});
garage();
