#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verrijk RGD-projecten: (1) geocode via PDOK Locatieserver (BAG, adres/straatniveau),
(2) voorbeeldscan (thumb+full) per project uit de METS. Met caches (pdok_cache/mets_cache)
zodat re-runs snel zijn; slaat tussentijds op (resumable)."""
import json, os, sys, time, re, urllib.parse, urllib.request

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
ALL = PLACE.lower() == "all"
FN = f"{WORK}/rgd_{'all' if ALL else PLACE.lower().replace(' ','_')}.json"
P = json.load(open(FN, encoding="utf-8"))
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"

def load(fn): return json.load(open(fn, encoding="utf-8")) if os.path.exists(fn) else {}
PC = load(f"{WORK}/pdok_cache.json")          # query -> hit|null
MC = load(f"{WORK}/mets_cache.json")          # mets-uuid -> file-id|null
def savecaches():
    json.dump(PC, open(f"{WORK}/pdok_cache.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(MC, open(f"{WORK}/mets_cache.json", "w", encoding="utf-8"), ensure_ascii=False)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

PDOK = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?"
PREC = {"adres": "adres", "weg": "straat", "postcode": "adres", "woonplaats": "plaats",
        "gemeente": "plaats", "wijk": "buurt", "buurt": "buurt"}
def pdok(q, fq):
    key = q + "||" + ";".join(fq)
    if key in PC: return PC[key]
    hit = None
    try:
        d = json.loads(get(PDOK + urllib.parse.urlencode({"q": q, "rows": 1, "fq": fq}, doseq=True)))
        docs = d.get("response", {}).get("docs", [])
        if docs:
            m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", docs[0].get("centroide_ll", ""))
            if m: hit = {"lon": float(m.group(1)), "lat": float(m.group(2)),
                         "type": docs[0].get("type", ""), "naam": docs[0].get("weergavenaam", "")}
        time.sleep(0.15)
    except Exception as e:
        print("  ! pdok", q, e)
    PC[key] = hit
    return hit

def geocode(stad, loc):
    """Adres GEBONDEN aan de kop-stad; lukt dat niet, dan de stad zelf (nooit een andere stad)."""
    bind = f'woonplaatsnaam:"{stad}" OR gemeentenaam:"{stad}"'
    if loc:
        h = pdok(f"{loc}, {stad}", ["type:(adres OR weg)", bind])
        if h: return h
    return pdok(stad, ["type:(woonplaats OR gemeente)"])   # stad-terugval

def scan_urls(mets):
    if mets not in MC:
        try:
            x = get(f"https://service.archief.nl/gaf/api/mets/v1/{mets}")
            m = re.search(r"/api/file/v1/default/([0-9a-f-]{36})", x)
            MC[mets] = m.group(1) if m else None
            time.sleep(0.15)
        except Exception:
            MC[mets] = None
    fid = MC.get(mets)
    if not fid: return None, None
    return (f"https://service.archief.nl/api/file/v1/thumb/{fid}",
            f"https://service.archief.nl/api/file/v1/default/{fid}")

npd = nsc = done = 0
for p in P:
    done += 1
    if p.get("lat") is None:                       # geocode (gebonden aan de kop-stad)
        stad = p.get("stad", PLACE)
        loc = (p.get("locatie") or "").replace("[", "").replace("]", "").split("/")[0].split(",")[0].strip()
        hit = geocode(stad, loc)
        if hit:
            p["lat"] = round(hit["lat"], 6); p["lon"] = round(hit["lon"], 6)
            p["prec"] = PREC.get(hit["type"], hit["type"]); p["bron_geo"] = "pdok"; p["geo_naam"] = hit["naam"]
    if p.get("lat") is not None: npd += 1
    if not p.get("thumb"):                          # voorbeeldscan
        sheet = next((s for s in p["sheets"] if s.get("mets")), None)
        if sheet:
            thumb, full = scan_urls(sheet["mets"])
            if thumb: p["thumb"] = thumb; p["scan_full"] = full
    if p.get("thumb"): nsc += 1
    if done % 200 == 0:
        json.dump(P, open(FN, "w", encoding="utf-8"), ensure_ascii=False, indent=1); savecaches()
        print(f"  .. {done}/{len(P)} (geo {npd}, scans {nsc})", flush=True)

json.dump(P, open(FN, "w", encoding="utf-8"), ensure_ascii=False, indent=1); savecaches()
from collections import Counter
print(f"{PLACE}: geo {npd}/{len(P)} (precisie {dict(Counter(p.get('prec') for p in P))}); voorbeeldscans {nsc}/{len(P)}")
