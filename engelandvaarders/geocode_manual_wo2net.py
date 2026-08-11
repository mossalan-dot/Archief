#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handmatige slotronde: herleidbare missers (typo's, oude/Indische namen) via gerichte query."""
import json, time, urllib.parse, urllib.request

Q = {
 'Frederikstad|Noorwegen':'Fredrikstad, Norway',
 'Tessine|Zwitserland':'Ticino, Switzerland',
 'Uykhoven|Belgïe':'Uikhoven, Lanaken, Belgium',
 'Bitzingen|België':'Bassenge, Belgium',
 'Chateau de Clairfont, Toulouse|Frankrijk':'Toulouse, France',
 'Moncourt Fremonville|Frankrijk':'Frémonville, France',
 'Majalengka (Madjalenka, Java)|Nederlands-Indië':'Majalengka, Indonesia',
 'Pankalan Brandan (Sumatra)|Nederlands-Indië':'Pangkalan Brandan, Indonesia',
 'Pampanua, Celebes (Sulawesi)|Nederlands-Indië':'Pampanua, Indonesia',
 'Wendisch-Karstnitz|Duitsland':'Karścino, Poland',
 'Patoe Kras (Batu Kras), Sumatra|Nederlands-Indië':'Batu Karas, Indonesia',
}
UA = "engelandvaarders-kaart/1.0 (mossalan@gmail.com)"
cache = json.load(open('geocache.json', encoding='utf-8'))
# artefact verwijderen
cache.pop('familie Van Niftrik|Putte, Nederland', None)
ok = miss = 0
for key, q in Q.items():
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format":"json","limit":1})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        if d:
            cache[key] = {"lat":float(d[0]["lat"]),"lon":float(d[0]["lon"]),"display":d[0].get("display_name","")}
            ok += 1; print("ok  ", key, "->", round(cache[key]['lat'],2), round(cache[key]['lon'],2))
        else:
            miss += 1; print("MISS", key, "  q=", q)
    except Exception as e:
        miss += 1; print("! fout", key, e)
    time.sleep(1.1)
json.dump(cache, open('geocache.json','w',encoding='utf-8'), ensure_ascii=False)
print(f"KLAAR: ok={ok} miss={miss} | geocache {len(cache)}")
