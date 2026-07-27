#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Street/waterway-level geocoding: '<detail>, <place>' validated against the
town coordinate (reject matches >MAXKM away). Cache: geocache_detail.json
key '<detail>||<place>'. Usage: geocode_detail.py [--limit N]"""
import json, os, sys, time, math, urllib.parse, urllib.request

WORK = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(f"{WORK}/dossiers_raw.json", encoding="utf-8"))
town = json.load(open(f"{WORK}/geocache.json", encoding="utf-8"))
CACHE = f"{WORK}/geocache_detail.json"
cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}

limit = None
if "--limit" in sys.argv:
    limit = int(sys.argv[sys.argv.index("--limit") + 1])
MAXKM = 15.0

# unique (detail, place) pairs where the town is geocoded
pairs = []
seen = set()
for r in recs:
    det = r.get("detail")
    if not det:
        continue
    for p in r["places"]:
        if not town.get(p):
            continue
        key = f"{det}||{p}"
        if key not in seen:
            seen.add(key); pairs.append((det, p, key))
todo = [x for x in pairs if x[2] not in cache]
if limit:
    todo = todo[:limit]
print(f"unieke detail+plaats-paren: {len(pairs)}; te doen nu: {len(todo)} (MAXKM={MAXKM})")

UA = "CarnegieHeldenfondsKaart/1.0 (mossalan@gmail.com)"
def nominatim(q):
    params = {"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "nl"}
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

def haversine(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

ok = far = miss = 0
for k, (det, p, key) in enumerate(todo, 1):
    tc = town[p]
    res = None
    try:
        res = nominatim(f"{det}, {p}, Nederland")
    except Exception as e:
        print(f"  ! {key}: {e}")
    if res:
        d0 = res[0]
        lat, lon = float(d0["lat"]), float(d0["lon"])
        dist = haversine(tc["lat"], tc["lon"], lat, lon)
        if dist <= MAXKM:
            cache[key] = {"lat": lat, "lon": lon, "prec": "straat",
                          "display": d0.get("display_name", ""),
                          "cls": d0.get("class", ""), "type": d0.get("type", ""),
                          "dist_km": round(dist, 2)}
            ok += 1
        else:
            cache[key] = {"lat": None, "reject": "te ver", "dist_km": round(dist, 2)}
            far += 1
    else:
        cache[key] = {"lat": None, "reject": "geen match"}
        miss += 1
    if k % 25 == 0:
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  .. {k}/{len(todo)} (straat {ok}, te ver {far}, geen {miss})")
    time.sleep(1.1)

json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
tot = ok + far + miss
print(f"klaar. straat-precisie: {ok}/{tot} ({100*ok/max(tot,1):.0f}%); verworpen te ver: {far}; geen match: {miss}")
