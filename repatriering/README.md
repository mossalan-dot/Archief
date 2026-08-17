# Repatriëring uit Indië 1945–1962

Route-/stroomkaart van de repatriëringsschepen die na de oorlog en de dekolonisatie Nederlanders en
militairen van Nederlands-Indië/Indonesië naar Nederland brachten. Bron: NRK-Informatiebureau,
passagierslijsten (**Nationaal Archief 2.19.277**, openbaar). Live op **repatriering.alanmoss.nl**.

Reis-/schipniveau (geen persoonsdata): per reis schip, vertrek/aankomst/via-haven + datum,
aantal opvarenden (waar geteld), en een link naar de passagierslijst-scan bij het NA.

## Pijplijn
1. `parse_repat.py` — parse de EAD-inventaris (`2.19.277.xml`, download bij het NA) → `repat_reizen.json`
   (641 reizen: schip, havens, datums, aantal personen, invnr, METS-scan).
2. `geocode_repat.py` — gecureerde coördinatentabel voor de (historische) havens; normaliseert typo's.
3. `build_map_repat.py` — Leaflet route-/stroomkaart (`site/index.html` + `data.json`); routes via Suez,
   tijdslider per jaar, klik = schip + route + datum + NA-scanlink.

`2.19.277.xml` staat in `.gitignore` (regenereerbaar). Deploy = `scp site → /var/www/repatriering/`.
