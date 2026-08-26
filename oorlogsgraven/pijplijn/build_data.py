#!/usr/bin/env python3
"""Stap 3: bouw de sitedata voor de OGS-kaart.
- twee lagen (herkomst = geboorteplaats, overlijden = overlijdensplaats)
- plaatsen gegroepeerd op coördinaat (varianten als 'Omg. Auschwitz' vallen samen)
- personen gekoppeld aan hun herkomst- en overlijdensstip via index
Schrijft site/ogs_data.json + site/personen.json.
"""
import json, os, re, csv
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(HERE + "/../site")

persons = json.load(open(HERE + "/persons.json", encoding="utf-8"))
agg = json.load(open(HERE + "/aggregaten.json", encoding="utf-8"))
geo = json.load(open(HERE + "/geocode.json", encoding="utf-8"))  # {place:[lat,lon]}

# --- type overlijdensplaats (feitelijk, op plaatsnaam; geen identiteitsclaim) ---
_KZ = re.compile(r"auschwitz|sobibor|bergen.?belsen|mauthausen|neuengamme|westerbork|vught|dachau|buchenwald|"
    r"ravensbr|flossenb|natzweiler|stutthof|sachsenhausen|oranienburg|majdanek|gross.?rosen|treblinka|"
    r"theresienstadt|blechhammer|monowitz|birkenau|mittelbau|\bdora\b|gusen|amersfoort|ellecom|"
    r"kdo\.|kommando|arbeitslager|konzentrationslager", re.I)
_GEV = re.compile(r"gevangenis|tuchthuis|zuchthaus|strafgef|huis van bewaring", re.I)
_INDIE_KAMP = re.compile(r"\bkamp\b|tjideng|struiswijk|glodok|kampili|halmaheira|bangkong|lampersari|"
    r"tjihapit|adek|kramat|si rengorengo|belalau|pakan ?baroe|ambarawa|banjoebiroe", re.I)
def death_ctx(op):
    o = (op or "").strip()
    if not o or o.lower() == "onbekend":
        return ""
    if _KZ.search(o): return "kamp"          # concentratie-/vernietigingskamp
    if _GEV.search(o): return "gevangenis"
    if _INDIE_KAMP.search(o): return "indie"  # interneringskamp Indië/Japan
    return "elders"

W = "https://nl.wikipedia.org/wiki/"
CAMP_REF = {   # kampstip -> naslag (Nederlandstalige Wikipedia)
    "auschwitz": W+"Concentratiekamp_Auschwitz", "sobibor": W+"Vernietigingskamp_Sobibor",
    "bergen-belsen": W+"Concentratiekamp_Bergen-Belsen", "mauthausen": W+"Concentratiekamp_Mauthausen",
    "neuengamme": W+"Concentratiekamp_Neuengamme", "westerbork": W+"Kamp_Westerbork",
    "vught": W+"Kamp_Vught", "dachau": W+"Concentratiekamp_Dachau", "buchenwald": W+"Concentratiekamp_Buchenwald",
    "ravensbr": W+"Concentratiekamp_Ravensbr%C3%BCck", "flossenb": W+"Concentratiekamp_Flossenbürg",
    "natzweiler": W+"Concentratiekamp_Natzweiler-Struthof", "stutthof": W+"Concentratiekamp_Stutthof",
    "sachsenhausen": W+"Concentratiekamp_Sachsenhausen", "gross-rosen": W+"Concentratiekamp_Groß-Rosen",
    "gross rosen": W+"Concentratiekamp_Groß-Rosen", "theresienstadt": W+"Concentratiekamp_Theresienstadt",
    "majdanek": W+"Vernietigingskamp_Majdanek", "treblinka": W+"Vernietigingskamp_Treblinka",
    "amersfoort": W+"Kamp_Amersfoort", "mittelbau": W+"Concentratiekamp_Mittelbau-Dora",
    "mauthausen-gusen": W+"Concentratiekamp_Mauthausen", "gusen": W+"Concentratiekamp_Mauthausen",
    "monowitz": W+"Concentratiekamp_Auschwitz", "birkenau": W+"Concentratiekamp_Auschwitz",
    "blechhammer": W+"Concentratiekamp_Auschwitz", "oranienburg": W+"Concentratiekamp_Sachsenhausen",
}
def camp_ref(label):
    k = label.lower()
    for name, url in CAMP_REF.items():
        if name in k:
            return url
    return ""

def clean_label(name):
    """Uniforme weergavenaam: land-suffixen en Kreis-toevoegsels eraf."""
    s = re.sub(r"\s+(stadt|land)kreis\b.*$", "", name, flags=re.I).strip()
    s = re.sub(r"[,\s]+(belgi[eë]|belg|blg|duitsland|frankrijk|engeland|nederland|polen|"
               r"denemarken|oostenrijk|provincie\s+\w+)\.?$", "", s, flags=re.I).strip()
    s = re.sub(r",\s*[A-Za-z]{1,4}\.?$", "", s).strip()   # ", Fr"  ", DK"  ", NOI"
    s = re.sub(r"\s+[A-Z]{1,2}\.$", "", s).strip()        # " O."  " D."
    return s or name

def build_layer(counts):
    """Groepeer geocode-bare plaatsen op coördinaat. Geeft (dots, place->dotindex)."""
    by_coord = defaultdict(lambda: {"n": 0, "names": Counter()})
    for place, c in counts.items():
        if place not in geo:
            continue
        lat, lon = geo[place]
        key = (round(lat, 3), round(lon, 3))
        by_coord[key]["n"] += c
        by_coord[key]["names"][place] += c
    dots = []
    place2idx = {}
    for (lat, lon), d in sorted(by_coord.items(), key=lambda kv: -kv[1]["n"]):
        idx = len(dots)
        label = clean_label(d["names"].most_common(1)[0][0])
        dots.append({"p": label, "lat": lat, "lon": lon, "n": d["n"]})
        for place in d["names"]:
            place2idx[place] = idx
    return dots, place2idx

herk_dots, h2i = build_layer(agg["herkomst"])
over_dots, o2i = build_layer(agg["overlijden"])
print(f"herkomst-stippen: {len(herk_dots)} | overlijden-stippen: {len(over_dots)}")

# niet op de kaart: vage + niet-geocodeerde plaatsen, per laag
def niet_op_kaart(counts, vaag):
    items = Counter()
    for p, c in counts.items():
        if p not in geo:
            items[p] += c
    for p, c in vaag.items():
        items[p] += c
    return items.most_common()

nok_h = niet_op_kaart(agg["herkomst"], agg["vaag_herkomst"])
nok_o = niet_op_kaart(agg["overlijden"], agg["vaag_overlijden"])

# personen: koppel aan stip-index per laag; compacte url (pad na de host)
HOST = "https://oorlogsgravenstichting.nl/"
pers_out = []
for p in persons:
    u = p["url"]
    upath = u[len(HOST):] if u.startswith(HOST) else ""
    pers_out.append({
        "n": p["n"], "gd": p["gd"], "gp": p["gp"], "od": p["od"], "op": p["op"],
        "nat": p["nat"], "u": upath, "na": p.get("na", ""), "na2": p.get("na2", ""),
        "hi": h2i.get(p["gp"], -1), "oi": o2i.get(p["op"], -1),
        "ctx": death_ctx(p["op"]),
    })

# type overlijdensplaats op de sterftestippen + naslag-link voor kampen
for d in over_dots:
    d["ctx"] = death_ctx(d["p"])
    r = camp_ref(d["p"])
    if r:
        d["ref"] = r

# ---- stats voor Inzichten (ingetogen) ----
sterfjaar = Counter(); gebjaar = Counter(); sterfmaand = Counter(); otype = Counter()
nat = Counter()
for p in persons:
    if p["od"][:4].isdigit(): sterfjaar[p["od"][:4]] += 1
    if p["gd"][:4].isdigit(): gebjaar[p["gd"][:4]] += 1
    m = p["od"][5:7]
    if m.isdigit() and m != "00": sterfmaand[m] += 1
    nat[p["nat"] or "ONBEKEND"] += 1
    otype[death_ctx(p["op"]) or "onbekend"] += 1
stats = {
    "totaal": len(persons),
    "met_geboortedatum": sum(1 for p in persons if p["gd"]),
    "met_correspondentie": sum(1 for p in persons if p.get("na2")),
    "sterfjaar": dict(sorted(sterfjaar.items())),
    "sterfmaand": dict(sorted(sterfmaand.items())),
    "geboortejaar": dict(sorted((y, c) for y, c in gebjaar.items() if 1850 <= int(y) <= 1945)),
    "nationaliteit": dict(nat.most_common()),
    "overlijden_type": dict(otype),
    "top_overlijden": [{"p": d["p"], "n": d["n"]} for d in over_dots[:15]],
    "top_herkomst": [{"p": d["p"], "n": d["n"]} for d in herk_dots[:15]],
}

data = {
    "herkomst": herk_dots, "overlijden": over_dots,
    "niet_op_kaart": {"herkomst": nok_h, "overlijden": nok_o},
    "stats": stats,
    "meta": {
        "geplaatst_herkomst": sum(d["n"] for d in herk_dots),
        "geplaatst_overlijden": sum(d["n"] for d in over_dots),
    },
}
os.makedirs(SITE, exist_ok=True)
json.dump(data, open(SITE + "/ogs_data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(pers_out, open(SITE + "/personen.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
sz = lambda f: os.path.getsize(SITE + "/" + f) / 1e6
print(f"ogs_data.json {sz('ogs_data.json'):.1f} MB | personen.json {sz('personen.json'):.1f} MB")
print(f"herkomst geplaatst {data['meta']['geplaatst_herkomst']} | overlijden geplaatst {data['meta']['geplaatst_overlijden']}")
print(f"niet op kaart: herkomst {sum(c for _,c in nok_h)} | overlijden {sum(c for _,c in nok_o)}")
