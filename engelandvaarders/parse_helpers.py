#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""helpers.json — passeurs, onderduikgevers, ontsnappingslijnen.
Voegt het gestructureerde 'helpers'-tabblad (rol/bron) samen met het helper-netwerk
uit parse_wo2net (helpernet.json: wie hielp welke Engelandvaarders).
Toont alleen publieke helper-rol + operatielocatie + bron; geen geboorte/overlijden."""
import openpyxl, json, re, os
HERE=os.path.dirname(os.path.abspath(__file__))
XLSX=os.path.join(os.path.dirname(HERE),"20260717 - Totaaloverzicht Engelandvaarders WO2Net.xlsx")

def s(v): return '' if v is None else str(v).strip()
_TITLES=r'(?:mr|mvr|dr|drs|ir|ds|jhr|jkvr|jonkheer|jonkvrouw|familie|fam|echtgenote|echtpaar|mevrouw|mevr|mej|dhr|mv|hr|heer|sir|oom|tante|wed|weduwe|echtgenoot|zuster|broeder|prof|pastoor|pater|kapelaan|dominee|abbe|abbé|monseigneur|mgr|monsieur|mme|madame|generaal|majoor|kapitein|luitenant|kolonel|korporaal|sergeant|consul|consul-generaal|burgemeester|graaf|gravin|baron|barones|reserve|dames|dame)'
def compkey(x):
    x=(x or '').lower().strip()
    x=re.sub(r'^(?:'+_TITLES+r'\.?[\s\-]+)+','',x)   # leidende titels weg voor het koppelen
    return re.sub(r'[^a-z0-9]','',x)

wb=openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
hs=wb["helpers"]; it=hs.iter_rows(min_row=1, values_only=True)
hdr=[s(c) for c in next(it)]
def gi(pfx):
    for i,h in enumerate(hdr):
        if h.startswith(pfx): return i
C=dict(colA=0, ach=hdr.index('Achternaam'), tus=gi('tussenvoegsel'), voor=gi('Voorna'),
       mv=gi('Man/vrouw'), city=gi('Woonplaats (opereerde'), land=gi('Locatie (opereerde'),
       beroep=gi('Beroep'), rol=gi('Rol'), opm=gi('Opmerkingen'))

byId={}   # key -> helper
def add(naam, plaats, land, **extra):
    plaats=re.sub(r'\s*\(.*$','',plaats or '').strip()
    if naam and ':' in naam: naam=naam.rsplit(':',1)[-1].strip()   # notities in de naam weg
    k=compkey(naam)
    if not k: return None
    h=byId.get(k)
    if not h:
        h=dict(id=k, naam=naam, plaats=plaats, land=land or '',
               beroep='', rol='', opmerkingen='', geslacht='', helped=[])
        byId[k]=h
    for kk,vv in extra.items():
        if vv and not h.get(kk): h[kk]=vv
    if plaats and not h['plaats']: h['plaats']=plaats
    if land and not h['land']: h['land']=land
    return h

# 1) gestructureerd tabblad (rol/bron/geslacht)
for r in it:
    if r is None or not any(r[:8]): continue
    ach=s(r[C['ach']]).split(',')[0].strip(); tus=s(r[C['tus']]); voor=s(r[C['voor']])   # "Kraay, S." -> "Kraay"
    naam=' '.join(x for x in [voor, (tus+' '+ach).strip() if tus else ach] if x).strip()
    if not naam: naam=re.sub(r'\s*\(.*$','', s(r[C['colA']])).strip()
    mv=s(r[C['mv']]).lower()
    add(naam, s(r[C['city']]), s(r[C['land']]),
        beroep=s(r[C['beroep']]), rol=s(r[C['rol']]),
        opmerkingen=re.sub(r'\s+',' ', s(r[C['opm']])).strip(),
        geslacht=('vrouw' if mv.startswith('v') else 'man' if mv.startswith('m') else ''))

# 2) netwerk uit helpernet.json (wie hielp wie) — voegt ook helpers toe die niet in het tabblad staan
net=json.load(open(os.path.join(HERE,'helpernet.json'),encoding='utf-8'))
for k,e in net.items():
    h=add(e['naam'], e.get('plaats',''), e.get('land',''))
    if h: h['helped']=e.get('helped',[])

# ---- samenvoegen: kale achternaam -> volledige naam, zelfde plaats ----
import collections
_TUS={'van','de','der','den','ten','ter','te',"'t","'s",'op','aan','bij','in','het','la','le','du','von','di','of'}
_NICK={'kees':'cornelis','cor':'cornelis','jan':'johannes','hans':'johannes','joop':'johannes',
       'sjaak':'jacobus','koos':'jacobus','wim':'willem','piet':'pieter','bram':'abraham',
       'toon':'antonius','antoon':'antonius','ton':'antonius','henk':'hendrik','gerrit':'gerardus',
       'dirk':'theodorus','bertus':'lambertus','guus':'gustaaf','fons':'alfons','bep':'elisabeth',
       'mien':'wilhelmina','riet':'margaretha','nel':'petronella','jo':'johanna','frits':'frederik'}
def _parts(naam):   # tokens zonder titels/leestekens; initialen als losse letters
    x=(naam or '').lower()
    x=re.sub(r'^(?:'+_TITLES+r'\.?[\s\-]+)+','',x)
    return re.findall(r"[a-zà-ÿ']+", x)
def _surn(naam):
    p=_parts(naam); return p[-1] if p else ''
def _firsts(naam):   # voornaam-tokens (zonder titels, tussenvoegsels, achternaam)
    p=_parts(naam)
    return [t for t in p[:-1] if t.strip("'") not in _TUS]
def _cf(t):
    t=t.strip("'").lower(); return _NICK.get(t,t)
def _compat(a,b):    # zijn a-voornamen een 'prefix' van b (met initialen + roepnamen)?
    if len(a)>len(b): return False
    for x,y in zip(a,b):
        if len(x)<=1 or len(y)<=1:
            if x[:1]!=y[:1]: return False       # initiaal vs (initiaal of voornaam)
        elif _cf(x)!=_cf(y): return False
    return True
def _fullcnt(naam):  # aantal echte voornamen (geen initialen)
    return sum(1 for t in _firsts(naam) if len(t)>1)
groups=collections.defaultdict(list)
for h in byId.values():
    groups[(re.sub(r'[^a-z]','',(h['plaats'] or '').lower()), _surn(h['naam']))].append(h)
remap={}
for (pl,sn),hs in groups.items():
    if not sn or len(hs)<2: continue
    # meest complete naam als canoniek (meeste echte voornamen, dan meeste 'hielp', dan langst)
    hs=sorted(hs, key=lambda h:(_fullcnt(h['naam']), len(h.get('helped') or []), len(h['naam'])), reverse=True)
    canons=[]
    for h in hs:
        hf=_firsts(h['naam']); target=None
        for c in canons:
            if _compat(hf, _firsts(c['naam'])): target=c; break
        if target is None:
            canons.append(h); continue
        target['helped']=(target.get('helped') or [])+(h.get('helped') or [])
        for fld in ('rol','beroep','opmerkingen','geslacht','land','plaats'):
            if not target.get(fld) and h.get(fld): target[fld]=h[fld]
        remap[h['id']]=target['id']
for oid in remap: byId.pop(oid, None)
for h in byId.values():   # dedup helped na merge
    seen=set(); dd=[]
    for x in (h.get('helped') or []):
        if x['id'] in seen: continue
        seen.add(x['id']); dd.append(x)
    h['helped']=dd

NAME_FIX={'vandenbosschedejong':'Van den Bossche-de Jong'}   # handmatige spelling-/casing-correcties
out=list(byId.values())
for h in out:
    if h['id'] in NAME_FIX: h['naam']=NAME_FIX[h['id']]
    h['n']=len(h['helped'])
    h['key']=f"{h['plaats']}|{h['land']}" if h['plaats'] else ''

json.dump(out, open(os.path.join(HERE,'helpers.json'),'w',encoding='utf-8'), ensure_ascii=False)

# ---- geholpen_door-koppelingen in people.json bijwerken (remap + canonieke naam) ----
_pp=os.path.join(HERE,'people.json')
if os.path.exists(_pp) and remap:
    id2h={h['id']:h for h in out}
    people=json.load(open(_pp,encoding='utf-8'))
    for p in people:
        if not p.get('geholpen_door'): continue
        seen=set(); nd=[]
        for g in p['geholpen_door']:
            nid=remap.get(g['id'], g['id'])
            if nid in seen: continue
            seen.add(nid); ch=id2h.get(nid)
            nd.append({'id':nid,'naam':(ch['naam'] if ch else g['naam']),'plaats':(ch['plaats'] if ch else g.get('plaats',''))})
        p['geholpen_door']=nd
    json.dump(people, open(_pp,'w',encoding='utf-8'), ensure_ascii=False)
    print(f"people.json geholpen_door bijgewerkt ({len(remap)} helpers samengevoegd)")
# geocode-todo
cache=json.load(open(os.path.join(HERE,'geocache.json'),encoding='utf-8'))
keys={h['key'] for h in out if h['key']}
todo=sorted(k for k in keys if k not in cache)
json.dump(todo, open(os.path.join(HERE,'geocode_helpers_todo.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=0)
plot=sum(1 for h in out if h['key'] and cache.get(h['key']))
print(f"helpers totaal: {len(out)} | met rol: {sum(1 for h in out if h['rol'])} | met 'hielp'-lijst: {sum(1 for h in out if h['n'])}")
print(f"plotbaar: {plot}/{len(out)} | nog te geocoden: {len(todo)}")
print("top 'hielp':", ', '.join(f"{h['naam']} ({h['n']})" for h in sorted(out,key=lambda x:-x['n'])[:6]))
