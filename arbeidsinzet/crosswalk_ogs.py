#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bidirectionele koppeling Oorlogsgravenstichting <-> Arbeidsinzet.

Matcht personen op (achternaam + eerste initiaal + exacte datum), waarbij de datum
zowel de GEBOORTE- als de STERFDATUM mag zijn. Beide sets bevatten naam, geboortedatum
en geboorteplaats; OGS bovendien sterfdatum/-plaats. Een koppeling is:
  'z' (zeker)        - bevestigd door twee onafhankelijke datums, OF door één datum
                       plus overeenkomende plaats (geboorte- of overlijdensplaats);
  'w' (waarschijnlijk) - één datum, achternaam en initiaal, zonder verdere bevestiging.

Schrijft de koppeling aan BEIDE kanten terug (idempotent):
  arbeidsinzet/site/personen.json : p['ogs'] = OGS-UUID,  p['ogz'] = 'z'|'w'
  oorlogsgraven/site/personen.json: p['ai']  = reconstructieid, p['aiz'] = 'z'|'w'
en een losse crosswalk_ogs_arbeidsinzet.json voor reproduceerbaarheid.

Draai NA build_data2.py (arbeidsinzet) en build_data.py (OGS). Vervangt link_ogs.py."""
import json, re, unicodedata
from collections import defaultdict

OGS = "/Users/alan/Downloads/oorlogsgraven/site/personen.json"
AI  = "/Users/alan/Downloads/arbeidsinzet/site/personen.json"
KD  = "/Users/alan/Downloads/arbeidsinzet/site/kaart_data.json"
XW  = "/Users/alan/Downloads/arbeidsinzet/crosswalk_ogs_arbeidsinzet.json"

def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', (s or '').lower().strip())
                if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z ]', ' ', s)

def ogs_key(n):
    """OGS-naam 'Achternaam, Voornamen tussenvoegsel' -> (achternaam, 1e-initiaal)."""
    sur, rest = (n.split(',', 1) + [''])[:2] if ',' in n else (n, '')
    sur = norm(sur).split(); rest = norm(rest).split()
    return (sur[-1], rest[0][0] if rest else '') if sur else None

def ai_key(n):
    """Arbeidsinzet-naam 'A Boenders' / 'Anton van Boenders' -> (achternaam, 1e-initiaal)."""
    t = norm(n).split()
    return (t[-1], t[0][0]) if len(t) >= 2 else None

# ---- OGS-personen indexeren op (datum, achternaam) ----
ogs = json.load(open(OGS, encoding='utf-8'))
by_bd = defaultdict(list); by_dd = defaultdict(list)
for idx, p in enumerate(ogs):
    k = ogs_key(p['n'])
    if not k: continue
    rec = {"i": idx, "init": k[1], "na": p.get('na', ''),
           "gp": norm(p.get('gp', '')), "op": norm(p.get('op', ''))}
    if len(p.get('gd', '')) >= 10: by_bd[(p['gd'], k[0])].append(rec)
    if len(p.get('od', '')) >= 10: by_dd[(p['od'], k[0])].append(rec)
    p.pop('ai', None); p.pop('aiz', None)   # idempotent
print(f"OGS: {len(ogs):,} personen | {len(by_bd):,} geboortedatum-sleutels | {len(by_dd):,} sterfdatum-sleutels")

def pick(cands, init, place):
    """Kies uit kandidaten met gelijke initiaal; plaats-overeenkomst als tiebreak.
    Geeft (record, plaats_bevestigd) of (None, False) bij ambiguïteit."""
    good = [c for c in cands if c['init'] == init]
    if not good: return None, False
    withplace = [c for c in good if place and (place == c['gp'] or place == c['op'])]
    if withplace:
        na = withplace[0]['na']
        return (withplace[0], True) if all(c['na'] == na for c in withplace) else (None, False)
    na = good[0]['na']
    return (good[0], False) if all(c['na'] == na for c in good) else (None, False)

# ---- arbeidsinzet-personen matchen ----
ai = json.load(open(AI, encoding='utf-8'))
links = []           # (reconstructieid, ogs_uuid, ogs_idx, zekerheid)
matched = zeker = waarschijnlijk = ambigu = 0
for p in ai:
    p.pop('ogs', None); p.pop('ogz', None)          # idempotent
    k = ai_key(p['n'])
    if not k: continue
    place = norm(p.get('p', ''))
    bd = p.get('bd', ''); dd = p.get('dd', '')
    rb, pb = pick(by_bd.get((bd, k[0]), []), k[1], place) if len(bd) >= 10 else (None, False)
    rd, pd = pick(by_dd.get((dd, k[0]), []), k[1], place) if len(dd) >= 10 else (None, False)
    if not rb and not rd:
        continue
    # conflict: beide datums matchen, maar naar verschillende OGS-personen -> overslaan
    if rb and rd and rb['na'] != rd['na']:
        ambigu += 1; continue
    rec = rb or rd
    both = bool(rb and rd)
    conf = 'z' if (both or pb or pd) else 'w'
    p['ogs'] = rec['na']; p['ogz'] = conf
    o = ogs[rec['i']]
    # OGS-kant: houd de sterkste koppeling als een persoon meerdere keren matcht
    if o.get('aiz') != 'z' or conf == 'z':
        o['ai'] = p['id']; o['aiz'] = conf
    links.append((p['id'], rec['na'], rec['i'], conf))
    matched += 1
    if conf == 'z': zeker += 1
    else: waarschijnlijk += 1

json.dump(ai, open(AI, "w", encoding='utf-8'), ensure_ascii=False, separators=(",", ":"))
json.dump(ogs, open(OGS, "w", encoding='utf-8'), ensure_ascii=False, separators=(",", ":"))
json.dump([{"ai": a, "ogs": o, "z": z} for a, o, i, z in links],
          open(XW, "w", encoding='utf-8'), ensure_ascii=False, separators=(",", ":"))
# meta bijwerken voor de Inzichten-KPI
kd = json.load(open(KD, encoding='utf-8'))
kd.setdefault('meta', {})
kd['meta']['ogs_gekoppeld'] = matched
kd['meta']['ogs_zeker'] = zeker
json.dump(kd, open(KD, "w", encoding='utf-8'), ensure_ascii=False, separators=(",", ":"))
ogs_side = sum(1 for p in ogs if p.get('ai'))
print(f"gekoppeld: {matched:,}  (zeker {zeker:,} | waarschijnlijk {waarschijnlijk:,})")
print(f"overgeslagen wegens conflict/ambiguïteit: {ambigu:,}")
print(f"OGS-personen met arbeidsinzet-koppeling: {ogs_side:,}")
print(f"crosswalk weggeschreven: {XW}")
