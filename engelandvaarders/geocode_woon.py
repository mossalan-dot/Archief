#!/usr/bin/env python3
"""Geocode unieke woonplaatsen → woon_geocache.json (key = originele woonplaats-string)."""
import json, time, os, re, urllib.parse, urllib.request
from collections import Counter

UA="engelandvaarders-kaart/1.0 (mossalan@gmail.com)"
CACHE="woon_geocache.json"
P=json.load(open("people.json"))
cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}

wp=Counter(p['woonplaats'].strip() for p in P if p['woonplaats'].strip())

def query(raw):
    # "Leiden; Amsterdam" -> eerste; "Antwerpen (België)" -> plaats + land
    s=raw.split(';')[0].strip()
    country=''
    m=re.match(r'^(.*?)\s*\(([^)]+)\)\s*$', s)
    if m: s, country = m.group(1).strip(), m.group(2).strip()
    q = f"{s}, {country}" if country else f"{s}, Nederland"
    url="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode({"q":q,"format":"json","limit":1})
    req=urllib.request.Request(url, headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: data=json.load(r)
        if data: return {"lat":float(data[0]["lat"]),"lon":float(data[0]["lon"])}
    except Exception as e: print("  !",raw,e)
    return None

todo=[w for w in wp if w not in cache]
print("te geocoden woonplaatsen:",len(todo))
for i,w in enumerate(todo):
    cache[w]=query(w)
    if (i+1)%20==0:
        json.dump(cache,open(CACHE,"w",encoding="utf-8"),ensure_ascii=False)
        print(f"  {i+1}/{len(todo)}")
    time.sleep(1.05)
json.dump(cache,open(CACHE,"w",encoding="utf-8"),ensure_ascii=False)
hit=sum(1 for v in cache.values() if v)
print(f"KLAAR. {len(cache)} woonplaatsen, {hit} gevonden")
