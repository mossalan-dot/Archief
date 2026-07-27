# Carnegie Heldenfonds — kaart & inzichten

Een interactieve kaart en een statistiekendashboard op basis van de **9.628 persoonsdossiers** van het
Nederlandse Carnegie Heldenfonds (Nationaal Archief, toegang [2.19.364](https://www.nationaalarchief.nl/onderzoeken/archief/2.19.364), 1903–1987).
Elke beloonde redding is met behulp van AI uit de dossierbeschrijvingen gestructureerd en op de kaart geplot.

- 🗺️ **Kaart:** <https://grisburgh.nl/carnegie>
- 📊 **Inzichten & statistiek:** <https://grisburgh.nl/carnegie/stats>
- ℹ️ **Over / verantwoording:** <https://grisburgh.nl/carnegie/over>
- 📄 **Data (download):** <https://grisburgh.nl/carnegie/dossiers.csv> · <https://grisburgh.nl/carnegie/dossiers.json>

> Deze repo bevat de **code** (de pijplijn-scripts). De afgeleide data en de gebouwde pagina's staan live op de
> bovenstaande adressen. Het draaien van de pijplijn vereist de inventaris-PDF van het Nationaal Archief (2.19.364).

## Wat het is

Het Carnegie Heldenfonds (opgericht 1911, naar het Amerikaanse voorbeeld van Andrew Carnegie) beloonde mensen
die met gevaar voor eigen leven anderen redden. De inventaris beschrijft elke redding volgens een vast stramien:
*"[naam], redde in [jaar] te [plaats] een kind uit het water van de [gracht]…"*. Die regelmaat maakt het
mogelijk alle ~9.600 beschrijvingen in één keer te lezen en te analyseren.

## De pijplijn

Elke stap is een los, reproduceerbaar script (`pijplijn/`):

| Script | Doet |
|---|---|
| `parse.py` | `pdftotext`-uitvoer van de inventaris → `dossiers_raw.json` (nr, namen, jaar, plaats, aard, openbaarheid, foto's). Herstelt o.a. over regeleinden afgebroken plaatsnamen. |
| `geocode.py` | Plaatsnamen → coördinaten via **Nominatim/OpenStreetMap**, met NL-bounding-box, alias-correcties en afstandsvalidatie. Cache: `geocache.json`. |
| `geocode_detail.py` | Straat/water-niveau: `"<detail>, <plaats>"`, gevalideerd op <15 km van de plaats. Cache: `geocache_detail.json`. |
| `cats.py` | Gedeelde logica: **categorisering** (aard van de redding), **afloop** (geslaagd/poging), **ondersteuning**-vlag, redder-naam en **Delpher**-zoekopdracht. |
| `gender.py` | Schatting van het **geslacht** van de redder (voornamenlijst + uitgangen + gehuwde-vrouw-vorm). |
| `stats.py` | Aggregaties → `stats.json`. |
| `export.py` | `dossiers.csv` + `dossiers.json` (incl. categorie, afloop, geslacht, coördinaten, NA- en Delpher-URL). |
| `build_map.py` | Genereert de self-contained kaart-HTML (Leaflet + markercluster). |
| `build_stats.py` | Genereert het dashboard-HTML (Chart.js). |

Reproduceren: `python3 parse.py && python3 geocode.py && python3 geocode_detail.py && python3 stats.py && python3 export.py && python3 build_map.py kaart.html && python3 build_stats.py`.

## Designkeuzes

- **Leaflet + OpenStreetMap**, geen Mapbox. Gratis, tokenloos, privacyvriendelijk — en 9.600 geclusterde punten
  draaien er prima op. (Wil je ooit vector-tiles/heatmap, dan is [MapLibre GL](https://maplibre.org) de gratis route.)
- **Grote steden** (Amsterdam ~1.400 dossiers op één punt) zouden een onbruikbare "wolk" geven; daarom opent een
  klik op een dichte cluster een **doorzoekbare dossierlijst** i.p.v. duizenden overlappende markers.
- **Straat/water-verfijning**: waar de beschrijving een gracht/haven noemt, staat de marker daar (±3.600 dossiers)
  i.p.v. in het stadscentrum.
- **Categorieën** zijn de *aard van de redding* (water, zee/kust, ijs, auto, trein, brand, op hol/dier). "Ondersteuning
  nabestaanden" is géén aard maar een **filtervlag**; de daad van de overleden redder wordt zelf gecategoriseerd.
- **Delpher-zoeklink**: `"<eerste voornaam> <achternaam>" + plaats + water-detail`. Volledige doopnamen geven nul
  krantentreffers; deze formule vindt het reddingsbericht zelf.
- **Eerlijke onzekerheid**: aard, afloop en geslacht zijn *afgeleid* uit vrije tekst en dus bij benadering. Het
  dashboard en deze README benoemen dat expliciet.

## Belangrijke kanttekeningen

- Het bestand is een **momentopname tot ~1987**; de stichting bestaat nog en kent nog steeds onderscheidingen toe.
  Tijdreeksen "verdampen" richting het einde — geen echte afname.
- De **Watersnoodramp van 1953** ontbreekt vrijwel: veel van die erkenningen kwamen pas decennia later, buiten dit
  dossierblok. Een gat in de data duid je pas met de context (inleiding, bestuursarchief 2.19.352, en
  C.P. Mulder & M. Spaans, *Honderd jaar helden*, 2011).
- De **geslachtsschatting** is indicatief (voornaam-heuristiek).

## Data & bronvermelding

- Bron: Nationaal Archief, *Stichting Carnegie Heldenfonds Nederland — Persoonsdossiers, 1903-1987* (2.19.364).
  De inventarisbeschrijvingen zijn openbaar; de fysieke dossiers zijn deels beperkt openbaar.
- Kaartachtergrond: © OpenStreetMap-bijdragers.
- De afgeleide dataset (CSV/JSON, te downloaden via de site) mag vrij worden hergebruikt met bronvermelding.

## Gemaakt met

Gebouwd met AI-ondersteuning (Claude) als experiment in het op schaal ontsluiten van archiefbeschrijvingen —
zie ook de begeleidende tekst *"Negenduizend helden, in één oogopslag"*.
