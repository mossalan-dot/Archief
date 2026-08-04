# Reizen van de Engelandvaarders 1940–1945

Interactieve kaart en inzichtendashboard van de reizen die Nederlandse verzetsdeelnemers ("Engelandvaarders") tijdens de Tweede Wereldoorlog aflegden om Engeland te bereiken.

**Live:** https://engelandvaarders.alanmoss.nl

- **Kaart** (`index.html`) — elke reis als lijn, gekleurd naar hoofdroute; zoeken op persoon, filters, reis-animatie, detailvenster met vlaggen en links naar het Nationaal Archief.
- **Inzichten** (`dashboard.html`) — kerncijfers, "Bijzondere vondsten"-carrousel en grafieken (vertrek per jaar/maand, hoofdroute, leeftijd, beroep, godsdienst, reisduur, aangedane plaatsen/landen).
- **Over** (`over.html`) — verantwoording en bronnen.

## Bron

Nationaal Archief, index **Engelandvaarders 1940–1945**
(zoekhulp: https://www.nationaalarchief.nl/onderzoeken/zoekhulpen/engelandvaarders-1940-1945).
De ruwe export staat in `bron.csv` (2.101 records).

## Pijplijn

```bash
python3 parse.py      # bron.csv → people.json + places_todo.json
python3 geocode.py    # geocodeert de ~1.250 unieke plaatsen via Nominatim → geocache.json
```

De kaart en het dashboard zijn statische HTML die `people.json` en `geocache.json` client-side inladen. Lokaal draaien:

```bash
python3 -m http.server 8899
```

## Licentie

Broncode: MIT. De onderliggende gegevens zijn afkomstig van het Nationaal Archief.
Kaartmateriaal © OpenStreetMap-bijdragers en CARTO.
