#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handmatige plaatsbepaling voor dossiers die het reguliere patroon mist.
Resolvt naar manual_coords.json: nr -> {lat, lon, prec, place}.
Types:
  place  -> geocode plaatsnaam (NL)                 prec 'plaats'
  detail -> geocode "straat/gracht, plaats" (NL)    prec 'straat' (val terug op plaats)
  water  -> geocode waternaam (NL)                  prec 'water'
  between-> midden tussen twee geocodeerde plaatsen prec 'hemelsbreed'
  abroad -> geocode plaatsnaam (buitenland toegestaan) prec 'plaats'
  coord  -> expliciete [lat,lon] (offshore/bijzonder)  prec naar keuze
"""
import json, os, time, urllib.parse, urllib.request

WORK = os.path.dirname(os.path.abspath(__file__))
CACHE = f"{WORK}/manual_geocache.json"
gc = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
UA = "CarnegieHeldenfondsKaart/1.0 (mossalan@gmail.com)"
NL_VIEWBOX = "3.2,53.7,7.4,50.6"

def nominatim(q, nl=True):
    if q in gc:
        return gc[q]
    params = {"q": q, "format": "jsonv2", "limit": 1}
    if nl:
        params["countrycodes"] = "nl"; params["viewbox"] = NL_VIEWBOX; params["bounded"] = 1
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.load(resp)
    except Exception as e:
        print("  ! fout", q, e); res = []
    time.sleep(1.1)
    hit = ({"lat": float(res[0]["lat"]), "lon": float(res[0]["lon"]), "display": res[0].get("display_name", "")}
           if res else None)
    gc[q] = hit
    json.dump(gc, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return hit

# --- de handmatige tabel ---
MANUAL = {
    # grachten / straten (straat-precisie; valt terug op plaats)
    510:  ("detail", "Lijnbaansgracht", "Amsterdam"),
    1246: ("detail", "Prinsengracht", "Amsterdam"),
    1394: ("detail", "Lijnbaansgracht", "Amsterdam"),
    6428: ("detail", "Lijnbaan", "'s-Gravenhage"),
    6518: ("detail", "Geldropseweg", "Eindhoven"),
    6955: ("detail", "Zwanenburgwal", "Amsterdam"),
    7028: ("place", "'s-Gravenhage"),           # "Binnengracht" onzeker -> centrum Den Haag
    7629: ("detail", "Singelgracht", "Amsterdam"),
    7665: ("detail", "Slachthuiskade", "'s-Gravenhage"),
    9017: ("detail", "Bloemgracht", "Amsterdam"),
    9029: ("detail", "Huisduinerweg", "Den Helder"),
    9160: ("detail", "Prunusstraat", "Terneuzen"),
    9607: ("detail", "Kieldiep", "Hoogezand"),
    # eenvoudige plaatsen
    1045: ("place", "'s-Gravenhage"),
    1247: ("place", "Maastricht"),
    1340: ("place", "Lent"),
    1493: ("place", "Rotterdam"),
    1565: ("place", "Woltersum"),
    2290: ("place", "De Meern"),
    2539: ("place", "'s-Gravenhage"),
    2751: ("place", "Eerste Exloërmond"),
    2974: ("place", "'s-Hertogenbosch"),
    3155: ("place", "Amsterdam"),
    3458: ("place", "'s-Gravenhage"),
    3975: ("place", "Deventer"),
    3981: ("place", "Rotterdam"),
    4430: ("place", "Rotterdam"),
    4835: ("place", "Schiermonnikoog"),
    4963: ("place", "De Wijk, Drenthe"),
    5498: ("place", "Amsterdam"),
    5513: ("place", "Sluis, Zeeland"),
    6157: ("place", "Amsterdam"),
    6628: ("place", "Oud-Beijerland"),
    6996: ("place", "Vlieland"),
    7152: ("place", "De Koog, Texel"),
    7321: ("place", "Terschelling"),
    7706: ("place", "Rottumeroog"),
    8063: ("place", "Krommenie"),
    9187: ("place", "Berkel en Rodenrijs"),
    # wateren (centreren)
    1137: ("water", "IJsselmeer"),
    4830: ("water", "IJsselmeer"),
    5822: ("water", "IJsselmeer"),
    7135: ("water", "IJsselmeer"),
    4420: ("water", "Braassemermeer"),
    1583: ("water", "Grevelingenmeer"),
    5917: ("water", "Hollands Diep"),
    7946: ("water", "Oosterschelde"),
    8834: ("water", "Oosterschelde"),
    8309: ("water", "Heegermeer"),
    8592: ("water", "Kagerplassen"),
    9622: ("water", "Kagerplassen"),
    7624: ("water", "Marsdiep"),
    6832: ("water", "Brielse Maas"),
    # midden tussen twee plaatsen
    518:  ("between", "Zunderdorp", "Ransdorp"),
    572:  ("between", "Delft", "Overschie"),
    1881: ("between", "Amersfoort", "Apeldoorn"),
    3251: ("between", "Eethen", "Drongelen"),
    7231: ("between", "Zwolle", "Heino"),
    7239: ("between", "Sint Laurens", "Serooskerke"),
    9053: ("between", "Woerden", "Gouda"),
    9089: ("between", "Alkmaar", "Harlingen"),
    9434: ("between", "Gaast", "Makkum"),
    # buitenland
    562:  ("abroad", "St Lucia, KwaZulu-Natal, South Africa"),
    5508: ("abroad", "Merauke, Indonesia"),
    5910: ("place", "Bath, Reimerswaal"),        # Nauw van Bath = Westerschelde (NL), niet Engeland
    6973: ("abroad", "Altenhuntorf, Elsfleth, Germany"),
    # offshore / bijzonder (expliciete coord)
    1451: ("coord", 52.30, 4.20, "water", "Noordzee"),
    2041: ("coord", 52.35, 4.15, "water", "Noordzee"),
    3046: ("coord", 52.25, 4.10, "water", "Noordzee"),
    6261: ("coord", 52.05, 4.15, "water", "Noordzee (voor Scheveningen)"),
    1600: ("coord", 53.45, 5.90, "water", "Waddenzee (bij Holwerd)"),
    1648: ("coord", 53.32, 5.62, "water", "Waddenzee (voor Het Bildt)"),
    7308: ("coord", 51.885, 4.64, "water", "splitsing Lek–Noord"),
    8846: ("coord", 52.62, 5.72, "water", "Ketelmeer (voorm. Ketelmond)"),
    5915: ("coord", -34.30, 22.50, "hemelsbreed", "Zuidkust Zuid-Afrika"),
    8583: ("coord", 54.00, 10.80, "water", "Lübecker Bocht (Oostzee)"),
}

out = {}
for nr, spec in MANUAL.items():
    t = spec[0]
    if t == "place":
        g = nominatim(spec[1]); prec = "plaats"
    elif t == "abroad":
        g = nominatim(spec[1], nl=False); prec = "plaats"
    elif t == "water":
        g = nominatim(spec[1]); prec = "water"
    elif t == "detail":
        g = nominatim(f"{spec[1]}, {spec[2]}")
        prec = "straat"
        if not g:
            g = nominatim(spec[2]); prec = "plaats"
    elif t == "between":
        a, b = nominatim(spec[1]), nominatim(spec[2])
        g = {"lat": (a["lat"]+b["lat"])/2, "lon": (a["lon"]+b["lon"])/2,
             "display": f"midden {spec[1]}–{spec[2]}"} if a and b else None
        prec = "hemelsbreed"
    elif t == "coord":
        g = {"lat": spec[1], "lon": spec[2], "display": spec[4]}; prec = spec[3]
    else:
        g = None; prec = "?"
    label = spec[-1] if t in ("place", "abroad", "water", "coord") else (spec[2] if t == "detail" else f"{spec[1]}–{spec[2]}")
    if g:
        out[str(nr)] = {"lat": round(g["lat"], 5), "lon": round(g["lon"], 5), "prec": prec,
                        "place": (spec[1] if t in ("place", "abroad") else label)}
        print(f"  {nr:5d} [{prec:11s}] {g['lat']:.4f},{g['lon']:.4f}  {g['display'][:52]}")
    else:
        print(f"  {nr:5d} !! NIET GEVONDEN: {spec}")

json.dump(out, open(f"{WORK}/manual_coords.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n{len(out)}/{len(MANUAL)} opgelost -> manual_coords.json")
