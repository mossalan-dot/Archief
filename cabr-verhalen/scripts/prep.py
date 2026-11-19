import json,re,html,sys
d=json.load(open(sys.argv[1]))
def t(x): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',' '.join(x.get('body') or []))).replace('\xa0',' ')).strip()
cab=[];ref=[]
for x in d:
    s=x['_source']; cat=s.get('field_story_category') or []
    txt=t(s)
    if not txt: continue
    rec=dict(titel=(s.get('title') or [''])[0],auteur=(s.get('field_author') or [''])[0],plaats=(s.get('field_location') or [''])[0],
             created=(s.get('created') or [0])[0],url=(s.get('url') or [''])[0],type=(s.get('field_story_type') or [''])[0],
             intro=re.sub('<[^>]+>','',html.unescape(' '.join(s.get('field_introtext') or []))).strip(),tekst=txt,cat=cat)
    (cab if "Kinderen over 'foute' ouders" in cat else ref if cat else []).append(rec)
json.dump(cab,open(sys.argv[2],'w'),ensure_ascii=False); json.dump(ref,open(sys.argv[3],'w'),ensure_ascii=False)
print(len(cab),len(ref))
