# Kenteken Check

Een eigen Nederlandse kentekenwebapp voor Umbrel, zonder betaalde API of betaalmuur. Dezelfde community-store en GHCR-buildopzet als Home Stock en Note Printer.

## Functies

- Registratie, APK-vervaldatum, WAM-indicatie, terugroepindicator, export en RDW-tellerstandoordeel.
- Technische gegevens, brandstof en emissies, gewichten en trekvermogen, assen, carrosserie en voertuigklasse.
- Zes officiële RDW Open Data-datasets; alle teruggegeven velden kunnen worden bekeken.
- Favorieten en recente zoekopdrachten in je browser, twee voertuigen vergelijken.
- JSON-download, afdrukken of opslaan als PDF via je browser.
- Mobiele interface met webappmanifest. Op iPhone: Safari → Deel → Zet op beginscherm.
- Cache op de Umbrel-server gedurende maximaal één uur, met expliciet vernieuwen en ophaaltijd.

## Installeren in Umbrel

1. Wacht op een geslaagde [GitHub Actions-build](https://github.com/TheRoyalCaptain/Kenteken-Check/actions).
2. Controleer dat het GHCR-pakket `kenteken-check` **Public** is. Een nieuw GHCR-pakket kan privé worden aangemaakt: GitHub → profiel → Packages → kenteken-check → Package settings → Change visibility → Public. De workflow heeft geen rechten om dit automatisch te veranderen.
3. Umbrel → App Store → Community App Stores → voeg `https://github.com/TheRoyalCaptain/Kenteken-Check` toe.
4. Installeer **Kenteken Check** en open de app via Umbrel.

Umbrel verzorgt het toegangsscherm; de app heeft geen extra login. Poort: 8767. De container luistert intern op 8080 en de Umbrel-proxy maakt deze bereikbaar. Er zijn geen API-sleutels nodig. Internettoegang naar `opendata.rdw.nl` is nodig voor nieuwe zoekopdrachten.

## Beschikbare gegevens en grenzen

Bronnen: [voertuig](https://opendata.rdw.nl/d/m9d7-ebf2), [brandstof](https://opendata.rdw.nl/d/8ys7-d773), [assen](https://opendata.rdw.nl/d/3huj-srit), [carrosserie](https://opendata.rdw.nl/d/vezc-m2t6), [specifieke carrosserie](https://opendata.rdw.nl/d/jhie-znh9), [voertuigklasse](https://opendata.rdw.nl/d/kmfi-hrps).

Niet elk veld is voor elk voertuig beschikbaar. De app onderscheidt een lege dataset van een mislukte aanvraag. Bij een storing van de basisregistratie wordt een fout getoond. Onvolledige aanvragen worden niet gecachet. Een kenteken zonder resultaat kan ontbreken uit de openbare registratie; dat bewijst niet dat het kenteken nooit bestaan heeft.

Geen eigenaargegevens, exacte kilometerstand, volledige schadehistorie, onderhoudshistorie, betaalde voertuigrapporten of actuele marktwaarde. Het tellerstandoordeel is geen tellerstand. Vermogen betreft RDW-vermogen per brandstofregistratie; bij een hybride is dit geen berekend gecombineerd systeemvermogen. De APK-datum en indicatoren zijn geregistreerde gegevens, geen garantie voor de actuele situatie. Er worden geen schattingen als officiële gegevens gepresenteerd.

Favorieten en recents zijn per browser/apparaat en verdwijnen wanneer je de websitegegevens wist. De cache staat in `/data/cache.sqlite` en blijft bestaan bij een containerupdate. Geen betaalde externe tracking of analytics. Kentekens worden naar RDW verstuurd om de gegevens op te halen. Servercache bevat maximaal zeven dagen aan opgehaalde registraties; oude regels worden bij een succesvolle nieuwe aanvraag verwijderd.

## Ontwikkeling

`python app.py` start de ontwikkelserver op `http://127.0.0.1:8080`. Gebruik bijvoorbeeld `DATA_DIR=./data python app.py` voor een lokale schrijfbare cache.

`docker compose up --build -d` start Gunicorn op `http://127.0.0.1:8767`. Deze lokale compose bindt uitsluitend aan localhost. Tests: `python -m unittest discover -s tests -v`; JavaScript: `node --check static/app.js`.

GitHub Actions test en publiceert `0.1.0` en `latest` voor AMD64 en ARM64. Voor een volgende release moeten de versie in de manifestbestanden, workflow, containerverwijzing en app worden bijgewerkt. Installatie en toegang via Umbrel moeten op de eigen Umbrel-server worden gecontroleerd.
