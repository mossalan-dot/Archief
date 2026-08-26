#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fase 2-pijplijn Arbeidsinzet — persoon-gericht.
Schrijft:
  site/kaart_data.json  — kreisen (met top-NL-herkomst + 'Nederland'-bak) + NL-herkomstplaatsen
  site/personen.json    — compacte persoonsindex op reconstructieid (naam, geb.jaar/plaats,
                          overlijden, álle Kreisen) — lazy-geladen bij de eerste zoekactie.
Ethiek: alles is publiek (CC-0, NA 2.19.323 sinds 2023); overlijden ingetogen, kamp-markering blijft."""
import re, csv, glob, json, collections
import xml.etree.ElementTree as ET

BASE = "/Users/alan/Downloads/arbeidsinzet"
EAD = f"{BASE}/inventaris-2.19.323.ead.xml"
CSVS = sorted(glob.glob(f"{BASE}/arbeitseinsatz/arbeitseinsatz_*.csv"))
GEOCACHE = f"{BASE}/geocode_cache.json"
SITE = f"{BASE}/site"

def s(t): return re.sub(r'\{.*?\}', '', t)
CAMP_KREISE = {'dachau','buchenwald','sachsenhausen','oranienburg','neuengamme','flossenburg',
    'flossenbürg','bergen-belsen','ravensbruck','ravensbrück','mittelbau','nordhausen',
    'mauthausen','esterwegen','papenburg','emsland','wewelsburg','fallingbostel'}

# ---------- 1. EAD -> invnr -> classificatie (uit build_stromen) ----------
tree = ET.parse(EAD); root = tree.getroot()
def node_fields(c):
    invnr = title = None
    for ch in c:
        if s(ch.tag) == 'head' and title is None: title = ''.join(ch.itertext()).strip()
        if s(ch.tag) == 'did':
            for d in ch:
                if s(d.tag) == 'unitid':
                    v = (d.text or '').strip()
                    if d.get('type') is None and v.isdigit(): invnr = v
                if s(d.tag) == 'unittitle': title = ''.join(d.itertext()).strip()
    return invnr, title
leaves = {}
def walk(c, anc):
    invnr, title = node_fields(c); label = title or '·'
    if invnr and invnr.isdigit(): leaves[invnr] = {"title": title or "", "ancestors": anc[:]}
    for ch in c:
        if s(ch.tag) == 'c': walk(ch, anc + [label])
for el in root.iter():
    if s(el.tag) == 'dsc':
        for ch in el:
            if s(ch.tag) == 'c': walk(ch, [])
        break
def classify(rec):
    title, anc = rec["title"], rec["ancestors"]
    blob = " > ".join(anc + [title]).lower()
    if re.search(r'ziekenh|krankenhaus|klinik|patient|patiënt|lazarett|heilanstalt|rontgen|röntgen|medisch', blob): cat="medisch"
    elif re.search(r'overled|overlijden|gestorben|verstorben|sterbe|doden|begraf|begraben|friedhof|grave', blob): cat="overlijden"
    elif re.search(r'huwelijk|heirat|trauung|eheschlie', blob): cat="huwelijk"
    elif re.search(r'geboort|geburt', blob): cat="geboorte"
    else: cat="arbeidsinzet"
    mz = re.search(r'(amerikaanse|engelse|britse|russische|sovjet|franse)\s+zone', blob)
    zone = {"amerikaanse":"Amerikaanse","engelse":"Engelse","britse":"Engelse","russische":"Russische",
            "sovjet":"Russische","franse":"Franse"}.get(mz.group(1)) if mz else None
    def pick_kreis(text):
        for m in re.finditer(r'kreis\s+([a-zà-ÿ][a-zà-ÿ.\-/ ]*?)(?=,|;|$|\sgemeente|\sstadt|\s>)', text):
            cand = m.group(1).strip()
            if cand and not re.search(r'zone|werkzaam|woonachtig|nederland|verpleegd|overleden|geboren|gehuwd', cand):
                return cand
        return None
    kreis = pick_kreis(title.lower()) or pick_kreis(blob)
    mg = re.search(r'gemeente\s+([a-zà-ÿ][a-zà-ÿ.\-/ ]*?)(?=,|;|$|\s>)', blob)
    gemeente = mg.group(1).strip() if mg else None
    stad = None
    for a in anc:
        al = a.lower()
        if a and a != '·' and 2 < len(a) < 26 and not re.search(
                r'nederland|patiënt|patient|status|lijst|kaart|zone|bestand|arbeider|overled|zijn |diverse|kreis', al):
            stad = a.strip(); break
    dest = (kreis or gemeente or stad or "onbekend").title()
    kreis = kreis.title() if kreis else None
    kamp = any(c in (dest + " " + blob).lower() for c in CAMP_KREISE)
    return dict(categorie=cat, zone=zone, kreis=kreis, bestemming=dest, kamp_nabij=kamp)
INV = {k: classify(v) for k, v in leaves.items()}

cache = json.load(open(GEOCACHE, encoding='utf-8'))

# ---------- 2. CSV streamen -> aggregatie + personen ----------
rx = re.compile(r'/invnr/(\d+)/')
dest_stat = collections.defaultdict(lambda: {"records":0,"cat":collections.Counter(),
    "kreis":None,"zone":None,"kamp":False,"nl":collections.Counter(),"nl_generiek":0,"g":collections.Counter()})
origin = {}                          # NL-plaats -> {records,lat,lon,dests:Counter}
persons = {}                         # reconstructieid -> dict
cat_tot = collections.Counter(); jaren = collections.Counter(); jaren_jaar = collections.Counter(); gender_tot = collections.Counter()
n = 0
for path in CSVS:
    with open(path, encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            n += 1
            m = rx.search(row['scanid'] or '')
            info = INV.get(m.group(1)) if m else None
            if not info or info["bestemming"] == "Onbekend": continue
            dest = info["bestemming"]; ds = dest_stat[dest]
            ds["records"] += 1; ds["cat"][info["categorie"]] += 1
            ds["kreis"] = ds["kreis"] or info["kreis"]; ds["zone"] = ds["zone"] or info["zone"]
            ds["kamp"] = ds["kamp"] or info["kamp_nabij"]
            grow = (row['gender_interpretatievrijwilliger'] or '').strip().lower()
            if grow.startswith('man'): ds["g"]['m'] += 1; gender_tot['m'] += 1
            elif grow.startswith('vrouw'): ds["g"]['v'] += 1; gender_tot['v'] += 1
            cat_tot[info["categorie"]] += 1
            y = (row['byear_st'] or '').strip()[:4]
            if y.isdigit() and 1850 <= int(y) <= 1945: jaren[int(y)//10*10] += 1; jaren_jaar[int(y)] += 1
            # herkomst
            bpl = (row['bplace'] or '').strip(); uri = row['bplace_uri'] or ''
            is_nl = 'gemeentegeschiedenis' in uri
            if is_nl and bpl:
                ds["nl"][bpl] += 1
                o = origin.setdefault(bpl, {"records":0,"lat":None,"lon":None,"dests":collections.Counter(),"g":collections.Counter()})
                o["records"] += 1; o["dests"][dest] += 1
                if grow.startswith('man'): o["g"]['m'] += 1
                elif grow.startswith('vrouw'): o["g"]['v'] += 1
                ll = (row['bplace_latlon'] or '').strip()
                if ll and o["lat"] is None:
                    try: la,lo = ll.split(","); o["lat"]=round(float(la),5); o["lon"]=round(float(lo),5)
                    except ValueError: pass
            else:
                ds["nl_generiek"] += 1        # 'Nederland' zonder plaats / leeg / buitenland
            # persoon (reconstructieid)
            rid = (row['reconstructieid'] or '').strip()
            if not rid: continue
            p = persons.get(rid)
            if p is None:
                p = persons[rid] = {"n":"","bd":"","p":"","g":"","dd":"","dp":"","dests":{},"cats":set()}
            if info["categorie"] != "arbeidsinzet": p["cats"].add(info["categorie"])
            if not p["n"]:
                fn=(row['fname'] or '').strip(); pf=(row['prefix'] or '').strip(); sn=(row['sname'] or '').strip()
                nm=" ".join(x for x in (fn,pf,sn) if x and x not in ('-','–','?'))
                nm=re.sub(r'\([^)]*\)', ' ', nm)                 # (alias)/(titel) weg
                nm=re.sub(r'^[\s:;.,*+\-\'"/]+', '', nm)          # leidende leestekens (:Leo, 'Wilhelmus, +Dirk)
                nm=re.sub(r'^\d[\d\-/.]*\s+', '', nm)             # leidende datum/nummer (27-10-44 Jacobus)
                nm=re.sub(r'\s+', ' ', nm).strip()
                if nm and '?' not in nm: p["n"]=nm
            if not p["bd"]:
                bd=(row['bdate_st'] or '').strip() or (y if y.isdigit() else '')   # volledige datum, anders jaar
                if bd: p["bd"]=bd
            if not p["g"]:
                g=(row['gender_interpretatievrijwilliger'] or '').strip().lower()
                if g.startswith('man'): p["g"]='m'
                elif g.startswith('vrouw'): p["g"]='v'
            if not p["p"] and is_nl and bpl: p["p"]=bpl
            if info["categorie"]=="overlijden" or (row['ddate_st'] or '').strip() or (row['dyear_st'] or '').strip():
                dd=(row['ddate_st'] or '').strip() or (row['dyear_st'] or '').strip()[:4]
                if dd and not p["dd"]: p["dd"]=dd
                dp=(row['dplace'] or '').strip()
                if dp and not p["dp"]: p["dp"]=dp
            rid = row['id'].strip()
            if rid: p["dests"].setdefault(dest, []).append(rid)   # álle record-ids per Kreis
print(f"records: {n:,} | bestemmingen: {len(dest_stat):,} | herkomst-NL: {len(origin):,} | personen: {len(persons):,}")

# ---------- 3. Kreisen samenstellen ----------
NIET_PLAATS = re.compile(r'dossier|personeel|stukken|kaartsysteem|namenlijst|onbekend', re.I)
kreisen = []
for d, st in dest_stat.items():
    if NIET_PLAATS.search(d): continue
    coord = cache.get(d)
    top_nl = st["nl"].most_common(60)     # top-NL-plaatsen (rest valt in 'Nederland'-bak)
    rest_nl = sum(st["nl"].values()) - sum(c for _,c in top_nl)
    kreisen.append({"naam":d,"kreis":st["kreis"],"zone":st["zone"],"kamp_nabij":st["kamp"],
        "records":st["records"],"lat":coord[0] if coord else None,"lon":coord[1] if coord else None,
        "cats":dict(st["cat"]),
        "g":{"m":st["g"].get('m',0),"v":st["g"].get('v',0)},
        "nl":[[p,c] for p,c in top_nl],
        "nl_overig": rest_nl + st["nl_generiek"]})     # 'Nederland (zonder plaats)'-bak, onderaan
kreisen.sort(key=lambda x:-x["records"])
kidx = {k["naam"]:i for i,k in enumerate(kreisen)}     # naam -> index (voor personen)

# ---------- 4. Herkomst (NL-plaatsen) met top-bestemmingen ----------
# Handmatige correctie: NA-bron plaatst enkele IJssel-steden ~0,3° te ver west (in de latere
# Flevoland-polder / het IJsselmeer). Juiste moderne coördinaten:
HERK_FIX = {"Kampen": (52.5551, 5.9114), "Hasselt": (52.5931, 6.0981), "Wilsum": (52.5169, 6.0878),
            "Genemuiden": (52.6289, 6.0492), "Grafhorst": (52.5719, 5.9846), "IJsselmuiden": (52.5636, 5.9207)}
herkomst = []
for naam,o in origin.items():
    if naam in HERK_FIX: o["lat"], o["lon"] = HERK_FIX[naam]
    if o["lat"] is None or o["records"] < 3: continue
    top = [[dst, c] for dst,c in o["dests"].most_common(12) if dst in kidx]
    herkomst.append({"naam":naam,"lat":o["lat"],"lon":o["lon"],"records":o["records"],"dests":top,
                     "g":{"m":o["g"].get('m',0),"v":o["g"].get('v',0)}})
herkomst.sort(key=lambda x:-x["records"])

# ---------- 5. Personen-index (alleen met naam + minstens 1 gegeocodeerde Kreis) ----------
pout = []
for rid,p in persons.items():
    if not p["n"]: continue
    ks=[]; rs=[]
    for dst,recids in p["dests"].items():
        i = kidx.get(dst)
        if i is not None and kreisen[i]["lat"] is not None: ks.append(i); rs.append(recids)  # recids = lijst
    if not ks: continue
    e = {"id":rid,"n":p["n"],"k":ks,"r":rs}   # reconstructieid = stabiele deeplink-sleutel
    if p["bd"]: e["bd"]=p["bd"]
    if p["p"]: e["p"]=p["p"]
    if p["g"]: e["g"]=p["g"]
    if p["dd"]: e["dd"]=p["dd"]
    if p["dp"]: e["dp"]=p["dp"]
    if p["cats"]: e["c"]=sorted(p["cats"])
    pout.append(e)

# ---------- overlijden: sterfjaar + leeftijd (per persoon, ingetogen) ----------
sterfjaar = collections.Counter(); leeftijd = collections.Counter()
for p in persons.values():
    dd = p.get('dd', ''); bd = p.get('bd', '')
    if len(dd) >= 4 and dd[:4].isdigit():
        dy = int(dd[:4])
        if 1938 <= dy <= 1948: sterfjaar[dy] += 1
        if len(bd) >= 4 and bd[:4].isdigit():
            age = dy - int(bd[:4])
            if 10 <= age <= 90: leeftijd[age] += 1

# ---------- Bijzondere vondsten (voor het inzichten-dashboard) ----------
def kname(i): return kreisen[i]["naam"]
meeste = max(pout, key=lambda e:len(e["k"]))
huwelijk = next((e for e in pout if "huwelijk" in e.get("c",[]) and e.get("bd")), None)
geboorte = next((e for e in pout if "geboorte" in e.get("c",[]) and e.get("p")), None)
overleden = next((e for e in sorted(pout,key=lambda e:-len(e["k"])) if e.get("dd") and e.get("dp")), None)
def vd(e, kop, tekst):
    return {"kop":kop,"naam":e["n"],"jaar":e.get("bd","")[:4],"plaats":e.get("p",""),
            "kreisen":[kname(i) for i in e["k"]][:8],"tekst":tekst,
            "record":(e["r"][0][0] if e.get("r") and e["r"][0] else "")}
vondsten = []
if meeste: vondsten.append(vd(meeste,"Meeste Kreisen",f"komt voor in {len(meeste['k'])} verschillende Kreisen"))
if huwelijk: vondsten.append(vd(huwelijk,"Huwelijk","in de administratie staat ook een huwelijk geregistreerd"))
if geboorte: vondsten.append(vd(geboorte,"Geboorte","van deze persoon is een geboorte in Duitsland vastgelegd"))
if overleden: vondsten.append(vd(overleden,"Overlijden",f"overleden in {overleden.get('dp','')}"))

pout.sort(key=lambda e:e["n"])

json.dump({"kreisen":kreisen,"herkomst":herkomst,"vondsten":vondsten,
    "geboortejaren":dict(sorted(jaren.items())),
    "geboortejaren_jaar":dict(sorted(jaren_jaar.items())),
    "sterfjaar":dict(sorted(sterfjaar.items())),
    "overlijdensleeftijd":dict(sorted(leeftijd.items())),
    "per_categorie":dict(cat_tot),
    "gender":dict(gender_tot),
    "meta":{"records_totaal":n,"personen":len(pout),"unieke_herkomst":len(herkomst),
            "bron":"Nationaal Archief 2.19.323 (CC-0)"}},
    open(f"{SITE}/kaart_data.json","w",encoding='utf-8'), ensure_ascii=False, separators=(",",":"))
json.dump(pout, open(f"{SITE}/personen.json","w",encoding='utf-8'), ensure_ascii=False, separators=(",",":"))

# platte CSV-export (Kreis-niveau) voor hergebruik
import csv
CATS_ORD = ["arbeidsinzet","overlijden","medisch","huwelijk","geboorte"]
with open(f"{SITE}/arbeidsinzet_kreisen.csv","w",encoding="utf-8",newline="") as f:
    w = csv.writer(f)
    w.writerow(["kreis","zone","personen"]+CATS_ORD+["lat","lon","top_herkomst_nl"])
    for k in kreisen:
        top = "; ".join(f"{p} ({c})" for p,c in k["nl"][:3])
        w.writerow([k["naam"], k["zone"] or "", k["records"]]+[k["cats"].get(c,0) for c in CATS_ORD]+
                   [k["lat"] if k["lat"] is not None else "", k["lon"] if k["lon"] is not None else "", top])
import os
print(f"kreisen: {len(kreisen)} (geocoded {sum(1 for k in kreisen if k['lat'])}) | herkomst: {len(herkomst)} | personen: {len(pout):,}")
print(f"kaart_data.json: {os.path.getsize(SITE+'/kaart_data.json')//1024} KB | personen.json: {os.path.getsize(SITE+'/personen.json')//1024} KB")
