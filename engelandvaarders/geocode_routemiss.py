import json,time,re,urllib.parse,urllib.request
G=json.load(open("geocache.json"))
miss=[k for k,v in G.items() if not v]
UA="engelandvaarders-kaart/1.0 (mossalan@gmail.com)"
def parse(k):
    if '\n' in k or '[' in k: return None,None
    if '|' in k: p,land=k.split('|',1)
    else: p,land=k,''
    p=re.sub(r'\s*\([^)]*\)','',p).strip()
    return p,land.strip()
def geo(q):
    url="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode({"q":q,"format":"json","limit":1})
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA})
        d=json.load(urllib.request.urlopen(req,timeout=30))
        if d: return {"lat":float(d[0]["lat"]),"lon":float(d[0]["lon"]),"display":d[0].get("display_name","")}
    except: pass
    return None
rec=0
for i,k in enumerate(miss):
    p,land=parse(k)
    if not p: continue
    q=f"{p}, {land}" if land and land!=p else p
    r=geo(q)
    if r: G[k]=r; rec+=1
    if i%20==0: json.dump(G,open("geocache.json","w",encoding="utf-8"),ensure_ascii=False)
    time.sleep(1.05)
json.dump(G,open("geocache.json","w",encoding="utf-8"),ensure_ascii=False)
print("hersteld:",rec)
