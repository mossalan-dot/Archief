import json,re,sys,random,collections
cab=json.load(open(sys.argv[1])); rx=re.compile(sys.argv[2],re.I); n=int(sys.argv[3])
S=[]
for x in cab:
    for s in re.split(r'(?<=[.!?])\s+',x['tekst']):
        if rx.search(s) and 40<len(s)<320: S.append((x['auteur'] or x['titel'][:20],s))
random.seed(1); random.shuffle(S); print(len(S))
for a,s in S[:n]: print(f'[{a}] {s}')
