# Holland-Amerika Lijn — emigrantenkaart (1900–1969)

Interactieve stromenkaart van de HAL-passagierslijsten (Stadsarchief Rotterdam **318-04**),
via **Open Archieven** (index 27, ~2,78 mln vermeldingen, CC0). LIVE: **hal.alanmoss.nl**.

## Aanpak (gekalibreerde schatting)
- **Exacte jaartotalen** via de Open Archieven statistiek-API (`stats/breakdown.json?group_by=year`).
- **Bestemmings-/schipverdeling** uit een API-steekproef, per jaar **opgeschaald** naar het exacte jaartotaal.
- **Richting** (emigratie/retour) uit de geografie van de bestemming (Amerika=west, Europa=oost).

## Pijplijn
1. `harvest_range.py <y0> <y1> <cap> <out.json>` — naam-sweep → folio's in jaarvenster → Show (Open Archieven API).
2. `accumulate.py <out.json>` — dedup toevoegen aan `harvest_all.json`.
3. `build_period.py harvest_all.json <y0> <y1>` — geocode (`geocode_full.py`) + kalibratie → `site/data.json` + `misses_current.json`.
4. `make_misses_xlsx.py` — niet-gematchte bestemmingen → Excel (2e check).

`geocode_full.py` gebruikt GeoNames `cities1000.txt` + `admin1.txt` (in `geo/`; cities1000 los downloaden van geonames.org) plus gecureerde havens/exonymen en Passagestaten-code-decodes (N.=New York, Mo.=Montreal, Hal.=Halifax, Qu.=Quebec).

## Site
`site/` = statische kaart (`index.html`), inzichten-dashboard (`inzichten.html`), over-pagina, `data.json`.
Deploy: `scp site/* root@server:/var/www/hal/`.

## Bekende beperkingen
- Dekking ~86% (vóór 1930 ~93%, 1950–69 ~82% door enkele-letter-codes in de Passagestaten-serie).
- Ambigue codes (S./L./C./H./M.) nog niet gedecodeerd — zie Excel.
