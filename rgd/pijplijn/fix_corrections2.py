#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vervolg op apply_corrections: los de gefaalde (Friese/oude-spelling) plaatsen op via aliassen.
Matcht de nog-niet-gecorrigeerde rijen (stad ongewijzigd) en geocodeert opnieuw."""
import json, os, re, time, urllib.parse, urllib.request
import openpyxl

WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(f"{WORK}/rgd_all.json", encoding="utf-8"))
PC = json.load(open(f"{WORK}/pdok_cache.json", encoding="utf-8"))
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"
PDOK = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?"
PREC = {"adres": "adres", "weg": "straat", "woonplaats": "plaats", "gemeente": "plaats"}
ALIAS = {"veenwouden": "Feanwâlden", "bergum": "Burgum", "hardegarijp": "Hurdegaryp",
         "noordbergum": "Noardburgum", "hattum": "Hattem", "seghwaart": "Zoetermeer",
         "skasterlân": "Joure", "dongeradeel": "Dokkum", "tolkade": "Tolkamer"}

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
    place = ALIAS.get((place or "").strip().lower(), (place or "").strip())
    bind = f'woonplaatsnaam:"{place}" OR gemeentenaam:"{place}"'
    if street:
        h = pdok(f"{street}, {place}", ["type:(adres OR weg)", bind])
        if h: return h
    h = pdok(place, ["type:(woonplaats OR gemeente)"])
    if h: return h
    if street and not re.search(r"\d", street):                 # straat blijkt de plaats
        return pdok(ALIAS.get(street.lower(), street), ["type:(woonplaats OR gemeente)"])
    return None

idx = {}
for p in A:
    k = ((p.get("uid") or "").split("-")[0], (p.get("locatie") or "").strip(), p.get("stad"))
    idx.setdefault(k, []).append(p)

rows = list(openpyxl.load_workbook("/Users/alan/Downloads/rgd_controlelijst.xlsx").active.iter_rows(values_only=True))[1:]
fixed = still = 0
for r in rows:
    inv, adres, stad = str(r[0]), (r[2] or "").strip(), r[3]
    new_street = (r[8] or "").strip() or None
    new_place = (r[9] or "").strip() or None
    hits = idx.get((inv, adres, stad))                          # alleen nog-ongewijzigde (gefaalde) rijen
    if not hits: continue
    p = hits[0]
    street = new_street or adres or None
    place = new_place or stad
    h = geocode(street, place)
    if not h:
        print("  ! blijft zonder coord:", inv, "|", street, "|", place); still += 1; continue
    p["lat"] = round(h["lat"], 6); p["lon"] = round(h["lon"], 6)
    p["prec"] = PREC.get(h["type"], "plaats"); p["bron_geo"] = "pdok"
    if new_street: p["locatie"] = new_street
    if new_place: p["stad"] = new_place
    fixed += 1

json.dump(A, open(f"{WORK}/rgd_all.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(PC, open(f"{WORK}/pdok_cache.json", "w", encoding="utf-8"), ensure_ascii=False)
from collections import Counter
print(f"alsnog opgelost: {fixed} | blijft open: {still} | totaal: {len(A)}")
print("precisie:", dict(Counter(p.get("prec") for p in A if p.get("lat") is not None)))
