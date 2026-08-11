#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_wo2net.py — bouwt people_new.json uit het rijke bronbestand
"20260717 - Totaaloverzicht Engelandvaarders WO2Net.xlsx".

Regels (afgesproken 10 aug 2026):
- Uitsluiten: Status == 'afgevallen - politiek onbetrouwbaar'  +  politiek bevat 'NSB'.
- Privacy: een NIEUWE toevoeging (niet al in de open NT-data) tonen we alleen als er
  een sterfdatum is OF de persoon geboren is vóór 1916-08-10 (110 jaar).
- Alles wat al in de huidige open dataset (people.json, uit NT00464) staat: blijft.
- Unie: huidige 2.101 blijven gegarandeerd; niet-gematchte live-records worden
  overgenomen (zonder etappe-datums), zodat niemand wegvalt.
"""
import openpyxl, json, re, datetime, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(os.path.dirname(HERE), "20260717 - Totaaloverzicht Engelandvaarders WO2Net.xlsx")
LIVE = os.path.join(HERE, "people_nt00464.json")   # vaste NT00464-referentie (NIET overschrijven!)
OUT  = os.path.join(HERE, "people_new.json")

CUTOFF = datetime.date(1916, 8, 10)   # geboren vóór deze datum => 110+ jaar, tonen ok

def norm(s):
    return re.sub(r'[^a-z]', '', (s or '').lower())

_TITLES=r'(?:mr|mvr|dr|drs|ir|ds|jhr|jkvr|jonkheer|jonkvrouw|familie|fam|echtgenote|echtpaar|mevrouw|mevr|mej|dhr|mv|hr|heer|sir|oom|tante|wed|weduwe|echtgenoot|zuster|broeder|prof|pastoor|pater|kapelaan|dominee|abbe|abbé|monseigneur|mgr|monsieur|mme|madame|generaal|majoor|kapitein|luitenant|kolonel|korporaal|sergeant|consul|consul-generaal|burgemeester|graaf|gravin|baron|barones|reserve|dames|dame)'
def compkey(x):
    """Sleutel voor namen (leidende titels + leestekens/spaties genegeerd)."""
    x=(x or '').lower().strip()
    x=re.sub(r'^(?:'+_TITLES+r'\.?[\s\-]+)+','',x)
    return re.sub(r'[^a-z0-9]', '', x)

def s(v):
    if v is None: return ''
    if isinstance(v, datetime.datetime): return v.date().isoformat()
    return str(v).strip()

def to_int(v):
    v = s(v)
    if re.fullmatch(r'\d{1,4}', v): return int(v)
    return None

def parse_date(v):
    """Excel-cel -> 'YYYY-MM-DD' of None. '00:00:00'/leeg -> None."""
    if v is None: return None
    if isinstance(v, datetime.datetime): return v.date().isoformat()
    t = str(v).strip()
    if not t or t == '00:00:00': return None
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', t)
    return m.group(0) if m else None

def day_diff(a, b):
    """Aantal dagen tussen twee 'YYYY-MM-DD'-datums (b - a); None indien onbekend/negatief."""
    if not a or not b: return None
    try:
        da=datetime.date.fromisoformat(a[:10]); db=datetime.date.fromisoformat(b[:10])
    except Exception: return None
    d=(db-da).days
    return d if 0 <= d <= 3000 else None

LOC_RE = re.compile(r'^\s*(?:\[(?P<camp>[^\]]+)\]\s*)?(?P<place>.+?)\s*\((?P<country>[^)]+)\)\s*$')
def _dedup(legs):
    dr=[]
    for leg in legs:
        if dr and dr[-1]['key']==leg['key'] and leg['key']:
            if not dr[-1].get('date') and leg.get('date'): dr[-1]['date']=leg['date']
            continue
        dr.append(leg)
    return dr
def parse_helper_mentions(v):
    """'Naam (Plaats, Land) | Naam (Plaats)' -> [{key,naam,plaats,land}]."""
    out=[]
    for part in re.split(r'[|\n]+', s(v)):
        part=part.strip().strip('"').strip()
        if not part: continue
        naam=re.sub(r'\s*\(.*$','',part).strip()               # naam = alles vóór de eerste '('
        if ':' in naam: naam=naam.rsplit(':',1)[-1].strip()    # "Tweede mislukte reis: Jet Rozenberg" -> "Jet Rozenberg"
        mp=re.search(r'\((.*)\)\s*$', part)                    # plaats = binnen de buitenste haakjes
        loc=re.sub(r'\s*\([^)]*\)','', mp.group(1)) if mp else ''  # inner "(Brabant)" weg
        pl,_,la=loc.partition(',')
        k=compkey(naam)
        if k: out.append({'key':k,'naam':naam,'plaats':pl.strip(),'land':la.strip()})
    return out
def parse_route_string(v):
    """'Loc (Land) - [kamp X] Loc (Land) - ...' -> legs (zonder datum). Fallback voor rijen zonder etappes."""
    t = s(v)
    if not t: return []
    out=[]
    for part in re.split(r'\s+-\s+', t):
        L=parse_loc(part)
        if L: out.append(dict(L, date=None))
    return _dedup(out)
def parse_loc(v):
    """'[kamp X] Plaats (Land)' -> (camp, place, country) ; None-onderdelen waar afwezig."""
    t = s(v)
    if not t: return None
    if re.match(r'^(familie|fam\.)\b', t, re.I): return None   # reisgezelschap-artefact, geen locatie
    m = LOC_RE.match(t)
    if not m:
        return {'camp': None, 'place': t, 'country': '', 'key': ''}
    place = m.group('place').strip()
    country = m.group('country').strip()
    return {'camp': (m.group('camp') or None), 'place': place, 'country': country,
            'key': f"{place}|{country}"}

# ---------- inlezen ----------
wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
ws = wb["Overzicht Engelandvaarders"]
it = ws.iter_rows(min_row=2, values_only=True)
hdr = [ (str(c).strip() if c is not None else '') for c in next(it) ]

def col(exact):
    return hdr.index(exact)
def colp(prefix):
    for i, h in enumerate(hdr):
        if h.startswith(prefix): return i
    raise KeyError(prefix)

C = dict(
    status=col('Status'), uuid=col('UUID'), nameD=colp('Achternaam, Initialen'),
    ach=col('Achternaam'), tus=col('tussenvoegsel(s)'), init=colp('Initialen'),
    voor=colp('Voorna'), roep=col('Roepnaam/bijnaam'), mv=col('Man/vrouw'),
    gj=col('geboortedatum jaar'), gm=col('geboortedatum maand'), gd=col('geboortedatum dag'),
    gpl=col('Geboorteplaats'), gland=col('Geboorteland'),
    ovlh=col('Overlijdensdatum handmatig'), ovlc=col('Overlijdensdatum CBG (NRO match)'),
    woon=col('Woonplaats'), beroep=col('Beroep'), bs=col('Burgelijke staat'),
    gods=col('Godsdienst'), pol=col('Politieke richting'), lvertr=col('Land van vertrek'),
    dvertr=col('Datum vertrek uit bezet gebied'), daank=col('Datum aankomst in VK'),
    hoofd=colp('Hoofdroute'), landen=colp('Landen op de route'), locroute=colp('Locaties op de route'),
)
# etappe-kolomindexen (in volgorde)
et_lv=[i for i,h in enumerate(hdr) if h.startswith('Locatie vertrek etappe')]
et_la=[i for i,h in enumerate(hdr) if h.startswith('Locatie aankomst etappe')]
et_dv=[i for i,h in enumerate(hdr) if h.startswith('Datum vertrek etappe')]
et_da=[i for i,h in enumerate(hdr) if h.startswith('Datum aankomst etappe')]
et_rg=[i for i,h in enumerate(hdr) if h.startswith('Reisgezelschap')]
et_ru=[i for i,h in enumerate(hdr) if h.startswith('UUID Reisgezelschap')]
arch_cols=[(h.split()[0], i) for i,h in enumerate(hdr) if h[:2]=='2.']
samH=colp('Helpers (samengevoegd')

# ---------- live-sleutels (voor 'in_nt') ----------
live = json.load(open(LIVE, encoding='utf-8'))
live_inv=set(); live_full=set(); live_by_full={}; live_by_inv={}
def live_invnr(r):
    m=re.search(r'/archief/([\d.]+)/invnr/(\w+)', r.get('na_link') or '')
    return (m.group(1), str(m.group(2))) if m else None
for r in live:
    k=live_invnr(r)
    if k: live_inv.add(k); live_by_inv.setdefault(k, r)
    f=norm(r.get('naam'))
    if f: live_full.add(f); live_by_full.setdefault(f, r)

# scan-URL-kolom per archieftoegang (koppen: "Bestandsnaam scans 2.09.06")
scan_by_toegang={}
for i,h in enumerate(hdr):
    if h.startswith('Bestandsnaam scans'):
        mm=re.search(r'2\.[\d.]+', h)
        if mm: scan_by_toegang[mm.group(0)]=i

def archive_links(r, full, invnr):
    """record_link (NT-recordpagina), na_link (scan/dossier), oorlog (oorlogsbronnen)."""
    lr = live_by_full.get(full) or (live_by_inv.get(invnr) if invnr else None) or {}
    record_link = lr.get('record_link') or ''
    oorlog = lr.get('link') or ''
    na = lr.get('na_link') or ''
    if not na and invnr:
        tg, nr = invnr
        si = scan_by_toegang.get(tg)
        scanv = s(r[si]) if si is not None else ''
        if scanv.startswith('http'): na = scanv
        else: na = f"https://www.nationaalarchief.nl/onderzoeken/archief/{tg}/invnr/{nr}"
    return record_link, na, oorlog

def death_of(r):
    for c in (C['ovlh'], C['ovlc']):
        v=parse_date(r[c])
        if v: return v
    return None

def born_before_cutoff(y,m,d):
    if not y: return False
    try: bd=datetime.date(y, m or 1, d or 1)
    except Exception: bd=datetime.date(y,1,1)
    return bd < CUTOFF

EXCL_STATUS={'afgevallen - politiek onbetrouwbaar'}

# ---------- verwerken ----------
rows=list(it)
kept=[]; dropped=[]; stats=dict(total=0, excl_status=0, excl_nsb=0, excl_privacy=0,
                                in_nt=0, new_death=0, new_old=0, enriched=0)
matched_full=set(); matched_inv=set()
new_places=set()

for r in rows:
    if r is None or not any(r[:5]): continue
    stats['total']+=1
    status=s(r[C['status']]) or '—'
    pol=s(r[C['pol']])
    # naam
    ach=s(r[C['ach']]); tus=s(r[C['tus']]); voor=s(r[C['voor']]); init=s(r[C['init']]); roep=s(r[C['roep']])
    naam=' '.join(x for x in [voor or init, (tus+' '+ach).strip() if tus else ach] if x).strip()
    full=norm(voor)+norm(tus)+norm(ach)
    invnr=None
    for tg,ci in arch_cols:
        v=s(r[ci])
        if v and re.match(r'^\d[\d\-/]*$', v): invnr=(tg,v); break   # alleen echte inventarisnummers
    in_nt = full in live_full or (invnr in live_inv if invnr else False)

    # ---- filters ----
    if status in EXCL_STATUS:
        stats['excl_status']+=1; dropped.append((naam,'politiek onbetrouwbaar')); continue
    if re.search(r'\bNSB\b', pol):
        stats['excl_nsb']+=1; dropped.append((naam,'NSB')); continue
    gj=to_int(r[C['gj']]); gm=to_int(r[C['gm']]); gd=to_int(r[C['gd']])
    death=death_of(r)
    if not in_nt:
        if death: stats['new_death']+=1
        elif born_before_cutoff(gj,gm,gd): stats['new_old']+=1
        else:
            stats['excl_privacy']+=1; dropped.append((naam,'mogelijk levend')); continue

    if in_nt:
        stats['in_nt']+=1
        if full in live_full: matched_full.add(full)
        if invnr in live_inv: matched_inv.add(invnr)

    # ---- route uit etappes (met datums) ----
    route=[]
    first=True
    for lv,la,dv,da in zip(et_lv,et_la,et_dv,et_da):
        L=parse_loc(r[lv]); A=parse_loc(r[la])
        dvv=parse_date(r[dv]); daa=parse_date(r[da])
        if L and first:
            L=dict(L); L['date']=dvv; route.append(L); first=False
        if A:
            A=dict(A); A['date']=daa; route.append(A)
    route=_dedup(route)
    got_dates = any(l.get('date') for l in route)
    # fallback 1: 'Locaties op de route'-string (zonder datums) als etappes te dun zijn
    if len([l for l in route if l['key']])<2:
        rs=parse_route_string(r[C['locroute']])
        if len(rs)>=2: route=rs; got_dates=False
    # fallback 2: bestaande live-route (in_nt, gematcht op volledige naam)
    if len([l for l in route if l['key']])<2 and full in live_by_full:
        lr=live_by_full[full].get('route') or []
        if len(lr)>=2:
            route=[dict(l, date=l.get('date')) for l in lr]; got_dates=False
    # verblijfsduur per locatie = dagen tot de volgende stop
    for i,leg in enumerate(route):
        leg['days']=day_diff(leg.get('date'), route[i+1].get('date')) if i+1<len(route) else None
    for leg in route:
        if leg['key']: new_places.add(leg['key'])
    gpl=s(r[C['gpl']]); gland=s(r[C['gland']]); lvertr=s(r[C['lvertr']])
    if gpl: new_places.add(f"{gpl}|{gland or 'Nederland'}")

    rec=dict(
        id=s(r[C['uuid']]), uuid=s(r[C['uuid']]), status=status, naam=naam, roepnaam=roep,
        geslacht=('man' if s(r[C['mv']]).lower().startswith('m') else ('vrouw' if s(r[C['mv']]).lower().startswith('v') else '')),
        geboortejaar=gj, geboorteplaats=gpl, geboorte_key=(f"{gpl}|{gland or 'Nederland'}" if gpl else ''),
        overlijdensdatum=death,
        woonplaats=s(r[C['woon']]), beroep=s(r[C['beroep']]), burgstaat=s(r[C['bs']]),
        godsdienst=s(r[C['gods']]), politiek=pol, land_vertrek=lvertr,
        vertrek_key=(f"{lvertr}|{lvertr}" if lvertr else ''),
        datumvertr=parse_date(r[C['dvertr']]), datumaank=parse_date(r[C['daank']]),
        hoofdroute=s(r[C['hoofd']]), landen_op_route=s(r[C['landen']]),
        route=route, heeft_route=len([l for l in route if l['key']])>=2,
        route_dates=got_dates, in_nt=in_nt,
    )
    rec['record_link'], rec['na_link'], rec['link'] = archive_links(r, full, invnr)
    # reisgenoten (mede-Engelandvaarders) uit alle etappe-reisgezelschap-kolommen
    comps=set()
    for ci in et_rg:
        v=s(r[ci])
        if not v: continue
        for part in re.split(r'[|\n]+', v):
            part=part.strip().strip('"').strip()
            if part: comps.add(part)
    rec['_comps']=comps
    rec['_namekey']=s(r[C['nameD']])
    rec['_geh']=parse_helper_mentions(r[samH])
    kept.append(rec)
    if got_dates: stats['enriched']+=1

# ---- niet-gematchte live-records overnemen (unie; niemand kwijt) ----
carried=0
for r in live:
    f=norm(r.get('naam')); k=live_invnr(r)
    if f in matched_full or (k and k in matched_inv): continue
    rec=dict(r)  # oude schema
    rec['status']='Engelandvaarder'; rec['in_nt']=True; rec['uuid']=rec.get('uuid') or ''
    rec['overlijdensdatum']=None
    # oude route heeft geen datums -> date=None per leg
    for leg in rec.get('route',[]): leg.setdefault('date', None)
    kept.append(rec); carried+=1

# unieke id's afdwingen (bron heeft enkele dubbele UUID's)
_seen={}
for rec in kept:
    i=rec.get('id') or rec.get('uuid') or ''
    if i in _seen: _seen[i]+=1; rec['id']=f"{i}-{_seen[i]}"
    else: _seen[i]=1

# reisgenoten koppelen (naam -> id); alleen personen die zélf in de dataset staan
key2id={}
for rec in kept:
    k=compkey(rec.get('_namekey',''))
    if k: key2id.setdefault(k, rec['id'])
id2naam={rec['id']:rec['naam'] for rec in kept}
for rec in kept:
    selfk=compkey(rec.get('_namekey',''))
    out=[]; seen=set()
    for c in rec.pop('_comps', []) or []:
        ck=compkey(c)
        if not ck or ck==selfk: continue
        rid=key2id.get(ck)
        if rid and rid!=rec['id'] and rid not in seen:
            seen.add(rid); out.append({'id':rid, 'naam':id2naam.get(rid,'')})
    rec['reisgenoten']=out
    rec.pop('_namekey', None)

# helpers koppelen: per persoon 'geholpen_door' + omgekeerd netwerk helpernet
helpernet={}
for rec in kept:
    disp=[]; seen=set()
    for h in rec.pop('_geh', []) or []:
        hk=h['key']
        if hk in seen: continue
        seen.add(hk)
        disp.append({'id':hk, 'naam':h['naam'], 'plaats':h['plaats']})
        e=helpernet.setdefault(hk, {'naam':h['naam'], 'plaats':h['plaats'], 'land':h['land'], 'helped':[]})
        if not e['plaats'] and h['plaats']: e['plaats']=h['plaats']
        if not e['land'] and h['land']: e['land']=h['land']
        e['helped'].append({'id':rec['id'], 'naam':rec['naam']})
    rec['geholpen_door']=disp
json.dump(helpernet, open(os.path.join(HERE,'helpernet.json'),'w',encoding='utf-8'), ensure_ascii=False)

json.dump(kept, open(OUT,'w',encoding='utf-8'), ensure_ascii=False)
json.dump(sorted(new_places), open(os.path.join(HERE,'placekeys_new.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=0)

# ---- rapport ----
print(f"BRON-rijen: {stats['total']}")
print(f"  al in NT (blijft):        {stats['in_nt']}")
print(f"  nieuw, met sterfdatum:    {stats['new_death']}")
print(f"  nieuw, geboren <1916:     {stats['new_old']}")
print(f"UITGESLOTEN:")
print(f"  politiek onbetrouwbaar:   {stats['excl_status']}")
print(f"  NSB:                      {stats['excl_nsb']}")
print(f"  mogelijk levend:          {stats['excl_privacy']}")
print(f"OVERGENOMEN uit live (niet in Excel): {carried}")
print(f"--> TOTAAL people_new.json: {len(kept)}")
nroute=sum(1 for k in kept if k.get('heeft_route'))
print(f"met route (>=2 plaatsen): {nroute}  | met per-etappe DATUMS: {stats['enriched']}")
print(f"unieke plaats-keys (voor geocoding): {len(new_places)}")
# hoeveel daarvan al in geocache?
gc=os.path.join(HERE,'geocache.json')
if os.path.exists(gc):
    cache=json.load(open(gc))
    miss=[k for k in new_places if k not in cache]
    print(f"  nog te geocoden (niet in geocache): {len(miss)}")
    json.dump(sorted(miss), open(os.path.join(HERE,'geocode_todo_wo2net.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=0)
