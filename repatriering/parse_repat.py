#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse de EAD-inventaris 2.19.277 (NRK-repatriëringsschepen Indië→Nederland, 1945-1959)
naar reisrecords: schip, vertrek/aankomst/via-plaats + -datum, aantal personen, invnr, METS-scan.
Schrijft repat_reizen.json."""
import re, json, os
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
EAD = f"{BASE}/2.19.277.xml"

def strip(t): return re.sub(r'\{.*?\}', '', t)
def txt(el): return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip() if el is not None else ''

KEYS = ['Maltanummer', 'Herkomst', 'Datum lijst', 'Naam boot/vliegtuig', 'Vertrekplaats',
        'Vertrekdatum', 'Via plaats', 'Via datum', 'Aankomstplaats', 'Aankomstdatum', 'Aantal personen']
KEYPAT = '|'.join(re.escape(k) for k in KEYS)

def parse_fields(title):
    out = {}
    for m in re.finditer(r'(' + KEYPAT + r'):\s*(.*?)(?=\s+-\s+(?:' + KEYPAT + r'):|$)', title):
        out[m.group(1)] = m.group(2).strip(' .-–')
    return out

MND = {'januari':1,'februari':2,'maart':3,'april':4,'mei':5,'juni':6,'juli':7,'augustus':8,
       'september':9,'oktober':10,'november':11,'december':12}
def iso_date(s):
    if not s: return None
    s = s.strip()
    m = re.match(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', s)          # 1-2-1946
    if m: return f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r'(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})', s)           # 5 april 1946
    if m and m.group(2).lower() in MND: return f"{int(m.group(3)):04d}-{MND[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    m = re.search(r'(19[3-6]\d)', s)                                # alleen jaar
    if m: return f"{m.group(1)}-00-00"
    return None
def year_of(*dates):
    for d in dates:
        if d and d[:4].isdigit(): return int(d[:4])
    return None

root = ET.parse(EAD).getroot()
reizen = []
for c in root.iter():
    if strip(c.tag) != 'c': continue
    did = next((ch for ch in c if strip(ch.tag) == 'did'), None)
    if did is None: continue
    title = txt(next((d for d in did if strip(d.tag) == 'unittitle'), None))
    if 'Naam boot' not in title: continue
    invnr = mets = handle = None
    for u in did:
        if strip(u.tag) == 'unitid':
            if u.get('type') == 'handle': handle = txt(u)
            elif u.get('audience') != 'internal': invnr = txt(u)
        if strip(u.tag) == 'dao':
            m = re.search(r'/mets/v1/([0-9a-f-]{36})', u.get('href', ''))
            if m: mets = m.group(1)
    f = parse_fields(title)
    vd, ad = iso_date(f.get('Vertrekdatum')), iso_date(f.get('Aankomstdatum'))
    dl = iso_date(f.get('Datum lijst'))
    aantal = None
    if f.get('Aantal personen'):
        mm = re.search(r'\d[\d.]*', f['Aantal personen'].replace('.', ''))
        if mm: aantal = int(mm.group())
    reizen.append({
        "invnr": invnr, "mets": mets, "handle": handle,
        "schip": f.get('Naam boot/vliegtuig'),
        "van": f.get('Vertrekplaats'), "van_datum": vd,
        "via": f.get('Via plaats'), "via_datum": iso_date(f.get('Via datum')),
        "naar": f.get('Aankomstplaats'), "naar_datum": ad,
        "aantal": aantal, "herkomst_lijst": f.get('Herkomst'), "malta": f.get('Maltanummer'),
        "jaar": year_of(vd, ad, dl)})

json.dump(reizen, open(f"{BASE}/repat_reizen.json", "w", encoding='utf-8'), ensure_ascii=False, indent=1)
import collections
print(f"reizen: {len(reizen)}")
print(f"  met schip: {sum(1 for r in reizen if r['schip'])} | met vertrek: {sum(1 for r in reizen if r['van'])} | met aankomst: {sum(1 for r in reizen if r['naar'])}")
print(f"  met aantal: {sum(1 for r in reizen if r['aantal'])} | met jaar: {sum(1 for r in reizen if r['jaar'])} | met scan: {sum(1 for r in reizen if r['mets'])}")
print(f"  jaren: {dict(sorted(collections.Counter(r['jaar'] for r in reizen if r['jaar']).items()))}")
print(f"  totaal personen (waar bekend): {sum(r['aantal'] for r in reizen if r['aantal']):,}")
