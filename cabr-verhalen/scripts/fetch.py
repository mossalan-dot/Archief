import json,urllib.request,sys
out=[]
for p in range(0,20):
    body=json.dumps({"language":"nl","pillars":"Beleven","searchTerm":"","resultsPerPage":100,"page":p,"sortResults":"_score desc"}).encode()
    r=urllib.request.Request("https://www.nationaalarchief.nl/zoek/content/stories",data=body,headers={"Content-Type":"application/json"})
    d=json.load(urllib.request.urlopen(r))
    docs=d['documents']
    if not docs: break
    out+=docs
    print(p,len(docs),d['totalResults'],file=sys.stderr)
json.dump(out,open(sys.argv[1],'w'),ensure_ascii=False)
