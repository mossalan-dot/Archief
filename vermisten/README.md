# Vermiste Personen — namenindex op de klapper (Nationaal Archief 2.09.34.02)

Een doorzoekbare **namenindex** op de kaartenklapper van de **Commissie tot het doen van
Aangifte van Overlijden van Vermisten** (VP-dossiers, 1949–1962), met per persoon een
verwijzing naar de **onderliggende VP-dossiers** (serie A) en hun inventarisnummers.

## Waarom

De commissie stelde na de oorlog vast dat vermiste personen — grotendeels **slachtoffers
van de Tweede Wereldoorlog**, waaronder zeer veel Joodse slachtoffers — als overleden
konden worden aangegeven. Toegang tot de persoonsdossiers loopt via een alfabetische
**kaartenbak** (de "klapper", inv.nr 614–744). Die kaarten zijn wél **gedigitaliseerd**,
maar **niet ge-OCR'd**: er is dus geen zoekfunctie op naam. Wie een naam zoekt moet de
scans bladzij voor bladzij doorbladeren.

Dit project leest de klapperkaarten machinaal uit tot een naamindex, zodat je op naam
kunt zoeken en meteen naar het juiste onderliggende dossier springt.

## De kaart

Elke kaart is een voorgedrukt formulier (model 8328-'49) met grotendeels **getypte**
sleutelvelden (naam, voornamen, geboortedatum/-plaats, beroep, adres, Staatscourant-datum
en het **dossiernummer**) en enkele handgeschreven velden (ouders, echtgeno(o)t(e)). Het
`Dossier nr` rechtsboven is de sleutel naar het persoonsdossier.

## Structuur van het archief (uit de EAD afgeleid)

| Serie | Inv.nr | Inhoud |
|---|---|---|
| **A1.1** | 1–592 | Persoonsdossiers **mét** aangifte van overlijden — dossiers 1–118.139, ~200 per inv.nr |
| **A1.2** | 593–613 | Persoonsdossiers **zonder** aangifte (aparte, grovere reeksen) |
| **B** | 614–744 | De **klapper** (namenindex), ~115.000 kaartscans, alfabetisch per inv.nr |

Een dossiernummer op een kaart leidt via de bereiken in de EAD naar het inv.nr in serie A.
Bij overlap tussen A1.1 en A1.2 wint A1.1 zodra de kaart een Staatscourant-datum draagt
(dan is er daadwerkelijk aangifte van overlijden gedaan).

## Pijplijn (`pijplijn/`)

| Script | Doet |
|---|---|
| `dossiermap.py` | Leest de EAD-inventaris → interval-tabel **dossiernr → inv.nr** + NA-deeplinks (`dossiermap.json`). |
| `harvest_klapper.py` | Leest serie B uit de EAD, haalt per klapper-inv.nr het METS op → plat **scan-manifest** met directe JPEG-URL's (`klapper_manifest.json`). |
| `extract_cards.py` | Leest elke kaart gestructureerd uit met een **vision-taalmodel** (Anthropic API) → `kaarten.jsonl`. Resumable; cachet scans in `scans/`. |
| `build_site.py` | Voegt records + manifest + dossiermap samen → `site/kaarten.json`. |

De EAD staat als `pijplijn/2.09.34.02.ead.xml` in de repo (download:
`https://www.nationaalarchief.nl/onderzoeken/archief/2.09.34.02/download/xml`).

### Reproduceren (steekproef, werkt zonder API-key)

```bash
cd pijplijn
python3 dossiermap.py
python3 harvest_klapper.py --only 614 --out klapper_manifest.sample.json
python3 build_site.py --records kaarten.sample.jsonl --manifest klapper_manifest.sample.json
python3 -m http.server 8971 --directory ../site   # open http://localhost:8971
```

### Volledige run

```bash
python3 harvest_klapper.py                       # alle 131 klapper-inv.nrs (~115k scans)
export ANTHROPIC_API_KEY=...
python3 extract_cards.py --manifest klapper_manifest.json
python3 build_site.py --manifest klapper_manifest.json
```

## Stand van zaken

`site/kaarten.json` bevat nu een **handmatig geverifieerde steekproef** uit inv.nr 614
(“Aa – Adelaar”), zodat de zoekpagina werkt en de aanpak controleerbaar is. De
volledige uitlezing (`extract_cards.py` over alle inv.nrs) is de opschaalstap; die
kost een OCR-run over ~115.000 kaarten.

## Ethiek & bron

De geregistreerden zijn overleden; de gegevens komen uit een **openbaar** archief van het
Nationaal Archief (open data). Behandel de index met de gepaste piëteit — het gaat om
oorlogsslachtoffers. Bronvermelding bij hergebruik: *Nationaal Archief, Den Haag,
Commissie tot het doen van Aangifte van Overlijden van Vermisten (2.09.34.02)*.

## Licentie

Broncode: MIT. Onderliggende gegevens © Nationaal Archief (open data). Scans via
`service.archief.nl`.
