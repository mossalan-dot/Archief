import json,urllib.request,urllib.parse,time,random,sys,re,collections
UA="alanmoss-archiefkaart/1.0 (mossalan@gmail.com; onderzoek HAL passagierslijsten)"
Y0,Y1,CAP,OUT=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
def get(url):
    r=urllib.request.Request(url,headers={'User-Agent':UA})
    for _ in range(4):
        try:
            with urllib.request.urlopen(r,timeout=45) as x: return json.load(x)
        except Exception: time.sleep(1.3)
    return None
B="https://api.openarch.nl/1.1/records"
names=["Jansen","de Vries","van Dijk","Bakker","Visser","Smit","Meijer","de Boer","Mulder","Bos","Peters","Dekker",
 "Muller","Schmidt","Schneider","Fischer","Weber","Wagner","Becker","Hoffmann","Koch","Bauer","Meyer","Wolf",
 "Kowalski","Nowak","Wisniewski","Kaminski","Lewandowski","Zielinski","Wojcik",
 "Rossi","Russo","Ferrari","Esposito","Bianchi","Romano",
 "Cohen","Levi","Goldberg","Rosenberg","Katz","Klein","Friedman","Schwartz","Kaplan",
 "Johnson","Smith","Brown","Anderson","Williams","Miller","Jones","Davis",
 "Nielsen","Hansen","Larsen","Petersen","Andersson","Johansson","Nilsson",
 "Novak","Horvath","Popovic","Ivanov","Petrov","Sokolov","Garcia","Martinez","Gonzalez","Rodriguez",
 "Kelly","Murphy","OBrien","Petersson","Berg","Lind","Olsen",
 "van der Berg","van Leeuwen","de Jong","Hendriksen","Willemsen","Timmermans","Scholten","Prins","Postma","Kuipers",
 "Schulz","Hoffman","Krause","Lange","Werner","Krüger","Hartmann","Zimmermann","Braun","Neumann",
 "Wojciechowski","Kozlowski","Jankowski","Mazur","Krawczyk","Kaczmarek","Piotrowski","Grabowski",
 "Marino","Greco","Conti","Ricci","Costa","Gallo","Bruno",
 "Levine","Weiss","Gross","Adler","Stein","Roth","Berkowitz","Feldman",
 "Wilson","Taylor","Thomas","Roberts","Evans","Walker","White","Clark",
 "Hansson","Karlsson","Eriksson","Pettersson","Jensen","Christensen","Sorensen",
 "Kovacs","Toth","Nagy","Balog","Dimitrov","Georgiev","Stojanovic","Markovic","Fernandez","Lopez","Perez","Sanchez"]
folios={}
for nm in names:
    u=f"{B}/search.json?name={urllib.parse.quote(nm)}&archive=srt&sourcetype=Passagiersregisters&number_show=1500&lang=nl"
    d=get(u); time.sleep(0.28)
    for doc in (d or {}).get('response',{}).get('docs',[]) or []:
        y=(doc.get('eventdate') or {}).get('year')
        if y and Y0<=int(y)<=Y1: folios[doc['identifier']]=1
print(f"unieke folio's {Y0}-{Y1}: {len(folios)}",flush=True)
def shipclean(s): return (re.sub(r'\s*\(.*?\)\s*$','',s).strip() or None) if s else None
def parseline(b):
    m=re.search(r'lijn\s+(.+?)\s*\(?(westbound|eastbound)?\)?\s*:',b,re.I)
    return (m.group(1).strip(), (m.group(2) or '').lower() or None) if m else (None,None)
ids=list(folios); random.seed(2); random.shuffle(ids); ids=ids[:CAP]
V=[]; done=0
for gid in ids:
    d=get(f"{B}/show.json?archive=srt&identifier={gid}"); time.sleep(0.26+random.random()*0.05)
    if not d or 'Person' not in d: continue
    P=d['Person']; P=P if isinstance(P,list) else [P]
    ev=d.get('Event') or {}; src=d.get('Source') or {}; ref=src.get('SourceReference') or {}
    date=ev.get('EventDate') or {}; ship=shipclean((ev.get('EventRemark') or {}).get('Value'))
    dep=(ev.get('EventPlace') or {}).get('Place'); line,dr=parseline(ref.get('Book') or '')
    if not dr: dr='west' if (dep or '')=='Rotterdam' else 'east'
    sc=(src.get('SourceAvailableScans') or {}).get('Scan') or {}
    if isinstance(sc,list): sc=sc[0] if sc else {}
    nc=collections.Counter()
    for p in P:
        rem={r.get('@Key'):(r.get('Value') or '').strip() for r in (p.get('PersonRemark') or []) if isinstance(r,dict)}
        if rem.get('Naar'): nc[rem['Naar']]+=1
    V.append({"guid":gid,"year":int(date['Year']) if date.get('Year') else None,"dep":dep,"ship":ship,
        "dir":dr,"invnr":ref.get('RegistryNumber'),"n":len(P),"naar":dict(nc),
        "scan":sc.get('UriViewer') or sc.get('Uri'),"handle":src.get('SourceDigitalOriginal')})
    done+=1
    if done%250==0: print("getoond",done,flush=True)
json.dump(V,open(OUT,'w'),ensure_ascii=False)
print(f"KLAAR {OUT}: folio's {len(V)} personen {sum(v['n'] for v in V)}",flush=True)
