/* Derived summaries, not a new vehicle database. Shared with Node tests. */
(function(root){
 'use strict';
 function date(value){
  const s=String(value||''),m=s.match(/^(\d{4})-?(\d{2})-?(\d{2})(?:T.*)?$/);
  if(!m)return null;
  const d=new Date(Date.UTC(+m[1],+m[2]-1,+m[3]));
  return d.getUTCFullYear()===+m[1]&&d.getUTCMonth()===+m[2]-1&&d.getUTCDate()===+m[3]?d:null;
 }
 function assess(data,now=new Date()){
  const s=data.sections||{},v=s.voertuig?.[0]||{},rows=[];
  const add=(title,status,value,reason,source)=>rows.push({title,status,value,reason,source});
  const flag=(title,key,bad,explanation)=>{
   const value=v[key],known=['Ja','Nee'].includes(value);
   add(title,known?(value===bad?'attention':'reported'):'unknown',known?value:'Niet beschikbaar',known?explanation:'De bron levert dit gegeven niet; de status is onbekend.','RDW · '+key);
  };
  flag('Wacht op keuren','wacht_op_keuren','Ja','Een WOK-status is geen volledige schadehistorie en zegt niet wat de oorzaak is.');
  flag('Overschrijven mogelijk','tenaamstellen_mogelijk','Nee','Registratiestatus volgens RDW; controleer deze opnieuw bij overdracht.');
  flag('Export','export_indicator','Ja','Dit is de ontvangen exportindicator, niet de volledige exportgeschiedenis.');
  flag('WAM-verzekerd','wam_verzekerd','Nee','Dit is een registratie-indicator, geen dekking voor jou of toestemming om te rijden.');
  flag('Openstaande terugroepactie','openstaande_terugroepactie_indicator','Ja','Bekijk de kentekengekoppelde actie en laat de herstelstatus bevestigen.');
  const expiry=date(v.vervaldatum_apk),today=Date.UTC(now.getFullYear(),now.getMonth(),now.getDate()),days=expiry?Math.round((expiry.getTime()-today)/86400000):null;
  add('APK',days===null?'unknown':days<=30?'attention':'reported',days===null?'Niet beschikbaar':days<0?`${-days} dagen verstreken`:days===0?'Vervaldatum vandaag':`${days} dagen tot vervaldatum`,days===null?'Geen geldige APK-vervaldatum geleverd. Dit kan ook een voertuig zonder APK-plicht zijn.':'Een geldige APK is geen aankoopkeuring of garantie op technische staat.','RDW · vervaldatum_apk');
  const verdict=v.tellerstandoordeel;
  add('Tellerstandoordeel',verdict==='Onlogisch'?'attention':verdict==='Logisch'?'reported':'unknown',verdict||'Niet beschikbaar','Een logisch oordeel is geen actuele kilometerstand, geen volledige tellerhistorie en geen bewijs van schadevrijheid.','RDW · tellerstandoordeel');
  const first=date(v.datum_eerste_toelating),nl=date(v.datum_eerste_tenaamstelling_in_nederland);
  add('Importindicatie',first&&nl&&nl>=first?'context':'unknown',first&&nl&&nl>=first?(nl>first?'Eerste NL-registratie is later':'Geen verschil tussen registratiedatums'):'Niet beschikbaar','Afgeleid uit twee registratiedatums. Import is op zichzelf geen gebrek; buitenlandse historie is hiermee niet gecontroleerd.','Afgeleid · RDW-registratiedatums');
  add('Diefstalcheck','unknown','Niet beschikbaar','Er is geen geverifieerde diefstalbron aangesloten. Overschrijfbaarheid of een ontbrekende melding bewijst niet dat de auto niet gestolen is.','Geen aangesloten diefstalbron');
  return {evaluated_at:now.toISOString(),disclaimer:'Signalen uit ontvangen registraties, geen aankoopadvies, betrouwbaarheidsscore of garantie.',checks:rows};
 }
 const COST_FIELDS=['km_year','litres_100','fuel_price','kwh_100','electric_price','insurance_month','tax_quarter','maintenance_year','tyres_year','other_year','purchase','resale','years'];
 function costs(input){
  const values={},missing=[],invalid=[];
  for(const key of COST_FIELDS){const raw=input[key];if(raw===undefined||raw===null||String(raw).trim()===''){missing.push(key);continue;}
   const n=Number(String(raw).replace(',','.'));if(!Number.isFinite(n)||n<0||n>1e9||(key==='years'&&n===0))invalid.push(key);else values[key]=n;
  }
  if(missing.length||invalid.length)return {complete:false,missing,invalid};
  if(values.resale>values.purchase)return {complete:false,missing:[],invalid:['resale']};
  const fuel=values.km_year/100*values.litres_100*values.fuel_price,electric=values.km_year/100*values.kwh_100*values.electric_price;
  const annual={fuel,electric,insurance:values.insurance_month*12,tax:values.tax_quarter*4,maintenance:values.maintenance_year,tyres:values.tyres_year,other:values.other_year,depreciation:(values.purchase-values.resale)/values.years};
  const year=Object.values(annual).reduce((a,b)=>a+b,0);
  return {complete:true,annual,year,month:year/12,per_km:values.km_year?year/values.km_year:null};
 }
 const api={assess,costs,COST_FIELDS,date};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.KCInsights=api;
})(typeof globalThis!=='undefined'?globalThis:this);
