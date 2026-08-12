#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geocode unique place names via Nominatim, cached to geocache.json.
Usage: geocode.py [NR_MIN] [NR_MAX]   (default: all records)"""
import json, sys, time, urllib.parse, urllib.request, os, re

WORK = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(f"{WORK}/dossiers_raw.json", encoding="utf-8"))
CACHE = f"{WORK}/geocache.json"
cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}

nr_min = int(sys.argv[1]) if len(sys.argv) > 1 else 0
nr_max = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9

places = []
seen = set()
for r in recs:
    if nr_min <= r["nr"] <= nr_max:
        for p in r["places"]:
            if p not in seen:
                seen.add(p); places.append(p)

# plaatsen die we bewust NIET plotten: NL-begrensde geocoder matcht ze fout
# (St. Lucia = piloot boven zee, geen Brabants gehucht) -> geforceerd op None, nooit retryen
SKIP = {"St. Lucia"}
for p in SKIP:
    cache[p] = None

# retry entries that previously failed (cache value None) with the improved logic
todo = [p for p in places if not cache.get(p) and p not in SKIP]
print(f"unieke plaatsen in bereik {nr_min}-{nr_max}: {len(places)}; te (her)geocoderen: {len(todo)}")

UA = "CarnegieHeldenfondsKaart/1.0 (mossalan@gmail.com)"
# corrections for source typos / mis-parses that otherwise match abroad
ALIAS = {
    "Galadammen": "Galamadammen",        # -> Friesland (was Noorwegen)
    "Ursum": "Ursem",                    # -> Noord-Holland (was Jemen)
    "Wansum": "Wanssum",                 # -> Limburg (was VK)
    "Wychen": "Wijchen",                 # -> Gelderland (was Polen)
    "Camp": "Bergen, Noord-Holland",     # "Camp (Bergen)" Noordzee (was Texas)
    "Snek": "Sneek",                     # bron-typfout
    "Monnikendam": "Monnikendam, Noord-Holland",  # stad in Waterland (was: city_gate 'Monnikendam' te Amersfoort)
    # bron-/OCR-typefouten -> juiste spelling
    "'s-Gravenhagen": "'s-Gravenhage", "'s-Gravenhag": "'s-Gravenhage",
    "Herenveen": "Heerenveen", "Veendendaal": "Veenendaal", "Eindhoen": "Eindhoven",
    "Yrseke": "Yerseke", "Warfum": "Warffum", "Standaarbuiten": "Standdaarbuiten",
    "Rijsburg": "Rijnsburg", "Etten-Leuk": "Etten-Leur", "St Michielgestel": "Sint-Michielsgestel",
    "Nieuw-Ginniken": "Ginneken", "Nieuwehoorn": "Nieuwenhoorn", "Balkburg": "Balkbrug",
    "Veenwoude": "Veenwouden", "Bennebroer": "Bennebroek", "Nijholtpa": "Nijeholtpade",
    "Jutpaas": "Jutphaas", "Bassingerhorn": "Barsingerhorn", "Kootsertille": "Kootstertille",
    "Bergummerdam": "Burgum", "Wijntjeterp": "Wijnjeterp", "Breukelen-Neijenrode": "Breukelen",
    "Emmercompascuum": "Emmer-Compascuum", "Gasselte-Nijveen": "Gasselternijveen",
    "Harbrinkbroek": "Harbrinkhoek", "Nieuwelande": "Nieuwlande", "Rinsumageest": "Rinsumageast",
    "Terheijde aan Zee": "Ter Heijde", "Dirkland": "Dirksland", "Wervershoef": "Wervershoof",
    "Otterleek": "Oterleek", "Wiedum": "Weidum", "Lijtshuizen": "IJlst",
    "Ouderwerk aan den IJssel": "Ouderkerk aan den IJssel", "Nieuw-Pekela": "Nieuwe Pekela, Groningen",
    "Breukelerveen": "Breukeleveen", "Limmel-Meerssen": "Limmel, Maastricht",
    # voormalige (Friese/Groningse) gemeenten -> representatieve hoofdplaats
    "Wymbritseradeel": "IJlst", "Wonseradeel": "Witmarsum", "Oostdongeradeel": "Metslawier",
    "Dantumadeel": "Damwoude", "Datumadeel": "Damwoude", "Hennaarderadeel": "Wommels",
    "Achtkaspelen": "Buitenpost", "Franekeradeel": "Franeker", "Zwollerkerspel": "Zwolle",
    "Bellingwedde": "Wedde",
}
# buitenland-aliassen: gecodeerd met abroad=True (niet NL-begrensd)
ALIAS_ABROAD = {
    "Norresunby": "Nørresundby, Danmark", "Tandjong Priok": "Tanjung Priok, Jakarta",
    "Tjipatoedjah": "Cipatujah, Indonesia", "Campos de Jordao in Brazilië": "Campos do Jordão, Brazil",
    "Flambourough Head": "Flamborough Head, England", "Haiming Titol": "Haiming, Tirol",
}
# European-NL bounding box so nl-queries never return Caribbean "Nederland" (Curaçao etc.)
NL_VIEWBOX = "3.2,53.7,7.4,50.6"
def nominatim(q, nl=True):
    params = {"q": q, "format": "jsonv2", "limit": 1}
    if nl:
        params["countrycodes"] = "nl"
        params["viewbox"] = NL_VIEWBOX
        params["bounded"] = 1
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

def candidates(p):
    """Ordered query candidates for a place string; first hit wins.
    (base, allow_abroad) tuples. Trimmed/expanded fragments stay NL-only."""
    seen = set()
    def add(q, abroad):
        q = q.strip(" ,.;:-")
        if q and q not in seen:
            seen.add(q); out.append((q, abroad))
    out = []
    if p in ALIAS:
        add(ALIAS[p], False)                       # known correction, NL only
    if p in ALIAS_ABROAD:
        add(ALIAS_ABROAD[p], True)                 # known foreign correction, abroad allowed
    add(p, True)                                   # full string, abroad allowed
    n = re.sub(r'\bSt\.?\b', 'Sint', p)            # St / St. -> Sint
    if n != p: add(n, True)
    if ' en ' in p:                                # "Hooge en Lage Zwaluwe" -> "Lage Zwaluwe"
        add(p.split(' en ', 1)[1], False)
    toks = p.split()
    for k in range(len(toks) - 1, 0, -1):          # progressive trailing trim (NL only)
        add(' '.join(toks[:k]), False)
    return out

found = notfound = 0
for k, p in enumerate(todo, 1):
    hit = None; used = None
    for q, abroad in candidates(p):
        try:
            res = nominatim(q, nl=True)
            time.sleep(1.1)
            if not res and abroad:
                res = nominatim(q, nl=False)       # allow abroad for the base string
                time.sleep(1.1)
        except Exception as e:
            print(f"  ! fout bij '{q}': {e}")
            res = None
        if res:
            hit = res[0]; used = q; break
    if hit:
        cache[p] = {"lat": float(hit["lat"]), "lon": float(hit["lon"]),
                    "display": hit.get("display_name", ""), "type": hit.get("type", ""),
                    "matched": used}
        found += 1
        if used != p:
            print(f"  ~ '{p}' via '{used}'")
    else:
        cache[p] = None
        notfound += 1
        print(f"  - niet gevonden: {p}")
    if k % 25 == 0:
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  .. {k}/{len(todo)} (gevonden {found}, niet {notfound})")

json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_ok = sum(1 for p in places if cache.get(p))
n_bad = sum(1 for p in places if not cache.get(p))
print(f"klaar. gecodeerd: {found}, niet gevonden nu: {notfound}")
print(f"totaal in bereik met coords: {n_ok}/{len(places)}; zonder: {n_bad}")
if n_bad:
    print("zonder coords:", [p for p in places if not cache.get(p)][:40])
