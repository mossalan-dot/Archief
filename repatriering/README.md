# Repatriëring uit Indië 1945–1962

Route-/stroomkaart van de schepen die na de oorlog en de dekolonisatie mensen tussen
Nederlands-Indië/Indonesië en Nederland vervoerden. Reis-/schipniveau (geen persoonsdata):
per reis schip, vertrek/aankomst/via-haven + datum, aantal opvarenden (waar geteld), en een
link naar de passagierslijst-scan bij het NA. Live op **repatriering.alanmoss.nl**.

## Bronnen (passagierslijsten van het Nationaal Archief)

| Toegang | Bron | Inhoud |
|---|---|---|
| **2.19.277** | NRK-Informatiebureau, passagierslijsten | Repatriëringsschepen Indië → Nederland, 1945–1959; havens, datums, aantallen. |
| **2.13.103** | Collectie Troepenverschepingen van en naar Nederlands-Indië | Militaire troepen-/repatriantentransporten, 1945–1952; per schip de losse overtochten als datumbereik (havens/aantallen meestal niet vermeld → richting-neutraal getoond). |

Beide zijn uit de [zoekhulp Passagierslijsten 1878–1970](https://www.nationaalarchief.nl/onderzoeken/zoekhulpen/passagierslijsten-1878-1970).
De overige daar genoemde archieven (SMN 2.20.23, KJCPL 2.20.58.02, NASSI 2.20.27, …) zijn
bedrijfs-/organisatiearchieven zonder per-reis structuur en leveren geen route-records.

## Pijplijn
1. `parse_repat.py` — parse de EAD-inventaris `2.19.277.xml` → `repat_reizen.json`.
2. `parse_troepen.py` — parse `2.13.103.xml` (schip → per reis een datumbereik) → `troepen_reizen.json`.
3. `geocode_repat.py [bestand.json]` — gecureerde coördinatentabel voor de (historische) havens;
   normaliseert typo's; voegt `van_ll/via_ll/naar_ll` toe. Draai voor elke bron:
   `python3 geocode_repat.py repat_reizen.json && python3 geocode_repat.py troepen_reizen.json`.
4. `build_map_repat.py` — voegt beide bronnen samen → `index.html` + `data.json` (route-/stroomkaart),
   plus `inzichten.html` en `over.html`. Routes via Suez; tijdslider per jaar; **zoeken op scheepsnaam**;
   troepenverschepingen in een eigen kleur; klik = schip + route + datum + NA-scanlink per bron.

De EAD-XML's (`2.19.277.xml`, `2.13.103.xml`) staan in `.gitignore` (regenereerbaar: download bij het NA).
De geocodeerde `*_reizen.json` en de gebouwde pagina's staan wél in git.

Deploy = `scp index.html data.json inzichten.html over.html → /var/www/repatriering/`.

## Zoeken op scheepsnaam
Het zoekveld op de kaart filtert live op scheepsnaam (deelstring); de kaart zoomt mee op de
gevonden reizen. Werkt samen met de jaar-tijdschuif.
