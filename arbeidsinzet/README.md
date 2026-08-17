# Arbeidsinzet 1940–1945

Interactieve kaart van Nederlanders die tijdens de bezetting in Duitsland tewerkgesteld werden,
uit de geïndexeerde collectie Arbeidsinzet van het Nederlandse Rode Kruis
(Nationaal Archief **2.19.323**, index nt00475, CC-0). Live op **arbeidsinzet.alanmoss.nl**.

Persoon-gericht: zoek een persoon → diens Kreisen lichten op de kaart op, met een recordkaartje.
Twee weergaven (Herkomst NL / Bestemmingen DE) als gegradeerde bolletjes, klikbaar voor detail.

## Pijplijn (in deze volgorde)
1. `build_data2.py` — leest de EAD-inventaris + 3 CSV's (850.825 records), groepeert personen op
   `reconstructieid`, en schrijft `kaart_data.json` (kreisen + herkomst + gender + geboortejaren) en
   `personen.json` (~300.000 personen, lazy geladen op de kaart) + `arbeidsinzet_kreisen.csv`.
2. `geocode_missing.py` — geocodeert Kreisen zonder coördinaat (Nominatim, met naam-opschoning).
3. `link_ogs.py` — koppelt de **overledenen** aan de **Oorlogsgravenstichting**-index
   (NA nt00446, `~/Downloads/NT00446_OORLOGSGRAVEN.csv`) op achternaam + volledige sterfdatum
   (voornaam/geboorteplaats als tiebreak) → voegt `ogs` (UUID) toe aan `personen.json`.
   In de kaart krijgt een overledene dan een link naar het OGS-dossier bij het NA + een
   Oorlogsbronnen-zoeklink. (~9.700 van 27.500 overledenen gekoppeld.)

`personen.json`, de bron-CSV's (arbeitseinsatz + OGS) en de EAD staan in `.gitignore`
(te groot / regenereerbaar). Deploy = `scp site-bestanden → /var/www/arbeidsinzet/`.
