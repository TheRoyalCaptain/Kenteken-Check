# Kenteken Check — 0.11.0

## Operationeel voertuigregister (0.11.0)

Een nieuwe registerstijl met donkerblauw en antraciet, compacte gegevensrijen, genummerde dossiergroepen, technische datum- en tellernotatie en duidelijke statuskleuren. De app behoudt de eigen naam Kenteken Check en gebruikt een eigen KC-icoon. Geen politienaam, politielogo of officiële emblemen. Ook het inlogscherm, de mobiele weergave en het webapp-icoon sluiten aan op het nieuwe ontwerp.

## Dossierontwerp en zoekteller (0.10.0)

Een rustiger donker ontwerp met gegroepeerde dossiernavigatie, een geïntegreerde samenvatting en minder decoratieve kaartjes. Op mobiel schuift het dossiermenu horizontaal; alle onderdelen blijven bereikbaar.

Elk kenteken en VIN heeft een **persoonlijke zoekteller per account**, blijvend opgeslagen in SQLite. Een bewuste zoekopdracht (ook uit de cache of vanuit je garage) telt één keer. Vernieuwen, bronkeuzes, dagelijkse controles en mislukte aanvragen tellen niet mee. De teller begint bij deze versie: eerdere zoekopdrachten zijn niet achteraf te reconstrueren. Andere gebruikers zien jouw aantallen niet. Tellerwijzigingen maken geen nieuwe voertuigversie.

Een kentekenwebapp die alle ontvangen gegevens toont, met expliciete beschikbaarheid per bron. Zelf te hosten in Umbrel. De ingebouwde openbare bronnen vereisen geen API-sleutel of betaling.

## Accounts, database en dagelijkse controles (0.10.0)

De app gebruikt een eigen inlogscherm. Het Umbrel-pakket zet `PROXY_AUTH_ADD: "false"`. Maak bij de eerste opening direct je beheeraccount met een zelfgekozen wachtwoord van 12–128 tekens; er zijn geen standaardinloggegevens en geen openbare zelfregistratie na deze eerste inrichting. Rond dit af op je eigen vertrouwde netwerk voordat je de app aan anderen beschikbaar maakt. Via **Mijn account** kunnen beheerders gebruikers of extra beheerders aanmaken, accounts inschakelen/uitschakelen en wachtwoorden opnieuw instellen. Gebruikers wijzigen hun eigen wachtwoord met hun huidige wachtwoord. Houd voor herstel desgewenst een tweede beheerder aan; er is geen achterdeur of automatisch e-mailherstel.

Wachtwoorden zijn **scrypt-hashes** met een unieke willekeurige salt van 16 bytes, N=131072, r=8, p=1 en een afleiding van 64 bytes. Er staat geen leesbaar of ontsleutelbaar wachtwoord in de database. De instellingen volgen [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html). Een gestolen hash kan nog offline worden aangevallen; kies dus een sterk wachtwoord. Sessietokens zijn willekeurig met 256 bits; alleen hun SHA-256-hash staat in de database. Cookies zijn HttpOnly, SameSite=Lax en bij HTTPS Secure. Sessies verlopen na maximaal 12 uur of 30 minuten inactiviteit. Uitloggen verwijdert de sessie; wachtwoordwijziging/-reset en uitschakeling trekken bestaande sessies in. Inloggen is begrensd per account en server-waargenomen netwerkadres. Mutaties vereisen CSRF-controle; setup/login vereisen een header die een vreemde website zonder toegestane CORS niet kan versturen. Voertuig-, historie-, foto- en rapport-API’s vereisen een ingelogd account. Alleen de interfacebestanden en healthcheck zijn publiek.

Hashing beschermt opgeslagen wachtwoorden, niet netwerkverkeer. **Gebruik HTTPS voor toegang buiten je vertrouwde lokale netwerk.** `SESSION_COOKIE_SECURE=true` dwingt Secure-cookies af; standaard volgt dit HTTPS of de door de proxy doorgegeven HTTPS-indicator. Back-ups bevatten voertuiggegevens en wachtwoordhashes en moeten privé blijven. Toegang tot serverbeheer valt buiten de bescherming van een app-wachtwoord.

SQLite draait met WAL voor gelijktijdige toegang van webapp en monitor. `/data/platform.sqlite` bevat gebruikers, sessies, loginbegrenzing, favorieten, voorkeuren/begrotingen en controleplanning. `/data/users/<gebruikers-id>/cache.sqlite` bevat de gescheiden voertuigcache, bronkeuzes en versies. PDF’s en fotocaches staan in dezelfde persoonlijke omgeving. Er is geen losse databaseserver of databasewachtwoord nodig. Databasebestanden krijgen bestandsrechten 0600; nieuwe persoonlijke mappen 0700. Alles blijft op het persistente Umbrel-datavolume.

Bij de eerste beheerder worden de bestaande voertuigdatabase en PDF-/fotogegevens naar diens omgeving gemigreerd. De databasekopie wordt gecontroleerd en per kenteken/VIN begrensd op vier snapshots. Pas na het vastleggen van het beheeraccount wordt de oude database uit de hoofdmap verwijderd. Oude PDF-/fotomappen blijven als migratiekopie in de hoofdmap staan, maar zijn niet via andere gebruikers toegankelijk. Nieuwe gebruikers beginnen leeg. Voor oude browserfavorieten en hun begrotingen is er een expliciete beheerknop **Oude browserfavorieten importeren**. Nieuwe favorieten, recente zoekopdrachten en begrotingen staan in je account en werken ook op andere apparaten.

**Bewaren** slaat een voertuig op in je eigen garage. Voor Nederlandse kentekens staat dagelijkse controle standaard aan; die kan worden gepauzeerd. VIN’s kunnen worden bewaard, maar worden niet automatisch aan een mogelijk betaalde VIN-decoder aangeboden. De aparte `monitor`-container controleert iedere minuut de persistente planning en haalt verse kentekenresultaten op, ook met alle browsers gesloten. Na succes volgt de volgende controle 24 uur later; na een mislukking volgt na één uur een nieuwe poging. Een onderbroken job heeft een lease van 30 minuten en kan daarna opnieuw worden opgepakt. Tijdens de lease voeren meerdere monitorprocessen niet dezelfde job uit. Na downtime worden vervallen controles ingehaald. Maximaal 50 opgeslagen voertuigen per gebruiker. De monitor gebruikt per-kenteken opgeslagen bronkeuzes en eventueel de ingestelde 123kentekencheck-sleutel, binnen leveranciersquota. EEA blijft expliciet inschakelbaar; eerder gekozen bronopties gelden ook voor dagelijkse controles.

Per kenteken/VIN blijft **de huidige bewaarde versie plus maximaal drie oudere versies** staan. Ongewijzigde inhoud werkt alleen de laatste bevestigingsdatum bij. Bronstoringen of gedeeltelijk mislukte antwoorden verdringen geen goede versie. Veranderende contextbronnen of bronkeuzes kunnen ook een nieuwe snapshot opleveren; dat bewijst geen fysieke voertuigwijziging. Handmatige zoekopdrachten en de monitor gebruiken dezelfde bewaarlimiet. Meer dan drie oudere snapshots worden verwijderd. Bij **Versies** kun je de volledige ontvangen gegevens per bewaard moment bekijken; de historie-export bevat deze snapshots. Een favoriet verwijderen stopt de controle, maar wist niet het dossier of de maximaal vier snapshots. De limiet geldt voor snapshots, niet voor losse originele rapporten of records binnen een snapshot.

## Wat is toegevoegd?

- **Archief & status**: als een actuele RDW-basisregistratie ontbreekt of tijdelijk onbereikbaar is, zoekt de app het meest recente eerder bewaarde positieve voertuigrecord. Alle oorspronkelijke datasets uit diezelfde snapshot blijven apart leesbaar, doorzoekbaar en exporteerbaar, met waarnemingsdatum en laatste bevestiging van die ongewijzigde snapshot. Historische APK, verzekering en exportindicator worden niet in actuele velden teruggezet. Zonder eerdere waarneming blijft het archief expliciet niet beschikbaar.

### Voormalige kentekens: export, sloop en andere statussen

[RDW beschrijft de registerdekking](https://www.rdw.nl/over-rdw/dienstverlening/betaald-toegang-tot-ongevoelige-kentekengegevens): gesloopte voertuigen staan niet in dit register; exportinformatie kan tot twee jaar daarna beschikbaar zijn. Diefstalstatus zit niet in de open databestanden. Een lege actuele basisregistratie betekent daarom **niet** automatisch gesloopt, geëxporteerd, geschorst of gestolen. Een bronstoring krijgt een andere melding. Sloop-, schorsings- en diefstalstatus zijn in deze app niet bevestigd door een aangesloten onafhankelijke bron.

De openbare exportfilter (`hbkz-ufqe`) is een weergave van dezelfde RDW-basisdataset, geen historisch archief. CBS-uitvaltabellen geven totalen, geen individuele oude kentekendossiers. De reeds ondersteunde 123kentekencheck-API vermeldt RDW Open Data als onderliggende bron en is niet geverifieerd als oplossing voor verdwenen voertuigrecords. VWE heeft leveranciers-API’s voor voertuiginformatie, maar er is geen geautoriseerde leveranciersaccount aangesloten of vrij historisch endpoint bevestigd. Andere sites kunnen aanvullende gegevens tonen; de app claimt geen toegang tot hun databases.

Het lokale archief begint bij kentekens die **in deze installatie eerder met voertuiggegevens zijn opgezocht**. Het reconstrueert geen ontbrekende oudere dossiers van nog nooit opgezochte kentekens. Snapshots blijven in de bestaande SQLite-opslag, ook als de korte cache verloopt. Het archief bewijst alleen wat de app toen ontvangen heeft en geen huidige status. Externe PDF-rapporten kunnen per kenteken bij Rapporten worden bewaard; de inhoud wordt niet automatisch als geverifieerde status geïnterpreteerd.

- **Aankoopcheck**: APK-termijn, WOK, overschrijfbaarheid, export, WAM, tellerstandoordeel, terugroepindicator en afgeleide importindicatie. Onbekende controles blijven onbekend; geen commerciële betrouwbaarheidsscore of garantie. Evaluatie gebeurt op de dag van openen en staat in de JSON-export, met bronveld en uitleg.
- **Kostenplanner**: eigen praktijkverbruik en energieprijzen, kilometers, verzekering, kwartaalbelasting, onderhoud, banden, overige kosten en lineaire afschrijving. Volledig uitgewerkte begroting per jaar, maand en kilometer. Leeg is onbekend; niet van toepassing vul je zelf als 0 in. Geen verzonnen belastingtarieven, dagwaarde of RDW-testverbruik als praktijkmeting. Invoer wordt in je account opgeslagen per kenteken en wordt met herkomstlabel mee geëxporteerd.
- **Informatiedekking**: per onderwerp beschikbaar / deels beschikbaar / niet beschikbaar / ophalen mislukt. Openbare APK-data, modelcontext en voorbeeldfoto’s zijn geen volledige individuele historie. Diefstalhistorie en exacte fabrieksopties worden expliciet als niet beschikbaar gemeld.

### Vergelijking met andere kentekenchecks (9 oktober 2026)

Onderzocht: [Finnik](https://finnik.nl/account/), [AutoWeek](https://www.autoweek.nl/kentekencheck/), [KentekenCheck](https://www.kentekencheck.nl/schade-check) en [Carscanner](https://www.carscanner.nl/). Hun openbare productbeschrijvingen noemen voertuigstatus, technische/milieugegevens, APK, eigenaren, tellerstanden, waarde, kosten, opties, schade en advertenties. AutoWeek gebruikt naast RDW ook een eigen CarBase. Finnik onderscheidt gratis en premiuminformatie; KentekenCheck verkoopt aanvullende schaderapporten. Een zichtbare functie op een andere website betekent niet dat de onderliggende dataset of API vrij te gebruiken is.

De app ontsluit de ontvangen RDW-gegevens en bestaande aanvullende bronnen en voegt bovenstaande samenvatting, eigen kostenbegroting en dekkingsweergave toe. Er is geen volledige gelijkwaardigheid aan hun eigen/gelicentieerde databases. Exacte marktwaarde, historische eigenaren, schadebedragen/-foto’s, volledige kilometerreeksen, diefstalhistorie, historische advertenties en VIN-bouwlijsten zijn niet vrij beschikbaar gemaakt door deze vergelijking. Er worden geen betaalde rapporten besteld, concurrenten op kenteken gescrapet of ontbrekende gegevens ingevuld. Een bestaande eigen PDF kan in het lokale dossier worden toegevoegd, maar wordt niet automatisch als geverifieerde historie geïnterpreteerd.

- Alle **32 relevante officiële RDW-datasets** uit de gecontroleerde catalogus zijn gekoppeld: 14 op kenteken, 6 op gevonden referentiecodes en 12 op typegoedkeuring.
- Status per dataset: **Beschikbaar**, **Niet beschikbaar** of **Ophalen mislukt**, met reden en aantal records. Een lege bron wordt niet als geslaagd resultaat met volledige informatie gepresenteerd.
- Het tabblad **Alle ontvangen data** toont alle daadwerkelijk ontvangen velden, inclusief kenteken, bronlinks, oorspronkelijke datum/tijdvelden, lege strings, nullwaarden, onbekende velden en geneste externe JSON. Er worden geen velden weggefilterd. Meerdere records zijn uitklapbaar.
- Het tabblad **Bronnen** toont ook welke catalogusvelden wel of niet voor het kenteken zijn geleverd.
- **Historie** combineert gedateerde registratiegebeurtenissen, beschikbare keuringsmeldingen, gebreken, objectmontages en terugroeppublicaties. Het bewaart daarnaast eigen waarnemingen en veranderingen sinds het opzoeken in deze app.
- Een volledige geschiedenis-export bevat de bewaarde oorspronkelijke gegevens per waarneming.
- Optionele externe koppeling met de gedocumenteerde gratis API van 123kentekencheck.nl. Zonder persoonlijke sleutel wordt deze bron als niet beschikbaar / niet aangesloten vermeld.
- Ook zonder actuele basisregistratie worden onafhankelijke datasets en opgeslagen historie getoond.

## Voorbeeldfoto’s van model en kleur

Boven het overzicht en in **Foto’s** verschijnen maximaal vier herbruikbare Wikimedia Commons-foto’s. De zoekopdracht gebruikt merk, volledige handelsbenaming en eerste RDW-kleur; kenteken en VIN worden niet naar Commons verstuurd. Kies eerst het juiste model en de generatie bij **Aanvullende bronnen** of via **Model/generatie kiezen**. De app vereist een ondersteunde generatiecode (Romeins nummer of chassiscode) en controleert merk, volledige modelnaam en die generatie samen in één bronlabel, plus de kleur in bronmetadata en toont geen andere kleur als vervanging. Bij ontbrekende gegevens, geen passende zoekresultaten of een bronstoring verschijnt de reden in de bronstatus.

Het zijn voorbeeldauto’s, geen foto’s van het opgezochte kenteken. De match gebruikt bronmetadata, geen visuele herkenning. De generatie is door jou gekozen en op bronmetadata gematcht. Carrosserie, uitvoering en exacte lak blijven onbevestigd; RDW geeft een brede kleurcategorie, geen lakcode. Zonder modelkeuze of ondersteunde generatiecode worden geen foto’s getoond. Facelift wordt alleen geaccepteerd wanneer de modelmetadata dit expliciet bevestigen. Bouwjaar alleen wordt niet gebruikt om een generatie te raden. Oude fotocaches uit 0.5.0 worden niet gebruikt. Er is geen garantie dat Commons voor ieder model en elke kleur een geschikte foto heeft.

Elke foto vermeldt auteur, oorspronkelijke bron en licentie. Alleen ondersteunde vrije licenties worden geaccepteerd; bronmetadata blijven volledig in de gegevens en export staan. Afbeeldingen worden via de eigen server geladen. Internettoegang naar `commons.wikimedia.org`, `upload.wikimedia.org` en `thumb.wikimedia.org` is nodig. Zoekresultaten worden 24 uur lokaal gecachet; thumbnails worden lokaal bewaard. **Vernieuwen** ververst voertuiggegevens, maar respecteert deze fotocache. De kleine voorbeeldgalerij is geen volledige foto- of advertentiehistorie.

## Europese modelrapporten en eigen PDF’s (0.10.0)

**Rapporten** koppelt openbare modelrapporten van Euro NCAP, Green NCAP en ADAC. De app zoekt kandidaten uit de openbare bronindex op merk en modelfamilie. Dit zijn kandidaten, geen automatische bevestiging van generatie, motor of uitrusting. ADAC toont een selectie recente tests, geen volledige historische catalogus. Je kunt ook een directe HTTPS-modelrapportlink van een van deze drie bronnen invoeren. Controleer het originele rapport en bevestig de uitvoering vóór koppelen. De server controleert officiële host, rapportpad en merk/modelfamilie in de titel; bij twijfel wordt geen rapport gekoppeld.

De app haalt rapporttitel, bronbeschrijving en gevonden originele PDF-links op. Voor Euro NCAP wordt daarnaast de openbare testsamenvatting gelezen met testjaar, geteste uitvoering, sterren en beschikbare procentuele veiligheidsscores. Ontbrekende samenvattingsvelden worden niet ingevuld. Scores of rapportinhoud worden niet als feiten van het individuele kenteken geïnterpreteerd. De oorspronkelijke rapporten blijven bij de leverancier; beschikbaarheid en auteursrechten blijven daar gelden. Er is geen gegarandeerde openbare API: deze adapters lezen de openbare HTML-index en rapportpagina, en Euro NCAP de openbare sitemap. Bronwijzigingen kunnen een foutstatus of ontbrekende kandidaten opleveren. Een directe rapportlink blijft mogelijk wanneer de index niet beschikbaar is. Index en rapportmetadata worden 24 uur in servergeheugen gecachet. Kenteken en VIN worden niet naar deze bronnen verstuurd; kandidaten worden lokaal gefilterd op merk/modelfamilie.

Eigen PDF’s zoals Car-Pass, HistoVec, dealeruitdraaien en rechtmatig verkregen historie- of keuringsrapporten kun je per kenteken uploaden, downloaden en verwijderen. Maximaal 6 MB per bestand, 30 documenten per kenteken. Ze staan persistent in `/data/reports/`, los van voertuigcache en fotocache. Uploads worden niet naar externe bronnen verstuurd en hun inhoud wordt niet automatisch uitgelezen of als bewezen historie ingevoerd. De JSON-export bevat documentmetadata na openen van het rapporttabblad; PDF-bestanden download je afzonderlijk. Verwijderen wist het document direct. De app blijft achter het Umbrel-toegangsscherm: gebruikers met toegang tot deze app kunnen ook de rapporten benaderen.

CARFAX en carVertical worden niet automatisch bevraagd of aangekocht. Car-Pass en HistoVec worden niet als gratis openbare kenteken-API voorgesteld. Er worden geen accounts, betaalmuren of aanmeldschermen omzeild.

De interface heeft een donkere grafietstijl met duidelijke panelen, grotere tekst, hoog contrast en leesbare mobiele statistieken. Afdrukken gebruikt een lichte weergave.

## VIN / chassisnummer (0.10.0)

Kies **VIN / chassisnummer** bij het zoekveld of open een bewaard VIN. De app ondersteunt moderne VIN’s van 17 letters/cijfers zonder I, O of Q. Spaties en kleine letters worden genormaliseerd; oude kortere chassisnummers worden nog niet ondersteund. VIN-resultaten hebben een eigen overzicht, bronstatussen, doorzoekbare ontvangen velden, favorieten, recente zoekopdrachten, vergelijking, JSON-export, eigen waarnemingen en lokale PDF-rapporten. VIN en kenteken blijven afzonderlijke dossiers; er wordt geen voertuig op een vergelijkbaar model gekoppeld.

De gratis lokale controle toont de WMI-code, de tekenposities en het identificatiedeel. Alleen het invoerformaat wordt bevestigd, niet het bestaan van het voertuig of de toewijzing van WMI aan een fabrikant. Modeljaar, fabriek en controlecijfer worden niet volgens één universele regel gegokt. Ontbrekende schade-, kilometer-, onderhouds-, eigenaar-, diefstal- en individuele terugroepgegevens worden expliciet als niet beschikbaar gemeld. RDW Open Data levert geen openbare VIN-naar-kentekenzoekfunctie in de aangesloten datasets.

Voor uitgebreide VIN-decodering is een optionele Europese leveranciersadapter beschikbaar: **Vincario / vindecoder.eu**. Zet eigen `VINCARIO_API_KEY` en `VINCARIO_SECRET_KEY` in de containeromgeving. Sleutels worden niet naar de browser gestuurd of in GitHub gezet. Open het VIN-overzicht en schakel de bron expliciet in. De volledige VIN wordt dan naar de provider verstuurd. Deze bron gebruikt proefquota of betaald tegoed en is geen onbeperkte gratis API. Zonder sleutels of zonder inschakelen wordt geen externe aanvraag verstuurd. De adapter gebruikt het gedocumenteerde SHA-1-controlegetal en decode-endpoint, controleert het teruggeleverde volledige VIN en bewaart alle ontvangen JSON-velden. De adapter is met gecontroleerde antwoorden getest; er zijn hier geen eigen leverancierssleutels voor een live betaalde/geautoriseerde proef.

VIN-resultaten worden maximaal een uur gecachet; **Vernieuwen** kan bij ingeschakelde decoder opnieuw quota gebruiken. Bronkeuze wordt lokaal per VIN onthouden. Bij een providerstoring blijven de structuurcontrole en eigen documenten beschikbaar en wordt geen onvolledig resultaat gecachet. Eigen waarnemingen zijn geen gereconstrueerde geschiedenis van vóór het gebruik van de app. PDF’s staan in `/data/users/<gebruikers-id>/reports/<VIN>/`. Er wordt geen VIN naar RDW, fotobronnen of modelrapportbronnen doorgestuurd vanuit de VIN-check.

## Installeren en bijwerken

Umbrel → App Store → Community App Stores → voeg `https://github.com/TheRoyalCaptain/Kenteken-Check` toe. Ververs de store en installeer of update **Kenteken Check 0.11.0**. Herlaad de pagina na de update. Poort: 8767.

De [GitHub Actions-build](https://github.com/TheRoyalCaptain/Kenteken-Check/actions) publiceert AMD64 en ARM64 in GHCR. Het pakket moet openbaar zijn. De app verzorgt eigen accounts en het toegangsscherm. Voor ophalen is internettoegang naar `opendata.rdw.nl` nodig; de externe koppeling gebruikt `123kentekencheck.nl`.

## Bronnen en koppeling

De meegeleverde `rdw_catalog.json` is gecontroleerd tegen de officiële Socrata-catalogus van `opendata.rdw.nl` op **9 oktober 2026**. De app gebruikt alle 32 relevante voertuig-, keuring-, terugroep-, telleruitleg- en typegoedkeuringsdatasets uit die inventarisatie. Geen aparte aanvragen naar communityfilters die dezelfde onderliggende RDW-data dupliceren, en geen willekeurige koppelingen naar parkeerdata, bedrijfsregisters of tariefcatalogi die niet bij het voertuig horen.

Aanvullende kentekendatasets omvatten keuringsvervaldata (`vkij-7mwc`), voertuigsubcategorie (`2ba7-embk`), voertuigbijzonderheden (`7ug8-2dtt`) en rupsbanden (`3xwf-ince`). Terugroepgevaren (`9ihi-jgpf`), informeren (`mh8w-8cup`) en modellen (`mu2x-mu5e`) zijn gekoppeld op een terugroepreferentie die voor dit kenteken gevonden is. De modellenlijst beschrijft de actie en is geen lijst van eigenschappen van dit individuele voertuig. Telleruitleg (`jqs4-4kvw`) gebruikt de geregistreerde toelichtingscode.

De twaalf TGK-datasets omvatten basisuitvoering, aandrijving, versnelling, energiebron, assen, koppelingen, carrosserie, merk, handelsbenaming, speciale doeleinden, rupsbandsets en intrekkingen. De app gebruikt het **exacte** typegoedkeuringsnummer, en waar de dataset dat verlangt ook de exacte variant en uitvoering. Geen koppeling bij ontbrekende benodigde codes, geen afkappen van revisienummers en geen gok op een vergelijkbaar model. Goedkeuringsrevisies en technische grenswaarden behoren bij een typegoedkeuring en zijn geen bewijs van wijzigingen aan dit individuele voertuig.

## Aanvullende Nederlandse en Europese bronnen (0.10.0)

De app gebruikt Nederlandse en Europese voertuiggegevens. Wikimedia Commons levert daarnaast herbruikbare voorbeeldfoto’s. Geen Amerikaanse VIN-, EPA-, crashtest- of modeldatabronnen. Alle aanvullende bronnen staan met status in zoekresultaten, **Bronnen** en **Alle ontvangen data**.

- **Teruggeroepen.nl**: automatisch gekoppeld op de terugroepreferenties die RDW voor het kenteken heeft geleverd. Het volledige oorspronkelijke antwoord bevat ook broninformatie, modellen, aantallen en datums. De onderliggende data komen uit RDW; dit is geen onafhankelijke extra bevestiging. Een ontbrekende melding en een storing krijgen verschillende statussen. Attribution en bronlink staan bij de resultaten. Documentatie: https://www.teruggeroepen.nl/api
- **autoseeker.eu**: gratis Europese modelcatalogus onder CC BY 4.0. Open **Aanvullende bronnen** en selecteer zelf een model/generatie van hetzelfde merk. De server controleert merk en catalogus-ID. Geen automatische gok op model of bouwjaar. Alle originele specificaties en catalogusmetadata worden getoond en bewaard, met bronvermelding en link. De catalogus is indicatief en bevat niet iedere historische uitvoering; gegevens zijn geen bewezen eigenschappen van jouw specifieke auto. Documentatie: https://autoseeker.eu/data/
- **European Environment Agency (EEA)**: de openbare Discodata-API met Europese CO2-registraties. Expliciet inschakelbaar bij **Aanvullende bronnen**; vóór het ophalen staan de te versturen typegoedkeurings-, variant- en uitvoeringscodes in beeld. Het kenteken wordt niet verstuurd. De adapter gebruikt de volledige exacte codes, filtert ook de ontvangen records op letterlijke overeenstemming en haalt alle pagina's op. Geen koppeling als codes ontbreken of de exacte uitvoering niet wordt gevonden. Gegevens tonen Europese registraties van dezelfde uitvoering, met land, registratiejaar, voorlopige/definitieve status en originele emissie-/technische velden. Dit is geen historie van het individuele voertuig. Documentatie: https://discodata.eea.europa.eu/Help.html

EEA is standaard uitgeschakeld. De openbare API en schema zijn gecontroleerd met een algemeen voorbeeldrecord. Een live proef met codes uit het lokale voertuigresultaat is door automatische goedkeuringscontrole geblokkeerd en daardoor niet afgerond. De adapter is met gecontroleerde bronantwoorden getest; toestemming voor die specifieke live proef is nog nodig. De Nederlandse terugroep-API en Europese modelcatalogus zijn wel live gecontroleerd.

Modelkeuze en EEA-keuze worden per kenteken lokaal bewaard en bij latere zoekopdrachten gebruikt. Verwijder een modelkeuze met **Modelselectie verwijderen**. Schakel EEA uit door het vinkje weg te halen en **EEA-keuze opslaan** te kiezen. Eerder ontvangen context blijft in de historie-export; wijzigingen van contextbronnen worden niet als individuele voertuiggebeurtenissen gepresenteerd. De modelcatalogus wordt maximaal 24 uur in geheugen gecachet. Voor grote bronnen toont de interface 50 records tegelijk, met **Toon volgende records**; alle opgehaalde records staan in de JSON-export en zijn doorzoekbaar.

De optionele 123kentekencheck-koppeling blijft beschikbaar met persoonlijke API-sleutel. Andere leveranciers met alleen een gratis demo of testdataset zijn niet als onbeperkte gratis bron aangesloten.

## Externe gegevens

De optionele integratie gebruikt de gedocumenteerde endpoints:

- `/api/v1/kenteken/{kenteken}`
- `/api/v1/kenteken/{kenteken}/apk`
- `/api/v1/kenteken/{kenteken}/terugroepacties`
- `/api/v1/kenteken/{kenteken}/waarde`

Deze bron adverteert een gratis API met een persoonlijke sleutel en fair-use-limieten. De provider bepaalt welke gegevens per kenteken worden geleverd. API-key aanvragen: `https://123kentekencheck.nl/api/aanmelden`. Zet de ontvangen sleutel zelf in de containeromgeving als `KENTEKEN_API_KEY`; zet geen sleutel in GitHub. De composebestanden ondersteunen deze omgevingsvariabele. Op Umbrel moet de variabele in de daadwerkelijk gebruikte containerconfiguratie beschikbaar zijn. Zonder sleutel wordt er geen aanvraag naar deze provider gedaan.

De externe adapter bewaart en toont de gehele JSON-respons zonder een onbekend schema als officiële feiten te interpreteren. Waarde-indicaties zijn externe schattingen. Deze integratie is met gecontroleerde antwoorden getest; een persoonlijke sleutel is hier niet beschikbaar, dus een echte geautoriseerde providerrespons is niet getest. De standaard RDW-koppelingen zijn live getest.

## Wat betekent “alle data”?

Alle gegevens die de aangesloten bronnen bij een succesvolle aanvraag leveren, worden behouden en zijn zichtbaar of uitklapbaar. Ontbrekende velden worden niet ingevuld met verzonnen waarden. **Dit betekent niet dat alle informatie die ooit over een voertuig heeft bestaan openbaar beschikbaar is.**

Kilometerstandhistorie, volledige eigenaarshistorie, volledige schadehistorie, onderhoudsbeurten en advertentiehistorie worden expliciet als niet beschikbaar via de aangesloten bronnen vermeld. Een laatste tenaamstellingsdatum is geen reeks eigenaarwisselingen. Het RDW-voertuigrapport kan aanvullende historie bevatten, maar vereist toegang van de eigenaar/houder via DigiD of zakelijke authenticatie en is geen openbare API. Er worden geen betaalmuren, inlogschermen of anti-botbeperkingen omzeild.

Historische websites zijn onderzocht. Andere RDW-overzichten zonder geverifieerde openbare API zijn niet als werkende historische bron toegevoegd. De app beweert niet dat ontbrekende historie niet bestaat; alleen dat ze via de aangesloten bronnen niet geleverd wordt. Een storing krijgt de aparte status **Ophalen mislukt**.

## Historie en bewaren

Waarnemingen staan in `/data/users/<gebruikers-id>/cache.sqlite` en blijven bij updates bestaan. De eerste waarneming komt uit de eerste zoekopdracht, of uit een nog aanwezige cache van een eerdere appversie. De oorspronkelijke ophaaldatum wordt behouden. Een latere eigen waarneming is **geen bewezen datum waarop de voertuigwijziging werkelijk plaatsvond**. Bij een storing wordt geen verdwenen voertuiggegeven als een wijziging gepresenteerd. Een andere volgorde van dezelfde bronrecords levert geen wijziging op.

Voor opgeslagen kentekens met controle ingeschakeld draait de monitor dagelijks; zoekopdrachten en Vernieuwen kunnen ook nieuwe versies opleveren. Per dossier blijven de huidige versie en maximaal drie oudere versies behouden. Er is geen gereconstrueerde historie van vóór de eerste bewaarde waarneming.

Volledige resultaten worden maximaal een uur gecachet. Vernieuwen haalt opnieuw op. Aanvullende bronstoringen worden zichtbaar gemeld en dergelijke resultaten worden niet gecachet. Oude cachegegevens worden na zeven dagen bij een geslaagde aanvraag opgeschoond; de historie blijft bewaard. De update gebruikt een nieuwe schemaversie, zodat oude cache niet als een volledig nieuw resultaat wordt getoond.

Alle bronpagina's worden met paginering opgehaald; er is geen vaste limiet van 5000 records meer. Time-outs, een te groot individueel antwoord of fouten blijven mogelijk en krijgen een foutstatus. Geen stil afgekapt resultaat.

Favorieten en recente zoekopdrachten staan in je persoonlijke databaseopslag. Kentekens worden verstuurd naar de benodigde RDW-bronnen en, alleen met een ingestelde sleutel, de externe provider. Geen analytics of tracking.

## Ontwikkeling en tests

- `DATA_DIR=./data python app.py`
- `DATA_DIR=./data python worker.py` (naast de webapp; Docker Compose start deze service automatisch)
- `docker compose up --build -d`
- `python -m unittest discover -s tests -v`
- `node --check static/app.js`
- `node --check static/accounts.js`
- `node tests/insights.cjs`
- `npm install --no-save --package-lock=false playwright@1.61.1`
- `npx playwright install --with-deps chromium`
- `node tests/browser-smoke.cjs`

GitHub Actions voert backend- en browsercontroles uit vóór het bouwen van de container. Tests controleren bronstatussen, exacte koppelingen, paginering, historische snapshots, ontbrekende sleutels, tabbladen, oorspronkelijke velden, zoeken, favorieten, vergelijken, export en de mobiele layout. Installatie en werking via Umbrel moeten op de eigen server worden gecontroleerd.
