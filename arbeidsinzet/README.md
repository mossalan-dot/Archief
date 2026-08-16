# Arbeidsinzet 1940–1945

Interactieve kaart van Nederlanders die tijdens de bezetting in Duitsland tewerkgesteld werden,
uit de geïndexeerde collectie Arbeidsinzet van het Nederlandse Rode Kruis
(Nationaal Archief **2.19.323**, index nt00475, CC-0). Live op **arbeidsinzet.alanmoss.nl**.

Persoon-gericht: zoek een persoon → diens Kreisen lichten op de kaart op, met een recordkaartje.
Twee weergaven (Herkomst NL / Bestemmingen DE) als gegradeerde bolletjes, klikbaar voor detail.

## Pijplijn
- `build_data2.py` — leest de EAD-inventaris + 3 CSV's (850.825 records), groepeert personen op
  `reconstructieid`, en schrijft `kaart_data.json` (kreisen + herkomst + vondsten) en `personen.json`
  (~300.000 personen, lazy geladen op de kaart).
- `geocode_missing.py` — geocodeert Kreisen zonder coördinaat (Nominatim, met naam-opschoning).

`personen.json`, de CSV-download en de EAD staan in `.gitignore` (te groot / regenereerbaar).
Deploy = `scp site-bestanden → /var/www/arbeidsinzet/`.
