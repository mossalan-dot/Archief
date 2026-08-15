#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolveer per blad de scan-file-id uit de METS -> thumbnail + volledige-scan-URL.
Parallel, met cache mets_cache.json (mets-uuid -> file-id) zodat herdraaien instant is."""
import json, os, sys, re, urllib.request
from concurrent.futures import ThreadPoolExecutor

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
FN = f"{WORK}/rgd_{'all' if PLACE.lower()=='all' else PLACE.lower().replace(' ','_')}.json"
P = json.load(open(FN, encoding="utf-8"))
CACHE = f"{WORK}/mets_cache.json"
cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"

def fetch(mets):
    for _ in range(2):
        try:
            req = urllib.request.Request(f"https://service.archief.nl/gaf/api/mets/v1/{mets}", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                x = r.read().decode("utf-8", "replace")
            m = re.search(r"/api/file/v1/default/([0-9a-f-]{36})", x)
            return mets, (m.group(1) if m else None)
        except Exception:
            continue
    return mets, None

todo = sorted({s["mets"] for p in P for s in p["sheets"] if s.get("mets") and s["mets"] not in cache})
print(f"{PLACE}: {sum(len(p['sheets']) for p in P)} bladen, {len(todo)} nieuwe METS op te halen")
done = 0
with ThreadPoolExecutor(max_workers=5) as ex:
    for mets, fid in ex.map(fetch, todo):   # hoofdthread schrijft -> geen race
        cache[mets] = fid; done += 1
        if done % 100 == 0:
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  .. {done}/{len(todo)}")
json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

ok = 0
for p in P:
    for s in p["sheets"]:
        fid = cache.get(s.get("mets"))
        if fid:
            s["thumb"] = f"https://service.archief.nl/api/file/v1/thumb/{fid}"
            s["full"] = f"https://service.archief.nl/api/file/v1/default/{fid}"
            ok += 1
    # projectvoorbeeld = eerste blad met thumb
    fs = next((s for s in p["sheets"] if s.get("thumb")), None)
    if fs: p["thumb"] = fs["thumb"]; p["scan_full"] = fs["full"]
json.dump(P, open(FN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"klaar: {ok} bladen met thumbnail")
