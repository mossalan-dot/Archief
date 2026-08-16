#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pas de handmatige correcties uit rgd_controlelijst.xlsx toe op rgd_all.json.
Kolommen: inv.nr, gebouw, adres, stad, prec, lat, lon, NA, [8]juist adres, [9]Andere plaats,
[10]juiste lat, [11]juiste lon, [12]Anders. Geocodeert opnieuw (adres gebonden aan de plaats)."""
import json, os, re, time, urllib.parse, urllib.request
import openpyxl

WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(f"{WORK}/rgd_all.json", encoding="utf-8"))
PC = json.load(open(f"{WORK}/pdok_cache.json", encoding="utf-8"))
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"
PDOK = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?"
PREC = {"adres": "adres", "weg": "straat", "woonplaats": "plaats", "gemeente": "plaats"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
        return r.read().decode("utf-8", "replace")

def pdok(q, fq):
    key = q + "||" + ";".join(fq)
    if key in PC: return PC[key]
    hit = None
    try:
        d = json.loads(get(PDOK + urllib.parse.urlencode({"q": q, "rows": 1, "fq": fq}, doseq=True)))
        docs = d.get("response", {}).get("docs", [])
        if docs:
            m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", docs[0].get("centroide_ll", ""))
            if m: hit = {"lon": float(m.group(1)), "lat": float(m.group(2)), "type": docs[0].get("type", "")}
        time.sleep(0.15)
    except Exception as e:
        print("  ! pdok", q, e)
    PC[key] = hit
    return hit

def geocode(street, place):
    place = (place or "").strip()
    bind = f'woonplaatsnaam:"{place}" OR gemeentenaam:"{place}"'
    if street:
        h = pdok(f"{street}, {place}", ["type:(adres OR weg)", bind])
        if h: return h
    h = pdok(place, ["type:(woonplaats OR gemeente)"])
    return h or pdok(place, ["type:(woonplaats OR gemeente OR adres OR weg)"])

# index projecten op (uid-prefix, locatie, stad)
idx = {}
for p in A:
    k = ((p.get("uid") or "").split("-")[0], (p.get("locatie") or "").strip(), p.get("stad"))
    idx.setdefault(k, []).append(p)

rows = list(openpyxl.load_workbook("/Users/alan/Downloads/rgd_controlelijst.xlsx").active.iter_rows(values_only=True))[1:]
upd = split = miss = 0
for r in rows:
    inv, adres, stad = str(r[0]), (r[2] or "").strip(), r[3]
    new_street = (r[8] or "").strip() or None
    new_place = (r[9] or "").strip() or None
    man_lat, man_lon, anders = r[10], r[11], (r[12] or "").strip()
    hits = idx.get((inv, adres, stad)) or []
    if not hits:
        print("  ? geen match:", inv, "|", adres, "|", stad); miss += 1; continue
    p = hits[0]

    if anders and "meerdere plaatsen" in anders.lower():        # multi-plaats -> splitsen
        places = [x.strip() for x in re.split(r"[/,]", adres) if x.strip()]
        A.remove(p)
        for pl in places:
            h = geocode(None, pl)
            if not h: print("  ! multi geen coord:", pl); continue
            q = dict(p); q["stad"] = pl; q["locatie"] = None
            q["titel"] = f"{pl}: {p.get('gebouw', p.get('titel',''))}"
            q["lat"] = round(h["lat"], 6); q["lon"] = round(h["lon"], 6)
            q["prec"] = PREC.get(h["type"], "plaats"); q["bron_geo"] = "handmatig"
            A.append(q); split += 1
        continue

    if man_lat and man_lon:                                     # handmatige coord wint
        p["lat"] = round(float(man_lat), 6); p["lon"] = round(float(man_lon), 6)
        p["prec"] = "adres"; p["bron_geo"] = "handmatig"
    else:
        street = new_street or adres or None
        place = new_place or stad
        h = geocode(street, place)
        if not h: print("  ! geen coord:", inv, street, place); continue
        p["lat"] = round(h["lat"], 6); p["lon"] = round(h["lon"], 6)
        p["prec"] = PREC.get(h["type"], "plaats"); p["bron_geo"] = "pdok"
    if new_street: p["locatie"] = new_street
    if new_place: p["stad"] = new_place
    upd += 1

json.dump(A, open(f"{WORK}/rgd_all.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(PC, open(f"{WORK}/pdok_cache.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"bijgewerkt: {upd} | multi-plaats splits: {split} | zonder match: {miss} | totaal nu: {len(A)}")
from collections import Counter
print("precisie:", dict(Counter(p.get("prec") for p in A if p.get("lat") is not None)))
