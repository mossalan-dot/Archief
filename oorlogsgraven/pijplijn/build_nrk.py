#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bouw de Rode Kruis-kampdossiers voor de OGS-kaart (pagina /archief/).

Bron: Nationaal Archief 2.19.321 — Het Nederlandse Rode Kruis, Kampen en Gevangenissen.
Leest de EAD-inventaris (wordt gedownload als hij ontbreekt), ordent per kamp/gevangenis,
classificeert elk dossier naar thema (overledenen, transport, repatriëring, ooggetuigen…)
en bepaalt de openbaarheid per stuk (openbaar = geen beperking; beperkt = <accessrestrict>).

Schrijft:
  site/nrk_kampen.json  — per kamp: thema's met dossiers (titel, inv.nr, openbaarheid)
  site/nrk_match.json   — genormaliseerde plaatsnaam -> slug, voor de kaart-doorklik
"""
import xml.etree.ElementTree as ET, re, json, os, unicodedata, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(HERE + "/../site")
EAD = HERE + "/ead_2.19.321.xml"
URL = "https://www.nationaalarchief.nl/onderzoeken/archief/2.19.321/download/xml"

if not os.path.exists(EAD):
    print("EAD ophalen…")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    open(EAD, "wb").write(urllib.request.urlopen(req).read())

def txt(e): return re.sub(r"\s+", " ", "".join(e.itertext())).strip() if e is not None else ""
def local(t): return t.split("}")[-1]
def strip(s): return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
def slug(s):
    s = re.sub(r"\(.*?\)", "", strip(s).lower()); return re.sub(r"[^a-z0-9]+", "-", s).strip("-")
def mkey(s):
    s = re.sub(r"[^a-z0-9 ]", "", strip(s).lower()); return re.sub(r"\s+", " ", s).strip()

# thema-classificatie op dossiertitel (volgorde = prioriteit; 2.19.321-categorieën)
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

CAT = {"Concentratiekampen op alfabetische ordening": "concentratiekamp",
       "Internerings-, straf-, en dwangarbeidskampen": "interneringskamp",
       "Werkkampen": "werkkamp", "Gevangenissen": "gevangenis"}

r = ET.parse(EAD).getroot()
for el in r.iter(): el.tag = local(el.tag)
dsc = r.find(".//archdesc/dsc")
kampen, match, used = [], {}, set()
for c01 in dsc.findall("./c"):
    cat = txt(c01.find("./did/unittitle"))
    if cat not in CAT: continue
    for c02 in c01.findall("./c"):
        naam = txt(c02.find("./did/unittitle"))
        leaves = [c for c in c02.iter() if local(c.tag) == "c" and not c.findall("./c")]
        bt = defaultdict(list); no = nb = 0
        for lf in leaves:
            ti = txt(lf.find("./did/unittitle")) or "(geen beschrijving)"
            inv = next((txt(u) for u in lf.findall("./did/unitid") if re.match(r"^\d+$", txt(u))), "")
            b = 1 if lf.find("./accessrestrict") is not None else 0
            bt[theme(ti)].append({"t": ti[:160], "inv": inv, "b": b})
            nb += b; no += 1 - b
        sl = slug(naam)
        while sl in used: sl += "-x"
        used.add(sl)
        kampen.append({"slug": sl, "naam": naam, "cat": CAT[cat], "n": len(leaves),
                       "open": no, "beperkt": nb,
                       "themes": [{"thema": th, "items": bt[th]} for th in ORDER if th in bt]})
        if "kommando" not in naam.lower() and "commando" not in naam.lower():
            match[mkey(re.sub(r"\(.*?\)", "", naam))] = sl
            par = re.search(r"\((.*?)\)", naam)
            if par: match[mkey(par.group(1))] = sl

data = {"meta": {"bron": "Nationaal Archief 2.19.321 — Nederlandse Rode Kruis, Kampen en Gevangenissen",
                 "regime": "Deels openbaar, deels beperkt openbaar (A+B)",
                 "zoekhulp": "https://www.nationaalarchief.nl/onderzoeken/zoekhulpen/inzage-in-beperkt-openbaar-archief",
                 "invnr_url": "https://www.nationaalarchief.nl/onderzoeken/archief/2.19.321/invnr/"},
        "kampen": kampen, "match": match}
json.dump(data, open(SITE + "/nrk_kampen.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(match, open(SITE + "/nrk_match.json", "w"), ensure_ascii=False, separators=(",", ":"))
tot = sum(k["n"] for k in kampen)
print(f"kampen: {len(kampen)} | dossiers: {tot} | openbaar {sum(k['open'] for k in kampen)} | "
      f"beperkt {sum(k['beperkt'] for k in kampen)} | match-keys: {len(match)}")
