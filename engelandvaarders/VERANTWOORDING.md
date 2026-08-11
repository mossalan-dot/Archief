# Verantwoording — brondata en selectie Engelandvaarders-kaart

_Laatst bijgewerkt: 10 augustus 2026_

Dit document legt de methodologische en ethische keuzes vast achter de dataset van de
interactieve kaart op **engelandvaarders.alanmoss.nl**, in het bijzonder na de overstap
van de open NA-index naar het rijkere bronbestand van juli 2026.

## 1. Bronnen

- **Oorspronkelijke bron (t/m juli 2026):** de online index **Engelandvaarders 1940–1945**
  van het Nationaal Archief (toegang/index **NT00464**), 2.101 records. Openbaar
  raadpleegbaar; per persoon een recordpagina (GUID) en veelal een scanverwijzing.
- **Nieuwe bron (vanaf 10 augustus 2026):** `20260717 - Totaaloverzicht Engelandvaarders
  WO2Net.xlsx` — een gecureerd totaaloverzicht (3.141 personen, 3.123 UUID's) met o.a.
  reisetappes mét datums, overlijdensdata, politieke richting, reisgezelschap en
  verwijzingen naar zeven archieftoegangen. Daarnaast een tabblad **helpers** (±115
  passeurs, onderduikgevers en ontsnappingslijnen).

De nieuwe bron is leidend voor de verrijking; de open NA-index blijft de ondergrens van
wat sowieso getoond wordt (zie §3).

## 2. Afbakening: wie is "Engelandvaarder"?

Het bronbestand kent een veld **Status** dat personen indeelt. Wij hanteren drie lagen:

1. **Engelandvaarders** (kern) — de eigenlijke Engelandvaarders. Standaard zichtbaar.
2. **Randgevallen** — *twijfelgeval*, *Indiëvaarder* en de diverse *afgevallen –* categorieën
   (bijv. "niet via bezet gebied", "vanuit Zweden niet doorgereisd", "Vreemdelingenlegioen",
   "linecrosser", "Internationale Brigades"). Deze horen niet zonder meer bij de kern, maar
   zijn historisch verwant; ze worden als apart, gedempt filterlaagje getoond.
3. **Uitgesloten** — zie §4.

De keuze om randgevallen wél te bewaren maar visueel te scheiden, volgt de opzet van de
bron zelf en voorkomt dat we stilzwijgend een interpretatie opleggen over wie "echt"
telde.

## 3. Ethiek en privacy

Leidend beginsel: **geen mogelijk nog levende personen zonder noodzaak in beeld brengen.**
Concreet:

- **Reeds openbaar blijft openbaar.** Iedereen die al in de open NA-index (NT00464) stond,
  blijft opgenomen — die gegevens waren immers al publiek toegankelijk.
- **Nieuwe toevoegingen** (personen die *niet* al in de NA-index staan) nemen we alléén op
  wanneer aan minstens één van deze voorwaarden is voldaan:
  - er is een **overlijdensdatum** vastgesteld, **of**
  - de persoon is geboren **vóór 10 augustus 1916** (op de peildatum ≥110 jaar).
- Nieuwe toevoegingen die mogelijk nog leven (geen sterfdatum én geboren op/na 10-8-1916)
  worden **weggelaten**.

Deze drempel van 110 jaar sluit aan bij de gangbare archiefpraktijk voor het openbaar maken
van persoonsgegevens bij ontbrekende sterfdatum.

## 4. Categorieën die wij uitsluiten

Twee groepen laten we principieel **niet** zien, ook niet als randgeval:

- **Politiek onbetrouwbaar** (Status "afgevallen – politiek onbetrouwbaar").
- **NSB** (personen met politieke richting NSB).

Reden: deze etiketten zijn belastend en betreffen een oordeel over de persoon dat niet past
bij het karakter van dit project (het in kaart brengen van vluchtroutes), en dat we niet
zonder nadere duiding willen reproduceren.

## 5. Koppeling oude ↔ nieuwe data

Om te bepalen of iemand "al in de NA-index stond", koppelen we het nieuwe bestand aan de
bestaande dataset via:

1. het **inventarisnummer** in de bestaande NA-link (`…/archief/2.09.06/invnr/<nr>`), dat
   als kolomwaarde ook in het nieuwe bestand voorkomt (harde sleutel); en
2. een **genormaliseerde volledige naam** (alle naamdelen aaneen, zonder leestekens) als
   terugvalsleutel.

Van de 2.101 bestaande records vinden we er langs deze weg **2.087 terug** (14 niet, door
spellingsvarianten). Om te voorkomen dat iemand die al openbaar was door de overstap
verdwijnt, hanteren we een **unie**: niet-teruggevonden bestaande records worden
ongewijzigd overgenomen. **Niemand valt weg.**

## 6. Reisroutes en datums

- De reis wordt opgebouwd uit de **etappekolommen** (locatie + datum van vertrek en aankomst
  per etappe). Interneringskampen staan als `[kamp …]` / `[Centre d'Accueil]` voor de
  plaatsnaam en krijgen een eigen weergave.
- Waar etappegegevens ontbreken, vallen we terug op (a) het samengevatte route-veld
  "Locaties op de route" en anders (b) de eerder geparste route uit de oude dataset — steeds
  zonder verzonnen datums.
- Plaatsen worden geocodeerd via OpenStreetMap/Nominatim (1 verzoek/seconde, met cache en
  handmatige correcties). Onopgeloste plaatsen (bijv. verdwenen gehuchten of parse-artefacten)
  worden niet geplot maar blijven wel in de reistekst zichtbaar.

## 7. Cijfers van deze selectie (10 augustus 2026)

| | aantal |
|---|---:|
| Bronbestand (Overzicht Engelandvaarders) | 3.141 |
| Reeds in NA-index (blijft) | 2.143 |
| Nieuw, met overlijdensdatum | 280 |
| Nieuw, geboren vóór 10-8-1916 | 253 |
| Overgenomen uit bestaande data (niet in bronbestand) | 14 |
| **Getoond op de kaart** | **2.690** |
| Uitgesloten — politiek onbetrouwbaar | 123 |
| Uitgesloten — NSB | 2 |
| Uitgesloten — mogelijk nog levend | 340 |
| Personen met reisroute (≥2 plaatsen) | 1.311 |
| …waarvan met datums per etappe | 1.243 |
| Geocode-dekking van plaats-keys | 1.418 / 1.435 (98,8%) |

## 8. Reisgenoten en overlijdensdatum

- **Reisgenoten** worden per persoon afgeleid uit de reisgezelschap-velden van alle etappes
  (mede-Engelandvaarders, genoteerd als "Achternaam, Initialen"). Namen worden gekoppeld aan
  personen in de dataset. **Alleen reisgenoten die zélf op de kaart getoond worden, worden
  klikbaar** — namen van uitgesloten of niet-getoonde personen verschijnen niet, om dezelfde
  privacyredenen als in §3. Bij grote groepsovertochten wordt de lijst ingekort (met telling).
- **Overlijdensdatum** wordt ingetogen getoond wanneer bekend (handmatig vastgesteld of via
  een CBG/NRO-match), passend bij de aard van het onderwerp.
- **Helpers** (passeurs, onderduikgevers, koeriers van ontsnappingslijnen) staan als aparte
  kaartmodus. De koppeling "wie hielp wie" komt uit het bronveld *Helpers (samengevoegd)* per
  Engelandvaarder; per persoon tonen we "Geholpen door", per helper "Hielp N Engelandvaarders"
  (beide klikbaar). Helpers tonen we op hun publieke rol, operatielocatie en bron — geen
  privé-gegevens. Het gestructureerde helpers-tabblad en dit netwerk zijn samengevoegd.
- **Verblijfsduur per locatie** (aantal dagen tot de volgende stop) wordt getoond waar beide
  datums bekend zijn; dat maakt lange wachttijden in interneringskampen zichtbaar.

## 9. Bekende beperkingen

- De 110-jaarsdrempel is een benadering: een enkele persoon die vóór 10-8-1916 geboren is
  kan in theorie nog leven, maar dat is statistisch verwaarloosbaar.
- Een kleine rest (16 keys: obscure gehuchten en OCR-verbasterde namen) is niet betrouwbaar te
  geocoderen; die stops staan wel in de reistekst maar worden niet als punt geplot. Coördinaten
  verzinnen zou de kaart vervuilen en is daarom bewust nagelaten.
- De koppeling oude↔nieuwe data mist 14 records door spellingsverschillen; die zijn via de
  unie behouden maar niet met nieuwe data verrijkt.
- Het tabblad **helpers** (passeurs e.d.) is nog niet in de kaart verwerkt (latere fase).

---
_Verwerkt met `parse_wo2net.py`; brondata en scripts staan in de projectmap._
