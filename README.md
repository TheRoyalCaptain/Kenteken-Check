# Kenteken Check

Een compacte kentekenwebapp voor Nederlandse voertuigen, met twaalf officiële RDW-datasets. Zelf te hosten in Umbrel, zonder betaalde API of API-sleutel.

## Versie 0.2.0

Volledig vernieuwde interface met een compacte zoekbalk, acht kerngegevens en tabbladen voor overzicht, techniek, motor en energie, keuringen, terugroepacties, extra en alle gegevens. Zoek op veldnaam of inhoud door alle beschikbare gegevens. Lege velden worden in het overzicht weggelaten.

Extra gegevens: keuringsmeldingen, geconstateerde gebreken met omschrijvingen die passen bij de keuringsdatum, ingebouwde objecten en kentekengebonden terugroepstatussen met actieomschrijving, mogelijke gevolgen en herstelmaatregel. Motorvermogen, WLTP-verbruik, elektrische actieradius en emissies zijn zichtbaar in een eigen tabblad wanneer geregistreerd.

Favorieten en recente zoekopdrachten blijven op hetzelfde apparaat. Vergelijk twee voertuigen, download het volledige JSON-resultaat of druk het compacte overzicht af als PDF.

## Installeren of bijwerken in Umbrel

1. Controleer de [buildstatus](https://github.com/TheRoyalCaptain/Kenteken-Check/actions).
2. Voeg in App Store → Community App Stores `https://github.com/TheRoyalCaptain/Kenteken-Check` toe.
3. Installeer **Kenteken Check**, of vernieuw de store en installeer de update naar **0.2.0**.
4. Herlaad de webapp na de update. Poort: 8767.

Umbrel verzorgt het toegangsscherm. De container gebruikt intern poort 8080. Internettoegang naar `opendata.rdw.nl` is nodig. De GHCR-image moet openbaar zijn; controleer bij een downloadfout GitHub → Packages → kenteken-check → Package settings → visibility. GitHub Actions bouwt AMD64 en ARM64.

## Databronnen

| Onderdeel | Officiële RDW-dataset |
|---|---|
| Voertuigregistratie | [m9d7-ebf2](https://opendata.rdw.nl/d/m9d7-ebf2) |
| Brandstof, motor en emissies | [8ys7-d773](https://opendata.rdw.nl/d/8ys7-d773) |
| Assen | [3huj-srit](https://opendata.rdw.nl/d/3huj-srit) |
| Carrosserie | [vezc-m2t6](https://opendata.rdw.nl/d/vezc-m2t6) |
| Specifieke carrosserie | [jhie-znh9](https://opendata.rdw.nl/d/jhie-znh9) |
| Voertuigklasse | [kmfi-hrps](https://opendata.rdw.nl/d/kmfi-hrps) |
| Keuringsmeldingen | [sgfe-77wx](https://opendata.rdw.nl/d/sgfe-77wx) |
| Geconstateerde gebreken | [a34c-vvps](https://opendata.rdw.nl/d/a34c-vvps) |
| Gebrekbeschrijvingen | [hx2c-gt7k](https://opendata.rdw.nl/d/hx2c-gt7k) |
| Ingebouwde objecten | [sghb-dzxx](https://opendata.rdw.nl/d/sghb-dzxx) |
| Kentekengebonden terugroepstatus | [t49b-isb7](https://opendata.rdw.nl/d/t49b-isb7) |
| Terugroepactie-details | [j9yg-7rg9](https://opendata.rdw.nl/d/j9yg-7rg9) |

De app haalt tien datasets op kenteken op. Omschrijvingen en actiedetails worden aanvullend op de gevonden codes opgehaald; bij geen codes is geen aanvullende aanvraag nodig. Er wordt geen recall op alleen merk of model als een bevestigde actie voor dit kenteken gepresenteerd.

## Interpretatie en beschikbaarheid

Gegevens zijn een momentopname. Een keuringsconstatering bewijst niet dat het gebrek nu nog aanwezig is. Een lege dataset bewijst niet dat een voertuig probleemvrij is. Keuringsmeldingen zijn geen volledige onderhouds-, APK- of schadehistorie. Geen eigenaargegevens, exacte kilometerstand of marktwaardeschatting. Tellerstandoordeel en tellerstand zijn verschillende gegevens.

Vermogen wordt per RDW-brandstofregistratie getoond en bij hybrides niet bij elkaar opgeteld. WLTP en NEDC blijven apart gelabeld. De importindicatie is afgeleid van een eerste registratie in Nederland die later ligt dan de eerste toelating. Ontbrekende datums leveren geen importoordeel op.

Bij een onbereikbare aanvullende bron blijven andere gegevens beschikbaar en is de storing zichtbaar. Historische gebrekbeschrijvingen worden geselecteerd op de geldigheidsperiode op de keuringsdatum. Als geen passende omschrijving bestaat, blijft de code zichtbaar. Langere datasets worden met paginering opgehaald; boven de limiet van 5000 regels wordt een expliciete fout getoond in plaats van een stil ingekort resultaat.

## Bewaren en privacy

De cache staat in `/data/cache.sqlite` en blijft behouden bij updates. Volledige resultaten worden maximaal een uur hergebruikt; **Vernieuwen** haalt opnieuw op. De schemawijziging negeert oude cache-uitkomsten, zodat de nieuwe onderdelen direct kunnen worden opgehaald. Onvolledige resultaten worden niet gecachet. Cachegegevens ouder dan zeven dagen worden bij een succesvolle nieuwe aanvraag verwijderd.

Favorieten en recente zoekopdrachten staan in browseropslag, blijven bij dezelfde URL behouden en verdwijnen als je websitegegevens wist. Kentekens worden naar de RDW gestuurd voor een zoekopdracht. Er is geen analytics of externe tracking.

## Ontwikkeling en controles

- `DATA_DIR=./data python app.py`: ontwikkelserver op `http://127.0.0.1:8080`.
- `docker compose up --build -d`: Gunicorn op `http://127.0.0.1:8767`.
- `python -m unittest discover -s tests -v`: backendtests.
- `node --check static/app.js`: JavaScript-syntaxis.
- Installeer Playwright voor de browserchecks: `npm install --no-save --package-lock=false playwright@1.61.1`, `npx playwright install --with-deps chromium`, vervolgens `node tests/browser-smoke.cjs`.

De browserchecks testen tabbladen, zoeken in gegevens, twee brandstoffen, terugroepdetails, fouten, lege resultaten, favorieten, vergelijken, JSON-export en layout op 320/390 pixels. GitHub Actions voert deze controles uit vóór het publiceren van de container.

De productie-app gebruikt alleen Python, Gunicorn en de meegeleverde statische bestanden. Geen Node-runtime vereist. Installatie en toegang via Umbrel moeten op de eigen server worden gecontroleerd.
