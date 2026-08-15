#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verrijk RGD-projecten met Wikidata (streng): zoek gebouw+stad, accepteer alleen
een sterke naam-match met coordinaat (P625). Voegt p['wd']={id,label,url,lat,lon} toe."""
import json, os, sys, time, re, urllib.parse, urllib.request

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
FN = f"{WORK}/rgd_{'all' if PLACE.lower()=='all' else PLACE.lower().replace(' ','_')}.json"
P = json.load(open(FN, encoding="utf-8"))
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"
API = "https://www.wikidata.org/w/api.php?"
STOP = set("de het een en van der den ten te op aan voor gebouw tekeningen tekening opmeting ontwerp "
           "voormalig voormalige oud oude nieuw nieuwe c.a bureau kantoor huis".split())

def jget(params):
    for _ in range(3):                       # retry tegen throttling (429/timeouts)
        try:
            req = urllib.request.Request(API + urllib.parse.urlencode(params), headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)
        except Exception:
            time.sleep(1.2)
    return {}

def toks(s):
    return {w for w in re.findall(r"[a-zàâäéèêëïîôöùûüç]+", (s or "").lower()) if w not in STOP and len(w) > 2}

def strong(a, b):
    ta, tb = toks(a), toks(b)
    if not ta or not tb: return False
    na, nb = a.lower(), b.lower()
    if na in nb or nb in na: return True
    inter = ta & tb
    return len(inter) >= 1 and len(inter) / min(len(ta), len(tb)) >= 0.5

import math
def hav(a, b):
    R = 6371; p = math.pi / 180
    x = (math.sin((b[0]-a[0])*p/2)**2 + math.cos(a[0]*p)*math.cos(b[0]*p)*math.sin((b[1]-a[1])*p/2)**2)
    return 2*R*math.asin(math.sqrt(x))

def coord_of(qid):
    try:
        ent = jget({"action": "wbgetentities", "ids": qid, "props": "claims|labels", "format": "json"})["entities"][qid]
        time.sleep(0.12)
        p625 = ent.get("claims", {}).get("P625", [])
        if not p625: return None
        v = p625[0]["mainsnak"]["datavalue"]["value"]
        labs = ent.get("labels", {})
        label = (labs.get("nl") or labs.get("en") or {}).get("value", qid)
        return round(v["latitude"], 6), round(v["longitude"], 6), label
    except Exception:
        return None

matched = []; done = 0
for p in P:
    done += 1
    if p.get("prec") not in ("adres", "straat", "buurt"): continue    # alleen geo-verifieerbaar (precies geplot)
    geb = p.get("gebouw", "")
    if not geb or toks(geb) <= {"politiebureau", "politie", "villa", "toren", "woonhuis"}: continue  # te generiek
    stad = p.get("stad", "")                                          # zoek op gebouw + de éígen stad
    d = jget({"action": "query", "list": "search", "srsearch": f"{geb} {stad}",
              "srnamespace": "0", "srlimit": 6, "format": "json"})
    time.sleep(0.15)
    res = [s["title"] for s in d.get("query", {}).get("search", [])]
    pick = None
    for qid in res[:5]:
        cc = coord_of(qid)
        if not cc: continue
        clat, clon, label = cc
        if hav((p["lat"], p["lon"]), (clat, clon)) <= 1.2:           # Wikidata-gebouw bij het PDOK-punt
            pick = (qid, label, round(hav((p["lat"], p["lon"]), (clat, clon)), 2)); break
    if pick:
        qid, label, dist = pick
        p["wd"] = {"id": qid, "label": label, "url": "https://www.wikidata.org/wiki/" + qid}  # alleen link, geen coord
        matched.append((p["uid"], geb, label, qid, dist))
    if done % 200 == 0:
        json.dump(P, open(FN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  .. {done}/{len(P)} ({len(matched)} matches)", flush=True)

json.dump(P, open(FN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{PLACE}: {len(matched)} Wikidata-matches (geo-geverifieerd)")
for u, g, l, q, dist in matched[:40]:
    print(f"  {u:12s} {g[:30]:30s} -> {l} ({q}) {dist}km")
