#!/usr/bin/env python3
"""Geocode unieke plaatsen via Nominatim, met cache (hervatbaar)."""
import json, time, os, urllib.parse, urllib.request

CACHE = "geocache.json"
TODO = "places_todo.json"
UA = "engelandvaarders-kaart/1.0 (mossalan@gmail.com)"

# handmatige overrides / verduidelijkingen (Nederlandse -> zoekterm)
OVERRIDE = {
    "Schotland|Verenigd Koninkrijk": "Scotland, United Kingdom",
    "Gibraltar|": "Gibraltar",
    "Engeland|Verenigd Koninkrijk": "England, United Kingdom",
    "Wales|Verenigd Koninkrijk": "Wales, United Kingdom",
}

def load(p, d):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d

def query(name, country, key):
    if key in OVERRIDE:
        q = OVERRIDE[key]
    elif country and country != name:
        q = f"{name}, {country}"
    else:
        q = name
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": q, "format": "json", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        if data:
            return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]),
                    "display": data[0].get("display_name", "")}
    except Exception as e:
        print("  ! fout", key, e)
    return None

def main():
    todo = load(TODO, [])
    cache = load(CACHE, {})
    done = miss = 0
    for i, (key, info) in enumerate(todo):
        if key in cache:
            continue
        res = query(info["name"], info["country"], key)
        cache[key] = res
        if res: done += 1
        else: miss += 1
        if (done + miss) % 25 == 0:
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  {i+1}/{len(todo)}  ok={done} miss={miss}")
        time.sleep(1.05)  # Nominatim policy
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    hit = sum(1 for v in cache.values() if v)
    print(f"KLAAR. cache={len(cache)} gevonden={hit} niet={len(cache)-hit}")

if __name__ == "__main__":
    main()
