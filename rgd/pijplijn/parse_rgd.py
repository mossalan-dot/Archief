#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse het RGD-tekeningenarchief (EAD 4.RGD) tot bouwproject-records.
Argument: één plaats-kop (bv. Amsterdam) OF 'ALL' voor alle plaats-georganiseerde secties
(IB+IIB objectenarchief = tekeningen, IC = foto's, ID = bestekken, III = overig)."""
import re, json, sys
import xml.etree.ElementTree as ET

SRC = "/Users/alan/Downloads/4.RGD.xml"
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
ALL = PLACE.upper() == "ALL"
# (series_code, materiaaltype) van de plaats-georganiseerde secties
SECTIONS = [("IB", "tekening"), ("IIB", "tekening"), ("IC", "foto"), ("ID", "bestek"), ("III", "tekening")]

raw = open(SRC, encoding="utf-8").read()
body = raw[raw.find("<dsc"):]

def balanced(startpat):
    m = re.search(startpat, body)
    if not m: return None
    start = body.rfind("<c ", 0, m.start()); depth = 0; i = start
    while i < len(body):
        if body.startswith("</c>", i): depth -= 1; i += 4
        elif body.startswith("<c ", i) or body.startswith("<c>", i): depth += 1; i += 3
        else: i += 1
        if depth == 0: break
    return body[start:i]

def txt(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""

from rgd_categories import categorie, soort_tekening

def split_title(t):
    loc, rest = None, t
    if ":" in t:
        loc, rest = t.split(":", 1); loc = loc.strip(); rest = rest.strip()
    if " - " in rest:
        rest = rest.rsplit(" - ", 1)[0].strip()
    return loc, rest

def first_uid(did):
    for u in did.findall("unitid"):
        if u.get("type") not in ("handle", "series_code") and u.get("audience") != "internal":
            return txt(u)
    return ""

def parse_project(c, stad, mat, sectie):
    did = c.find("did")
    if did is None: return None
    title = txt(did.find("unittitle"))
    if not title or title.lower().startswith("tekening"): return None
    pdate = did.find("unitdate")
    years = [int(y) for y in re.findall(r"\d{4}", pdate.get("normal") or "")] if pdate is not None and pdate.get("normal") else []
    sheets, scales, micro = [], set(), 0
    for it in c.iter("c"):
        d = it.find("did")
        if d is None or d.find("dao") is None: continue
        ud = d.find("unitdate"); yr = None
        if ud is not None and ud.get("normal"):
            mm = re.search(r"\d{4}", ud.get("normal")); yr = int(mm.group()) if mm else None
        if yr: years.append(yr)
        sc = d.find("materialspec")
        if sc is not None and txt(sc): scales.add(txt(sc).replace("Schaal", "").strip())
        ch = it.find("custodhist"); is_micro = ch is not None and "microfiche" in txt(ch).lower()
        if is_micro: micro += 1
        gid = re.search(r"([0-9a-f-]{36})", d.find("dao").get("href", ""))
        handle = next((txt(u) for u in d.findall("unitid") if u.get("type") == "handle"), "")
        sheets.append({"id": first_uid(d), "title": txt(d.find("unittitle")), "year": yr,
                       "scale": txt(sc) if sc is not None else "", "micro": is_micro,
                       "mets": gid.group(1) if gid else "", "handle": handle})
    if not sheets: return None
    loc, gebouw = split_title(title); cat, em = categorie(title)
    return {"uid": first_uid(did), "stad": stad, "titel": title, "locatie": loc, "gebouw": gebouw,
            "cat": cat, "emoji": em, "soort": soort_tekening(title), "mat": mat, "sectie": sectie,
            "jaar_min": min(years) if years else None, "jaar_max": max(years) if years else None,
            "n_bladen": len(sheets), "n_micro": micro, "schalen": sorted(scales)[:6], "sheets": sheets}

def parse_section(code, mat):
    sub = balanced(r'<unitid type="series_code">' + re.escape(code) + r"</unitid>")
    if sub is None: return []
    root = ET.fromstring(sub)
    out = []
    for pc in root.findall("./c"):          # plaats-subseries
        d = pc.find("did"); stad = txt(d.find("unittitle")) if d is not None else ""
        if not stad or "zie" in stad.lower() or pc.find("./c") is None: continue
        for c in pc.findall("./c"):
            p = parse_project(c, stad, mat, code)
            if p: out.append(p)
    return out

if ALL:
    projects = []
    for code, mat in SECTIONS:
        n0 = len(projects); projects += parse_section(code, mat)
        print(f"  {code} ({mat}): +{len(projects)-n0} projecten")
else:
    sub = balanced(r"<unittitle>" + re.escape(PLACE) + r"</unittitle>")
    root = ET.fromstring(sub); projects = []
    for c in root.findall("./c"):
        p = parse_project(c, PLACE, "tekening", "IB")
        if p: projects.append(p)

out = f"rgd_{'all' if ALL else PLACE.lower().replace(' ', '_')}.json"
json.dump(projects, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(f"{'ALLES' if ALL else PLACE}: {len(projects)} bouwprojecten, {sum(p['n_bladen'] for p in projects)} bladen -> {out}")
print("materiaal:", dict(Counter(p['mat'] for p in projects)))
print("met straat-locatie:", sum(1 for p in projects if p['locatie']))
