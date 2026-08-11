#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tweede geocode-ronde voor de missers: moderne namen (Indië), typo's, oude gemeenten,
landcorrecties. Werkt alleen op keys die nu None zijn; hervatbaar; 1/sec."""
import json, time, re
from geocode import query

cache = json.load(open('geocache.json', encoding='utf-8'))
ISLANDS = {'java','sumatra','borneo','celebes','bali','flores','sumba','bangka','molukken',
           'kalimantan','sulawesi','meranti-eilanden','sudetenland'}
COUNTRY = {'Nederlands-Indië':'Indonesia', 'Sovjet-Unie':'', 'Joegoslavië':'',
           'Oostenrijk-Hongarije':'', 'Palestina':'Israel', 'Nederlandse Antillen':'Curaçao',
           'Faeröer eilanden':'Faroe Islands', 'tegenwoordig: Most in Tsjechië':'Czechia',
           'Belgïe':'België', 'Belgie':'België'}
# volledige-key overrides (zekere gevallen); waarde None = géén locatie, overslaan
OVERRIDE = {
 'familie Van Niftrik|Putte, Nederland': None,
 'Trontheim|Noorwegen':'Trondheim, Norway', 'Schotlland|Verenigd Koninkrijk':'Scotland, UK',
 'Cuxhafen|Duitsland':'Cuxhaven, Germany', 'Svendsborg|Denemarken':'Svendborg, Denmark',
 'Zaragossa|Spanje':'Zaragoza, Spain', 'Figueires|Spanje':'Figueres, Spain',
 'Lissabon|Spanje':'Lisbon, Portugal', 'Annemas|Frankrijk':'Annemasse, France',
 'Ennecy|Frankrijk':'Annecy, France', 'Vevrier|Zwitserland':'Veyrier, Switzerland',
 'Heilo|Nederland':'Heiloo, Nederland', 'Stad Almelo|Nederland':'Almelo, Nederland',
 'Franekeradeel|Nederland':'Franeker, Nederland',
 'ldaarderadeel (Leeuwarden)|Nederland':'Leeuwarden, Nederland',
 'Norg (Veenhuizen)|Nederland':'Norg, Nederland',
 'Oost- en West Souburg|Nederland':'Oost-Souburg, Nederland',
 'Hooge en Lage Zwaluwe|Nederland':'Lage Zwaluwe, Nederland',
 'Oud en Nieuw Gastel|Nederland':'Oud Gastel, Nederland',
 'Roosendaal en Nispe|Nederland':'Roosendaal, Nederland',
 'Rinsumageest|Nederland':'Rinsumageast, Nederland',
 'Gasselternijenveen|Nederland':'Gasselternijveen, Nederland',
 'Huizem|Nederland':'Huizum, Leeuwarden, Nederland',
 'Koningsbergen|Duitsland':'Kaliningrad, Russia',
 'Belgrado|Joegoslavië':'Belgrade, Serbia', 'Zagreb|Joegoslavië':'Zagreb, Croatia',
 'Odessa|Sovjet-Unie':'Odesa, Ukraine', 'Haifa|Palestina':'Haifa, Israel',
 'Rehovot|Palestina':'Rehovot, Israel', 'El Quantara|Egypte':'El Qantara, Egypt',
 'Torshavn|Faeröer eilanden':'Tórshavn, Faroe Islands',
 'Willemstad (Curaçao)|Nederlandse Antillen':'Willemstad, Curaçao',
 'Brüx, Sudetenland|tegenwoordig: Most in Tsjechië':'Most, Czechia',
 'Bielitz (Bielsko-Biała)|Oostenrijk-Hongarije':'Bielsko-Biała, Poland',
 'Poozel (Pecs)|Hongarije':'Pécs, Hungary', 'Meknez|Marokko':'Meknes, Morocco',
 'Marnia|Marokko':'Maghnia, Algeria', 'Rensburg|Duitsland':'Rendsburg, Germany',
 'Grenade-sur-Ardour|Frankrijk':"Grenade-sur-l'Adour, France",
 'Aire-sur-Ardour|Frankrijk':"Aire-sur-l'Adour, France", 'Bosost|Spanje':'Bossòst, Spain',
 'Kreis Zell a/d Mosel|Duitsland':'Zell (Mosel), Germany',
 'Hohnstein an der Elbe|Duitsland':'Hohnstein, Sachsen, Germany',
 'Hüthum (Emerik)|Duitsland':'Hüthum, Emmerich, Germany', 'Olou|Finland':'Oulu, Finland',
}

def build_query(key):
    if key in OVERRIDE: return OVERRIDE[key]        # kan None zijn
    place, _, country = key.partition('|')
    parens = re.findall(r'\(([^)]+)\)', place)
    base = re.sub(r'\s*\([^)]*\)', '', place).split(',')[0].strip()
    modern = None
    for pr in parens:
        pr = pr.strip()
        if pr.lower() in ISLANDS: continue
        modern = pr.split(',')[0].strip()
    name = modern or base
    c = COUNTRY.get(country, country)
    return f"{name}, {c}" if c else name

miss = [k for k in cache if cache[k] is None]
print(f"missers om opnieuw te proberen: {len(miss)}")
ok = skip = still = 0
for i, key in enumerate(miss, 1):
    q = build_query(key)
    if q is None:
        del cache[key]; skip += 1; continue      # artefact: verwijderen uit cache
    place, _, country = key.partition('|')
    r = query(place, country, key) if False else None
    # directe query op de opgeschoonde string
    import urllib.parse, urllib.request
    try:
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format":"json","limit":1})
        req = urllib.request.Request(url, headers={"User-Agent":"engelandvaarders-kaart/1.0 (mossalan@gmail.com)"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        r = {"lat":float(data[0]["lat"]), "lon":float(data[0]["lon"]), "display":data[0].get("display_name","")} if data else None
    except Exception as e:
        print("  ! fout", key, e); r = None
    if r: cache[key] = r; ok += 1
    else: still += 1; print("  nog steeds miss:", key, "  q=", q)
    if i % 20 == 0:
        json.dump(cache, open('geocache.json','w',encoding='utf-8'), ensure_ascii=False)
    time.sleep(1.1)
json.dump(cache, open('geocache.json','w',encoding='utf-8'), ensure_ascii=False)
print(f"KLAAR: opgelost={ok} artefact-verwijderd={skip} nog-miss={still} | geocache {len(cache)}")
