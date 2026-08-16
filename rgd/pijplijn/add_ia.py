#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Voeg de IA/IIA-tekeningen toe die de gebruiker handmatig op plaats zette (CSV: ID;SubID;Plaats).
Groepeert de bladen per (inventarisnummer, plaats), geocodeert (gebonden aan de stad), haalt scans,
en schrijft rgd_ia.json (om in rgd_all.json te mergen)."""
import csv, json, os, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from rgd_categories import categorie, soort_tekening

WORK = os.path.dirname(os.path.abspath(__file__))
SRC = "/Users/alan/Downloads/4.RGD.xml"
CSVF = "/Users/alan/Downloads/rgd toevoegingen.csv"
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"
PDOK = "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?"
MC = json.load(open(f"{WORK}/mets_cache.json", encoding="utf-8")) if os.path.exists(f"{WORK}/mets_cache.json") else {}
PC = json.load(open(f"{WORK}/pdok_cache.json", encoding="utf-8")) if os.path.exists(f"{WORK}/pdok_cache.json") else {}

# ---- CSV -> {inv: {volgnr: plaats}} (bereiken als 1-26 uitklappen) ----
CSVMAP = {}
for row in csv.reader(open(CSVF), delimiter=";"):
    if len(row) < 3 or not row[0].strip().isdigit(): continue
    inv, sub, plaats = row[0].strip(), row[1].strip(), row[2].strip()
    if not plaats: continue
    subs = []
    if "-" in sub:
        a, b = sub.split("-", 1)
        if a.strip().isdigit() and b.strip().isdigit(): subs = [str(n) for n in range(int(a), int(b) + 1)]
    elif sub.isdigit():
        subs = [sub]
    for s in subs: CSVMAP.setdefault(inv, {})[s] = plaats
INVS = set(CSVMAP)
print("CSV: inv.nrs", sorted(INVS, key=int), "; plaats-toewijzingen", sum(len(v) for v in CSVMAP.values()))

def get(url, binary=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
        return r.read() if binary else r.read().decode("utf-8", "replace")

def txt(el): return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""
def first_uid(did):
    for u in did.findall("unitid"):
        if u.get("type") not in ("handle", "series_code") and u.get("audience") != "internal": return txt(u)
    return ""

def pdok(q, fq):
    key = q + "||" + ";".join(fq)
    if key in PC: return PC[key]
    hit = None
    try:
        d = json.loads(get(PDOK + urllib.parse.urlencode({"q": q, "rows": 1, "fq": fq}, doseq=True)))
        docs = d.get("response", {}).get("docs", [])
        if docs:
            m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", docs[0].get("centroide_ll", ""))
            if m: hit = {"lon": float(m.group(1)), "lat": float(m.group(2)), "type": docs[0].get("type", "")}
        time.sleep(0.15)
    except Exception as e:
        print("  ! pdok", q, e)
    PC[key] = hit
    return hit
PREC = {"adres": "adres", "weg": "straat", "woonplaats": "plaats", "gemeente": "plaats"}
# Historische/dialectspellingen -> moderne plaatsnaam die PDOK wél kent
ALIAS = {
    "bergschehoek": "Bergschenhoek", "bergum": "Burgum", "birdaard": "Burdaard",
    "beetgumermolen": "Bitgummole", "beekgamermolen": "Bitgummole", "daarlo": "Daarle",
    "diemerbrug": "Diemen", "driet": "Driel", "eis": "Eys", "giekerk-oenkerk": "Gytsjerk",
    "hattum": "Hattem", "melvoirt": "Helvoirt", "murmerwoude": "Damwâld",
    "nijehorne": "Nieuwehorne", "oostermeer": "Eastermar", "oudehaste": "Oudehaske",
    "stamprooi": "Stramproy", "tietjerk-suowoude": "Tytsjerk", "urssem": "Ursem",
    "wahneperveen": "Wanneperveen", "warga": "Wergea", "warmerhuizen": "Warmenhuizen",
    "wolpkaartsdijk": "Wolphaartsdijk", "woudenburg": "Woudenberg", "zoetelande": "Zoutelande",
    "zoeterwoud": "Zoeterwoude", "zwaagwesteinde-kolummerzwaag": "Zwaagwesteinde",
    "metslawier": "Metslawier", "beckum": "Beckum", "glanerbrug": "Glanerbrug", "kethel": "Kethel",
}
def geocode(place):
    place = ALIAS.get(place.strip().lower(), place).strip()
    if "," in place:                                        # "Stad, Straat nr" -> adres gebonden aan de stad
        city, street = [x.strip() for x in place.split(",", 1)]
        bind = f'woonplaatsnaam:"{city}" OR gemeentenaam:"{city}"'
        h = pdok(f"{street}, {city}", ["type:(adres OR weg)", bind])
        return h or pdok(city, ["type:(woonplaats OR gemeente)"])
    h = pdok(place, ["type:(woonplaats OR gemeente)"])      # kale plaatsnaam
    return h or pdok(place, ["type:(woonplaats OR gemeente OR adres OR weg)"])  # laatste redmiddel

def scan_urls(mets):
    if mets not in MC:
        try:
            x = get(f"https://service.archief.nl/gaf/api/mets/v1/{mets}")
            m = re.search(r"/api/file/v1/default/([0-9a-f-]{36})", x); MC[mets] = m.group(1) if m else None
            time.sleep(0.1)
        except Exception: MC[mets] = None
    fid = MC.get(mets)
    return (f"https://service.archief.nl/api/file/v1/thumb/{fid}", f"https://service.archief.nl/api/file/v1/default/{fid}") if fid else (None, None)

# ---- XML: IA + IIA-subbomen ----
body = open(SRC, encoding="utf-8").read(); body = body[body.find("<dsc"):]
def subtree(code):
    m = re.search(r'<unitid type="series_code">' + re.escape(code) + r"</unitid>", body)
    s = body.rfind("<c ", 0, m.start()); d = 0; i = s
    while i < len(body):
        if body.startswith("</c>", i): d -= 1; i += 4
        elif body.startswith("<c ", i) or body.startswith("<c>", i): d += 1; i += 3
        else: i += 1
        if d == 0: break
    return body[s:i]

titlemap = {}   # inv -> filegrp-titel
bladen = {}     # inv -> [ {id, volgnr, ...} ]
for code in ("IA", "IIA"):
    root = ET.fromstring(subtree(code))
    for c in root.iter("c"):
        did = c.find("did")
        if did is None: continue
        t = txt(did.find("unittitle"))
        uid = first_uid(did)
        inv = uid.split(".")[0] if uid else ""
        if inv in INVS and t and not t.lower().startswith("tekening"):
            titlemap.setdefault(inv, t)                       # filegrp-titel
        dao = did.find("dao")
        if dao is None or inv not in INVS: continue
        volgnr = uid.split(".")[1] if "." in uid else uid
        ud = did.find("unitdate"); yr = None
        if ud is not None and ud.get("normal"):
            mm = re.search(r"\d{4}", ud.get("normal")); yr = int(mm.group()) if mm else None
        sc = did.find("materialspec")
        gid = re.search(r"([0-9a-f-]{36})", dao.get("href", ""))
        handle = next((txt(u) for u in did.findall("unitid") if u.get("type") == "handle"), "")
        bladen.setdefault(inv, []).append({"id": uid, "volgnr": volgnr, "year": yr,
            "scale": txt(sc) if sc is not None else "", "micro": False,
            "mets": gid.group(1) if gid else "", "handle": handle})

# ---- groepeer per (inv, plaats) -> project ----
from collections import defaultdict
projects = []
for inv, bl in bladen.items():
    title = titlemap.get(inv, "Ontwerptekening")
    cat, em = categorie(title)
    byplace = defaultdict(list)
    for s in bl:
        plaats = CSVMAP.get(inv, {}).get(s["volgnr"])
        if plaats: byplace[plaats].append(s)
    for plaats, sheets in byplace.items():
        hit = geocode(plaats)
        if not hit: print("  ! geen coord:", plaats); continue
        stad_p, loc_p = ([x.strip() for x in plaats.split(",", 1)] if "," in plaats else (plaats, None))
        for s in sheets:
            t, f = scan_urls(s["mets"]);
            if t: s["thumb"] = t; s["full"] = f
        years = [s["year"] for s in sheets if s["year"]]
        projects.append({"uid": f"{inv}", "stad": stad_p, "titel": f"{plaats}: {title}",
            "locatie": loc_p, "gebouw": title, "cat": cat, "emoji": em, "soort": soort_tekening(title),
            "mat": "tekening", "sectie": "IA/IIA", "invnr": inv,
            "jaar_min": min(years) if years else None, "jaar_max": max(years) if years else None,
            "n_bladen": len(sheets), "n_micro": 0, "schalen": sorted({s["scale"].replace("Schaal", "").strip() for s in sheets if s["scale"]})[:6],
            "lat": round(hit["lat"], 6), "lon": round(hit["lon"], 6), "prec": PREC.get(hit["type"], "plaats"),
            "bron_geo": "pdok", "sheets": sheets})

json.dump(PC, open(f"{WORK}/pdok_cache.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(MC, open(f"{WORK}/mets_cache.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(projects, open(f"{WORK}/rgd_ia.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"toegevoegd: {len(projects)} projecten (IA/IIA), {sum(p['n_bladen'] for p in projects)} bladen -> rgd_ia.json")
from collections import Counter
print("per inv.nr:", dict(Counter(p['invnr'] for p in projects)))
