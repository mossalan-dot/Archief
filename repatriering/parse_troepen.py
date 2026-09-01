#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse de EAD-inventaris 2.13.103 (Collectie Troepenverschepingen van en naar
Nederlands-Indië, 1945-1952) naar reisrecords in hetzelfde schema als parse_repat.py.

Structuur: per schip een component ("ms Amarapoora, 1950") met per reis een
subcomponent als datumbereik ("1950 mei 15 - juni 29"). De havens staan meestal
niet per reis vermeld; het zijn pendeldiensten Indië<->Nederland, dus de richting
is per reis vaak onbekend. We tonen ze daarom richting-neutraal (richting "troepen")
op het corridor Tandjong Priok–Rotterdam, tenzij de titel expliciete havens noemt.

Schrijft troepen_reizen.json. Geocoding gebeurt daarna met geocode_repat.py --file.
"""
import re, json, os
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
EAD = f"{BASE}/2.13.103.xml"
TOEGANG = "2.13.103"
BRON = "Troepenverschepingen 2.13.103"

def strip(t): return re.sub(r'\{.*?\}', '', t)
def txt(el): return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip() if el is not None else ''
def own_title(c):
    did = next((ch for ch in c if strip(ch.tag) == 'did'), None)
    return txt(next((d for d in did if strip(d.tag) == 'unittitle'), None)) if did is not None else ''
def did_of(c): return next((ch for ch in c if strip(ch.tag) == 'did'), None)

def ids_of(did):
    invnr = handle = mets = None
    for u in did or []:
        if strip(u.tag) == 'unitid':
            if u.get('type') == 'handle': handle = txt(u)
            elif u.get('audience') != 'internal': invnr = txt(u)
        if strip(u.tag) == 'dao':
            m = re.search(r'/mets/v1/([0-9a-f-]{36})', u.get('href', ''))
            if m: mets = m.group(1)
    return invnr, handle, mets

MND = {'jan':1,'feb':2,'mrt':3,'maart':3,'apr':4,'mei':5,'jun':6,'juni':6,'jul':7,'juli':7,
       'aug':8,'sep':9,'sept':9,'okt':10,'nov':11,'dec':12}
def mnum(w): return MND.get(re.sub(r'\.$','',w.strip().lower())[:4].rstrip('.'), MND.get(re.sub(r'[^a-z]','',w.lower())[:3]))

def parse_daterange(s):
    """'1950 mei 15 - juni 29' / '1949 dec. 20 - 1950 jan. 12' -> (van_iso, naar_iso, jaar)."""
    s = s.strip()
    parts = re.split(r'\s*[-–]\s*', s, maxsplit=1)
    def one(tok, fallback_year=None):
        # varianten: 'YYYY mon d' | 'mon d' | 'YYYY'
        m = re.search(r'(\d{4})\s+([A-Za-z]+\.?)\s+(\d{1,2})', tok)   # YYYY mon d
        if m:
            mo = mnum(m.group(2))
            return (int(m.group(1)), mo, int(m.group(3))) if mo else None
        m = re.search(r'([A-Za-z]+\.?)\s+(\d{1,2})', tok)            # mon d
        if m and mnum(m.group(1)) and fallback_year:
            return (fallback_year, mnum(m.group(1)), int(m.group(2)))
        m = re.search(r'(\d{4})', tok)
        if m: return (int(m.group(1)), 0, 0)
        return None
    a = one(parts[0])
    yr = a[0] if a else None
    b = one(parts[1], fallback_year=yr) if len(parts) > 1 else None
    def iso(t): return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}" if t else None
    return iso(a), iso(b), yr

PORT_HINTS = ['Tandjong Priok', 'Batavia', 'Rotterdam', 'Amsterdam', 'Singapore', 'Belawan',
              'Soerabaja', 'Semarang', 'Padang', 'Napels', 'Genua', 'Southampton', 'Colombo']
def route_from_title(t):
    """Vind expliciete havens in bv. 'Tandjong Priok 25 mei - Rotterdam 19 juni 1950'."""
    found = [p for p in PORT_HINTS if p.lower() in t.lower()]
    if len(found) >= 2:
        # volgorde van voorkomen in de tekst
        found.sort(key=lambda p: t.lower().index(p.lower()))
        return found[0], found[-1]
    return None, None

def ship_name(t):
    t = re.sub(r'^(m\.?s\.?|s\.?s\.?)\s*', '', t.strip(), flags=re.I)   # prefix weg
    t = re.split(r'[:.,]', t, maxsplit=1)[0]                             # tot eerste scheiding
    return t.strip() or None

def main():
    root = ET.parse(EAD).getroot()
    reizen = []
    for c in root.iter():
        if strip(c.tag) != 'c': continue
        t = own_title(c)
        if not re.match(r'^(m\.?s\.?|s\.?s\.?)\s', t, re.I): continue
        schip = ship_name(t)
        v0, n0 = route_from_title(t)
        kids = [ch for ch in c if strip(ch.tag) == 'c']
        entries = kids if kids else [c]     # geen subreizen -> schip-component zelf
        for k in entries:
            kt = own_title(k)
            invnr, handle, mets = ids_of(did_of(k))
            vd, ad, jaar = parse_daterange(kt if kids else t)
            kv, kn = route_from_title(kt)
            van = kv or v0 or "Tandjong Priok"
            naar = kn or n0 or "Rotterdam"
            reizen.append({
                "invnr": invnr, "mets": mets, "handle": handle,
                "schip": schip,
                "van": van, "van_datum": vd,
                "via": None, "via_datum": None,
                "naar": naar, "naar_datum": ad,
                "aantal": None, "herkomst_lijst": None, "malta": None,
                "jaar": jaar if (jaar and 1945 <= jaar <= 1955) else None,
                "richting": "troepen", "bron": BRON, "toegang": TOEGANG,
            })
    json.dump(reizen, open(f"{BASE}/troepen_reizen.json", "w", encoding='utf-8'),
              ensure_ascii=False, indent=1)
    import collections
    print(f"troepenreizen: {len(reizen)}")
    print(f"  schepen: {len(set(r['schip'] for r in reizen if r['schip']))}")
    print(f"  met van_datum: {sum(1 for r in reizen if r['van_datum'])} | met jaar: {sum(1 for r in reizen if r['jaar'])}")
    print(f"  expliciete route (niet-default): {sum(1 for r in reizen if r['van']!='Tandjong Priok' or r['naar']!='Rotterdam')}")
    print(f"  jaren: {dict(sorted(collections.Counter(r['jaar'] for r in reizen if r['jaar']).items()))}")

if __name__ == "__main__":
    main()
