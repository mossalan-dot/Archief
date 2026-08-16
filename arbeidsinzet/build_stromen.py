#!/usr/bin/env python3
"""Fase 1 — stroom-aggregatie Arbeidsinzet.
Leidt per invnr de bestemming (Kreis/gemeente/stad + zone + categorie) af uit de EAD,
koppelt aan de CSV-records, geocodeert de Duitse bestemmingen (Nominatim, met cache),
en schrijft geaggregeerde herkomst->bestemming-stromen weg voor de kaart.

Ethische regels in de data:
  - medisch  -> alleen plaats, nooit kliniek/afdeling (klinieknaam valt buiten output)
  - overlijden -> categorie meegegeven; markering kamp_nabij voor terughoudende weergave
"""
import re, csv, glob, json, time, random, collections, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

BASE = "/Users/alan/Downloads/arbeidsinzet"
EAD = f"{BASE}/inventaris-2.19.323.ead.xml"
CSVS = sorted(glob.glob(f"{BASE}/arbeitseinsatz/arbeitseinsatz_*.csv"))
GEOCACHE = f"{BASE}/geocode_cache.json"

def s(t): return re.sub(r'\{.*?\}', '', t)

CAMP_KREISE = {
    'dachau','buchenwald','sachsenhausen','oranienburg','neuengamme','flossenburg',
    'flossenbürg','bergen-belsen','ravensbruck','ravensbrück','mittelbau','nordhausen',
    'mauthausen','esterwegen','papenburg','emsland','wewelsburg','fallingbostel',
}

# ---------- 1. EAD -> invnr -> classificatie ----------
tree = ET.parse(EAD); root = tree.getroot()

def node_fields(c):
    invnr = title = None
    for ch in c:
        if s(ch.tag) == 'head' and title is None:
            title = ''.join(ch.itertext()).strip()
        if s(ch.tag) == 'did':
            for d in ch:
                if s(d.tag) == 'unitid':
                    v = (d.text or '').strip()
                    if d.get('type') is None and v.isdigit(): invnr = v
                if s(d.tag) == 'unittitle': title = ''.join(d.itertext()).strip()
    return invnr, title

leaves = {}
def walk(c, anc):
    invnr, title = node_fields(c)
    label = title or '·'
    if invnr and invnr.isdigit():
        leaves[invnr] = {"title": title or "", "ancestors": anc[:]}
    for ch in c:
        if s(ch.tag) == 'c': walk(ch, anc + [label])
for el in root.iter():
    if s(el.tag) == 'dsc':
        for ch in el:
            if s(ch.tag) == 'c': walk(ch, [])
        break

def classify(rec):
    title, anc = rec["title"], rec["ancestors"]
    blob = " > ".join(anc + [title]).lower()
    # categorieën: overlijden/medisch/huwelijk/geboorte apart; 'burgerlijke stand'
    # valt logisch onder 'arbeidsinzet (algemeen)'
    if re.search(r'ziekenh|krankenhaus|klinik|patient|patiënt|lazarett|heilanstalt|rontgen|röntgen|medisch', blob):
        cat = "medisch"
    elif re.search(r'overled|overlijden|gestorben|verstorben|sterbe|doden|begraf|begraben|friedhof|grave', blob):
        cat = "overlijden"
    elif re.search(r'huwelijk|heirat|trauung|eheschlie', blob):
        cat = "huwelijk"
    elif re.search(r'geboort|geburt', blob):
        cat = "geboorte"
    else:
        cat = "arbeidsinzet"
    mz = re.search(r'(amerikaanse|engelse|britse|russische|sovjet|franse)\s+zone', blob)
    zone = {"amerikaanse":"Amerikaanse","engelse":"Engelse","britse":"Engelse","russische":"Russische",
            "sovjet":"Russische","franse":"Franse"}.get(mz.group(1)) if mz else None
    def pick_kreis(text):                 # eerste échte Kreis-naam (geen zone-frase)
        for m in re.finditer(r'kreis\s+([a-zà-ÿ][a-zà-ÿ.\-/ ]*?)(?=,|;|$|\sgemeente|\sstadt|\s>)', text):
            cand = m.group(1).strip()
            if cand and not re.search(r'zone|werkzaam|woonachtig|nederland|verpleegd|overleden|geboren|gehuwd', cand):
                return cand
        return None
    kreis = pick_kreis(title.lower()) or pick_kreis(blob)   # leaf-titel gaat vóór ancestors
    mg = re.search(r'gemeente\s+([a-zà-ÿ][a-zà-ÿ.\-/ ]*?)(?=,|;|$|\s>)', blob)
    gemeente = mg.group(1).strip() if mg else None
    # stad uit medische tak: eerste ancestor onder de patiënten-serie (bv. 'Berlijn','Rottweil')
    stad = None
    for a in anc:
        al = a.lower()
        if a and a != '·' and 2 < len(a) < 26 and not re.search(
                r'nederland|patiënt|patient|status|lijst|kaart|zone|bestand|arbeider|overled|zijn |diverse|kreis', al):
            stad = a.strip(); break
    dest = kreis or gemeente or stad
    dest = (dest or "onbekend").title()
    kreis = kreis.title() if kreis else None
    kamp = any(c in (dest + " " + blob).lower() for c in CAMP_KREISE)
    return dict(categorie=cat, zone=zone, kreis=kreis, gemeente=(gemeente.title() if gemeente else None),
                bestemming=dest, kamp_nabij=kamp)

INV = {k: classify(v) for k, v in leaves.items()}

# ---------- 2. CSV inlezen -> aggregeren ----------
rx = re.compile(r'/invnr/(\d+)/')
origin = {}                       # bplace -> {records, lat, lon}
dest_stat = collections.defaultdict(lambda: {"records":0, "cat":collections.Counter(),
                                             "kreis":None,"zone":None,"kamp":False})
flows = collections.Counter()     # (bplace, dest) -> count
cat_tot = collections.Counter()
jaren = collections.Counter()     # geboorte-decennium -> aantal (gekoppelde records)
samples = collections.defaultdict(list)   # dest -> [{naam,jaar,plaats,id}]
seen_s = collections.Counter()            # dest -> aantal geschikte records (voor reservoir)
SAMPLE_CAP = 30
n_records = n_flow = 0
for path in CSVS:
    with open(path, encoding='utf-8') as fh:
        r = csv.DictReader(fh)
        for row in r:
            n_records += 1
            m = rx.search(row['scanid'] or '')
            info = INV.get(m.group(1)) if m else None
            if not info: continue
            cat_tot[info["categorie"]] += 1
            y = row['byear_st'].strip()[:4]
            if y.isdigit() and 1850 <= int(y) <= 1945: jaren[int(y)//10*10] += 1
            dest = info["bestemming"]
            ds = dest_stat[dest]
            ds["records"] += 1; ds["cat"][info["categorie"]] += 1
            ds["kreis"] = ds["kreis"] or info["kreis"]; ds["zone"] = ds["zone"] or info["zone"]
            ds["kamp"] = ds["kamp"] or info["kamp_nabij"]
            # steekproef individuele records (naam toegestaan: gepubliceerd = overleden)
            sn = row['sname'].strip(); fn = row['fname'].strip(); pl = row['bplace'].strip()
            clean = (sn and '?' not in sn and sn not in ('-','–') and '?' not in fn
                     and pl and row['id'].strip())     # alleen leesbare, complete records
            if clean and dest != "Onbekend":
                naam = " ".join(x for x in (fn, row['prefix'].strip(), sn) if x and x not in ('-','–'))
                rec = {"naam":naam, "jaar":row['byear_st'].strip(), "plaats":pl, "id":row['id'].strip()}
                lst = samples[dest]; seen_s[dest] += 1     # reservoir-sampling -> representatief
                if len(lst) < SAMPLE_CAP: lst.append(rec)
                else:
                    j = random.randint(0, seen_s[dest]-1)
                    if j < SAMPLE_CAP: lst[j] = rec
            bpl = row['bplace'].strip()
            ll = row['bplace_latlon'].strip()
            if bpl:
                o = origin.setdefault(bpl, {"records":0,"lat":None,"lon":None,"nl":False})
                o["records"] += 1
                if 'gemeentegeschiedenis.nl' in (row['bplace_uri'] or ''):
                    o["nl"] = True     # Nederlandse gemeente (vs. wikidata = buitenland)
                if ll and o["lat"] is None:
                    try:
                        la, lo = ll.split(","); o["lat"]=round(float(la),5); o["lon"]=round(float(lo),5)
                    except ValueError: pass
                if o["lat"] is not None and dest != "Onbekend":
                    flows[(bpl, dest)] += 1; n_flow += 1

print(f"records verwerkt: {n_records:,} | in stroom bruikbaar: {n_flow:,}")
print(f"unieke herkomstplaatsen: {len(origin):,} | unieke bestemmingen: {len(dest_stat):,}")

# ---------- 3. Bestemmingen geocoderen (Nominatim, met cache) ----------
try:
    with open(GEOCACHE, encoding='utf-8') as fh: cache = json.load(fh)
except FileNotFoundError:
    cache = {}

NIET_PLAATS = re.compile(r'dossier|personeel|stukken|kaartsysteem|namenlijst|onbekend', re.I)

def _query(term):
    q = urllib.parse.quote(f"{term}, Deutschland")
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent":"arbeidsinzet-kaart/1.0 (mossalan@gmail.com)"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    time.sleep(1.1)                # Nominatim fair-use: max 1/sec
    return [round(float(data[0]["lat"]),5), round(float(data[0]["lon"]),5)] if data else None

def variants(name):
    yield name
    if 'ü' in name.lower(): yield re.sub('ü','ö',name); yield re.sub('Ü','Ö',name)
    # compound "X en Y" / "X-Holstein" -> eerste deel; suffix "Stadt" weg
    first = re.split(r'\s+en\s+|\s+En\s+|/', name)[0].strip()
    if first != name: yield first
    base = re.sub(r'\s+(stadt|land)$','',first,flags=re.I).strip()
    if base != first: yield base
    base2 = re.sub(r'-holstein$','',base,flags=re.I).strip()
    if base2 != base: yield base2

def geocode(name):
    if name in cache: return cache[name]
    res = None
    if not NIET_PLAATS.search(name):
        for v in dict.fromkeys(variants(name)):     # unieke varianten, volgorde behouden
            try:
                res = _query(v)
            except Exception as e:
                print("  geocode-fout", v, e); res = None
            if res: break
    cache[name] = res
    with open(GEOCACHE, "w", encoding='utf-8') as fh: json.dump(cache, fh, ensure_ascii=False)
    return res

# bestemmingen met genoeg records; herprobeer ook eerdere mislukkingen (None in cache)
todo = [d for d,st in dest_stat.items()
        if d != "Onbekend" and st["records"] >= 25 and cache.get(d) is None
        and not NIET_PLAATS.search(d)]
print(f"te (her)geocoderen bestemmingen (>=25 records, geen coord): {len(todo)}")
for i,d in enumerate(sorted(todo),1):
    if d in cache: del cache[d]      # forceer nieuwe poging met varianten
    geocode(d)
    if i%20==0: print(f"  {i}/{len(todo)} geocoded")

# ---------- 4. Wegschrijven ----------
destinations = []
for d, st in dest_stat.items():
    if d == "Onbekend": continue
    coord = cache.get(d)
    destinations.append({"naam":d, "kreis":st["kreis"], "zone":st["zone"],
                         "kamp_nabij":st["kamp"], "records":st["records"],
                         "lat":coord[0] if coord else None, "lon":coord[1] if coord else None,
                         "categorieen":dict(st["cat"]),
                         "voorbeelden":samples.get(d, [])})
destinations.sort(key=lambda x:-x["records"])

# stromen: alleen waar bestemming geocodeerd is en herkomst coords heeft, drempel >=3
dest_coord = {d["naam"]:(d["lat"],d["lon"]) for d in destinations if d["lat"] is not None}
flow_out = []
for (bpl,dest),cnt in flows.items():
    if cnt < 3: continue
    o = origin.get(bpl); dc = dest_coord.get(dest)
    if not o or o["lat"] is None or not dc: continue
    flow_out.append({"van":bpl,"o_lat":o["lat"],"o_lon":o["lon"],
                     "naar":dest,"d_lat":dc[0],"d_lon":dc[1],"n":cnt})
flow_out.sort(key=lambda x:-x["n"])

# NL = zeker (gemeentegeschiedenis-URI) OF binnen NL-bbox, met uitsluiting van grote
# buitenlandse grenssteden op NL-lengtegraad en het generieke "Nederland".
FOREIGN = {'nederland','aken','aachen','düsseldorf','dusseldorf','duisburg','essen','keulen','köln',
           'koln','krefeld','mönchengladbach','moenchengladbach','antwerpen','wesel','emmerik','emmerich','kleef'}
def final_nl(name, v):
    if v["nl"]: return True
    if name.lower() in FOREIGN: return False
    return 50.6 <= v["lat"] <= 53.6 and 3.3 <= v["lon"] <= 7.25
origins_out = [{"naam":k,"lat":v["lat"],"lon":v["lon"],"records":v["records"],"nl":final_nl(k,v)}
               for k,v in origin.items() if v["lat"] is not None and v["records"]>=3]
origins_out.sort(key=lambda x:-x["records"])

with open(f"{BASE}/kaart_data.json","w",encoding='utf-8') as fh:
    json.dump({"per_categorie":dict(cat_tot),
               "bestemmingen":destinations,
               "herkomst":origins_out,
               "stromen":flow_out,
               "geboortejaren":dict(sorted(jaren.items())),
               "meta":{"records_totaal":n_records,"stroom_records":n_flow,
                       "gekoppeld":sum(cat_tot.values()),
                       "unieke_herkomst":len(origins_out),
                       "bron":"Nationaal Archief 2.19.323 (CC-0)"}},
              fh, ensure_ascii=False)
print(f"\ngeschreven: kaart_data.json")
print(f"  bestemmingen: {len(destinations)} (gegeocodeerd: {sum(1 for d in destinations if d['lat'])})")
print(f"  herkomstpunten: {len(origins_out)} | stromen (>=3): {len(flow_out)}")
