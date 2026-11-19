# Kinderen van 'foute' ouders: verhalen uit het CABR-verhalenarchief

Analyse van de 210 verhalen (118 vertellers, ±412.000 woorden) in de categorie
*Kinderen over 'foute' ouders* van het Verhalenarchief van het Nationaal Archief,
ingezonden 2008–2014. Vergeleken met de 345 verhalen uit *65 Jaar Bevrijding*.

- `index.html` — de inzichten: emoties, terugkerende woorden, thema's, citaten met bronlink.
- `inzichten.json` — alle tellingen (per thema: vermeldingen, verhalen, vertellers, per 10k, referentie).
- `scripts/` — ophalen en analyseren.

## Opnieuw draaien

```bash
python3 scripts/fetch.py all.json                          # zoekdienst NA, alle 741 verhalen
python3 scripts/prep.py all.json cabr.json ref.json        # tekst schoonmaken, splitsen
# referentie = alleen '65 Jaar Bevrijding' uit ref.json
python3 scripts/analyse.py cabr.json bevrijding.json scripts/stop.txt inzichten.json
python3 scripts/zinnen.py cabr.json 'schaamte|schaamde' 20 # zinnen terugzoeken
```

De volledige verhaalteksten staan bewust niet in de repo; ze zijn van de schrijvers en
staan op de site van het NA. Het ophaalscript haalt ze opnieuw op.

De zoekdienst is `POST https://www.nationaalarchief.nl/zoek/content/stories` met
`{"language":"nl","pillars":"Beleven","resultsPerPage":100,"page":N}`; een categorie-filter
in de body werkt niet, dus er wordt lokaal gefilterd op `field_story_category`.
