#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geocode RGD-bouwprojecten binnen hun stad via Nominatim/OSM. Cache: geocache_rgd.json."""
import json, os, sys, time, re, urllib.parse, urllib.request

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
FN = f"{WORK}/rgd_{PLACE.lower().replace(' ', '_')}.json"
projects = json.load(open(FN, encoding="utf-8"))
CACHE = f"{WORK}/geocache_rgd.json"
gc = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"
# grove bounding box per proefstad (voorkomt gelijknamige straten elders)
CITY_VIEWBOX = {"Amsterdam": "4.68,52.44,5.07,52.28"}

def nomi(q, viewbox=None):
    if q in gc: return gc[q]
    params = {"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "nl"}
    if viewbox: params["viewbox"] = viewbox; params["bounded"] = 1
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: res = json.load(r)
    except Exception as e:
        print("  ! fout", q, e); res = []
    time.sleep(1.1)
    hit = ({"lat": float(res[0]["lat"]), "lon": float(res[0]["lon"]),
            "type": res[0].get("type", ""), "display": res[0].get("display_name", "")[:70]} if res else None)
    gc[q] = hit
    return hit

vb = CITY_VIEWBOX.get(PLACE)
ok = 0
for p in projects:
    loc = (p.get("locatie") or "").split("/")[0].split(",")[0].strip()
    hit = None; prec = ""
    if loc:
        hit = nomi(f"{loc}, {PLACE}", vb)
        if hit: prec = "adres" if re.search(r"\d", loc) else "straat"
    if not hit and p.get("gebouw"):                       # landmark-gebouw
        hit = nomi(f"{p['gebouw']}, {PLACE}", vb)
        if hit: prec = "gebouw"
    if not hit:                                            # val terug op stadscentrum
        hit = nomi(PLACE, None); prec = "plaats"
    if hit:
        p["lat"] = round(hit["lat"], 6); p["lon"] = round(hit["lon"], 6); p["prec"] = prec
        ok += 1
    json.dump(gc, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

json.dump(projects, open(FN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(f"{PLACE}: {ok}/{len(projects)} met coord; precisie:", dict(Counter(p.get("prec", "-") for p in projects)))
for p in projects[:6]:
    print(f"  {p['uid']:10s} [{p.get('prec','-'):7s}] {p['lat']:.5f},{p['lon']:.5f}  {str(p.get('locatie'))[:26]}")
