#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse Carnegie Heldenfonds inventaris (2.19.364) -> dossiers.json"""
import re, json, sys

WORK = "/private/tmp/claude-501/-Users-alan-Library-Mobile-Documents-com-apple-CloudDocs-DnD-app/9da558d1-094e-4b97-b779-ef97845dd92f/scratchpad"
raw = open(f"{WORK}/full.txt", encoding="utf-8").read()
lines = raw.split("\n")

# Lines to ignore entirely (headers/footers)
def is_noise(l):
    s = l.strip()
    if not s:
        return True
    if "Carnegie Heldenfonds / Persoonsdossiers" in l:
        return True
    if s == "2.19.364" or s.startswith("2.19.364 "):
        return True
    return False

# year + unit line, e.g. "1955-1956            1 omslag"  /  "1948   1 deel"
UNIT_RE = re.compile(r'^\s*(\d{4}(?:\s*-\s*\d{4})?)\s+\d+\s*(omslag|omslagen|pak|deel|delen|stuk|stukken|band|banden|katern|katernen|charter)\b', re.I)
# a record-start line: number in left margin, then >=2 spaces, then a DESCRIPTION
# (must begin with an uppercase letter or a Dutch article-apostrophe like 's-/'t;
#  this excludes year+unit lines such as "1920   1 omslag").
REC_RE = re.compile(r"^\s{0,18}(\d{2,5})\s{2,}((?:'[sStT]\S|[A-ZÀ-Þ]).*)$")

def is_record_start(line):
    if is_noise(line):
        return None
    m = REC_RE.match(line)
    if not m:
        return None
    if UNIT_RE.match(line):          # e.g. "1920   1 omslag"
        return None
    return int(m.group(1)), m.group(2).strip()
META_RE = re.compile(r'^\s*(Openbaarheid beperkt tot|Bevat foto|Bevat een foto|Leeg omslag|Geen openbaarheidsbeperking|Deels openbaar)', re.I)
OPENB_RE = re.compile(r'Openbaarheid beperkt tot\s*([\d-]+)', re.I)

records = []
i = 0
n = len(lines)

while i < n:
    rs = is_record_start(lines[i])
    if rs is None:
        i += 1
        continue
    num, first = rs
    desc_parts = [first]
    year = None
    openb = None
    fotos = False
    i += 1
    # gather until unit line
    while i < n:
        l2 = lines[i]
        if is_noise(l2):
            i += 1
            continue
        um = UNIT_RE.match(l2)
        if um:
            year = um.group(1).replace(" ", "")
            i += 1
            # trailing meta lines (openbaarheid / foto's)
            while i < n:
                l3 = lines[i]
                if is_noise(l3):
                    i += 1
                    continue
                if META_RE.match(l3):
                    om = OPENB_RE.search(l3)
                    if om:
                        openb = om.group(1)
                    if "foto" in l3.lower():
                        fotos = True
                    i += 1
                    continue
                break
            break
        # another record starts before we saw a unit line? bail out
        if is_record_start(l2) is not None:
            break
        # otherwise it's a description continuation line
        desc_parts.append(l2.strip())
        i += 1
    desc = re.sub(r'\s+', ' ', " ".join(desc_parts)).strip()
    if "Bevat foto" in desc:
        fotos = True
    records.append({
        "nr": num,
        "desc": desc,
        "year": year,
        "openbaar_tot": openb,
        "fotos": fotos,
    })

# ---- place & metadata extraction ----
HARD_STOP = {"een","twee","drie","vier","vijf","zes","zeven","acht","negen","tien",
             "elf","twaalf","tijdens","uit","om","tot","toen","na","door","met",
             "zijn","haar","hun","de","het","dat","die","aanvraag","gratificatie",
             "waarbij","waarna","nadat","toen","enkele","meerdere","verschillende",
             "veel","vele","beide","alle","hij","zij"}
CONNECTORS = {"aan","den","der","op","en","ter","'t","'s","bij","de","van","het","in","voor"}

def is_place_start(t):
    if not t:
        return False
    if t[0].isupper():
        return True
    # Dutch article-apostrophe place names: 's-Gravenhage, 't Zand, 's Heerenberg
    if re.match(r"^['’][sStT]", t):
        return True
    return False

def extract_places(desc):
    places = []
    # normalise the 'te te' typo and split article-apostrophe hyphen artefacts
    d = re.sub(r'\bte te\b', 'te', desc)
    d = re.sub(r"(['’][sStT])-\s+", r"\1-", d)   # "'s- Gravenhage" -> "'s-Gravenhage"
    for mm in re.finditer(r'\b(?:te|nabij)\s+', d):
        start = mm.end()
        rest = d[start:]
        toks = rest.split()
        picked = []
        j = 0
        while j < len(toks):
            t = toks[j].strip(",.;:")
            tl = t.lower().strip("'’")
            if not t:
                break
            if is_place_start(t):
                picked.append(t)
                j += 1
                continue
            # lowercase: allowed only as internal connector if a later uppercase token follows soon
            if tl in CONNECTORS and picked:
                # lookahead for an uppercase token within next 2 tokens
                look = [toks[k].strip(",.;:") for k in range(j+1, min(j+3, len(toks)))]
                if any(x[:1].isupper() for x in look if x):
                    picked.append(t)
                    j += 1
                    continue
            break
        if picked:
            # strip trailing connectors
            while picked and picked[-1].lower().strip("'’") in CONNECTORS:
                picked.pop()
            if picked:
                place = " ".join(picked)
                place = place.strip(",.;: ")
                if place and place not in places:
                    places.append(place)
    return places

# --- location detail (waterway / street) extraction ---
# Anchor on a water/ice word so we don't catch surname particles like "van den Akker".
WATERWORDS = (r'water|ijs|wak|gracht|kanaal|haven|vaart|sloot|singel|plas|meer|kolk|wiel|'
              r'dok|rivier|vijver|dijk|kade|kolk|boezem|tocht|leede?|wetering|ringvaart')
DETAIL_RE = re.compile(
    r'\b(?:' + WATERWORDS + r')\b[^,.;:]{0,25}?\b(?:van|aan|langs|in|op|bij|nabij|onder)\s+'
    r"(?:de|het|den|'t|'s)?\s*"
    r"((?:De\s+)?[A-ZÀ-Þ][\wäöüéèëï.'-]+(?:\s+(?:De\s+)?[A-ZÀ-Þ][\wäöüéèëï.'-]+){0,3})")
# direct "uit de Noordzee / uit het IJ / uit de Maas"
DETAIL_RE2 = re.compile(
    r'\buit\s+(?:de|het|\'t)\s+((?:Noordzee|IJ|IJssel|Maas|Waal|Lek|Rijn|Merwede|Schelde|'
    r'Amstel|Zuiderzee|Waddenzee|Dollard|Eems|Vecht|Dinkel|Berkel|Regge|Dieze|Rotte|Gouwe)\b)')

def extract_detail(desc):
    m = DETAIL_RE.search(desc)
    if m:
        d = m.group(1).strip(" .,-")
        # drop a leading bare "De" duplicate artefact "De De Wittenkade" -> keep as-is
        return d
    m = DETAIL_RE2.search(desc)
    if m:
        return m.group(1).strip()
    return None

def normalize_desc(desc):
    # rejoin place names split across a line-wrap by pdftotext, e.g. "'s-Grav enhage"
    desc = re.sub(r"'s-\s?Gr[a-z]* ?[a-z]*hage", "'s-Gravenhage", desc)
    desc = re.sub(r"'s-\s?Her[a-z]* ?[a-z]*bosch", "'s-Hertogenbosch", desc)
    return desc

for r in records:
    r["desc"] = normalize_desc(r["desc"])
    r["places"] = extract_places(r["desc"])
    r["detail"] = extract_detail(r["desc"])
    r["afgewezen"] = bool(re.search(r'afgewezen|afwijzen|afgewe zen', r["desc"], re.I))
    # first year as int
    if r["year"]:
        r["year_from"] = int(r["year"][:4])
    else:
        r["year_from"] = None

json.dump(records, open(f"{WORK}/dossiers_raw.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- diagnostics ----
tot = len(records)
noplace = [r for r in records if not r["places"]]
nums = [r["nr"] for r in records]
print(f"records: {tot}")
print(f"nr range: {min(nums)}..{max(nums)}")
# check gaps / duplicates
dups = [x for x in nums if nums.count(x) > 1]
print(f"duplicate nrs: {len(set(dups))}")
print(f"zonder plaats: {len(noplace)} ({100*len(noplace)/tot:.1f}%)")
afg = [r for r in records if r["afgewezen"]]
print(f"afgewezen: {len(afg)}")
from collections import Counter
allplaces = Counter(p for r in records for p in r["places"])
print(f"unieke plaatsen: {len(allplaces)}")
print("top 15 plaatsen:", allplaces.most_common(15))
print("\n--- 6 voorbeelden zonder plaats ---")
for r in noplace[:6]:
    print(r["nr"], "|", r["desc"][:110])
print("\n--- 8 voorbeelden mét plaats ---")
for r in records[:8]:
    print(r["nr"], "|", r["places"], "|", r["year"], "| foto=",r["fotos"],"| afg=",r["afgewezen"])
