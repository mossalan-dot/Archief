# -*- coding: utf-8 -*-
import csv,re,os,json,unicodedata
BASE=os.path.dirname(os.path.abspath(__file__)); GEO=os.path.join(BASE,'geo')
def deacc(s): return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn')
# --- admin1 code -> naam ---
adm={}
for ln in open(os.path.join(GEO,'admin1.txt'),encoding='utf-8'):
    p=ln.rstrip('\n').split('\t')
    if len(p)>=2: adm[p[0]]=p[1]           # "CA.08" -> "Ontario"
# --- GeoNames steden ---
by_city_region={}; by_city={}; by_city_na={}
with open(os.path.join(GEO,'cities1000.txt'),encoding='utf-8') as f:
    for row in csv.reader(f,delimiter='\t'):
        try:
            name=row[1]; asc=row[2]; lat=float(row[4]); lon=float(row[5])
            cc=row[8]; a1=adm.get(cc+'.'+row[10],''); pop=int(row[14] or 0)
        except Exception: continue
        for nm in {name.lower(), asc.lower(), deacc(name.lower())}:
            k=(nm,a1.lower())
            if k not in by_city_region or pop>by_city_region[k][3]: by_city_region[k]=[lat,lon,cc,pop,name]
            if nm not in by_city or pop>by_city[nm][3]: by_city[nm]=[lat,lon,cc,pop,name]
            if cc in ('US','CA') and (nm not in by_city_na or pop>by_city_na[nm][3]): by_city_na[nm]=[lat,lon,cc,pop,name]
# --- gecureerde havens/steden (override, ook voor ambigue namen) ---
C={
 'New York':[40.7128,-74.0060,'US'],'Quebec':[46.8139,-71.2080,'CA'],'Halifax':[44.6488,-63.5752,'CA'],
 'Montreal':[45.5019,-73.5674,'CA'],'Rotterdam':[51.9244,4.4777,'NL'],'Southampton':[50.9097,-1.4044,'GB'],
 'Le Havre':[49.4944,0.1079,'FR'],'London (UK)':[51.5074,-0.1278,'GB'],'Parijs':[48.8566,2.3522,'FR'],
 'Boulogne':[50.7264,1.6139,'FR'],'Boston':[42.3601,-71.0589,'US'],'Hoboken':[40.7439,-74.0324,'US'],
 'Fort William':[48.3809,-89.2477,'CA'],'Port Arthur':[48.4001,-89.2333,'CA'],'Sudbury':[46.4917,-80.9930,'CA'],
 # Europese exonymen (retour + vroege periode)
 'Den Haag':[52.0705,4.3007,'NL'],'Antwerpen':[51.2194,4.4025,'BE'],'Brussel':[50.8503,4.3517,'BE'],
 'Wenen':[48.2082,16.3738,'AT'],'Kopenhagen':[55.6761,12.5683,'DK'],'Berlijn':[52.5200,13.4050,'DE'],
 'München':[48.1351,11.5820,'DE'],'Zürich':[47.3769,8.5417,'CH'],'Keulen':[50.9375,6.9603,'DE'],
 'Frankfurt':[50.1109,8.6821,'DE'],'Praag':[50.0755,14.4378,'CZ'],'Milaan':[45.4642,9.1900,'IT'],
 'Genève':[46.2044,6.1432,'CH'],'Hamburg':[53.5511,9.9937,'DE'],'Bremen':[53.0793,8.8017,'DE'],
 'Warschau':[52.2297,21.0122,'PL'],'Boedapest':[47.4979,19.0402,'HU'],'Stockholm':[59.3293,18.0686,'SE'],
 'Lissabon':[38.7223,-9.1393,'PT'],'Rome':[41.9028,12.4964,'IT'],'Napels':[40.8518,14.2681,'IT'],
 'Genua':[44.4056,8.9463,'IT'],'Triëst':[45.6495,13.7768,'IT'],
 # Midden/Oost-Europese exonymen + historische namen (retourmigratie, vroege periode)
 'Krakau':[50.0647,19.9450,'PL'],'Posen':[52.4064,16.9252,'PL'],'Lemberg':[49.8397,24.0297,'UA'],
 'Agram':[45.8150,15.9819,'HR'],'Thorn':[53.0138,18.5984,'PL'],'Kaschau':[48.7164,21.2611,'SK'],
 'Tilsit':[55.0806,21.8853,'RU'],'Allenstein':[53.7784,20.4801,'PL'],'Tarnopol':[49.5535,25.5948,'UA'],
 'Ostrowo':[51.6549,17.8107,'PL'],'Myslowitz':[50.2415,19.1664,'PL'],'Breslau':[51.1079,17.0385,'PL'],
 'Kattowitz':[50.2649,19.0238,'PL'],'Danzig':[54.3520,18.6466,'PL'],'Stettin':[53.4285,14.5528,'PL'],
 'Königsberg':[54.7104,20.4522,'RU'],'Bromberg':[53.1235,18.0084,'PL'],'Gnesen':[52.5348,17.5826,'PL'],
 'Czernowitz':[48.2921,25.9358,'UA'],'Pressburg':[48.1486,17.1077,'SK'],'Czenstochau':[50.8118,19.1203,'PL'],
 'Lodz':[51.7592,19.4560,'PL'],'Mielec':[50.2874,21.4237,'PL'],'Hermannstadt':[45.7983,24.1256,'RO'],
 # spoorgrensstations van de transmigratie
 'Oderberg':[49.9241,18.2902,'CZ'],'Eydtkuhnen':[54.6417,22.7503,'RU'],'Prostken':[53.6976,22.4194,'PL'],
 'Illowo':[53.5000,20.3000,'PL'],'Alexandrowo':[52.8718,18.6960,'PL'],'Ottlotschin':[52.8300,18.6000,'PL'],
 'Sosnowitz':[50.2863,19.1040,'PL'],
 # overige exonymen
 'Londres':[51.5074,-0.1278,'GB'],'Belgrado':[44.7866,20.4489,'RS'],'Kristiania':[59.9139,10.7522,'NO'],
 'Christiania':[59.9139,10.7522,'NO'],'Bazel':[47.5596,7.5886,'CH'],'Basel':[47.5596,7.5886,'CH'],
 'Straatsburg':[48.5734,7.7521,'FR'],'Boekarest':[44.4268,26.1025,'RO'],'Wilna':[54.6872,25.2797,'LT'],
 'Laibach':[46.0569,14.5058,'SI'],'Insterburg':[54.6510,21.8180,'RU'],'Temesvar':[45.7489,21.2087,'RO'],
 'Bajohren':[55.2833,21.2500,'LT'],'Nürnberg':[49.4521,11.0767,'DE'],
 # jaren 1920: Spaanse aanloophaven + Mexico-lijn + Midden-Europese grensstations
 'La Coruña':[43.3623,-8.4115,'ES'],'Veracruz':[19.1903,-96.1533,'MX'],'Habana':[23.1136,-82.3666,'CU'],
 'Vigo':[42.2406,-8.7207,'ES'],'Santander':[43.4623,-3.8100,'ES'],'Bilbao':[43.2630,-2.9350,'ES'],
 'Bodenbach':[50.7742,14.2046,'CZ'],'Bentschen':[52.2450,15.9070,'PL'],'Lundenburg':[48.7589,16.8820,'CZ'],
 'South Bethlehem':[40.6120,-75.3705,'US'],'Cobh':[51.8503,-8.2943,'IE'],
}
CA={
 'Hal.':'Halifax','Mo.':'Montreal','Qu.':'Quebec','Qeubec':'Quebec','Sou.':'Southampton','S.F.':'San Francisco',
 'Leh.':'Le Havre','Le Hâvre':'Le Havre','Paris':'Parijs','London Engel.':'London (UK)','Boulogne s/mer':'Boulogne',
 'N.Y.':'New York','N.Y':'New York','Phila.':'Philadelphia','Munchen':'München','Muenchen':'München','Zurich':'Zürich',
 "'s-Gravenhage":'Den Haag','Scheveningen':'Den Haag','Napoli':'Napels','Genoa':'Genua',
 'Geneve':'Genève','Kopenhaguen':'Kopenhagen','Weenen':'Wenen','iIllowo':'Illowo',
 'Crakau':'Krakau','Krakow':'Krakau','Posen (Duitschland)':'Posen','Warschau (Rusland)':'Warschau',
 "'s Gravenhage":'Den Haag','Coruña':'La Coruña','Coruna':'La Coruña','A Coruña':'La Coruña',
 'Vera-Cruz':'Veracruz','Vera Cruz':'Veracruz','V. Cruz':'Veracruz','Havana':'Habana','Havanna':'Habana',
}
# Passagestaten-afkortingen (1950-69) -> volledige havennaam; hoog-vertrouwen, uit schip/route-correlatie
# (N=New York, Mo/Mon=Montreal, Hal/Ha=Halifax, Qu/Q=Quebec, So=Southampton). Ambigue S./L./C./H./M. NIET.
CODE_DECODE={'N.':'New York','Mo.':'Montreal','Mon.':'Montreal','Hal.':'Halifax','Ha.':'Halifax',
 'Qu.':'Quebec','Q.':'Quebec','So.':'Southampton','Hob.':'Hoboken','Cob.':'Cobh'}
SUFFIX=re.compile(r'\s*[,\s](Frankr\.?|Frankrijk|Fr\.?|France|Eng\.?|Engeland|England|Duitsl\.?|Duitsland|Germany|Belg\.?|Belgie|België|Ned\.?|Nederl\.?|Nederland|Zwits\.?|Zwitserland|It\.?|Italie|Italië|Am\.?|Schotland|Schotl\.?|Ierland|Ierl\.?)\.?$',re.I)
REGION={'ontario':'Ontario','quebec':'Quebec','québec':'Quebec','alberta':'Alberta','manitoba':'Manitoba',
 'british columbia':'British Columbia','saskatchewan':'Saskatchewan','nova scotia':'Nova Scotia',
 'new brunswick':'New Brunswick'}
DROP=re.compile(r'^(westbound|eastbound|\?+|onbekend|n\.?|s\.?|m\.?|)$',re.I)

def geocode(naar, direction='west'):
    s=(naar or '').strip()
    s=CODE_DECODE.get(s,s)                      # Passagestaten-afkortingen decoderen
    if DROP.match(s): return None
    s=SUFFIX.sub('',s).strip()                 # "Parijs Frankr." -> "Parijs"
    s=CA.get(s,s)
    if s in ('London','Londen'): s='London (UK)' if direction!='west' else 'London (ON)'
    if s=='London (ON)':
        v=by_city_region.get(('london','ontario'));  return _mk('London (ON)',v) if v else None
    if s in C: la,lo,cc=C[s]; return (s,la,lo,cc)
    city=s; region=''
    if ',' in s:
        parts=[x.strip() for x in s.split(',')]
        city=CA.get(parts[0],parts[0]); region=parts[-1]
    # curated na komma-split
    if city in C: la,lo,cc=C[city]; return (city,la,lo,cc)
    rl=region.lower()
    for cand in _vars(city):
        cl=cand.lower()
        v=by_city_region.get((cl,REGION.get(rl,region).lower())) or by_city_region.get((cl,region.lower()))
        if v: return _mk(cand,v)
    if direction=='west':                       # emigratie: VS/Canada voorrang bij ambigue namen
        for cand in _vars(city):
            v=by_city_na.get(cand.lower())
            if v: return _mk(v[4],v)
    for cand in _vars(city):
        v=by_city.get(cand.lower())
        if v: return _mk(v[4],v)
    return None
def _vars(c):                                   # St./Saint/So.-varianten + accentloos
    out=[c]; low=c.lower()
    if low.startswith('so. '): out.append('South '+c[4:])
    elif low.startswith('st. '): out.append('Saint '+c[4:])
    elif low.startswith('st '): out.append('Saint '+c[3:])
    elif low.startswith('saint '): out.append('St. '+c[6:]); out.append('St '+c[6:])
    if ' st. ' in low: out.append(re.sub(r'\bSt\.?\b','Saint',c))   # Sault St. Marie -> Sault Saint Marie
    for x in list(out):
        d=deacc(x)
        if d!=x: out.append(d)
    return out
def _mk(label,v): return (label, v[0], v[1], v[2])

if __name__=='__main__':
    V=json.load(open('harvest_voyages.json'))
    import collections
    tot=collections.Counter(); ok=collections.Counter(); miss=collections.Counter()
    for vv in V:
        for naar,c in (vv.get('naar') or {}).items():
            tot[vv['dir']]+=c
            g=geocode(naar,vv['dir'])
            if g: ok[vv['dir']]+=c
            else: miss[naar]+=c
    for d in ('west','east'):
        print(f"{d}: {ok[d]}/{tot[d]} = {100*ok[d]/max(1,tot[d]):.0f}% geocoded")
    print("top missers:",miss.most_common(20))
