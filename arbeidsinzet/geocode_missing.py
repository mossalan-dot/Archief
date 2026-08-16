#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Geocodeer de Kreisen die nog geen coördinaat hebben (Nominatim, met opschoning van
historische/Duitse/Nederlandse ruis in de naam). Vult geocode_cache.json aan onder de
oorspronkelijke naam, zodat build_data2.py ze oppikt."""
import json, re, time, urllib.parse, urllib.request

BASE = "/Users/alan/Downloads/arbeidsinzet"
GEOCACHE = f"{BASE}/geocode_cache.json"
cache = json.load(open(GEOCACHE, encoding='utf-8'))
kreisen = json.load(open(f"{BASE}/site/kaart_data.json", encoding='utf-8'))["kreisen"]
missing = [k["naam"] for k in kreisen if k["lat"] is None]
NIET_PLAATS = re.compile(r'dossier|personeel|stukken|kaartsysteem|namenlijst|onbekend', re.I)

def variants(name):
    seen = []
    def add(x):
        x = re.sub(r'\s+', ' ', x).strip()
        if x and x not in seen: seen.append(x)
    add(name)
    low = name
    # NL-ruis en historische toevoegingen weghalen
    low = re.sub(r'\s+zijn begraven$', '', low, flags=re.I)
    low = re.sub(r'\s+in mainfranken$', '', low, flags=re.I)
    low = re.sub(r'\s+an der (saale|unstrut|elster)$', r' (\1)', low, flags=re.I)  # Naumburg (Saale)
    low = re.sub(r'\s+in th[uü]ringen$', '', low, flags=re.I)
    low = re.sub(r'\s+am main$', '', low, flags=re.I)
    low = re.sub(r'^land\s+', '', low, flags=re.I)           # Land Hadeln -> Hadeln
    low = re.sub(r'^st\.?\s+', 'Sankt ', low, flags=re.I)    # St. Wendel -> Sankt Wendel
    add(low)
    add(re.sub(r'\s*\([^)]*\)$', '', low))                   # zonder haakjes: Naumburg
    # samengestelde districten -> eerste deel (Beeskow-Storkow -> Beeskow)
    add(re.split(r'[-/]', low)[0])
    # historische Kreis-achtervoegsels laten vallen
    add(re.sub(r'(gebirgs|see)?kreis$', '', low, flags=re.I))
    return [v for v in seen if v]

def query(term):
    q = urllib.parse.quote(f"{term}, Deutschland")
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent":"arbeidsinzet-kaart/1.0 (mossalan@gmail.com)"})
    with urllib.request.urlopen(req, timeout=20) as r: data = json.load(r)
    time.sleep(1.1)
    return [round(float(data[0]["lat"]),5), round(float(data[0]["lon"]),5)] if data else None

ok = fail = 0
for name in missing:
    if NIET_PLAATS.search(name): continue
    res = None
    for v in variants(name):
        try: res = query(v)
        except Exception as e: print("  fout", v, e)
        if res: break
    cache[name] = res
    if res: ok += 1
    else: fail += 1; print("  GEEN:", name)
    json.dump(cache, open(GEOCACHE, "w", encoding='utf-8'), ensure_ascii=False)
print(f"gegeocodeerd: {ok} | mislukt: {fail}")
