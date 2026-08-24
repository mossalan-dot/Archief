# Oorlogsgravenstichting op de kaart — ogs.alanmoss.nl

Sobere kaart bij het OGS-archief (Nationaal Archief 2.19.255, ~206k personen):
twee lagen (herkomst = geboorteplaats, waar omgekomen = overlijdensplaats),
vaste stippen met kleur=aantal, doorzoekbaar op naam, per persoon een OGS-link.

## Pijplijn (`pijplijn/`)
1. `parse.py`     — verrijkte CSV → aggregaten + geocoding-targets + persons.json
2. `geocode.py`   — GeoNames (cities1000 + NL-dump) + gecureerde kampen/Indië → geocode.json (~93% dekking)
3. `build_data.py`— → `site/ogs_data.json` (0,7MB) + `site/personen.json` (35MB, gitignored)

Gazetteers niet in git: cities1000.txt, NL.txt (download.geonames.org). Bron-CSV: NT00446_OORLOGSGRAVEN_verrijkt.csv.
Deploy: scp `site/` naar /var/www/ogs (Caddy-vhost ogs.alanmoss.nl).
