#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verrijk RGD-projecten: (1) her-geocode via PDOK Locatieserver (BAG, adres/pand-niveau),
Nominatim-coord blijft terugval; (2) haal per project de voorbeeldscan (thumb+full) uit de METS."""
import json, os, sys, time, re, urllib.parse, urllib.request

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
ALL = PLACE.lower() == "all"
FN = f"{WORK}/rgd_{'all' if ALL else PLACE.lower().replace(' ','_')}.json"
P = json.load(open(FN, encoding="utf-8"))
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

PDOK = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?"
PREC = {"adres": "adres", "weg": "straat", "postcode": "adres", "woonplaats": "plaats",
        "gemeente": "plaats", "wijk": "buurt", "buurt": "buurt"}
def pdok(q):
    try:
        d = json.loads(get(PDOK + urllib.parse.urlencode({"q": q, "rows": 1,
            "fq": "type:(adres OR weg OR woonplaats OR gemeente)"})))
        docs = d.get("response", {}).get("docs", [])
        if not docs: return None
        c = docs[0].get("centroide_ll", "")
        m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", c)
        if not m: return None
        return {"lon": float(m.group(1)), "lat": float(m.group(2)),
                "type": docs[0].get("type", ""), "naam": docs[0].get("weergavenaam", "")}
    except Exception as e:
        print("  ! pdok", q, e); return None

def scan_urls(mets_uuid):
    try:
        x = get(f"https://service.archief.nl/gaf/api/mets/v1/{mets_uuid}")
        m = re.search(r"/api/file/v1/default/([0-9a-f-]{36})", x)
        if not m: return None, None
        fid = m.group(1)
        return (f"https://service.archief.nl/api/file/v1/thumb/{fid}",
                f"https://service.archief.nl/api/file/v1/default/{fid}")
    except Exception as e:
        print("  ! mets", mets_uuid, e); return None, None

npd = nsc = 0
for p in P:
    stad = p.get("stad", PLACE)
    loc = (p.get("locatie") or "").split("/")[0].split(",")[0].strip()
    hit = pdok(f"{loc}, {stad}") if loc else None
    if loc: time.sleep(0.2)
    if not hit and loc:
        hit = pdok(f"{loc} {stad}"); time.sleep(0.2)
    if not hit:
        hit = pdok(stad); time.sleep(0.2)            # stad-terugval
    if hit:
        p["lat"] = round(hit["lat"], 6); p["lon"] = round(hit["lon"], 6)
        p["prec"] = PREC.get(hit["type"], hit["type"]); p["bron_geo"] = "pdok"; p["geo_naam"] = hit["naam"]
        npd += 1
    # voorbeeldscan: eerste blad met een mets-id
    sheet = next((s for s in p["sheets"] if s.get("mets")), None)
    if sheet:
        thumb, full = scan_urls(sheet["mets"]); time.sleep(0.2)
        if thumb:
            p["thumb"] = thumb; p["scan_full"] = full; nsc += 1

json.dump(P, open(FN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(f"{PLACE}: PDOK-hits {npd}/{len(P)} (precisie {dict(Counter(p.get('prec') for p in P))}); voorbeeldscans {nsc}/{len(P)}")
