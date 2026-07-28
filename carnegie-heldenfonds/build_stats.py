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
geplot_pct = pct(S["geplot"], S["totaal"])
nietplot_n = S["totaal"] - S["geplot"]
data_json = json.dumps(S, ensure_ascii=False, separators=(",",":"))

# gecureerde bijzondere gevallen (emoji, titel, tekst, plaats/jaar, inv.nr.)
HIGHLIGHTS = [
 ("🦁","Een ontsnapte leeuw","Drie kinderen bedreigd door een leeuw die was ontsnapt uit de dresseerkooi van het Duitse circus Barnum.","Haps, 1974",218),
 ("🐻","Uit de klauwen","Twee mannen probeerden de eigenaar van dierentuin Put te redden uit de klauwen van twee Himalaya­beren.","Apeldoorn, 1959",446),
 ("🐺","De wolfskooi","Een kind stak haar hand door de tralies van een wolfskooi en werd door de wolf beetgepakt; de redder bevrijdde haar.","Doornspijk, 1951",1559),
 ("🌊","Circa 300 drenkelingen","Jacob ‘Tabbie’ Bakker redde als lid van de reddingsbrigade in zijn leven zo’n 300 schipbreukelingen.","reddingsbrigade, ~1932",316),
 ("🚢","70 van de ‘Eastwell’","Mattheüs van der Put hielp 70 mensen redden toen het Engelse stoomschip zonk — zijn aanvraag werd tóch afgewezen.","IJmuiden, 1913",6203),
 ("👥","Een ploeg van 21","Een van de grootste reddersploegen van het hele bestand: eenentwintig mensen tegelijk beloond voor één redding.","1923",7317),
 ("⚡","Door de bliksem getroffen","Vier kinderen gered uit een woning die door de bliksem was getroffen.","Zelhem, 1942",5784),
 ("👶","De kinderwagen","Een moeder trok de kinderwagen met haar baby weg van een vallende benzinetank.","Rotterdam, 1954",643),
 ("🏅","36 levens — afgewezen","Jeremias van Doorn zou in zijn leven 36 mensen hebben gered; zijn aanvraag werd niettemin afgewezen.","1954",1502),
 ("🌍","Een zeldzaam spoor","Mehmet Cakici redde een kind uit het water — een van de zeer weinige redders met een naam die wijst op de naoorlogse arbeidsmigratie. In de rest van het bestand blijft die geschiedenis vrijwel onzichtbaar.","Hengelo, 1984",9232),
 ("🏖️","Held op Mallorca","R. ten Cate redde een Engelsman uit zee bij het strand van El Arenal en kreeg er een bronzen medaille en oorkonde voor van de Spaanse reddingsbond — een Nederlandse held, onderscheiden in den vreemde.","Mallorca, 1967",9261),
 ("🌏","Schipbreuk bij Sumatra","Anton Kortlandt redde verscheidene opvarenden van een schipbreuk voor de kust van Sumatra. Ver van huis, en tóch: zijn aanvraag werd afgewezen.","Sumatra, Indonesië",4235),
 ("🔥","Zes kinderen uit het vuur","Anna Cornelia Dijkman zou zes kinderen uit een brandend huis hebben gered. Wat het fonds haar toekende, is in het dossier onbekend gebleven.","Amsterdam, 1922",1752),
 ("👧","Voor haar broertje en zusje","Antonia Maria Grootaert haalde haar eigen broertje en zusje uit een brandend pand.","Rijsenhout, 1966",2409),
 ("🤝","Samen uit het water","Saida Errouk en Annemarie Veldhuizen redden samen met omstanders een drenkeling — twee vrouwen aan het hoofd van de reddersploeg, en meteen een tweede zeldzaam migratie­spoor in het bestand.","Vlijmen, 1982",1945),
]
def _hl(emo,title,text,place,nr):
    na = f"https://www.nationaalarchief.nl/onderzoeken/archief/2.19.364/invnr/{nr}"
    return (f'<div class="cslide"><div class="hlcard"><div class="em">{emo}</div><div><h3>{title}</h3>'
            f'<p>{text}</p><div class="meta">{place} &middot; '
            f'<a href="{na}" target="_blank" rel="noopener">nr. {nr} &#8599;</a></div></div></div></div>')
highlights_html = "".join(_hl(*h) for h in HIGHLIGHTS)

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
  .tile{position:relative;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:15px 16px;box-shadow:var(--shadow)}
  .tile .n{font-size:26px;font-weight:800;letter-spacing:-.02em;line-height:1}
  .qm{width:18px;height:18px;border-radius:50%;background:#eef1f4;color:#6b7280;flex:none;
      font-size:11px;font-weight:700;display:grid;place-items:center;cursor:help;user-select:none;border:1px solid var(--line)}
  .tile .qm{position:absolute;top:9px;right:10px}
  .qm:hover,.tile:focus-within .qm,.help:focus-within .qm{background:var(--accent);color:#fff;border-color:var(--accent)}
  .help{position:relative;margin-left:auto;display:inline-grid;place-items:center}
  .tt{position:absolute;top:calc(100% + 6px);left:0;z-index:40;width:340px;text-align:left;
      background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 6px 26px #0000001f;
      padding:13px 15px;font-size:12.5px;line-height:1.5;color:#374151;opacity:0;visibility:hidden;
      transform:translateY(-4px);transition:opacity .14s,transform .14s}
  .help .tt{left:auto;right:0}
  .tile:hover .tt,.tile:focus-within .tt,.help:hover .tt,.help:focus-within .tt{opacity:1;visibility:visible;transform:none}
  .tt b{color:var(--ink)} .tt ul{margin:6px 0 0;padding-left:18px} .tt li{margin:3px 0}
  .tt .src{margin-top:9px;font-size:11.5px;color:var(--muted)}
  .tile .l{font-size:12px;color:var(--muted);margin-top:5px;line-height:1.3}
  /* bijzondere gevallen — carrousel */
  .hlsec{margin:26px 0 30px;background:linear-gradient(135deg,#faf6ea,#f6efe0);border:1px solid #ece0c8;border-radius:20px;padding:16px 18px 18px}
  .hlsec .lbl2{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#a07d3c;margin:0 0 12px}
  .carousel{display:flex;align-items:stretch;gap:10px}
  .cbtn{flex:none;width:42px;border:1px solid var(--line);background:#fff;border-radius:12px;cursor:pointer;font-size:22px;color:var(--muted);box-shadow:var(--shadow);line-height:1}
  .cbtn:hover{color:var(--ink);border-color:#cbd5e1}
  .cviewport{flex:1;min-width:0;overflow:hidden;border-radius:14px}
  .ctrack{display:flex;transition:transform .35s ease}
  .cslide{flex:0 0 100%;min-width:0;padding:0 1px;box-sizing:border-box}
  .hlcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 24px;box-shadow:var(--shadow);display:flex;gap:16px;align-items:center;min-height:118px;box-sizing:border-box}
  .hlcard .em{font-size:40px;line-height:1;flex:none}
  .hlcard h3{margin:0 0 4px;font-size:16px;letter-spacing:-.01em}
  .hlcard p{margin:0 0 7px;font-size:14px;color:#374151;line-height:1.5}
  .hlcard .meta{font-size:12px;color:var(--muted)}
  .hlcard .meta a{color:var(--accent);text-decoration:none;font-weight:600}
  .cdots{display:flex;justify-content:center;gap:6px;margin-top:12px}
  .cdot{width:7px;height:7px;border-radius:50%;background:#d1d5db;border:none;cursor:pointer;padding:0;transition:.2s}
  .cdot.on{background:var(--accent);width:18px;border-radius:4px}
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
  @media(max-width:520px){.tt{width:260px;left:auto;right:0}}
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

  <div class="tiles" style="margin-bottom:12px">
    <div class="tile"><div class="n">__TOT__</div><div class="l">reddingsdossiers</div></div>
    <div class="tile" tabindex="0"><span class="qm" aria-hidden="true">?</span>
      <div class="n">__GEPLOT__%</div><div class="l">als punt op de kaart geplot</div>
      <div class="tt" role="tooltip">
        Van de __TOT__ dossiers staan er <b>__GEPLOTN__</b> (__GEPLOT__%) als punt op de kaart. Waar de beschrijving een gracht, haven of straat noemt, staat de marker dáár; anders in het centrum van de plaats.
        <div style="margin-top:7px">De overige <b>__NIETPLOT__</b> laten we bewust weg:</div>
        <ul>
          <li><b>Geen reddingsplaats</b> — administratieve/steundossiers.</li>
          <li><b>Open water</b> — "voor de kust", Noordzee, IJsselmeer: geen precies punt.</li>
          <li><b>Te onzeker</b> — een handvol plaatsnamen niet betrouwbaar thuisgebracht.</li>
        </ul>
        <div class="src">Meer op de <a href="../over">over-pagina</a>.</div>
      </div>
    </div>
    <div class="tile"><div class="n">__PLA__</div><div class="l">verschillende plaatsen</div></div>
  </div>
  <div class="tiles">
    <div class="tile"><div class="n">__GESL__%</div><div class="l">geslaagde reddingen</div></div>
    <div class="tile"><div class="n">__KIND__%</div><div class="l">van de geredden was een kind</div></div>
    <div class="tile"><div class="n">__VRPCT__%</div><div class="l">van de redders vrouw <span style="opacity:.7">(schatting)</span></div></div>
    <div class="tile"><div class="n">__MEER__%</div><div class="l">met meerdere redders</div></div>
  </div>

  <div class="hlsec">
    <div class="lbl2">Bijzondere gevallen</div>
    <div class="carousel">
      <button class="cbtn" id="cPrev" aria-label="vorige">&lsaquo;</button>
      <div class="cviewport"><div class="ctrack" id="ctrack">__HIGHLIGHTS__</div></div>
      <button class="cbtn" id="cNext" aria-label="volgende">&rsaquo;</button>
    </div>
    <div class="cdots" id="cdots"></div>
  </div>

  <div class="grid">
    <div class="card"><h2>Aard van de reddingen</h2>
      <p class="cap">Ruim driekwart is een redding <b>uit het water</b> — Nederland is een waterland.</p>
      <div class="cwrap"><canvas id="cAard"></canvas></div></div>

    <div class="card"><h2>Hoe gevaarlijk was elke redding?</h2>
      <p class="cap">Aandeel dat een <b>poging</b> bleef of de redder het leven kostte. Uit het <b>binnenwater</b> lukte het bijna altijd; <b>op hol geslagen paarden</b>, <b>auto's te water</b> en de <b>zee</b> waren veel gevaarlijker.</p>
      <div class="cwrap"><canvas id="cDanger"></canvas></div></div>

    <div class="card wide"><div class="h2row"><h2>Reddingen door de tijd</h2>
      <span class="seg" id="segRed"><button data-g="jaar" class="on">per jaar</button><button data-g="dec">per decennium</button></span></div>
      <p class="cap">Alle aanvragen per periode (vanaf 1910), gesplitst in <b>toegekend</b> en <b>afgewezen</b>. Het totaal piekt in de <b>jaren '50</b>; het afgewezen-aandeel groeit daarna mee.</p>
      <div class="cwrap"><canvas id="cTime"></canvas></div></div>

    <div class="card wide"><h2>Van paard naar auto</h2>
      <p class="cap">Als <b>aandeel van alle reddingen</b> per decennium (zo telt het ongelijke aantal dossiers per periode niet mee): reddingen van
      <b>op hol geslagen paarden</b> verdwijnen na de jaren '50, terwijl <b>auto's te water</b> juist opkomen — de tijdgeest in twee lijnen.</p>
      <div class="cwrap"><canvas id="cShift"></canvas></div></div>

    <div class="card wide"><div class="h2row"><h2>IJsreddingen en strenge winters</h2>
      <span class="help" tabindex="0"><span class="qm" aria-hidden="true">?</span>
        <div class="tt" role="tooltip">
          <b>Waarom het aandeel en niet het aantal?</b> Het absolute aantal ijsreddingen volgt vooral het totale dossiervolume (piek in de jaren '50); het <b>aandeel per jaar</b> legt de winters pas bloot.
          <div style="margin-top:7px">In <b>Elfstedentocht-jaren</b> was <b>__ICEELF__%</b> van alle reddingen een ijsredding, tegen <b>__ICEOTH__%</b> in andere jaren — ruim 1,7×.</div>
          <div class="src">De Elfstedentocht dient hier als graadmeter voor een strenge winter: we markeren de jaren waarin een tocht werd gehouden (de bekende lijst, 1909–1997). Jaren met weinig dossiers (bijv. 1985: 5) kunnen uitschieten — de tooltip per staaf toont de aantallen.</div>
        </div></span></div>
      <p class="cap">Het <b>aandeel</b> ijsreddingen per jaar. In <b>Elfstedentocht-jaren</b> <span style="color:#0e8ba8;font-weight:700">(blauw)</span> — graadmeter voor een strenge winter — was dat aandeel ruim <b>anderhalf keer</b> zo groot; de pieken vallen op ijswinters als <b>1929</b>, <b>1963</b> en <b>1979</b>.</p>
      <div class="cwrap"><canvas id="cIce"></canvas></div></div>

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

    <div class="card"><h2>Man of vrouw? — geslacht per aard</h2>
      <p class="cap">Absoluut aantal <b>mannelijke</b> en <b>vrouwelijke</b> redders per soort redding (geschat). Water levert veruit de meeste redders; het vrouwaandeel is overal een minderheid, maar relatief het grootst bij <b>water, ijs en brand</b>.</p>
      <div class="cwrap"><canvas id="cGenderCat"></canvas></div></div>

    <div class="card"><h2>Welke reddingen werden afgewezen?</h2>
      <p class="cap"><b>Auto te water</b> werd het vaakst afgewezen (~37%); <b>op hol geslagen paarden</b> — de klassieke heldendaad — juist het minst (~17%).</p>
      <div class="cwrap"><canvas id="cRejectCat"></canvas></div></div>

    <div class="card"><div class="h2row"><h2>Waar wordt gered? — top-plaatsen</h2>
      <span class="seg" id="segPlace"><button data-g="abs" class="on">absoluut</button><button data-g="pc">per 100.000 inw.</button></span></div>
      <p class="cap">Absoluut voeren de grote steden de lijst aan (<b>Amsterdam</b>, <b>Den Haag</b>). <b>Per hoofd</b> van de bevolking draaien de waterstadjes de rollen om: <b>Dordrecht</b>, <b>Leiden</b> en <b>Delft</b> bovenaan, Amsterdam en Rotterdam juist laag (indicatief, inwonertal rond 1947).</p>
      <div class="cwrap tall"><canvas id="cPlaces"></canvas></div></div>

    <div class="card"><div class="h2row"><h2>Per provincie</h2>
      <span class="seg" id="segProv"><button data-g="abs" class="on">absoluut</button><button data-g="pc">per 100.000 inw.</button></span></div>
      <p class="cap">De waterrijke <b>Randstad</b> domineert — ook <b>per hoofd</b> van de bevolking (indicatief, t.o.v. de volkstelling 1947). Bij 'absoluut' onderaan de reddingen in het <b>buitenland</b>.</p>
      <div class="cwrap tall"><canvas id="cProv"></canvas></div></div>

    <div class="card"><h2>In welk water?</h2>
      <p class="cap">Waar een specifieke gracht/haven/rivier genoemd is — de <b>Noordzee</b> bovenaan.</p>
      <div class="cwrap tall"><canvas id="cWater"></canvas></div></div>

    <div class="card"><h2>Reddingen in het buitenland</h2>
      <p class="cap">Bijna alles speelt zich in Nederland af (<b>__BINNEN__</b>), maar <b>__BUITEN__</b> reddingen gebeurden erbuiten — door Nederlanders op zee, in de koloniën of op reis.</p>
      <div class="cwrap tall"><canvas id="cLand"></canvas></div></div>

    <div class="card wide"><h2>Wanneer wordt het archief openbaar?</h2>
      <p class="cap">Nu is <b>__OPENPCT__%</b> van de dossiers openbaar; de rest opent geleidelijk (veelal ~75 jaar na de redding, om privacyredenen). Pas rond <b>2085</b> is alles openbaar.</p>
      <div class="cwrap"><canvas id="cOpenb"></canvas></div></div>
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
const withUnit = (n,unit) => money(n)+" "+(n===1 && unit==='reddingen' ? 'redding' : unit);
const gridX = {grid:{color:GRID,drawTicks:false},border:{display:false},ticks:{color:MUT}};
const noGrid = {grid:{display:false},border:{display:false},ticks:{color:MUT}};
const tip = {backgroundColor:"#111",padding:10,cornerRadius:8,titleFont:{weight:'700'},boxPadding:4};

// 1. Aard — horizontal bar (map colors; labels give secondary encoding)
{const cats=Object.keys(S.cat).sort((a,b)=>S.cat[b]-S.cat[a]);
new Chart(cAard,{type:'bar',data:{labels:cats.map(c=>CATEMO[c]+" "+CATLBL[c]),
  datasets:[{data:cats.map(c=>S.cat[c]),backgroundColor:cats.map(c=>CATCOL[c]),borderRadius:5,borderSkipped:false,maxBarThickness:26}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{...tip,callbacks:{label:c=>withUnit(c.raw,'reddingen')}}},
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
// Reddingen door de tijd — gestapeld: toegekend + afgewezen (per jaar vanaf 1910 / decennium)
(function(){
  const yi = S.years.findIndex(y=>y>=1910);      // per jaar vanaf 1910
  const yrL = S.years.slice(yi), yrC = S.year_counts.slice(yi), yrR = S.year_rej.slice(yi);
  const di = S.decades.findIndex(d=>d>=1910);    // decennia vanaf 1910
  const decL = decLabels.slice(di), decC = S.decade_counts.slice(di), decR = S.decade_rej.slice(di);
  let chart;
  function draw(g){
    if(chart) chart.destroy();
    const jaar = g==='jaar';
    const labels = jaar?yrL:decL, tot = jaar?yrC:decC, rej = jaar?yrR:decR;
    const toeg = tot.map((t,i)=>t-rej[i]);
    chart=new Chart(cTime,{type:'bar',data:{labels,datasets:[
      {label:'Toegekend',data:toeg,backgroundColor:ACC,stack:'s',maxBarThickness:44},
      {label:'Afgewezen',data:rej,backgroundColor:'#eb6834',stack:'s',maxBarThickness:44}]},
      options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
        plugins:{legend:{position:'top',labels:{color:INK,usePointStyle:true,boxWidth:10}},
          tooltip:{...tip,callbacks:{title:c=>jaar?c[0].label:("Jaren "+c[0].label),
            footer:it=>{const t=it.reduce((s,i)=>s+i.raw,0);const r=it.find(i=>i.dataset.label==='Afgewezen');
              return t?"totaal "+money(t)+" · "+Math.round(100*(r?r.raw:0)/t)+"% afgewezen":"";}}}},
        scales:{x:{...noGrid,stacked:true,ticks:{color:MUT,autoSkip:false,maxRotation:0,
                  callback:jaar?function(v,i){const y=labels[i];return y%5===0?y:'';}:undefined}},
                y:{...gridX,stacked:true,beginAtZero:true,ticks:{color:MUT,callback:v=>money(v)}}}}});
  }
  segRed.querySelectorAll('button').forEach(b=>b.onclick=()=>{segRed.querySelectorAll('button').forEach(x=>x.classList.remove('on'));b.classList.add('on');draw(b.dataset.g);});
  draw('jaar');
})();

// 3. Paard -> auto — als AANDEEL van alle reddingen per decennium (vanaf 1910),
//    zodat het ongelijke totaalvolume per periode het beeld niet vertekent.
{const di=S.decades.findIndex(d=>d>=1910);
 const dl=decLabels.slice(di), tot=S.decade_counts.slice(di);
 const pct=arr=>arr.slice(di).map((n,i)=>tot[i]?Math.round(1000*n/tot[i])/10:0);
new Chart(cShift,{type:'line',data:{labels:dl,datasets:[
  {label:"🐴 Op hol geslagen paard",data:pct(S.cat_decade.dier),borderColor:"#4a3aa7",backgroundColor:"#4a3aa7",tension:.35,borderWidth:2.5,pointRadius:3,pointHoverRadius:6},
  {label:"🚗 Auto te water",data:pct(S.cat_decade.auto),borderColor:"#e34948",backgroundColor:"#e34948",tension:.35,borderWidth:2.5,pointRadius:3,pointHoverRadius:6}]},
  options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
    plugins:{legend:{position:'top',labels:{color:INK,usePointStyle:true,pointStyle:'line',boxWidth:22}},
      tooltip:{...tip,callbacks:{title:c=>"Jaren "+c[0].label,label:c=>c.dataset.label+": "+c.raw+"% van de reddingen"}}},
    scales:{x:noGrid,y:{...gridX,beginAtZero:true,ticks:{color:MUT,callback:v=>v+"%"}}}}});}

// 3b. IJsreddingen als AANDEEL per jaar; Elfstedentocht-jaren (strenge winter) uitgelicht
{const ys=S.years, elf=new Set(S.elf_years);
new Chart(cIce,{type:'bar',data:{labels:ys,datasets:[{data:S.ice_share_year,
  backgroundColor:ys.map(y=>elf.has(y)?CATCOL.ijs:"#d7dde3"),
  borderRadius:3,borderSkipped:false,maxBarThickness:14}]},
  options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},tooltip:{...tip,callbacks:{
      title:c=>c[0].label+(elf.has(+c[0].label)?" · Elfstedentocht":""),
      label:c=>c.raw+"% ijs ("+S.ice_year[c.dataIndex]+" van "+S.year_counts[c.dataIndex]+" reddingen)"}}},
    scales:{x:{...noGrid,ticks:{color:MUT,autoSkip:true,maxTicksLimit:10,maxRotation:0}},
            y:{...gridX,beginAtZero:true,ticks:{color:MUT,callback:v=>v+"%"}}}}});}

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
    tooltip:{...tip,callbacks:{label:c=>withUnit(c.raw,unit)}}},scales:{x:{...gridX,ticks:{color:MUT,callback:v=>money(v)}},y:noGrid}}});}
// categorie-gekleurde horizontale balk (emoji-labels), waarde in %
function catbar(cv,pairs){
  new Chart(cv,{type:'bar',data:{labels:pairs.map(p=>CATEMO[p[0]]+" "+CATLBL[p[0]]),
    datasets:[{data:pairs.map(p=>p[1]),backgroundColor:pairs.map(p=>CATCOL[p[0]]),borderRadius:5,borderSkipped:false,maxBarThickness:22}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
      tooltip:{...tip,callbacks:{label:c=>c.raw+"%"}}},
      scales:{x:{...gridX,ticks:{color:MUT,callback:v=>v+"%"}},y:noGrid}}});
}
catbar(cDanger,S.danger);
catbar(cRejectCat,S.reject_cat);
hbar(cWater,S.top_waters.slice(0,12),"reddingen","#0891b2");
hbar(cLand,S.landen,"reddingen","#4a3aa7");

// Geslacht per aard — gestapelde absolute man/vrouw-balk
{const G=S.gender_cat_abs, L=G.map(r=>CATEMO[r[0]]+" "+CATLBL[r[0]]);
new Chart(cGenderCat,{type:'bar',data:{labels:L,datasets:[
  {label:'Man',data:G.map(r=>r[1]),backgroundColor:"#2a78d6",borderRadius:4,borderSkipped:false,maxBarThickness:22,stack:'g'},
  {label:'Vrouw',data:G.map(r=>r[2]),backgroundColor:"#1baf7a",borderRadius:4,borderSkipped:false,maxBarThickness:22,stack:'g'}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
    plugins:{legend:{position:'top',labels:{color:INK,usePointStyle:true,boxWidth:10}},
      tooltip:{...tip,callbacks:{label:c=>c.dataset.label+": "+money(c.raw)+
        " ("+Math.round(100*c.raw/(G[c.dataIndex][1]+G[c.dataIndex][2]))+"%)"}}},
    scales:{x:{...gridX,stacked:true,ticks:{color:MUT,callback:v=>money(v)}},y:{...noGrid,stacked:true}}}});}

// Top-plaatsen met toggle absoluut / per 100.000 inwoners
(function(){
  let chart;
  function draw(g){
    if(chart) chart.destroy();
    const pairs = g==='pc' ? S.top_places_pc : S.top_places.slice(0,12);
    const unit = g==='pc' ? 'per 100.000 inw.' : 'reddingen';
    chart=new Chart(cPlaces,{type:'bar',data:{labels:pairs.map(p=>p[0]),
      datasets:[{data:pairs.map(p=>p[1]),backgroundColor:ACC,borderRadius:5,borderSkipped:false,maxBarThickness:20}]},
      options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
        tooltip:{...tip,callbacks:{label:c=>withUnit(c.raw,unit)}}},
        scales:{x:{...gridX,ticks:{color:MUT,callback:v=>money(v)}},y:noGrid}}});
  }
  segPlace.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    segPlace.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); draw(b.dataset.g);
  });
  draw('abs');
})();

// Per provincie met toggle absoluut / per 100.000 inwoners
(function(){
  let chart;
  function draw(g){
    if(chart) chart.destroy();
    const pairs = g==='pc' ? S.provinces_pc : S.provinces;
    const unit = g==='pc' ? 'per 100.000 inw.' : 'reddingen';
    chart=new Chart(cProv,{type:'bar',data:{labels:pairs.map(p=>p[0]),
      datasets:[{data:pairs.map(p=>p[1]),backgroundColor:ACC,borderRadius:5,borderSkipped:false,maxBarThickness:20}]},
      options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
        tooltip:{...tip,callbacks:{label:c=>withUnit(c.raw,unit)}}},
        scales:{x:{...gridX,ticks:{color:MUT,callback:v=>money(v)}},y:noGrid}}});
  }
  segProv.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    segProv.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); draw(b.dataset.g);
  });
  draw('abs');
})();

// Openbaarheid door de tijd (cumulatief % openbaar)
new Chart(cOpenb,{type:'line',data:{labels:S.openb_years,datasets:[{data:S.openb_pct,
  borderColor:ACC,backgroundColor:ACC+"22",fill:true,tension:.25,borderWidth:2.5,pointRadius:0,pointHoverRadius:5}]},
  options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},tooltip:{...tip,callbacks:{title:c=>"in "+c[0].label,label:c=>c.raw+"% openbaar"}}},
    scales:{x:{...noGrid,ticks:{color:MUT,autoSkip:true,maxTicksLimit:9,maxRotation:0}},
            y:{...gridX,beginAtZero:true,max:100,ticks:{color:MUT,callback:v=>v+"%"}}}}});

// Carrousel 'Bijzondere gevallen'
(function(){
  const slides=[...document.querySelectorAll('.cslide')], track=document.getElementById('ctrack'), dots=document.getElementById('cdots');
  if(!slides.length) return;
  let ci=0, timer=null;
  slides.forEach((_,i)=>{const b=document.createElement('button');b.className='cdot';b.setAttribute('aria-label','ga naar '+(i+1));b.onclick=()=>{go(i);restart();};dots.appendChild(b);});
  function go(i){ci=(i+slides.length)%slides.length;track.style.transform=`translateX(-${ci*100}%)`;
    [...dots.children].forEach((d,j)=>d.classList.toggle('on',j===ci));}
  function restart(){clearInterval(timer);timer=setInterval(()=>go(ci+1),6000);}
  document.getElementById('cPrev').onclick=()=>{go(ci-1);restart();};
  document.getElementById('cNext').onclick=()=>{go(ci+1);restart();};
  const car=document.querySelector('.carousel');
  car.addEventListener('mouseenter',()=>clearInterval(timer));
  car.addEventListener('mouseleave',restart);
  go(0);restart();
})();
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
        .replace("__GEPLOTN__", f"{S['geplot']:,}".replace(",", "."))
        .replace("__GEPLOT__", str(geplot_pct))
        .replace("__NIETPLOT__", f"{nietplot_n:,}".replace(",", "."))
        .replace("__ICEELF__", str(S["ice_elf_pct"]).replace(".", ","))
        .replace("__ICEOTH__", str(S["ice_other_pct"]).replace(".", ","))
        .replace("__BINNEN__", f"{S['binnenbuiten']['binnenland']:,}".replace(",", "."))
        .replace("__BUITEN__", str(S['binnenbuiten']['buitenland']))
        .replace("__OPENPCT__", str(round(S['openb_pct'][0])))
        .replace("__HIGHLIGHTS__", highlights_html))
open(out, "w", encoding="utf-8").write(h)
print("geschreven:", out, "| bytes", len(h))
print(f"tiles: totaal={S['totaal']} geslaagd={geslaagd_pct}% kind={kind_pct}% vrouw={vrouw_pct}% meer={meer_pct}% plaatsen={S['plaatsen']}")
