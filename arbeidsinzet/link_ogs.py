#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verrijk de arbeidsinzet-overledenen met een koppeling naar de Oorlogsgravenstichting-index
(NA nt00446, toegang 2.19.255.01). De OGS-index heeft GEEN geboortedatum, maar wél sterfdatum,
-plaats en geboorteplaats. We matchen op (achternaam als anker + volledige sterfdatum), met
voornaam/geboorteplaats als tiebreak. Voegt per gematchte persoon `ogs` (UUID) toe aan personen.json.
Draai NA build_data2.py."""
import json, csv, unicodedata, collections, os

BASE = "/Users/alan/Downloads/arbeidsinzet"
OGS = "/Users/alan/Downloads/NT00446_OORLOGSGRAVEN.csv"
PJSON = f"{BASE}/site/personen.json"

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', (s or '').lower().strip())
                   if unicodedata.category(c) != 'Mn')

# ---- OGS-index op sterfdatum ----
by_date = collections.defaultdict(list)
for row in csv.DictReader(open(OGS, encoding='utf-8')):
    od = row['prs_overlijdensdatum']
    if not od or od == '0000-00-00': continue
    sn = norm((row['prs_tussenvoegsel'] + ' ' + row['prs_achternaam']).strip())
    if not sn: continue
    by_date[od].append({
        "uuid": row['vwz_UUID'], "sn": sn.split(),
        "init": norm(row['prs_initialen']).replace('.', '').replace(' ', ''),
        "voor": norm(row['prs_voornamen']), "gp": norm(row['prs_geboorteplaats']),
        "op": norm(row['prs_overlijdensplaats'])})
print(f"OGS: {sum(len(v) for v in by_date.values()):,} records met sterfdatum ({len(by_date):,} unieke datums)")

# ---- match arbeidsinzet-overledenen ----
P = json.load(open(PJSON, encoding='utf-8'))
matched = ambig = 0
for p in P:
    p.pop('ogs', None)                                   # idempotent
    dd = p.get('dd', '')
    if len(dd) < 10: continue                            # alleen volledige sterfdatum
    cands = by_date.get(dd)
    if not cands: continue
    nn = norm(p['n']); words = set(nn.split())
    fi = nn.split()[0][0] if nn.split() else ''
    pl = norm(p.get('p', ''))
    good = [r for r in cands if r['sn'] and all(w in words for w in r['sn'])]  # achternaam moet in naam zitten
    if not good: continue
    def score(r):
        s = 0
        if pl and r['gp'] and pl == r['gp']: s += 2
        if fi and ((r['init'] and r['init'][0] == fi) or (r['voor'].split() and r['voor'].split()[0][0] == fi)): s += 1
        return s
    good.sort(key=score, reverse=True)
    best = good[0]
    if len(good) == 1 or score(best) >= 1:               # uniek, of duidelijk beste
        p['ogs'] = best['uuid']; matched += 1
    else:
        ambig += 1

json.dump(P, open(PJSON, "w", encoding='utf-8'), ensure_ascii=False, separators=(",", ":"))
dood = sum(1 for p in P if len(p.get('dd', '')) >= 10)
print(f"OGS-koppeling: {matched:,} van {dood:,} overledenen gekoppeld ({round(100*matched/dood)}%); {ambig} te ambigu overgeslagen")
print(f"personen.json: {os.path.getsize(PJSON)//1024//1024} MB")
