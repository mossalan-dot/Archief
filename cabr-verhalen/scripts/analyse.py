import json,re,collections,math,sys
cab=json.load(open(sys.argv[1])); ref=json.load(open(sys.argv[2]))
def norm(s): return s.lower().replace('’',"'").replace('‘',"'")
def verteller(x):
    a=x['auteur'].strip()
    return a if a and a not in ('Diverse bezoekers',) else 'anon:'+x['titel']
# thema's: label -> regex (op woordgrenzen, lowercase)
TH={
 'Emoties':{
  'schaamte':r'\bscha(amte|amt|amde|amden|men|mend)\w*|\bbeschaamd\w*',
  'schuld(gevoel)':r'\bschuld(gevoel\w*|ig\w*)?\b|\bschuldbewust',
  'angst':r'\bangst\w*|\bbang\b|\bbange\b|\bvrees\w*|\bdoodsbang',
  'woede / boosheid':r'\bwoede\w*|\bwoedend\w*|\bboos\b|\bboze\b|\bboosheid|\bkwaad\b|\bkwade\b',
  'verdriet':r'\bverdriet\w*|\bhuil\w*|\bhuilde\w*|\btranen\b|\bgehuild',
  'eenzaamheid':r'\beenza(am|me|amheid)\w*|\balleen\s+(gelaten|op\s+de\s+wereld)',
  'haat / afkeer':r'\bhaat\b|\bhaatte\w*|\bgehaat\w*|\bverafschuw\w*|\bafkeer\b|\bwalg\w*',
  'liefde':r'\bliefde\w*|\bliefdevol\w*|\bhield\s+(veel\s+)?van\b|\bhou\s+van\b',
  'loyaliteit':r'\bloya\w*|\btrouw\b',
  'onbegrip / verwarring':r'\bbegreep\s+(niet|er\s+niets)|\bsnap\w*\s+niet|\bverwar\w*|\bonbegrip',
  'begrip':r'\bbegrip\b|\bbegrijp\w*\s+(nu|wel|hem|haar|het)',
  'vergeving / verzoening':r'\bverge(ef|ven|ving|eft)\w*|\bverzoen\w*',
  'opluchting / rust':r'\bopluchting|\bopgelucht|\brust\s+gevonden|\bvrede\b',
  'trauma / therapie':r'\btrauma\w*|\btherap\w*|\bpsychiat\w*|\bpsycholo\w*|\bdepress\w*',
  'trots':r'\btrots\w*',
 },
 'Zwijgen & spreken':{
  'zwijgen':r'\bzwijg\w*|\bzweeg\w*|\bgezwegen|\bstilzwijg\w*',
  'geheim':r'\bgeheim\w*',
  'taboe':r'\btaboe\w*',
  'er werd niet over gepraat':r'(niet|nooit)\s+(over\s+)?(ge)?(praat|sprak|spreken|gesproken|verteld|vertelde)',
  'vragen stellen':r'\bvragen\s+(stellen|gesteld)|\bdurfde\s+(niet\s+)?te\s+vragen',
 },
 'Stigma & uitsluiting':{
  'gepest / uitgescholden':r'\bgepest|\bpest\w*|\buitgescholden|\bscheld\w*|\bnageroepen|\bjouw\s+vader',
  "scheldwoorden (moffen-, NSB-kind, landverrader)":r'\bmoffen\w*|\bnsb-?(kind|jong|jongetje|meisje|kinderen)\w*|\blandverrader\w*|\bverraders?\b|\bfoute\s+kind\w*',
  'buitengesloten / anders':r'\bbuitengesloten|\buitgestoten|\bbuitenstaander|\bparia|\banders\s+dan\s+(de\s+)?anderen|\bniet\s+(meer\s+)?mocht\s+spelen',
  'school / juf / meester':r'\bschool\w*|\bjuf\b|\bjuffrouw|\bmeester\b|\bonderwijzer\w*|\bklas\b',
 },
 'Gebeurtenissen na 1945':{
  'arrestatie / opgepakt':r'\bgearresteerd|\barrestatie|\bopgepakt|\bweggehaald|\bmeegenomen',
  'kamp / internering':r'\binterner\w*|\bkamp\b|\bkampen\b|\bkamp\s+\w+|\bgevangen\w*|\bgevangenis|\bcel\b',
  'kaalgeschoren / Dolle Dinsdag / Bijltjesdag':r'\bkaalgeschoren|\bkaal\s+geschoren|\bdolle\s+dinsdag|\bbijltjesdag|\bmoffenmeid\w*',
  'tehuis / pleeggezin':r'\btehuis\w*|\bkindertehuis|\bweeshuis|\bpleeg\w*|\bondergebracht|\bstichting\s+toezicht|\bkinderhuis',
  'proces / tribunaal / veroordeeld':r'\btribunaal|\bveroordeel\w*|\bveroordeling|\bvonnis|\bbijzondere\s+rechtspleging|\brechtspleging|\bstraf\b|\bproces\b',
  'bezit afgenomen / armoede':r'\bin\s+beslag|\bbeslag\s+genomen|\bnbm\b|\barmoede|\bgeconfisqueerd|\bonteigend',
  'emigratie':r'\bemigr\w*|\bcanada|\baustrali\w*|\bzuid-afrika',
 },
 'De "foute" daad':{
  'NSB':r'\bnsb\w*|\bnationaal-?socialis\w*',
  'Waffen-SS / Oostfront':r'\bss\b|\bwaffen\w*|\boostfront|\brusland\b|\bstalingrad',
  'Jeugdstorm / Hitlerjugend':r'\bjeugdstorm\w*|\bhitlerjugend|\bhitler\s+jugend|\bhajo\w*',
  'Landwacht / politie':r'\blandwacht\w*|\bpolitie\w*|\bmarechaussee',
  'collaboratie / verraad':r'\bcollabor\w*|\bverra(ad|den|dde|dden)\w*|\baangegeven\b',
  'Joden / Jodenvervolging':r'\bjo(o)?d(en|se|s|e)?\b|\bjodenvervolging|\bholocaust|\bshoah',
  'Duits(er) / Duitsland':r'\bduits\w*|\bmof\b',
  'verzet (als contrast)':r'\bverzet\w*|\bonderduik\w*|\bondergedoken',
 },
 'Zoeken & weten':{
  'archief / CABR / dossier':r'\barchief\w*|\bcabr\b|\bdossier\w*|\bnationaal\s+archief|\binzien\b|\bingezien',
  'Werkgroep Herkenning / lotgenoten':r'\bherkenning\b|\bwerkgroep\b|\blotgeno\w*|\bgespreksgroep\w*',
  'brieven / dagboek / foto':r'\bbrie(f|ven)\w*|\bdagboek\w*|\bfoto\w*|\bschrift\w*',
  'waarheid / weten':r'\bwaarheid\w*|\bwilde\s+(het\s+)?weten|\bte\s+weten\s+komen|\bontdek\w*',
 },
}
# familie wie was fout
FAM={'vader':r'\b(mijn|onze|zijn|haar)\s+(vader|pa|papa|pappa|pappie)\b','moeder':r'\b(mijn|onze|zijn|haar)\s+(moeder|ma|mama|mamma|mammie)\b',
     'opa / grootvader':r'\b(mijn|onze)\s+(opa|grootvader)\b','oma / grootmoeder':r'\b(mijn|onze)\s+(oma|grootmoeder)\b','oom/tante':r'\b(mijn|onze)\s+(oom|tante)\b'}
def tok(s): return re.findall(r"[a-zà-ÿ][a-zà-ÿ'\-]*",norm(s))
words=sum(len(x['tekst'].split()) for x in cab)
vt=collections.defaultdict(str)
for x in cab: vt[verteller(x)]+=' '+x['tekst']
res={'n_verhalen':len(cab),'n_vertellers':len(vt),'woorden':words,'themas':{}}
for grp,d in TH.items():
    out=[]
    for lab,rx in d.items():
        R=re.compile(rx)
        hits=[len(R.findall(norm(x['tekst']))) for x in cab]
        vh=sum(1 for t in vt.values() if R.search(norm(t)))
        refhits=sum(len(R.findall(norm(x['tekst']))) for x in ref); refw=sum(len(x['tekst'].split()) for x in ref)
        out.append(dict(label=lab,totaal=sum(hits),verhalen=sum(1 for h in hits if h),vertellers=vh,
             per10k=round(sum(hits)/words*1e4,1),ref_per10k=round(refhits/refw*1e4,1)))
    res['themas'][grp]=out
# familie
fam=[]
for lab,rx in FAM.items():
    R=re.compile(rx); fam.append(dict(label=lab,verhalen=sum(1 for x in cab if R.search(norm(x['tekst']))),totaal=sum(len(R.findall(norm(x['tekst']))) for x in cab)))
res['familie']=fam
# 'fout' tussen aanhalingstekens
res['fout_aanhalingstekens']=sum(len(re.findall(r"['\"“”]fout(e|en)?['\"“”]",norm(x['tekst']))) for x in cab)
res['fout_totaal']=sum(len(re.findall(r"\bfout(e|en)?\b",norm(x['tekst']))) for x in cab)
# log-likelihood onderscheidende woorden
STOP=set(open(sys.argv[3]).read().split())
ca=collections.Counter(w for x in cab for w in tok(x['tekst'])); cb=collections.Counter(w for x in ref for w in tok(x['tekst']))
na,nb=sum(ca.values()),sum(cb.values())
dfv=collections.Counter(w for t in vt.values() for w in set(tok(t)))
ll=[]
for w,a in ca.items():
    if a<15 or w in STOP or len(w)<3 or dfv[w]<6: continue
    b=cb.get(w,0); e1=na*(a+b)/(na+nb); e2=nb*(a+b)/(na+nb)
    g=2*(a*math.log(a/e1)+(b*math.log(b/e2) if b else 0))
    if a/na>b/nb: ll.append((round(g,1),w,a,b,dfv[w]))
ll.sort(reverse=True); res['kenmerkend']=[dict(woord=w,ll=g,n=a,ref=b,vertellers=v) for g,w,a,b,v in ll[:120]]
# meestgebruikte inhoudswoorden
res['frequent']=[dict(woord=w,n=n,vertellers=dfv[w]) for w,n in ca.most_common(2000) if w not in STOP and len(w)>2][:150]
# positie in verhaal: emotie in eerste vs laatste derde
pos={}
for lab in ['schaamte','angst','woede / boosheid','verdriet','haat / afkeer','liefde','begrip','vergeving / verzoening','opluchting / rust','trauma / therapie','schuld(gevoel)','eenzaamheid']:
    rx=re.compile(TH['Emoties'][lab]); b=[0,0,0]
    for x in cab:
        t=norm(x['tekst']); L=len(t)
        for m in rx.finditer(t): b[min(2,int(3*m.start()/L))]+=1
    pos[lab]=b
res['positie']=pos
json.dump(res,open(sys.argv[4],'w'),ensure_ascii=False,indent=1)
