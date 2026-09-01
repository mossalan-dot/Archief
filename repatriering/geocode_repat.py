#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geocodeer de plaatsen in repat_reizen.json met een gecureerde tabel (historische havens).
Normaliseert typo's/compounds, voegt coördinaten toe (van_ll/via_ll/naar_ll) + nette plaatsnaam.
Schrijft repat_reizen.json terug."""
import json, re, os
BASE = os.path.dirname(os.path.abspath(__file__))

# canonieke plaats -> [lat, lon]
COORDS = {
    "Tandjong Priok": [-6.1064, 106.8817], "Batavia": [-6.1751, 106.8272], "Bandoeng": [-6.9175, 107.6191],
    "Soerabaja": [-7.2575, 112.7521], "Semarang": [-6.9667, 110.4167], "Makassar": [-5.1477, 119.4327],
    "Belawan": [3.7905, 98.6839], "Sabang": [5.8933, 95.3214], "Palembang": [-2.9761, 104.7754],
    "Padang": [-0.9492, 100.3543], "Nieuw-Guinea": [-2.5337, 140.7181], "Indonesië": [-6.1751, 106.8272],
    "Amsterdam": [52.3771, 4.8970], "Rotterdam": [51.9200, 4.4800], "Vlissingen": [51.4426, 3.5735],
    "Nederland": [51.9200, 4.4800], "Genua": [44.4108, 8.9327], "Napels": [40.8400, 14.2500],
    "Southampton": [50.9026, -1.4043], "Suez": [29.9668, 32.5498], "Port Said": [31.2565, 32.2841],
    "Colombo": [6.9271, 79.8612], "Singapore": [1.2905, 103.8520], "Paramaribo": [5.8520, -55.2038],
    "Curaçao": [12.1696, -68.9900], "Korea": [37.5665, 126.9780], "Bangkok": [13.7563, 100.5018],
    "Rangoon": [16.8661, 96.1951], "Hongkong": [22.3193, 114.1694], "Sydney": [-33.8688, 151.2093],
    "Brisbane": [-27.4698, 153.0251], "Australië": [-33.8688, 151.2093], "Londen": [51.5074, -0.1278],
    "Hamburg": [53.5511, 9.9937], "West-Indië": [12.1696, -68.9900],
    "Triëst": [45.6495, 13.7768], "Venetië": [45.4408, 12.3155],
}
# ruwe bronnaam -> canoniek
ALIAS = {
    "djakarta":"Batavia","batativa":"Batavia","indonesie":"Indonesië","midden-java":"Semarang",
    "west-java":"Bandoeng","macassar":"Makassar","celebes":"Makassar","soerabaia":"Soerabaja",
    "belawan deli":"Belawan","roterdam":"Rotterdam","amstedam":"Amsterdam","ansterdam":"Amsterdam",
    "nedeland":"Nederland","nederland - militairen":"Nederland","sauthampton":"Southampton",
    "candy":"Colombo","ceylon":"Colombo","paramarribo":"Paramaribo","suriname":"Paramaribo",
    "curacao":"Curaçao","groot brittanië":"Londen","duitsland":"Hamburg","australie":"Australië",
    "hong kong":"Hongkong","amserdam":"Amsterdam","tandjang priok":"Tandjong Priok",
    "tanndjong priok":"Tandjong Priok","parimaribo":"Paramaribo","nieuw guinea":"Nieuw-Guinea",
    "nederland (per trein)":"Nederland","triest":"Triëst","venetie":"Venetië",
}

def canon(raw):
    if not raw: return None, None
    s = raw.strip()
    if re.match(r'\d{1,2}[-/ ]', s): return None, None          # datum die in plaats-veld belandde

    # compounds: neem het eerste deel vóór 'en'/komma/haakjes-nummering
    s = re.sub(r'^\(\d\)\(?\d?\)?\s*', '', s)                  # (1)(2) Amsterdam
    s = re.split(r'\s+en\s+vervolgens\s+|\s+en\s+|,\s*', s)[0].strip()
    low = s.lower()
    name = ALIAS.get(low, s)
    # exacte of case-insensitieve match in COORDS
    if name in COORDS: return name, COORDS[name]
    for k, v in COORDS.items():
        if k.lower() == name.lower(): return k, v
    return None, None

import sys
FILE = sys.argv[1] if len(sys.argv) > 1 else f"{BASE}/repat_reizen.json"
if not os.path.isabs(FILE): FILE = f"{BASE}/{FILE}"
R = json.load(open(FILE, encoding='utf-8'))
mis = set()
for r in R:
    for fld, ll in (("van","van_ll"), ("via","via_ll"), ("naar","naar_ll")):
        nm, coord = canon(r.get(fld))
        r[ll] = coord
        r[fld + "_naam"] = nm or r.get(fld)
        if r.get(fld) and not coord: mis.add(r[fld])
    # jaar-sanity
    if r.get("jaar") and not (1945 <= r["jaar"] <= 1965): r["jaar"] = None

json.dump(R, open(FILE, "w", encoding='utf-8'), ensure_ascii=False, indent=1)
plot = sum(1 for r in R if r.get("van_ll") and r.get("naar_ll"))
print(f"reizen: {len(R)} | plotbaar (van+naar coord): {plot}")
print(f"ongegeocodeerd (rest, meestal ruis): {sorted(mis)}")
