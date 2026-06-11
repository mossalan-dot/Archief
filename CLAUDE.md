# CLAUDE.md — Archief

Dit document stuurt Claude bij het werk in deze repository. Lees het volledig
voordat je een taak uitvoert.

## Doel van dit project

Bezoekers van het Nationaal Archief makkelijker en sneller naar de juiste
informatie leiden. Dat doen we op twee manieren:

1. **Zoekhulpen vereenvoudigen** — bestaande zoekhulpen van
   nationaalarchief.nl omzetten naar heldere, jargonvrije versies die een
   bezoeker zonder archiefkennis begrijpt.
2. **Stappenplannen maken** — concrete, stap-voor-stap routes die een
   bezoeker volgt om voor een specifieke onderzoeksvraag bij de juiste bron
   uit te komen.

Het eindresultaat is altijd Nederlandstalige, voor beginners begrijpelijke
documentatie in deze repository.

## Doelpubliek

Schrijf primair voor een **beginnende bezoeker** — iemand zonder
archiefkennis. Concreet betekent dat:

- Vermijd jargon. Gebruik je een vakterm (bijv. *toegang*, *inventaris*,
  *archiefvormer*, *charter*), leg die dan bij eerste gebruik kort uit.
- Neem geen voorkennis aan. Leg elke stap uit, ook stappen die voor een
  ervaren onderzoeker vanzelfsprekend lijken.
- Wees concreet: noem knopnamen, menu-opties en wat de bezoeker letterlijk
  ziet of moet aanklikken.
- Korte zinnen, actieve formuleringen, een vriendelijke en geduldige toon.

## Bronhiërarchie (strikt)

Hanteer deze volgorde **strikt** bij elk onderzoek en elk stappenplan:

1. **Zoekhulpen en indices** — altijd eerst raadplegen en aanbieden.
2. **Inventarissen** — pas inzetten als zoekhulpen en indices geen uitkomst
   bieden, of als aanvulling daarop.

Begin een stappenplan dus nooit bij de inventaris als er een relevante
zoekhulp of index bestaat. Verwijs de bezoeker eerst daarheen.

## Bronnen

- **Primair**: `www.nationaalarchief.nl`. Dit is de leidende bron. Baseer
  inhoud op wat daar staat; verzin geen informatie en gok niet.
- **Secundair**: verwante officiële bronnen (bijv. `archieven.nl`, websites
  van regionale archieven, het CBG) mogen aanvullend, maar alleen als
  nationaalarchief.nl geen of onvoldoende uitkomst biedt. Maak in de tekst
  duidelijk wanneer een verwijzing naar een externe bron gaat.
- Vermeld bij elke claim en verwijzing de **bron-URL**, zodat de bezoeker
  het kan natrekken en de informatie controleerbaar blijft.
- Markeer onzekerheid expliciet. Weet je iets niet zeker op basis van de
  website, zeg dat dan in plaats van het in te vullen.

> Let op: de officiële website kan wijzigen. Controleer bij twijfel of een
> zoekhulp, index of URL nog actueel is voordat je die overneemt.

## Mappenstructuur

Output bewaren we als markdown, geordend per thema/onderwerp:

```
/zoekhulpen/      Vereenvoudigde versies van bestaande zoekhulpen
/stappenplannen/  Stap-voor-stap routes voor onderzoeksvragen
```

- Eén bestand per onderwerp, met een beschrijvende, kleine-letters
  bestandsnaam met koppeltekens, bijv.
  `zoekhulpen/voorouders-in-nederlands-indie.md`.
- Hergebruik bestaande bestanden waar dat kan; maak niet onnodig dubbele
  documenten over hetzelfde onderwerp.

## Sjabloon — vereenvoudigde zoekhulp

Gebruik deze opbouw voor een bestand in `/zoekhulpen/`:

```markdown
# [Titel van de zoekhulp]

## Waarvoor is dit?
Eén of twee zinnen: welke vraag helpt deze zoekhulp beantwoorden?

## Wat heb je nodig?
Welke gegevens moet de bezoeker bij de hand hebben (bijv. naam, jaartal,
plaats)?

## Zo zoek je
Stap-voor-stap, in begrijpelijke taal.

## Begrippen
Korte uitleg van vaktermen die in deze zoekhulp voorkomen.

## Bronnen
- [Naam](URL) — de originele zoekhulp op nationaalarchief.nl
```

## Sjabloon — stappenplan

Gebruik deze opbouw voor een bestand in `/stappenplannen/`:

```markdown
# Stappenplan: [onderzoeksvraag]

## Voor wie?
Voor welke bezoeker en welke vraag is dit stappenplan bedoeld?

## Stap 1 — Begin bij de zoekhulp / index
Verwijs eerst naar de relevante zoekhulp(en) of index(en). Link erheen.

## Stap 2 — ...
Vervolgstappen. Pas naar inventarissen verwijzen als de zoekhulpen/indices
geen uitkomst bieden.

## Als je vastloopt
Alternatieven, contactmogelijkheden of doorverwijzingen.

## Bronnen
- [Naam](URL)
```

## Werkwijze voor Claude

- Schrijf en communiceer in het **Nederlands**.
- Volg de bronhiërarchie strikt: zoekhulpen/indices eerst, inventarissen
  secundair.
- Controleer informatie op nationaalarchief.nl voordat je die overneemt;
  baseer je niet op aannames of geheugen over de inhoud van de website.
- Voeg altijd bron-URL's toe.
- Houd de doelgroep (beginnende bezoeker) als maatstaf: zou iemand zonder
  archiefkennis dit kunnen volgen?
- Vraag het na bij de archivaris als een vraag onduidelijk is of buiten de
  bovenstaande kaders valt.
