#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Voeg `prov` (provincie) toe aan elke NL-herkomstplaats in kaart_data.json (PDOK naam-lookup,
gecachet). Voor de plaats/provincie-toggle op de inzichten-pagina. Draai ná build_data2.py."""
import json, os, re, time, urllib.parse, urllib.request

BASE = "/Users/alan/Downloads/arbeidsinzet"
KD = f"{BASE}/site/kaart_data.json"
CACHE = f"{BASE}/prov_herkomst_cache.json"
PDOK = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?"
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}

def prov(naam):
    if naam in cache: return cache[naam]
    res = None
    try:
        url = PDOK + urllib.parse.urlencode({"q": naam, "rows": 1,
            "fq": "type:(woonplaats OR gemeente)", "fl": "provincienaam"})
        req = urllib.request.Request(url, headers={"User-Agent": "arbeidsinzet-kaart/1.0 (mossalan@gmail.com)"})
        with urllib.request.urlopen(req, timeout=20) as r:
            docs = json.load(r).get("response", {}).get("docs", [])
        if docs: res = docs[0].get("provincienaam")
        time.sleep(0.12)
    except Exception as e:
        print("  ! ", naam, e)
    cache[naam] = res
    return res

d = json.load(open(KD, encoding='utf-8'))
n = ok = 0
for o in d["herkomst"]:
    n += 1
    o["prov"] = prov(o["naam"])
    if o["prov"]: ok += 1
    if n % 100 == 0:
        json.dump(cache, open(CACHE, "w", encoding='utf-8'), ensure_ascii=False)
        print(f"  .. {n}/{len(d['herkomst'])} ({ok} met provincie)", flush=True)

json.dump(cache, open(CACHE, "w", encoding='utf-8'), ensure_ascii=False)
json.dump(d, open(KD, "w", encoding='utf-8'), ensure_ascii=False, separators=(",", ":"))
from collections import Counter
c = Counter(o["prov"] for o in d["herkomst"] if o["prov"])
print(f"provincie toegevoegd: {ok}/{len(d['herkomst'])} | {dict(c.most_common())}")
