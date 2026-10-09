# Kenteken Check — 0.5.1

Een kentekenwebapp die alle ontvangen gegevens toont, met expliciete beschikbaarheid per bron. Zelf te hosten in Umbrel. De ingebouwde openbare bronnen vereisen geen API-sleutel of betaling.

## Wat is toegevoegd?

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

## Installeren en bijwerken

Umbrel → App Store → Community App Stores → voeg `https://github.com/TheRoyalCaptain/Kenteken-Check` toe. Ververs de store en installeer of update **Kenteken Check 0.5.1**. Herlaad de pagina na de update. Poort: 8767.

De [GitHub Actions-build](https://github.com/TheRoyalCaptain/Kenteken-Check/actions) publiceert AMD64 en ARM64 in GHCR. Het pakket moet openbaar zijn. Umbrel verzorgt het toegangsscherm. Voor ophalen is internettoegang naar `opendata.rdw.nl` nodig; de externe koppeling gebruikt `123kentekencheck.nl`.

## Bronnen en koppeling

De meegeleverde `rdw_catalog.json` is gecontroleerd tegen de officiële Socrata-catalogus van `opendata.rdw.nl` op **9 oktober 2026**. De app gebruikt alle 32 relevante voertuig-, keuring-, terugroep-, telleruitleg- en typegoedkeuringsdatasets uit die inventarisatie. Geen aparte aanvragen naar communityfilters die dezelfde onderliggende RDW-data dupliceren, en geen willekeurige koppelingen naar parkeerdata, bedrijfsregisters of tariefcatalogi die niet bij het voertuig horen.

Aanvullende kentekendatasets omvatten keuringsvervaldata (`vkij-7mwc`), voertuigsubcategorie (`2ba7-embk`), voertuigbijzonderheden (`7ug8-2dtt`) en rupsbanden (`3xwf-ince`). Terugroepgevaren (`9ihi-jgpf`), informeren (`mh8w-8cup`) en modellen (`mu2x-mu5e`) zijn gekoppeld op een terugroepreferentie die voor dit kenteken gevonden is. De modellenlijst beschrijft de actie en is geen lijst van eigenschappen van dit individuele voertuig. Telleruitleg (`jqs4-4kvw`) gebruikt de geregistreerde toelichtingscode.

De twaalf TGK-datasets omvatten basisuitvoering, aandrijving, versnelling, energiebron, assen, koppelingen, carrosserie, merk, handelsbenaming, speciale doeleinden, rupsbandsets en intrekkingen. De app gebruikt het **exacte** typegoedkeuringsnummer, en waar de dataset dat verlangt ook de exacte variant en uitvoering. Geen koppeling bij ontbrekende benodigde codes, geen afkappen van revisienummers en geen gok op een vergelijkbaar model. Goedkeuringsrevisies en technische grenswaarden behoren bij een typegoedkeuring en zijn geen bewijs van wijzigingen aan dit individuele voertuig.

## Aanvullende Nederlandse en Europese bronnen (0.5.1)

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

Waarnemingen staan in `/data/cache.sqlite` en blijven bij updates bestaan. De eerste waarneming komt uit de eerste zoekopdracht, of uit een nog aanwezige cache van een eerdere appversie. De oorspronkelijke ophaaldatum wordt behouden. Een latere eigen waarneming is **geen bewezen datum waarop de voertuigwijziging werkelijk plaatsvond**. Bij een storing wordt geen verdwenen voertuiggegeven als een wijziging gepresenteerd. Een andere volgorde van dezelfde bronrecords levert geen wijziging op.

Er wordt niet op de achtergrond dagelijks gecontroleerd: nieuwe waarnemingen ontstaan bij zoekopdrachten die verse gegevens ophalen of bij **Vernieuwen**. Er is geen gereconstrueerde historie van vóór de eerste bewaarde waarneming. Snapshots worden niet automatisch verwijderd, zodat je historie behouden blijft; de opslag groeit met het aantal wijzigingen.

Volledige resultaten worden maximaal een uur gecachet. Vernieuwen haalt opnieuw op. Aanvullende bronstoringen worden zichtbaar gemeld en dergelijke resultaten worden niet gecachet. Oude cachegegevens worden na zeven dagen bij een geslaagde aanvraag opgeschoond; de historie blijft bewaard. De update gebruikt een nieuwe schemaversie, zodat oude cache niet als een volledig nieuw resultaat wordt getoond.

Alle bronpagina's worden met paginering opgehaald; er is geen vaste limiet van 5000 records meer. Time-outs, een te groot individueel antwoord of fouten blijven mogelijk en krijgen een foutstatus. Geen stil afgekapt resultaat.

Favorieten en recente zoekopdrachten staan in de browser. Kentekens worden verstuurd naar de benodigde RDW-bronnen en, alleen met een ingestelde sleutel, de externe provider. Geen analytics of tracking.

## Ontwikkeling en tests

- `DATA_DIR=./data python app.py`
- `docker compose up --build -d`
- `python -m unittest discover -s tests -v`
- `node --check static/app.js`
- `npm install --no-save --package-lock=false playwright@1.61.1`
- `npx playwright install --with-deps chromium`
- `node tests/browser-smoke.cjs`

GitHub Actions voert backend- en browsercontroles uit vóór het bouwen van de container. Tests controleren bronstatussen, exacte koppelingen, paginering, historische snapshots, ontbrekende sleutels, tabbladen, oorspronkelijke velden, zoeken, favorieten, vergelijken, export en de mobiele layout. Installatie en werking via Umbrel moeten op de eigen server worden gecontroleerd.
