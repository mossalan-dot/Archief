#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bouw de Rode Kruis-kampdossiers voor de OGS-kaart (pagina /archief/).

Bronnen (Nationaal Archief, Het Nederlandse Rode Kruis):
  2.19.321  Kampen en Gevangenissen  — per kamp geordend; thema uit de dossiertitel
  2.19.296  Kamp Westerbork          — per serie geordend; thema = serienaam
  2.19.315  Kamp Amersfoort          — per serie geordend; thema = serienaam
  2.19.283  Japanse burgerinterneringskampen Bandoeng/Tjimahi — alfabetisch kaartsysteem

Openbaarheid: openbaar = geen <accessrestrict>; beperkt = wel. Het A/B-regime staat per
toegang in de inleiding (archdesc). Hier vastgelegd per kamp (2.19.321/296/315 = B, 2.19.283 = A).

Schrijft site/nrk_kampen.json (per kamp: toegang, regime, thema's met dossiers) en
site/nrk_match.json (genormaliseerde plaatsnaam -> slug, voor de kaart-doorklik).
"""
import xml.etree.ElementTree as ET, re, json, os, unicodedata, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(HERE + "/../site")

def ead(a):
    f = f"{HERE}/ead_{a}.xml"
    if not os.path.exists(f):
        print(f"EAD {a} ophalen…")
        req = urllib.request.Request(f"https://www.nationaalarchief.nl/onderzoeken/archief/{a}/download/xml",
                                     headers={"User-Agent": "Mozilla/5.0"})
        open(f, "wb").write(urllib.request.urlopen(req).read())
    r = ET.parse(f).getroot()
    for el in r.iter(): el.tag = el.tag.split("}")[-1]
    return r

def txt(e): return re.sub(r"\s+", " ", "".join(e.itertext())).strip() if e is not None else ""
def strip(s): return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
def slug(s):
    s = re.sub(r"\(.*?\)", "", strip(s).lower()); return re.sub(r"[^a-z0-9]+", "-", s).strip("-")
def mkey(s):
    s = re.sub(r"[^a-z0-9 ]", "", strip(s).lower()); return re.sub(r"\s+", " ", s).strip()
def leaves(node): return [c for c in node.iter() if c.tag == "c" and not c.findall("./c")]
def is_file(c): return not c.findall("./c")
def item(lf, prefix=""):
    ti = txt(lf.find("./did/unittitle")) or ""
    if prefix:                                   # vervolgstuk: hoofdbeschrijving uit de ouder ervoor
        ti = f"{prefix} — {ti}" if ti else prefix
    inv = next((txt(u) for u in lf.findall("./did/unitid") if re.match(r"^\d+$", txt(u))), "")
    return {"t": ti or "(geen beschrijving)", "inv": inv, "b": 1 if lf.find("./accessrestrict") is not None else 0}

from collections import OrderedDict
def extract_sections(root, classify_direct=True):
    """Volg de archiefhiërarchie: directe subseries/subkampen worden secties;
    losse bestanden worden thematisch geclassificeerd; diepere vervolgstukken
    krijgen de titel van hun tussenliggende ouder als hoofdbeschrijving."""
    secs = OrderedDict()
    def push(title, it): secs.setdefault(title, []).append(it)
    for child in root.findall("./c"):
        if is_file(child):
            it = item(child)
            push(theme(it["t"]) if classify_direct else "Overige stukken", it)
        else:
            sect = clean_serie(txt(child.find("./did/unittitle"))) or "Overig"
            for sub in child.findall("./c"):
                if is_file(sub):
                    push(sect, item(sub))
                else:
                    head = txt(sub.find("./did/unittitle"))
                    for lf in leaves(sub):
                        push(sect, item(lf, prefix=head))
    return secs

# thema-classificatie op dossiertitel (2.19.321; volgorde = prioriteit)
THEMES = [
 ("Graven & identificatie", r"\bgraf\b|graven|begra|exhumat|urn|cremat|identificat"),
 ("Evacuaties & dodenmarsen", r"evacua|dodenmars|ontruiming|mars naar"),
 ("Overledenen & overlijden", r"overled|overlijd|dodenboek|doodsoorz|gesneuv|gestorven|sterf|\bdood|todesmeld|todesfall|sterbe"),
 ("Transport & deportatie", r"transport|deportat|gedeporteerd|getransporteerd|weggevoerd|afgevoerd|overgebracht"),
 ("Bevrijding & repatriëring", r"repatri|bevrijd|terugkeer|teruggekeerd|terugvoer"),
 ("Vermisten & opsporing", r"vermist|opsporing|opgespoord"),
 ("Ooggetuigen & verklaringen", r"verklaring|verslag|rapport|dagboek|getuige|ervaring|belevenis|relaas|memoires|ooggetuige"),
 ("Registratie & matricule", r"matricule|matrikel|nummerboek|kartothe|cartothe|stamboek|register|^nummer|kommandobuch|kommandantur|standortbefehl"),
 ("Kaarten & situatieschetsen", r"situatieschets|plattegrond|kaart van|kaarten en|schets"),
 ("Internering", r"internering|geïnterneerd|geinterneerd|gevangenschap|detentie"),
 ("Administratie & lijsten", r"lijst|naamlijst|namenlijst|administrat|correspondent|overzicht|opgave|inventaris|brief|stukken|namen|melding|bericht|mededeling|afschrift|extract|kopie"),
]
ORDER = [t[0] for t in THEMES] + ["Overig"]
def theme(t):
    tl = t.lower()
    for name, pat in THEMES:
        if re.search(pat, tl): return name
    return "Overig"
def clean_serie(s):
    return re.sub(r",?\s*\(?\d{4}\s*[-–]\s*\d{2,4}\)?\.?$", "", s).strip()  # jaartallen achteraan eraf

kampen, match, used = [], {}, set()
def add_match(naam, sl):
    if "kommando" in naam.lower() or "commando" in naam.lower(): return
    match[mkey(re.sub(r"\(.*?\)", "", naam))] = sl
    par = re.search(r"\((.*?)\)", naam)
    if par: match[mkey(par.group(1))] = sl

def register(naam, cat, arch, regime, secs, extra_keys=()):
    sl = slug(naam)
    while sl in used: sl += "-x"
    used.add(sl)
    themes = [{"thema": th, "items": its} for th, its in secs.items() if its]
    n = sum(len(t["items"]) for t in themes)
    op = sum(1 for t in themes for i in t["items"] if not i["b"])
    kampen.append({"slug": sl, "naam": naam, "cat": cat, "arch": arch, "regime": regime,
                   "n": n, "open": op, "beperkt": n - op, "themes": themes})
    add_match(naam, sl)
    for k in extra_keys: match[mkey(k)] = sl
    return sl

# ---- 2.19.321: per kamp; secties uit de archiefhiërarchie (subseries / subkampen) ----
r321 = ead("2.19.321")
CAT = {"Concentratiekampen op alfabetische ordening": "concentratiekamp",
       "Internerings-, straf-, en dwangarbeidskampen": "interneringskamp",
       "Werkkampen": "werkkamp", "Gevangenissen": "gevangenis"}
wb321 = None
for c01 in r321.find(".//archdesc/dsc").findall("./c"):
    cat = txt(c01.find("./did/unittitle"))
    if cat not in CAT: continue
    for c02 in c01.findall("./c"):
        naam = txt(c02.find("./did/unittitle"))
        secs = extract_sections(c02)
        if naam == "Westerbork":            # bewaar; ga samen met de diepe 2.19.296
            wb321 = secs; continue
        register(naam, CAT[cat], "2.19.321", "B", secs)

# ---- 2.19.296 Westerbork + 2.19.315 Amersfoort: secties = eigen serie-indeling ----
def whole_archive(a, naam, cat, regime, merge=None):
    secs = extract_sections(ead(a).find(".//archdesc/dsc"), classify_direct=False)
    if merge:
        secs["Overige stukken (toegang 2.19.321)"] = [{**i, "a": "2.19.321"}
                                                      for v in merge.values() for i in v]
    register(naam, cat, a, regime, secs)

whole_archive("2.19.296", "Westerbork", "concentratiekamp", "B", merge=wb321)
whole_archive("2.19.315", "Amersfoort", "concentratiekamp", "B")

# ---- 2.19.283 Bandoeng/Tjimahi: alfabetisch kaartsysteem (Japans interneringskamp, regime A) ----
b283 = OrderedDict()
b283["Kaartsysteem geïnterneerden (alfabetisch)"] = [item(lf)
    for lf in leaves(ead("2.19.283").find(".//archdesc/dsc"))]
register("Bandoeng / Tjimahi (Japanse interneringskampen)", "interneringskamp", "2.19.283", "A", b283,
         extra_keys=("bandoeng", "tjimahi", "bandung", "tjimahi bandoeng"))

data = {"meta": {"zoekhulp": "https://www.nationaalarchief.nl/onderzoeken/zoekhulpen/inzage-in-beperkt-openbaar-archief",
                 "invnr_base": "https://www.nationaalarchief.nl/onderzoeken/archief/"},
        "kampen": kampen, "match": match}
json.dump(data, open(SITE + "/nrk_kampen.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(match, open(SITE + "/nrk_match.json", "w"), ensure_ascii=False, separators=(",", ":"))
tot = sum(k["n"] for k in kampen)
print(f"kampen: {len(kampen)} | dossiers: {tot} | openbaar {sum(k['open'] for k in kampen)} | "
      f"beperkt {sum(k['beperkt'] for k in kampen)} | match-keys: {len(match)}")
for k in kampen:
    if k["arch"] != "2.19.321": print(f"   + {k['naam']} ({k['arch']}, regime {k['regime']}): {k['n']} stukken, {len(k['themes'])} thema's")
