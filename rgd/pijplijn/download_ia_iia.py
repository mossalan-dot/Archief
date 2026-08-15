#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download secties IA + IIA (generieke ontwerpen, niet aan plaats gekoppeld) als
~1200px IIIF-scans: één map per inventarisnummer, met een _index.txt met titels.
Bedoeld om handmatig te bekijken en de map te hernoemen naar de stad."""
import os, re, sys, json, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

SRC = "/Users/alan/Downloads/4.RGD.xml"
OUT = os.path.expanduser("~/Downloads/RGD-download")
UA = "RGDtekeningenkaart/1.0 (mossalan@gmail.com)"
SECTIONS = ["IA", "IIA"]

raw = open(SRC, encoding="utf-8").read()
body = raw[raw.find("<dsc"):]

def subtree(code):
    m = re.search(r'<unitid type="series_code">' + re.escape(code) + r'</unitid>', body)
    start = body.rfind("<c ", 0, m.start()); depth = 0; i = start
    while i < len(body):
        if body.startswith("</c>", i): depth -= 1; i += 4
        elif body.startswith("<c ", i) or body.startswith("<c>", i): depth += 1; i += 3
        else: i += 1
        if depth == 0: break
    return body[start:i]

def txt(el): return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""

def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if binary else r.read().decode("utf-8", "replace")

# 1) inventariseer alle items met scan
items = []   # (section, invnr, unitid, title, mets_uuid)
for sec in SECTIONS:
    root = ET.fromstring(subtree(sec))
    for c in root.iter("c"):
        d = c.find("did")
        if d is None or d.find("dao") is None: continue
        uid = next((txt(u) for u in d.findall("unitid")
                    if u.get("type") not in ("handle", "series_code") and u.get("audience") != "internal"), "")
        if not uid: continue
        gid = re.search(r"([0-9a-f-]{36})", d.find("dao").get("href", ""))
        items.append((sec, uid.split(".")[0], uid, txt(d.find("unittitle")), gid.group(1) if gid else ""))

print(f"IA+IIA: {len(items)} scans over {len({(s,i) for s,i,_,_,_ in items})} inventarisnummers")

# 2) mappen + _index.txt
from collections import defaultdict
byfolder = defaultdict(list)
for sec, inv, uid, title, mets in items:
    byfolder[(sec, inv)].append((uid, title))
for (sec, inv), lst in byfolder.items():
    fdir = f"{OUT}/{sec}/{inv}"; os.makedirs(fdir, exist_ok=True)
    with open(f"{fdir}/_index.txt", "w", encoding="utf-8") as f:
        f.write(f"# Sectie {sec} · inventarisnummer {inv}\n# (bekijk de scans en hernoem deze map naar de plaats)\n\n")
        for uid, title in sorted(lst): f.write(f"{uid}\t{title}\n")

# 3) download IIIF-scans (~1200px)
BASE = "https://service.archief.nl/iip/iipsrv?IIIF="
def dl(item):
    sec, inv, uid, title, mets = item
    if not mets: return 0
    fdir = f"{OUT}/{sec}/{inv}"
    try:
        x = get(f"https://service.archief.nl/gaf/api/mets/v1/{mets}")
        iiif = re.findall(r"IIIF=([^\"&]+\.jp2)", x)
    except Exception as e:
        print("  ! mets", uid, e); return 0
    got = 0
    for k, ident in enumerate(iiif):
        suffix = f"_p{k+1:02d}" if len(iiif) > 1 else ""
        fp = f"{fdir}/{uid}{suffix}.jpg"
        if os.path.exists(fp) and os.path.getsize(fp) > 1000: got += 1; continue
        try:
            data = get(f"{BASE}{ident}/full/1200,/0/default.jpg", binary=True)
            open(fp, "wb").write(data); got += 1
        except Exception as e:
            print("  ! img", uid, e)
    return got

done = tot = 0
with ThreadPoolExecutor(max_workers=6) as ex:
    for g in ex.map(dl, items):
        tot += g; done += 1
        if done % 100 == 0: print(f"  .. {done}/{len(items)} items, {tot} scans")
print(f"KLAAR: {tot} scans gedownload naar {OUT}/")
