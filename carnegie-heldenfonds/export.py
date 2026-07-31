#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export parsed + geocoded dossiers to dossiers.json and dossiers.csv."""
import json, os, csv
from cats import extract_person, delpher_query

WORK = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(f"{WORK}/dossiers_raw.json", encoding="utf-8"))
cache = json.load(open(f"{WORK}/geocache.json", encoding="utf-8"))
dpath = f"{WORK}/geocache_detail.json"
dcache = json.load(open(dpath, encoding="utf-8")) if os.path.exists(dpath) else {}
mpath = f"{WORK}/manual_coords.json"
mcoords = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {}

rows = []
for r in recs:
    places = r["places"]
    lat = lon = None; prec = ""; used_place = ""
    for p in places:
        g = cache.get(p)
        if g:
            used_place, lat, lon, prec = p, g["lat"], g["lon"], "plaats"
            det = r.get("detail")
            if det:
                dg = dcache.get(f"{det}||{p}")
                if dg and dg.get("lat") is not None:
                    lat, lon, prec = dg["lat"], dg["lon"], dg.get("prec", "straat")
            break
    if lat is None and str(r["nr"]) in mcoords:   # handmatige plaatsbepaling
        mc = mcoords[str(r["nr"])]
        lat, lon, prec, used_place = mc["lat"], mc["lon"], mc.get("prec", "hemelsbreed"), mc.get("place", "")
    na = f"https://www.nationaalarchief.nl/onderzoeken/archief/2.19.364/invnr/{r['nr']}"
    who = extract_person(r["desc"])
    delpher = delpher_query(who, used_place or None, r.get("detail"))
    rows.append({
        "nr": r["nr"],
        "beschrijving": r["desc"],
        "redder": who or "",
        "plaatsen": "; ".join(places),
        "plaats_gebruikt": used_place,
        "water_straat": r.get("detail") or "",
        "jaar": r["year"] or "",
        "jaar_van": r["year_from"] or "",
        "categorie": "",  # filled below
        "afgewezen": r["afgewezen"],
        "fotos": r["fotos"],
        "openbaar_beperkt_tot": r["openbaar_tot"] or "",
        "lat": lat if lat is not None else "",
        "lon": lon if lon is not None else "",
        "precisie": prec,
        "nationaal_archief_url": na,
        "delpher_url": delpher,
    })

# categorie + afloop via gedeelde module
from cats import categorize, outcome, is_steun
for row, r in zip(rows, recs):
    row["categorie"] = categorize(r["desc"], r.get("detail"))
    row["afloop"] = outcome(r["desc"])
    row["ondersteuning"] = is_steun(r["desc"])

json.dump(rows, open(f"{WORK}/dossiers.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(f"{WORK}/dossiers.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

geo = sum(1 for x in rows if x["lat"] != "")
straat = sum(1 for x in rows if x["precisie"] == "straat")
print(f"export: {len(rows)} dossiers -> dossiers.json + dossiers.csv")
print(f"met coördinaat: {geo} ({100*geo/len(rows):.1f}%); waarvan straat/water-precisie: {straat}")
