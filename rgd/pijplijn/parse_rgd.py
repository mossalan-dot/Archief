#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse het RGD-objectenarchief (EAD 4.RGD) tot bouwproject-records.
Proefdeel: één plaats-kop (default Amsterdam). Per bouwproject (filegrp):
  stad, straat/locatie, gebouw, functie-categorie, soort tekening, jaren,
  schaal-reeks, origineel/microfilm, aantal bladen, scan-links (dao).
"""
import re, json, sys, html as _html
import xml.etree.ElementTree as ET

SRC = "/Users/alan/Downloads/4.RGD.xml"
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
NEXT = sys.argv[2] if len(sys.argv) > 2 else None  # volgende plaats-kop (grens); auto indien leeg

raw = open(SRC, encoding="utf-8").read()
body = raw[raw.find("<dsc"):]

# --- knip de <c>-subboom van de plaats-kop uit ---
m = re.search(r"<unittitle>" + re.escape(PLACE) + r"</unittitle>", body)
if not m:
    sys.exit("plaats-kop niet gevonden: " + PLACE)
start = body.rfind("<c ", 0, m.start())
# balanced scan over <c ...> / </c>
depth = 0; i = start; n = len(body)
while i < n:
    if body.startswith("</c>", i): depth -= 1; i += 4;  # noqa
    elif body.startswith("<c ", i) or body.startswith("<c>", i): depth += 1; i += 3
    else: i += 1
    if depth == 0: break
sub = body[start:i]
# ElementTree wil één root; EAD heeft geen namespace
root = ET.fromstring(sub)

def txt(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""

FUNC = [
    ("politie", "👮", ["politiebureau", "politiepost", "marechaussee", "politie"]),
    ("gevangeniswezen", "🔒", ["huis van bewaring", "gevangenis", "cellenbarak", "strafgevangenis", "rijkswerkinrichting"]),
    ("rechtspraak", "⚖️", ["rechtbank", "gerechtsgebouw", "paleis van justitie", "kantongerecht", "gerechtshof"]),
    ("post & telegraaf", "✉️", ["post", "telegraaf", "telefoon"]),
    ("militair", "🎖️", ["kazerne", "militair", "marine", "fort", "genie", "arsenaal", "magazijn van oorlog"]),
    ("museum & paleis", "🏛️", ["museum", "paleis", "koninklijk"]),
    ("kerk & religie", "⛪", ["kerk", "kapel", "klooster", "synagoge"]),
    ("onderwijs & wetenschap", "🎓", ["school", "universiteit", "laboratorium", "proefstation", "sterrenwacht", "hogeschool", "gymnasium"]),
    ("douane & opslag", "📦", ["entrepot", "pakhuis", "douane", "loods", "magazijn"]),
    ("bestuur & financiën", "🏢", ["kantoor", "agentschap", "administratie", "belasting", "financiën", "ministerie", "rijksgebouw", "gouvernement", "provinciaal", "raadhuis", "stadhuis", "secretarie"]),
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
    """'Straat 12: Gebouw - Soort'  -> (locatie, gebouw)"""
    loc, rest = None, t
    if ":" in t:
        loc, rest = t.split(":", 1)
        loc = loc.strip(); rest = rest.strip()
    if " - " in rest:
        rest = rest.rsplit(" - ", 1)[0].strip()
    return loc, rest

# --- loop bouwprojecten (directe filegrp-kinderen van de plaats-kop) ---
projects = []
for c in root.findall("./c"):
    lvl = c.get("otherlevel") or c.get("level")
    did = c.find("did")
    if did is None: continue
    title = txt(did.find("unittitle"))
    if not title or title.lower().startswith("tekening"): continue
    uid = ""
    for u in did.findall("unitid"):
        if u.get("type") not in ("handle",) and u.get("audience") != "internal":
            uid = txt(u); break
    # projectdatum (staat vaak op filegrp-niveau)
    pdate = did.find("unitdate")
    if pdate is not None and pdate.get("normal"):
        years0 = [int(y) for y in re.findall(r"\d{4}", pdate.get("normal"))]
    else:
        years0 = []
    # verzamel bladen (afstammelingen met een dao)
    sheets, years, scales, micro = [], list(years0), set(), 0
    for it in c.iter("c"):
        d = it.find("did")
        if d is None: continue
        dao = d.find("dao")
        if dao is None: continue
        iid = ""
        for u in d.findall("unitid"):
            if u.get("type") not in ("handle",) and u.get("audience") != "internal":
                iid = txt(u); break
        ud = d.find("unitdate")
        yr = None
        if ud is not None and ud.get("normal"):
            mm = re.search(r"\d{4}", ud.get("normal")); yr = int(mm.group()) if mm else None
        if yr: years.append(yr)
        sc = d.find("materialspec")
        if sc is not None and txt(sc): scales.add(txt(sc).replace("Schaal", "").strip())
        ch = it.find("custodhist")
        is_micro = ch is not None and "microfiche" in txt(ch).lower()
        if is_micro: micro += 1
        href = dao.get("href", "")
        gid = re.search(r"([0-9a-f-]{36})", href)
        handle = ""
        for u in d.findall("unitid"):
            if u.get("type") == "handle": handle = txt(u)
        sheets.append({"id": iid, "title": txt(d.find("unittitle")), "year": yr,
                       "scale": txt(sc) if sc is not None else "", "micro": is_micro,
                       "mets": gid.group(1) if gid else "", "handle": handle})
    if not sheets:  # project zonder scans overslaan voor proefdeel
        continue
    loc, gebouw = split_title(title)
    cat, em = categorie(title)
    projects.append({
        "uid": uid, "stad": PLACE, "titel": title, "locatie": loc, "gebouw": gebouw,
        "cat": cat, "emoji": em, "soort": soort_tekening(title),
        "jaar_min": min(years) if years else None, "jaar_max": max(years) if years else None,
        "n_bladen": len(sheets), "n_micro": micro, "schalen": sorted(scales)[:6],
        "sheets": sheets,
    })

json.dump(projects, open("rgd_" + PLACE.lower().replace(" ", "_") + ".json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"{PLACE}: {len(projects)} bouwprojecten, {sum(p['n_bladen'] for p in projects)} bladen")
from collections import Counter
print("categorieën:", dict(Counter(p["cat"] for p in projects)))
print("soorten:", dict(Counter(p["soort"] for p in projects)))
print("met locatie (straat):", sum(1 for p in projects if p["locatie"]))
for p in projects[:8]:
    print(f"  {p['uid']:10s} [{p['emoji']}{p['cat'][:12]:12s}] loc={str(p['locatie'])[:22]:22s} {p['gebouw'][:34]:34s} {p['jaar_min']}-{p['jaar_max']} {p['n_bladen']}bl")
