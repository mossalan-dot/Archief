#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compute the insights dataset -> stats.json for the dashboard."""
import json, os, re
from collections import Counter, defaultdict
from gender import gender

WORK = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(f"{WORK}/dossiers_raw.json", encoding="utf-8"))
cache = json.load(open(f"{WORK}/geocache.json", encoding="utf-8"))

from cats import categorize, outcome, CAT_ORDER

PROVS = ["Groningen","Fryslân","Friesland","Drenthe","Overijssel","Flevoland","Gelderland",
         "Utrecht","Noord-Holland","Zuid-Holland","Zeeland","Noord-Brabant","Limburg"]
def province(place):
    g = cache.get(place)
    if not g: return None
    disp = g.get("display","")
    for p in PROVS:
        if p in disp:
            return "Friesland" if p in ("Fryslân","Friesland") else p
    return None

def in_nl(g): return g and 50.6 <= g["lat"] <= 53.7 and 3.2 <= g["lon"] <= 7.4
LAND = {"Ireland":"Ierland","Éire":"Ierland","United Kingdom":"Verenigd Koninkrijk","Deutschland":"Duitsland",
        "Danmark":"Denemarken","France":"Frankrijk","Indonesia":"Indonesië","España":"Spanje","Canada":"Canada",
        "Malaysia":"Maleisië","South Africa":"Zuid-Afrika","Belgi":"België","Nederland":"Nederland (Cariben)"}
def land(place):
    g = cache.get(place)
    if not g: return None
    tail = g.get("display","").split(",")[-1].strip()
    for k, v in LAND.items():
        if k.lower() in tail.lower():
            return v
    # bekende losse gevallen
    low = g.get("display","").lower()
    if "montenegro" in low or "crna gora" in low: return "Montenegro"
    if "italia" in low or "toscana" in low: return "Italië"
    if "qatar" in low or "قطر" in tail: return "Qatar"
    return tail or "onbekend"

CATS = CAT_ORDER
def decade(y): return (y//10)*10 if y else None

CHILD = re.compile(r'\b(kind|kinderen|jongen|meisje|meisjes|jongens|baby|kleuter|peuter|zuigeling|schooljongen|schoolkind)\b', re.I)
ADULT = re.compile(r'\b(persoon|personen|man|mannen|vrouw|vrouwen|tiener|tieners|vader|moeder|bejaarde|grijsaard|echtgeno|collega|buurman|buurvrouw|visser|matroos|militair)\b', re.I)
def victim(desc):
    c, a = bool(CHILD.search(desc)), bool(ADULT.search(desc))
    if c and not a: return "kind"
    if a and not c: return "volwassene"
    if c and a: return "beide"
    return "onbekend"

cat_counts = Counter()
out_counts = Counter()
gen_counts = Counter()
place_counts = Counter()
prov_counts = Counter()
water_counts = Counter()
decade_counts = Counter()
cat_decade = defaultdict(Counter)        # decade -> cat -> n
gender_decade = defaultdict(Counter)     # decade -> gender -> n
rej_decade = defaultdict(lambda: [0,0])  # decade -> [afgewezen, totaal]
year_counts = Counter()                  # jaar -> aantal
year_rej = Counter()                     # jaar -> afgewezen
group = Counter()                        # solo / meerdere
vic_counts = Counter()
bl_counts = Counter()                    # binnenland / buitenland
land_counts = Counter()                  # buitenland -> land

for x in recs:
    det = x.get("detail")
    cat = categorize(x["desc"], det)
    res = outcome(x["desc"])
    gen = gender(x["desc"])
    y = x.get("year_from")
    dec = decade(y)
    cat_counts[cat] += 1
    out_counts[res] += 1
    gen_counts[gen] += 1
    if det: water_counts[det] += 1
    for p in x["places"]:
        place_counts[p] += 1
        g = cache.get(p)
        if g:
            if in_nl(g):
                bl_counts["binnenland"] += 1
                pr = province(p)
                if pr: prov_counts[pr] += 1
            else:
                bl_counts["buitenland"] += 1
                land_counts[land(p)] += 1
        break  # primary place only
    vic_counts[victim(x["desc"])] += 1
    if y:
        year_counts[y] += 1
        if x["afgewezen"]: year_rej[y] += 1
    if dec:
        decade_counts[dec] += 1
        cat_decade[dec][cat] += 1
        gender_decade[dec][gen] += 1
        rej_decade[dec][1] += 1
        if x["afgewezen"]: rej_decade[dec][0] += 1
    # group size: is there a co-rescuer named before the verb?
    m = re.search(r'\b(redde|redden|poogde|poogden|bracht|brachten|namen)\b', x["desc"])
    head = x["desc"][:m.start()] if m else ""
    group["meerdere" if " en " in head else "solo"] += 1

decades = sorted(d for d in decade_counts)
stats = {
    "totaal": len(recs),
    "geplot": sum(1 for x in recs if any(cache.get(p) for p in x["places"])),
    "plaatsen": len(place_counts),
    "jaarspan": [min(x["year_from"] for x in recs if x["year_from"]),
                 max(x["year_from"] for x in recs if x["year_from"])],
    "cat": {c: cat_counts[c] for c in CATS},
    "outcome": dict(out_counts),
    "gender": {g: gen_counts[g] for g in ("man","vrouw","onbekend")},
    "group": dict(group),
    "decades": decades,
    "decade_counts": [decade_counts[d] for d in decades],
    "years": (yy := list(range(min(year_counts), max(year_counts)+1))),
    "year_counts": [year_counts[y] for y in yy],
    "year_rej": [year_rej[y] for y in yy],
    "decade_rej": [rej_decade[d][0] for d in decades],
    "victim": {k: vic_counts[k] for k in ("kind","volwassene","beide","onbekend")},
    "cat_decade": {c: [cat_decade[d][c] for d in decades] for c in CATS},
    "gender_decade_vrouwpct": [round(100*gender_decade[d]["vrouw"]/max(sum(gender_decade[d].values()),1),1) for d in decades],
    "rej_decade_pct": [round(100*rej_decade[d][0]/max(rej_decade[d][1],1),1) for d in decades],
    "top_places": place_counts.most_common(15),
    "provinces": prov_counts.most_common() + [["Buitenland", bl_counts["buitenland"]]],
    "binnenbuiten": {"binnenland": bl_counts["binnenland"], "buitenland": bl_counts["buitenland"]},
    "landen": land_counts.most_common(),
    "top_waters": water_counts.most_common(15),
}
json.dump(stats, open(f"{WORK}/stats.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

print("totaal", stats["totaal"], "| geplot", stats["geplot"])
print("cat", stats["cat"])
print("outcome", stats["outcome"], "| gender", stats["gender"], "| group", stats["group"])
print("decades", decades)
print("decade_counts", stats["decade_counts"])
print("vrouw% per decade", stats["gender_decade_vrouwpct"])
print("afgewezen% per decade", stats["rej_decade_pct"])
print("top provincies", stats["provinces"][:6])
print("top plaatsen", stats["top_places"][:6])
print("top wateren", stats["top_waters"][:8])
print("auto per decade", stats["cat_decade"]["auto"])
print("dier per decade", stats["cat_decade"]["dier"])
print("ijs  per decade", stats["cat_decade"]["ijs"])
