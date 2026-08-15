#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Voeg per project de provincie toe (op basis van de plaats-kop, via PDOK). Cache: prov_cache.json."""
import json, os, sys, time, urllib.parse, urllib.request
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "all"
FN = f"{WORK}/rgd_{'all' if PLACE.lower()=='all' else PLACE.lower().replace(' ','_')}.json"
P = json.load(open(FN, encoding="utf-8"))
CACHE = f"{WORK}/prov_cache.json"
pc = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"
PDOK = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?"

def provincie(stad):
    if stad in pc: return pc[stad]
    prov = None
    try:
        url = PDOK + urllib.parse.urlencode({"q": stad, "rows": 1, "fq": "type:(woonplaats OR gemeente)"})
        d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read())
        docs = d.get("response", {}).get("docs", [])
        if docs: prov = docs[0].get("provincienaam")
        time.sleep(0.15)
    except Exception as e:
        print("  ! ", stad, e)
    pc[stad] = prov
    return prov

steden = sorted({p["stad"] for p in P})
print(f"{len(steden)} unieke plaats-koppen")
for i, s in enumerate(steden, 1):
    provincie(s)
    if i % 50 == 0:
        json.dump(pc, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False); print(f"  .. {i}/{len(steden)}")
json.dump(pc, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

for p in P:
    pr = pc.get(p["stad"])
    if pr: p["provincie"] = pr
json.dump(P, open(FN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("provincies:", dict(Counter(p.get("provincie") for p in P if p.get("provincie")).most_common()))
print("zonder provincie:", sum(1 for p in P if not p.get("provincie")))
