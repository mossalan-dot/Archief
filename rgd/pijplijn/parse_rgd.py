#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse het RGD-objectenarchief (EAD 4.RGD) tot bouwproject-records.
Argument = één plaats-kop (bv. Amsterdam) OF 'ALL' voor het hele objectenarchief (serie IB).
Per bouwproject (filegrp): stad (kop), straat/locatie, gebouw, functie-categorie,
soort tekening, jaren, schaal-reeks, origineel/microfilm, aantal bladen, scan-handles/mets."""
import re, json, sys
import xml.etree.ElementTree as ET

SRC = "/Users/alan/Downloads/4.RGD.xml"
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
ALL = PLACE.upper() == "ALL"

raw = open(SRC, encoding="utf-8").read()
body = raw[raw.find("<dsc"):]

anchor = (r"<unittitle>BOUWTEKENINGEN: SPECIFIEKE ONTWERPEN[^<]*</unittitle>"
          if ALL else r"<unittitle>" + re.escape(PLACE) + r"</unittitle>")
m = re.search(anchor, body)
if not m: sys.exit("kop niet gevonden: " + PLACE)
start = body.rfind("<c ", 0, m.start())
depth = 0; i = start; n = len(body)
while i < n:
    if body.startswith("</c>", i): depth -= 1; i += 4
    elif body.startswith("<c ", i) or body.startswith("<c>", i): depth += 1; i += 3
    else: i += 1
    if depth == 0: break
root = ET.fromstring(body[start:i])

def txt(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""

FUNC = [
    ("politie", "👮", ["politiebureau", "politiepost", "marechaussee", "politie"]),
    ("gevangeniswezen", "🔒", ["huis van bewaring", "gevangenis", "cellenbarak", "strafgevangenis", "rijkswerkinrichting", "tuchthuis"]),
    ("rechtspraak", "⚖️", ["rechtbank", "gerechtsgebouw", "paleis van justitie", "kantongerecht", "gerechtshof"]),
    ("post & telegraaf", "✉️", ["post", "telegraaf", "telefoon"]),
    ("militair", "🎖️", ["kazerne", "militair", "marine", "fort", "genie", "arsenaal", "magazijn van oorlog", "wachtgebouw"]),
    ("museum & paleis", "🏛️", ["museum", "paleis", "koninklijk"]),
    ("kerk & religie", "⛪", ["kerk", "kapel", "klooster", "synagoge", "pastorie"]),
    ("onderwijs & wetenschap", "🎓", ["school", "universiteit", "laboratorium", "proefstation", "sterrenwacht", "hogeschool", "gymnasium", "academie"]),
    ("douane & opslag", "📦", ["entrepot", "pakhuis", "douane", "loods", "magazijn", "kantoor der invoerrechten"]),
    ("zorg", "🏥", ["ziekenhuis", "gasthuis", "sanatorium", "krankzinnig", "gesticht"]),
    ("bestuur & financiën", "🏢", ["kantoor", "agentschap", "administratie", "belasting", "financiën", "ministerie", "rijksgebouw", "gouvernement", "provinciehuis", "provinciaal", "raadhuis", "stadhuis", "secretarie", "ijkkantoor", "munt"]),
]
def categorie(s):
    low = s.lower()
    for name, em, kws in FUNC:
        if any(k in low for k in kws): return name, em
    return "overig", "📐"

def soort_tekening(s):
    low = s.lower()
    if "opmeting" in low: return "opmeting"
    if "bestek" in low or "werktekening" in low: return "bestek & werk"
    if "ontwerp" in low: return "ontwerp"
    if "verbouw" in low or "uitbreiding" in low or "aanbouw" in low: return "verbouw"
    if "situatie" in low or "kadast" in low: return "situatie"
    return "overig"

def split_title(t):
    loc, rest = None, t
    if ":" in t:
        loc, rest = t.split(":", 1); loc = loc.strip(); rest = rest.strip()
    if " - " in rest:
        rest = rest.rsplit(" - ", 1)[0].strip()
    return loc, rest

def first_uid(did):
    for u in did.findall("unitid"):
        if u.get("type") not in ("handle",) and u.get("audience") != "internal":
            return txt(u)
    return ""

def parse_project(c, stad):
    did = c.find("did")
    if did is None: return None
    title = txt(did.find("unittitle"))
    if not title or title.lower().startswith("tekening"): return None
    pdate = did.find("unitdate")
    years = [int(y) for y in re.findall(r"\d{4}", pdate.get("normal") or "")] if pdate is not None and pdate.get("normal") else []
    sheets, scales, micro = [], set(), 0
    for it in c.iter("c"):
        d = it.find("did")
        if d is None: continue
        dao = d.find("dao")
        if dao is None: continue
        ud = d.find("unitdate"); yr = None
        if ud is not None and ud.get("normal"):
            mm = re.search(r"\d{4}", ud.get("normal")); yr = int(mm.group()) if mm else None
        if yr: years.append(yr)
        sc = d.find("materialspec")
        if sc is not None and txt(sc): scales.add(txt(sc).replace("Schaal", "").strip())
        ch = it.find("custodhist"); is_micro = ch is not None and "microfiche" in txt(ch).lower()
        if is_micro: micro += 1
        gid = re.search(r"([0-9a-f-]{36})", dao.get("href", ""))
        handle = next((txt(u) for u in d.findall("unitid") if u.get("type") == "handle"), "")
        sheets.append({"id": first_uid(d), "title": txt(d.find("unittitle")), "year": yr,
                       "scale": txt(sc) if sc is not None else "", "micro": is_micro,
                       "mets": gid.group(1) if gid else "", "handle": handle})
    if not sheets: return None
    loc, gebouw = split_title(title); cat, em = categorie(title)
    return {"uid": first_uid(did), "stad": stad, "titel": title, "locatie": loc, "gebouw": gebouw,
            "cat": cat, "emoji": em, "soort": soort_tekening(title),
            "jaar_min": min(years) if years else None, "jaar_max": max(years) if years else None,
            "n_bladen": len(sheets), "n_micro": micro, "schalen": sorted(scales)[:6], "sheets": sheets}

# plaats-knopen: bij ALL de subseries onder IB; anders is root zelf de plaats
if ALL:
    place_nodes = []
    for c in root.findall("./c"):
        d = c.find("did")
        st = txt(d.find("unittitle")) if d is not None else ""
        if st and "zie" not in st.lower() and c.find("./c") is not None:
            place_nodes.append((st, c))
else:
    place_nodes = [(PLACE, root)]

projects = []
for stad, pc in place_nodes:
    for c in pc.findall("./c"):
        p = parse_project(c, stad)
        if p: projects.append(p)

out = f"rgd_{'all' if ALL else PLACE.lower().replace(' ', '_')}.json"
json.dump(projects, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(f"{'ALLE plaatsen' if ALL else PLACE}: {len(place_nodes)} plaats(en), {len(projects)} bouwprojecten, "
      f"{sum(p['n_bladen'] for p in projects)} bladen -> {out}")
print("categorieën:", dict(Counter(p['cat'] for p in projects).most_common()))
print("met straat-locatie:", sum(1 for p in projects if p['locatie']))
