# -*- coding: utf-8 -*-
"""Bouw data.json uit een harvest-steekproef + ijk op exacte jaartotalen (Breakdown).
Gebruik: python3 build_period.py <harvest.json> <y0> <y1>"""
import json,sys,os,collections,urllib.request
from geocode_full import geocode
HARV,Y0,Y1=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
UA="alanmoss-archiefkaart/1.0 (mossalan@gmail.com)"
V=json.load(open(HARV))
# exacte jaartotalen
def breakdown_year():
    u="https://api.openarch.nl/1.1/stats/breakdown.json?sourcetype=Passagiersregisters&group_by=year"
    d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA})))
    return {int(r['key']):r['count'] for r in d['results']}
EX=breakdown_year()

coords={}; voyages=[]; ships=collections.Counter()
samp_year=collections.Counter()          # steekproef: personen met Naar per jaar
tot=0; geoc=0; geoc_dir=collections.Counter(); misses=collections.Counter()
for v in V:
    y=v.get('year')
    d_am={}; d_eu={}                     # richting uit bestemmingsgeografie: Amerika=west, Europa=oost
    for naar,c in (v.get('naar') or {}).items():
        tot+=c
        if y: samp_year[y]+=c
        g=geocode(naar,'west')           # NA-voorkeur bij ambigue namen (emigratie domineert)
        if not g: g=geocode(naar,'east')
        if not g: misses[naar]+=c; continue
        place,la,lo,cc=g; geoc+=c
        coords.setdefault(place,[round(la,4),round(lo,4),cc])
        (d_am if lo<-20 else d_eu)[place]=(d_am if lo<-20 else d_eu).get(place,0)+c
    if sum(d_am.values())>=sum(d_eu.values()) and d_am: dr='west'; d=d_am
    elif d_eu: dr='east'; d=d_eu
    else: continue
    geoc_dir[dr]+=sum(d.values())
    if v.get('ship'): ships[v['ship']]+=sum(d.values())
    voyages.append({'s':v.get('ship'),'y':y,'dir':dr,'scan':v.get('scan'),'inv':v.get('invnr'),'d':d})
# ijkfactor per jaar = exact / steekproef(personen met Naar)
factor={y:(EX.get(y,0)/samp_year[y] if samp_year[y] else 0) for y in range(Y0,Y1+1)}
def slug(s):
    import re; return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',s.lower())).strip('-') or 'schip'
data={'meta':{'periode':f'{Y0}-{Y1}','sample_folios':len(voyages),
    'sample_personen':sum(v['n'] for v in V),
    'geocoded':geoc,'totaal':tot,'west_pers':geoc_dir['west'],'east_pers':geoc_dir['east'],
    'exact':{str(y):EX.get(y,0) for y in range(Y0,Y1+1)},
    'factor':{str(y):round(factor[y],2) for y in range(Y0,Y1+1)},
    'exact_som':sum(EX.get(y,0) for y in range(Y0,Y1+1))},
  'origin':{'west':[51.9244,4.4777],'east':[40.7128,-74.0060]},
  'coords':coords,'ships':[[s,n,slug(s)] for s,n in ships.most_common(80)],'voyages':voyages}
os.makedirs('site',exist_ok=True)
json.dump(data,open('site/data.json','w'),ensure_ascii=False)
# niet-gematchte namen wegschrijven (1 bestand = volledige huidige dataset, voor latere 2e check)
json.dump({'periode':f'{Y0}-{Y1}','misses':misses.most_common()},
    open('misses_current.json','w'),ensure_ascii=False,indent=1)
print(f"niet-gematcht: {sum(misses.values())} vermeldingen, {len(misses)} unieke -> misses_current.json")
print(f"folio's {len(voyages)} | schepen {len(ships)} | plaatsen {len(coords)} | geocoded {100*geoc/max(1,tot):.0f}% | west-pers {geoc_dir['west']} east-pers {geoc_dir['east']}")
print("ijkfactoren:",data['meta']['factor'])
print("bytes:",os.path.getsize('site/data.json'))
