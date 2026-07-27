#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the insights dashboard (self-contained) from stats.json."""
import json, os
from cats import CAT_ORDER, CAT_FULL, CAT_COL, CAT_EMO

WORK = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(f"{WORK}/stats.json", encoding="utf-8"))
out = f"{WORK}/stats.html"

def pct(a, b): return round(100*a/b) if b else 0
geslaagd_pct = pct(S["outcome"].get("geslaagd",0), S["totaal"])
vrouw_pct = pct(S["gender"]["vrouw"], S["gender"]["man"]+S["gender"]["vrouw"])
meer_pct = pct(S["group"].get("meerdere",0), S["totaal"])
v = S["victim"]
kind_pct = pct(v["kind"], v["kind"]+v["volwassene"]+v["beide"])
data_json = json.dumps(S, ensure_ascii=False, separators=(",",":"))

HTML = r"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carnegie Heldenfonds — inzichten</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root{
    --bg:#f6f7f5; --card:#ffffff; --ink:#171717; --muted:#6b7280; --line:#e7e7e4;
    --accent:#0e7490; --shadow:0 1px 3px #0000000f,0 8px 24px #00000010;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}
  a{color:var(--accent)}
  .wrap{max-width:1080px;margin:0 auto;padding:22px 20px 60px}
  header{display:flex;align-items:center;gap:14px;margin-bottom:6px}
  .logo{width:44px;height:44px;border-radius:11px;display:grid;place-items:center;font-size:24px;flex:none;
    background:linear-gradient(135deg,#0e7490,#0891b2);box-shadow:0 2px 8px #0e749055}
  h1{font-size:23px;margin:0;letter-spacing:-.02em}
  header .sub{color:var(--muted);font-size:13px;margin:2px 0 0}
  .back{margin-left:auto;font-size:13px;font-weight:600;text-decoration:none;background:#fff;border:1px solid var(--line);
    padding:8px 13px;border-radius:10px;white-space:nowrap}
  .lead{color:#374151;font-size:15px;line-height:1.55;max-width:70ch;margin:14px 0 22px}
  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:12px;margin-bottom:26px}
  .tile{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 16px;box-shadow:var(--shadow)}
  .tile .n{font-size:26px;font-weight:800;letter-spacing:-.02em;line-height:1}
  .tile .l{font-size:12px;color:var(--muted);margin-top:5px;line-height:1.3}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 18px 14px;box-shadow:var(--shadow)}
  .card.wide{grid-column:1/-1}
  .h2row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .card h2{font-size:15px;margin:0;letter-spacing:-.01em}
  .card .cap{font-size:12.5px;color:var(--muted);margin:3px 0 12px;line-height:1.4}
  .card .cap b{color:#374151}
  .seg{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;font-size:11px;margin-left:auto}
  .seg button{border:none;background:#fff;padding:4px 11px;cursor:pointer;color:var(--muted);font-weight:600;font-family:inherit}
  .seg button.on{background:var(--accent);color:#fff}
  .cwrap{position:relative;height:260px}
  .cwrap.tall{height:340px}
  .note{font-size:11px;color:#9ca3af;margin-top:9px}
  footer{color:var(--muted);font-size:12px;margin-top:30px;line-height:1.6;border-top:1px solid var(--line);padding-top:16px}
  @media(max-width:720px){.grid{grid-template-columns:1fr}.cwrap{height:240px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">🛟</div>
    <div>
      <h1>Carnegie Heldenfonds — inzichten</h1>
      <p class="sub">Analyse van __TOT__ dossiers · inventaris 2.19.364 · __Y0__–__Y1__</p>
    </div>
    <a class="back" href="../over" style="margin-left:auto">ℹ️ Over</a>
    <a class="back" href="../">← naar de kaart</a>
  </header>

  <p class="lead">Het Nederlandse Carnegie Heldenfonds beloonde mensen die met gevaar voor eigen leven
  anderen redden. Uit de __TOT__ persoonsdossiers is per redding automatisch de <b>aard</b>, <b>plaats</b>,
  <b>jaar</b>, <b>afloop</b>, <b>wie er gered werd</b> en (bij benadering) het <b>geslacht van de redder</b>
  afgeleid. Dat levert bijna een eeuw reddingsgeschiedenis in cijfers.</p>

  <div class="tiles">
    <div class="tile"><div class="n">__TOT__</div><div class="l">reddingsdossiers</div></div>
    <div class="tile"><div class="n">__GESL__%</div><div class="l">geslaagde reddingen</div></div>
    <div class="tile"><div class="n">__KIND__%</div><div class="l">van de geredden was een kind</div></div>
    <div class="tile"><div class="n">__VRPCT__%</div><div class="l">van de redders vrouw <span style="opacity:.7">(schatting)</span></div></div>
    <div class="tile"><div class="n">__MEER__%</div><div class="l">met meerdere redders</div></div>
    <div class="tile"><div class="n">__PLA__</div><div class="l">verschillende plaatsen</div></div>
  </div>

  <div class="grid">
    <div class="card"><h2>Aard van de reddingen</h2>
      <p class="cap">Ruim driekwart is een redding <b>uit het water</b> — Nederland is een waterland.</p>
      <div class="cwrap"><canvas id="cAard"></canvas></div></div>

    <div class="card"><div class="h2row"><h2>Reddingen door de tijd</h2>
      <span class="seg" id="segRed"><button data-g="jaar" class="on">per jaar</button><button data-g="dec">per decennium</button></span></div>
      <p class="cap">Het aantal beloonde reddingen piekt in het midden van de <b>jaren '50</b>.</p>
      <div class="cwrap"><canvas id="cTime"></canvas></div></div>

    <div class="card wide"><h2>Van paard naar auto</h2>
      <p class="cap">Reddingen van <b>op hol geslagen paarden</b> verdwijnen na de jaren '50, terwijl reddingen
      uit een <b>te water geraakte auto</b> juist toenemen met de opkomst van de auto — de tijdgeest in twee lijnen.</p>
      <div class="cwrap"><canvas id="cShift"></canvas></div></div>

    <div class="card"><h2>Wie werd er gered?</h2>
      <p class="cap">In verreweg de meeste dossiers gaat het om een <b>kind</b> — vaak te water geraakt.</p>
      <div class="cwrap"><canvas id="cVictim"></canvas></div></div>

    <div class="card"><h2>Geslacht van de redder</h2>
      <p class="cap">Onder de geregistreerde redders zijn mannen sterk in de meerderheid. Het geslacht is een schatting.</p>
      <div class="cwrap"><canvas id="cGender"></canvas></div>
      <p class="note">Geschat op basis van voornaam en de gehuwde-vrouw-vorm (achternaam met koppelteken). “Onbekend” = vooral namen met alleen initialen.</p></div>

    <div class="card wide"><h2>Aandeel vrouwelijke redders door de tijd</h2>
      <p class="cap">Na de Tweede Wereldoorlog stijgt het geschatte aandeel vrouwelijke redders van ~4% naar ~14%.</p>
      <div class="cwrap"><canvas id="cVrouwtijd"></canvas></div></div>

    <div class="card"><h2>Waar wordt gered? — top-plaatsen</h2>
      <p class="cap">De grote steden voeren de lijst aan; <b>Amsterdam</b> en <b>Den Haag</b> springen eruit.</p>
      <div class="cwrap tall"><canvas id="cPlaces"></canvas></div></div>

    <div class="card"><h2>Per provincie</h2>
      <p class="cap">De waterrijke <b>Randstad</b> (Zuid- en Noord-Holland) domineert; onderaan de reddingen in het <b>buitenland</b>.</p>
      <div class="cwrap tall"><canvas id="cProv"></canvas></div></div>

    <div class="card"><h2>In welk water?</h2>
      <p class="cap">Waar een specifieke gracht/haven/rivier genoemd is — de <b>Noordzee</b> bovenaan.</p>
      <div class="cwrap tall"><canvas id="cWater"></canvas></div></div>

    <div class="card"><h2>Reddingen in het buitenland</h2>
      <p class="cap">Bijna alles speelt zich in Nederland af (<b>__BINNEN__</b>), maar <b>__BUITEN__</b> reddingen gebeurden erbuiten — door Nederlanders op zee, in de koloniën of op reis.</p>
      <div class="cwrap tall"><canvas id="cLand"></canvas></div></div>

    <div class="card"><div class="h2row"><h2>Afwijzingen door de tijd</h2>
      <span class="seg" id="segRej"><button data-g="jaar" class="on">per jaar</button><button data-g="dec">per decennium</button></span></div>
      <p class="cap">Het <b>aantal afgewezen</b> aanvragen; als aandeel van alle aanvragen loopt dit op van ~14% (voor de oorlog) tot ~40% (jaren '50–'60).</p>
      <div class="cwrap"><canvas id="cReject"></canvas></div></div>
  </div>

  <footer>
    <p style="margin:0 0 10px;font-weight:600;color:#374151">Download de volledige dataset:
      <a href="../dossiers.csv" download>CSV</a> &middot; <a href="../dossiers.json" download>JSON</a>
      &nbsp;·&nbsp; <a href="../">← naar de kaart</a></p>
    Bron: Nationaal Archief, <b>Stichting Carnegie Heldenfonds Nederland — Persoonsdossiers, 1903-1987</b>
    (toegang 2.19.364). Aard, afloop, wie gered werd en geslacht zijn automatisch uit de dossieromschrijvingen
    afgeleid en daarom bij benadering.
  </footer>
</div>

<script>
const S = __DATA__;
const CATCOL = __CC__;
const CATLBL = __CL__;
const CATEMO = __CE__;
const INK="#171717", MUT="#6b7280", GRID="#00000010", ACC="#0e7490";
Chart.defaults.font.family="system-ui,-apple-system,Segoe UI,Roboto,sans-serif";
Chart.defaults.font.size=12; Chart.defaults.color=MUT;
const decLabels = S.decades.map(d=>d+"–"+String(d+9).slice(-2));   // Dutch decade notation
const yearLabels = S.years;
const money = n => n.toLocaleString('nl');
const gridX = {grid:{color:GRID,drawTicks:false},border:{display:false},ticks:{color:MUT}};
const noGrid = {grid:{display:false},border:{display:false},ticks:{color:MUT}};
const tip = {backgroundColor:"#111",padding:10,cornerRadius:8,titleFont:{weight:'700'},boxPadding:4};

// 1. Aard — horizontal bar (map colors; labels give secondary encoding)
{const cats=Object.keys(S.cat).sort((a,b)=>S.cat[b]-S.cat[a]);
new Chart(cAard,{type:'bar',data:{labels:cats.map(c=>CATEMO[c]+" "+CATLBL[c]),
  datasets:[{data:cats.map(c=>S.cat[c]),backgroundColor:cats.map(c=>CATCOL[c]),borderRadius:5,borderSkipped:false,maxBarThickness:26}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{...tip,callbacks:{label:c=>money(c.raw)+" reddingen"}}},
    scales:{x:{...gridX,ticks:{color:MUT,callback:v=>money(v)}},y:noGrid}}});}

// 2 & 10. time charts with per jaar / per decennium toggle
function timeChart(canvas, seg, yData, dData, color, unit){
  let chart;
  function draw(g){
    if(chart) chart.destroy();
    const jaar = g==='jaar';
    chart = new Chart(canvas,{type: jaar?'line':'bar',
      data:{labels: jaar?yearLabels:decLabels, datasets:[{data: jaar?yData:dData,
        borderColor:color, backgroundColor: jaar?color+"22":color, fill:jaar,
        tension:.3, borderWidth:2, pointRadius:0, pointHoverRadius:5,
        borderRadius:5, borderSkipped:false, maxBarThickness:34}]},
      options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{display:false},tooltip:{...tip,callbacks:{
          title:c=>jaar?c[0].label:("Jaren "+c[0].label), label:c=>money(c.raw)+" "+unit}}},
        scales:{x:{...noGrid,ticks:{color:MUT,autoSkip:true,maxTicksLimit: jaar?11:9,maxRotation:0}},
                y:{...gridX,beginAtZero:true,ticks:{color:MUT,callback:v=>money(v)}}}}});
  }
  seg.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    seg.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); draw(b.dataset.g);
  });
  draw('jaar');
}
timeChart(cTime, segRed, S.year_counts, S.decade_counts, ACC, "reddingen");
timeChart(cReject, segRej, S.year_rej, S.decade_rej, "#eb6834", "afgewezen");

// 3. Paard -> auto (two lines, decennium)
new Chart(cShift,{type:'line',data:{labels:decLabels,datasets:[
  {label:"🐴 Op hol geslagen paard",data:S.cat_decade.dier,borderColor:"#4a3aa7",backgroundColor:"#4a3aa7",tension:.35,borderWidth:2.5,pointRadius:3,pointHoverRadius:6},
  {label:"🚗 Auto te water",data:S.cat_decade.auto,borderColor:"#e34948",backgroundColor:"#e34948",tension:.35,borderWidth:2.5,pointRadius:3,pointHoverRadius:6}]},
  options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
    plugins:{legend:{position:'top',labels:{color:INK,usePointStyle:true,pointStyle:'line',boxWidth:22}},
      tooltip:{...tip,callbacks:{title:c=>"Jaren "+c[0].label}}},
    scales:{x:noGrid,y:{...gridX,beginAtZero:true,ticks:{color:MUT}}}}});

// 4. Wie werd gered — donut
{const vl=[["kind","Kind","#eda100"],["volwassene","Volwassene","#2a78d6"],["beide","Kind + volwassene","#4a3aa7"],["onbekend","Onbekend","#c9c9c4"]];
const tot=vl.reduce((s,x)=>s+S.victim[x[0]],0);
new Chart(cVictim,{type:'doughnut',data:{labels:vl.map(x=>x[1]),
  datasets:[{data:vl.map(x=>S.victim[x[0]]),backgroundColor:vl.map(x=>x[2]),borderColor:"#fff",borderWidth:3,hoverOffset:6}]},
  options:{responsive:true,maintainAspectRatio:false,cutout:'62%',plugins:{legend:{position:'right',labels:{color:INK,usePointStyle:true,boxWidth:10}},
    tooltip:{...tip,callbacks:{label:c=>c.label+": "+money(c.raw)+" ("+Math.round(100*c.raw/tot)+"%)"}}}}});}

// 5. Geslacht — donut (neutral, non-stereotyped colours)
{const g=S.gender,tot=g.man+g.vrouw+g.onbekend;new Chart(cGender,{type:'doughnut',
  data:{labels:["Man","Vrouw","Onbekend"],datasets:[{data:[g.man,g.vrouw,g.onbekend],
    backgroundColor:["#2a78d6","#1baf7a","#c9c9c4"],borderColor:"#fff",borderWidth:3,hoverOffset:6}]},
  options:{responsive:true,maintainAspectRatio:false,cutout:'62%',plugins:{legend:{position:'right',labels:{color:INK,usePointStyle:true,boxWidth:10}},
    tooltip:{...tip,callbacks:{label:c=>c.label+": "+money(c.raw)+" ("+Math.round(100*c.raw/tot)+"%)"}}}}});}

// 6. Vrouw% over tijd — single line (same hue as 'vrouw')
new Chart(cVrouwtijd,{type:'line',data:{labels:decLabels,datasets:[{data:S.gender_decade_vrouwpct,
  borderColor:"#1baf7a",backgroundColor:"#1baf7a22",fill:true,tension:.35,borderWidth:2.5,pointRadius:3,pointHoverRadius:6}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{...tip,callbacks:{title:c=>"Jaren "+c[0].label,label:c=>c.raw+"% vrouw"}}},
    scales:{x:noGrid,y:{...gridX,beginAtZero:true,ticks:{color:MUT,callback:v=>v+"%"}}}}});

// 7/8/9 horizontal single-hue bars
function hbar(cv,pairs,unit,color){const L=pairs.map(p=>p[0]),D=pairs.map(p=>p[1]);
new Chart(cv,{type:'bar',data:{labels:L,datasets:[{data:D,backgroundColor:color||ACC,borderRadius:5,borderSkipped:false,maxBarThickness:20}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{...tip,callbacks:{label:c=>money(c.raw)+" "+unit}}},scales:{x:{...gridX,ticks:{color:MUT,callback:v=>money(v)}},y:noGrid}}});}
hbar(cPlaces,S.top_places.slice(0,12),"reddingen");
hbar(cProv,S.provinces,"reddingen");
hbar(cWater,S.top_waters.slice(0,12),"reddingen","#0891b2");
hbar(cLand,S.landen,"reddingen","#4a3aa7");
</script>
</body>
</html>"""

def odict(dct): return json.dumps({c: dct[c] for c in CAT_ORDER}, ensure_ascii=False)
h = (HTML.replace("__CC__", odict(CAT_COL)).replace("__CL__", odict(CAT_FULL)).replace("__CE__", odict(CAT_EMO))
        .replace("__DATA__", data_json)
        .replace("__TOT__", f"{S['totaal']:,}".replace(",", "."))
        .replace("__Y0__", str(S["jaarspan"][0])).replace("__Y1__", str(S["jaarspan"][1]))
        .replace("__GESL__", str(geslaagd_pct))
        .replace("__KIND__", str(kind_pct))
        .replace("__VRPCT__", str(vrouw_pct))
        .replace("__MEER__", str(meer_pct))
        .replace("__PLA__", f"{S['plaatsen']:,}".replace(",", "."))
        .replace("__BINNEN__", f"{S['binnenbuiten']['binnenland']:,}".replace(",", "."))
        .replace("__BUITEN__", str(S['binnenbuiten']['buitenland'])))
open(out, "w", encoding="utf-8").write(h)
print("geschreven:", out, "| bytes", len(h))
print(f"tiles: totaal={S['totaal']} geslaagd={geslaagd_pct}% kind={kind_pct}% vrouw={vrouw_pct}% meer={meer_pct}% plaatsen={S['plaatsen']}")
