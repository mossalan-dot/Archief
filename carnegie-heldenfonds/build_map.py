#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the interactive Carnegie Heldenfonds map (self-contained HTML).
Usage: build_map.py OUT.html [NR_MIN] [NR_MAX]"""
import json, sys, os, re, html
from cats import categorize, outcome, is_steun, extract_person, CAT_ORDER, CAT_LABEL, CAT_FULL, CAT_COL, CAT_EMO

WORK = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(f"{WORK}/dossiers_raw.json", encoding="utf-8"))
cache = json.load(open(f"{WORK}/geocache.json", encoding="utf-8"))
# optional street/waterway-level cache: key "detail||place" -> {lat,lon,...}
dpath = f"{WORK}/geocache_detail.json"
dcache = json.load(open(dpath, encoding="utf-8")) if os.path.exists(dpath) else {}

out = sys.argv[1] if len(sys.argv) > 1 else f"{WORK}/carnegie-kaart.html"
nr_min = int(sys.argv[2]) if len(sys.argv) > 2 else 0
nr_max = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
note = sys.argv[4] if len(sys.argv) > 4 else ""

points = []
n_range = 0
n_placed = 0
for r in recs:
    if not (nr_min <= r["nr"] <= nr_max):
        continue
    n_range += 1
    det = r.get("detail")
    cat = categorize(r["desc"], det)
    res = outcome(r["desc"])
    steun = is_steun(r["desc"])
    who = extract_person(r["desc"])
    placed_any = False
    for p in r["places"]:
        g = cache.get(p)
        if not g:
            continue
        placed_any = True
        # prefer street/waterway-level coordinate if we have a good one
        prec = "plaats"; lat = g["lat"]; lon = g["lon"]
        if det:
            dg = dcache.get(f"{det}||{p}")
            if dg and dg.get("lat") is not None:
                lat, lon, prec = dg["lat"], dg["lon"], dg.get("prec", "straat")
        points.append({
            "nr": r["nr"],
            "desc": r["desc"],
            "year": r["year"],
            "y": r["year_from"],
            "place": p,
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "cat": cat,
            "afg": r["afgewezen"],
            "foto": r["fotos"],
            "openb": r["openbaar_tot"],
            "who": who,
            "det": det,
            "prec": prec,
            "res": res,
            "steun": steun,
        })
    if placed_any:
        n_placed += 1

years = [p["y"] for p in points if p["y"]]
ymin, ymax = (min(years), max(years)) if years else (1900, 1990)
data_json = json.dumps(points, ensure_ascii=False, separators=(",", ":"))

TPL = r"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carnegie Heldenfonds — kaart van reddingen</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<style>
  :root{
    --accent:#0e7490; --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb;
    --panel:#fffffff2; --shadow:0 8px 30px #00000026;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);
    -webkit-font-smoothing:antialiased}
  #map{position:absolute;inset:0}

  /* ---- control panel ---- */
  #panel{position:absolute;z-index:1000;top:14px;left:14px;width:322px;max-width:calc(100vw - 28px);
    background:var(--panel);backdrop-filter:blur(10px);border:1px solid #ffffff;border-radius:16px;
    box-shadow:var(--shadow);font-size:13px;max-height:calc(100vh - 28px);display:flex;flex-direction:column;overflow:hidden}
  .phead{display:flex;align-items:center;gap:10px;padding:14px 16px 12px;border-bottom:1px solid var(--line)}
  .phead .logo{width:34px;height:34px;flex:none;border-radius:9px;display:grid;place-items:center;font-size:19px;
    background:linear-gradient(135deg,#0e7490,#0891b2);box-shadow:0 2px 6px #0e749055}
  .phead h1{font-size:15px;margin:0;line-height:1.15;letter-spacing:-.01em}
  .phead .sub{color:var(--muted);font-size:10.5px;margin:1px 0 0}
  .phead .collapse{margin-left:auto;border:none;background:none;cursor:pointer;color:var(--muted);font-size:18px;
    width:26px;height:26px;border-radius:7px;flex:none}
  .phead .collapse:hover{background:#00000010;color:var(--ink)}
  .pbody{padding:10px 15px 12px;overflow-y:auto;overflow-x:hidden}
  #panel.collapsed .pbody{display:none}

  .count{font-size:21px;font-weight:700;letter-spacing:-.02em;line-height:1}
  .count small{font-size:11px;font-weight:500;color:var(--muted)}
  .noteband{background:#fef3c7;color:#92400e;padding:5px 9px;border-radius:8px;font-size:11px;margin:0 0 10px}

  .row{margin:11px 0 0}
  .row:first-child{margin-top:10px}
  .lbl{display:block;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.06em;
    color:var(--muted);margin-bottom:6px}
  .hint{text-transform:none;letter-spacing:0;font-weight:500;color:#9ca3af}
  /* collapsible sections */
  .acc{margin:11px 0 0;border-top:1px solid var(--line);padding-top:9px}
  .acc>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:6px;
    font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:1px 0}
  .acc>summary::-webkit-details-marker{display:none}
  .acc>summary::after{content:"▸";margin-left:auto;color:#9ca3af;font-size:11px;transition:transform .15s}
  .acc[open]>summary::after{transform:rotate(90deg)}
  .acc[open]>summary{margin-bottom:7px}
  .acc .toggle:first-of-type{margin-top:0}
  .acc.filtered>summary{color:var(--accent)}
  .acc.filtered>summary::before{content:"●";font-size:8px;color:var(--accent)}
  .yside{font-size:10px;font-weight:700;color:var(--muted);width:24px;flex:none;text-transform:uppercase;letter-spacing:.04em}
  input[type=search]{width:100%;padding:7px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:13px;background:#fff}
  input[type=search]:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px #0e749022}

  .cats{display:grid;grid-template-columns:1fr 1fr;gap:5px}
  .chip{display:flex;align-items:center;gap:5px;padding:5px 8px;border-radius:9px;cursor:pointer;font-size:12px;
    border:1px solid var(--line);background:#fff;user-select:none;transition:.12s;min-width:0}
  .chip:hover{border-color:#cbd5e1;background:#f8fafc}
  .chip input{display:none}
  .chip .em{font-size:14px;line-height:1;flex:none}
  .chip .nm{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
  .chip .ct{margin-left:auto;padding-left:4px;font-size:10px;color:var(--muted);font-variant-numeric:tabular-nums;flex:none}
  .chip.off{opacity:.42;background:#f1f5f9}
  .chip.off .em{filter:grayscale(1)}

  .ybadge{font-variant-numeric:tabular-nums;font-weight:700;font-size:12px;color:var(--accent)}
  /* dual-thumb range slider */
  .rangewrap{position:relative;height:26px;margin-top:8px}
  .rangetrack{position:absolute;top:11px;left:2px;right:2px;height:4px;border-radius:3px;background:#e5e7eb}
  .rangefill{position:absolute;top:11px;height:4px;border-radius:3px;background:var(--accent)}
  .rangewrap input[type=range]{position:absolute;top:0;left:0;width:100%;height:26px;margin:0;
    -webkit-appearance:none;appearance:none;background:none;pointer-events:none}
  .rangewrap input[type=range]::-webkit-slider-runnable-track{height:26px;background:none}
  .rangewrap input[type=range]::-moz-range-track{height:26px;background:none}
  .rangewrap input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;pointer-events:auto;
    width:16px;height:16px;border-radius:50%;background:#fff;border:2px solid var(--accent);
    box-shadow:0 1px 3px #0004;cursor:grab}
  .rangewrap input[type=range]::-moz-range-thumb{pointer-events:auto;width:16px;height:16px;border:2px solid var(--accent);
    border-radius:50%;background:#fff;box-shadow:0 1px 3px #0004;cursor:grab}
  .toggle{display:flex;align-items:center;gap:7px;font-size:12px;cursor:pointer;padding:2px 0}
  .toggle input{accent-color:var(--accent);width:15px;height:15px;flex:none}
  .toggle .ct{margin-left:auto;font-size:10px;color:var(--muted);font-variant-numeric:tabular-nums}
  .foot{border-top:1px solid var(--line);margin-top:12px;padding-top:9px;font-size:11px;color:var(--muted);
    display:flex;align-items:center;gap:6px}
  .foot a{color:var(--accent);text-decoration:none;font-weight:600}
  .foot a:hover{text-decoration:underline}

  /* ---- dossier list panel (big-city drill-in) ---- */
  #listp{position:absolute;z-index:1001;top:14px;right:14px;width:340px;max-width:calc(100vw - 28px);
    max-height:calc(100vh - 28px);background:var(--panel);backdrop-filter:blur(10px);border-radius:16px;
    box-shadow:var(--shadow);display:none;flex-direction:column;overflow:hidden}
  #listp.open{display:flex}
  .lhead{padding:12px 14px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:8px}
  .lhead .lt{font-weight:700;font-size:14px}
  .lhead .lc{font-size:11px;color:var(--muted)}
  .lhead .x{margin-left:auto;border:none;background:none;font-size:19px;cursor:pointer;color:var(--muted);
    width:26px;height:26px;border-radius:7px}
  .lhead .x:hover{background:#00000010;color:var(--ink)}
  #listSearch{margin:10px 14px 6px;padding:7px 10px;border:1px solid #d1d5db;border-radius:9px;font-size:12px}
  #listRows{overflow:auto;padding:2px 8px 10px}
  .lrow{display:flex;gap:8px;align-items:baseline;padding:7px 8px;border-radius:9px;cursor:pointer;border-bottom:1px solid #f1f5f9}
  .lrow:hover{background:#f0f9ff}
  .lrow .lnr{font-weight:700;font-size:11px;color:#fff;background:#334155;border-radius:5px;padding:1px 5px;flex:none}
  .lrow .lem{font-size:14px;flex:none}
  .lrow .ltx{font-size:12px;line-height:1.25;overflow:hidden}
  .lrow .lyr{margin-left:auto;font-size:10px;color:var(--muted);flex:none;font-variant-numeric:tabular-nums}

  /* ---- markers & popup ---- */
  .emoji-marker div{transition:transform .1s}
  .emoji-marker:hover div{transform:scale(1.25)}
  .lp{font-size:13px;line-height:1.4}
  .lp .nr{background:var(--accent);color:#fff;border-radius:6px;padding:2px 7px;font-weight:700;font-size:12px}
  .lp .badges{margin-top:8px}
  .lp .badge{display:inline-block;font-size:10px;padding:2px 7px;border-radius:20px;margin:2px 3px 0 0;color:#fff;font-weight:600}
  .lp a{color:var(--accent);font-weight:600;text-decoration:none}
  .lp a:hover{text-decoration:underline}
  .leaflet-popup-content-wrapper{border-radius:12px}
  .credit{position:absolute;z-index:1000;bottom:8px;left:14px;font-size:10px;color:#374151;background:#ffffffcc;
    padding:3px 8px;border-radius:7px}
  @media(max-width:600px){#panel{width:calc(100vw - 28px)} #listp{width:calc(100vw - 28px)}}
</style>
</head>
<body>
<div id="map"></div>
<div id="panel">
  <div class="phead">
    <div class="logo">🛟</div>
    <div>
      <h1>Carnegie Heldenfonds</h1>
      <p class="sub">Reddingen &middot; inventaris 2.19.364</p>
    </div>
    <button class="collapse" id="collapseBtn" title="In-/uitklappen">▾</button>
  </div>
  <div class="pbody">
    __NOTE__
    <div class="count"><span id="cnt">0</span> <small>reddingen zichtbaar <span id="cntsub"></span></small></div>
    <div class="row">
      <label class="lbl" for="q">Zoeken</label>
      <input id="q" type="search" placeholder="naam, plaats of inv.nr. — bijv. Amsterdam, Aa, 63">
    </div>
    <details class="acc" open>
      <summary>Aard van de redding</summary>
      <div class="cats" id="cats"></div>
    </details>
    <div class="row">
      <label class="lbl">Periode <span class="ybadge"><span id="yfromO"></span>–<span id="ytoO"></span></span></label>
      <div class="rangewrap">
        <div class="rangetrack"></div>
        <div class="rangefill" id="rangefill"></div>
        <input id="yfrom" type="range">
        <input id="yto" type="range">
      </div>
    </div>
    <details class="acc">
      <summary>Afloop</summary>
      <label class="toggle"><input type="checkbox" id="resOk" checked> ✅ geslaagde redding <span class="ct" id="ctOk"></span></label>
      <label class="toggle"><input type="checkbox" id="resPog" checked> ⭕ poging / omgekomen <span class="ct" id="ctPog"></span></label>
      <label class="toggle"><input type="checkbox" id="afg" checked> ⚖️ ook afgewezen aanvragen <span class="ct" id="ctAfg"></span></label>
      <label class="toggle"><input type="checkbox" id="steunTog" checked> 🤝 ook ondersteuning nabestaanden <span class="ct" id="ctSteun"></span></label>
    </details>
    <details class="acc">
      <summary>Openbaarheid</summary>
      <label class="toggle"><input type="checkbox" id="opOpen" checked> 🔓 openbaar <span class="ct" id="ctOpen"></span></label>
      <label class="toggle"><input type="checkbox" id="opRestr" checked> 🔒 beperkt openbaar <span class="ct" id="ctRestr"></span></label>
    </details>
    <div class="foot" style="justify-content:space-between">
      <a href="./stats" style="font-weight:700">📊 Inzichten &amp; statistiek →</a>
      <a href="./over" style="color:#6b7280">ℹ️ Over</a>
    </div>
  </div>
</div>

<div id="listp">
  <div class="lhead">
    <div><div class="lt" id="listTitle">Plaats</div><div class="lc" id="listCount"></div></div>
    <button class="x" id="listClose" title="Sluiten">×</button>
  </div>
  <input id="listSearch" type="search" placeholder="Filter deze lijst op naam of nr.">
  <div id="listRows"></div>
</div>

<div class="credit">Kaart &copy; OpenStreetMap-bijdragers &middot; data: Nationaal Archief 2.19.364</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const DATA = __DATA__;
const YMIN = __YMIN__, YMAX = __YMAX__;
const CATS = __CATS__;
const CATS_FULL = __CATSFULL__;
const COL  = __COL__;
const EMO  = __EMO__;

const map = L.map('map',{preferCanvas:true}).setView([52.13,5.25],8);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:''}).addTo(map);

// build category chips (with per-category counts)
const catCount={};
for(const p of DATA){catCount[p.cat]=(catCount[p.cat]||0)+1;}
const catBox = document.getElementById('cats');
const catState = {};
for(const c of Object.keys(CATS)){
  catState[c]=true;
  const l=document.createElement('label');
  l.className='chip'; l.dataset.cat=c;
  l.innerHTML=`<input type="checkbox" data-cat="${c}" checked><span class="em">${EMO[c]}</span>`+
    `<span class="nm">${CATS[c]}</span><span class="ct">${(catCount[c]||0).toLocaleString('nl')}</span>`;
  catBox.appendChild(l);
}

// dual-thumb year slider
const yfrom=document.getElementById('yfrom'), yto=document.getElementById('yto');
const yfromO=document.getElementById('yfromO'), ytoO=document.getElementById('ytoO'), rangefill=document.getElementById('rangefill');
for(const s of [yfrom,yto]){s.min=YMIN;s.max=YMAX;s.step=1;}
yfrom.value=YMIN; yto.value=YMAX;
function syncY(){
  let a=+yfrom.value, b=+yto.value;
  if(a>b){ if(document.activeElement===yfrom){yfrom.value=b;a=b;} else {yto.value=a;b=a;} }
  yfromO.textContent=a; ytoO.textContent=b;
  const p=v=>((v-YMIN)/(YMAX-YMIN))*100;
  rangefill.style.left=p(a)+'%'; rangefill.style.width=(p(b)-p(a))+'%';
  yfrom.style.zIndex=(document.activeElement===yfrom)?5:4;
  yto.style.zIndex=(document.activeElement===yto)?5:3;
}
syncY();

const qEl=document.getElementById('q'), afgEl=document.getElementById('afg');
const resOk=document.getElementById('resOk'), resPog=document.getElementById('resPog');
const opOpen=document.getElementById('opOpen'), opRestr=document.getElementById('opRestr');
const steunTog=document.getElementById('steunTog');
// counts for the toggle rows
(function(){
  let ok=0,pog=0,afg=0,open=0,restr=0,steun=0;
  for(const p of DATA){
    if(p.res==='poging')pog++; else ok++;
    if(p.afg)afg++;
    if(p.steun)steun++;
    if(p.openb)restr++; else open++;
  }
  const nl=n=>n.toLocaleString('nl');
  ctOk.textContent=nl(ok); ctPog.textContent=nl(pog); ctAfg.textContent=nl(afg);
  ctOpen.textContent=nl(open); ctRestr.textContent=nl(restr); ctSteun.textContent=nl(steun);
})();

const iconCache={};
function iconFor(cat,res){
  const key=cat+'|'+res;
  if(iconCache[key]) return iconCache[key];
  const emo=EMO[cat]||EMO.overig;
  const ring = res==='poging' ? 'box-shadow:0 0 0 2px #b91c1c;' : '';
  const ic=L.divIcon({className:'emoji-marker',
    html:`<div style="font-size:17px;line-height:22px;width:22px;height:22px;text-align:center;border-radius:50%;background:#ffffffcc;${ring}">${emo}</div>`,
    iconSize:[22,22],iconAnchor:[11,11],popupAnchor:[0,-10]});
  iconCache[key]=ic; return ic;
}
function esc(s){return (s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
// Build a targeted Delpher query: "<eerste voornaam> <achternaam>" + plaats + water/straat-detail.
// (volledige doopnamen geven 0 treffers; naam+plaats+detail vindt het reddingsbericht zelf.)
const TUSSEN=new Set(["van","de","der","den","ten","ter","te","op","aan","bij","in","het","'t","'s","vande","vander","uit","la","le","du"]);
function delpherURL(p){
  if(!p.who) return null;
  const parts=p.who.trim().split(/\s+/).filter(Boolean);
  if(!parts.length) return null;
  let si=parts.length-1;                       // surname start index
  for(let i=0;i<parts.length;i++){ if(TUSSEN.has(parts[i].toLowerCase())){ si=i; break; } }
  const surname=parts.slice(si).join(' ');
  const first=si>0?parts[0]:'';                // enkel de eerste voornaam/initiaal
  const name=((first?first+' ':'')+surname).trim();
  const q=(s)=>/\s/.test(s)?`"${s}"`:s;        // meerwoords-termen als frase
  let query=`"${name}"`;
  if(p.place) query+=' '+q(p.place);
  if(p.det)   query+=' '+q(p.det);
  return `https://www.delpher.nl/nl/kranten/results?query=${encodeURIComponent(query)}&coll=ddd`;
}
function popupHtml(p){
  const url=`https://www.nationaalarchief.nl/onderzoeken/archief/2.19.364/invnr/${p.nr}`;
  let b=`<div class="lp"><span class="nr">nr. ${p.nr}</span> &nbsp;<b>${esc(p.place)}</b>`;
  b+=`<div style="margin:6px 0">${esc(p.desc)}</div>`;
  b+=`<div style="color:#6b7280;font-size:12px">Jaar: ${esc(p.year||'?')}`;
  if(p.det) b+=` &middot; locatie: ${esc(p.det)}`;
  b+=` &middot; <span title="nauwkeurigheid van de marker">${p.prec==='straat'?'📍 straat/water':'🏙️ plaatsniveau'}</span></div>`;
  b+=`<div class="badges">`;
  b+=`<span class="badge" style="background:${COL[p.cat]}">${EMO[p.cat]} ${CATS_FULL[p.cat]}</span>`;
  b+=`<span class="badge" style="background:${p.res==='poging'?'#b45309':'#059669'}">${p.res==='poging'?'⭕ poging/omgekomen':'✅ geslaagd'}</span>`;
  if(p.afg) b+=`<span class="badge" style="background:#b91c1c">afgewezen</span>`;
  if(p.steun) b+=`<span class="badge" style="background:#78716c">🤝 ondersteuning nabestaanden</span>`;
  if(p.foto) b+=`<span class="badge" style="background:#059669">foto's</span>`;
  if(p.openb) b+=`<span class="badge" style="background:#6b7280">beperkt openbaar tot ${esc(p.openb)}</span>`;
  b+=`</div>`;
  b+=`<div style="margin-top:8px"><a href="${url}" target="_blank" rel="noopener">Bekijk in Nationaal Archief ↗</a></div>`;
  const durl=delpherURL(p);
  if(durl) b+=`<div style="margin-top:4px"><a href="${durl}" target="_blank" rel="noopener">Zoek krantenberichten (Delpher) ↗</a></div>`;
  b+=`</div>`;
  return b;
}

const cluster=L.markerClusterGroup({maxClusterRadius:48,spiderfyOnMaxZoom:false,
  showCoverageOnHover:false,zoomToBoundsOnClick:false,chunkedLoading:true,removeOutsideVisibleBounds:true});
const markers=DATA.map(p=>{
  const m=L.marker([p.lat,p.lon],{icon:iconFor(p.cat,p.res)});
  m.bindPopup(()=>popupHtml(p),{maxWidth:320});
  m._p=p;
  return m;
});
map.addLayer(cluster);

// Click a cluster: broad clusters zoom in to split; tight/coincident ones (a busy
// city plotted on one point) open a searchable dossier list instead of a useless spray.
cluster.on('clusterclick', a=>{
  const kids=a.layer.getAllChildMarkers();
  const b=a.layer.getBounds();
  const wide=(b.getNorth()-b.getSouth())>0.02 || (b.getEast()-b.getWest())>0.03;
  if(wide && map.getZoom()<13){ map.fitBounds(b.pad(0.2)); }
  else { openList(kids.map(m=>m._p)); }
});

// ---- dossier list panel ----
const listp=document.getElementById('listp'), listRows=document.getElementById('listRows'),
      listTitle=document.getElementById('listTitle'), listCount=document.getElementById('listCount'),
      listSearch=document.getElementById('listSearch');
let listData=[];
function renderList(){
  const q=listSearch.value.trim().toLowerCase();
  const rows=listData.filter(p=>!q || (p.desc+' '+p.nr+' '+(p.who||'')).toLowerCase().includes(q));
  listCount.textContent=`${rows.length} dossier${rows.length===1?'':'s'}`+(rows.length<listData.length?` (van ${listData.length})`:'');
  const frag=document.createDocumentFragment();
  for(const p of rows.slice(0,800)){
    const r=document.createElement('div'); r.className='lrow';
    const who=p.who||p.desc.split(',')[0];
    r.innerHTML=`<span class="lnr">${p.nr}</span><span class="lem">${EMO[p.cat]}</span>`+
      `<span class="ltx">${esc(who)}${p.det?` — <i>${esc(p.det)}</i>`:''}</span><span class="lyr">${esc(p.year||'')}</span>`;
    r.onclick=()=>{ map.setView([p.lat,p.lon], Math.max(map.getZoom(),13));
      L.popup({maxWidth:320}).setLatLng([p.lat,p.lon]).setContent(popupHtml(p)).openOn(map); };
    frag.appendChild(r);
  }
  listRows.innerHTML=''; listRows.appendChild(frag);
  if(rows.length>800){const m=document.createElement('div');m.style.cssText='padding:8px;color:#6b7280;font-size:11px';
    m.textContent=`… en ${rows.length-800} meer — verfijn met het filter hierboven`;listRows.appendChild(m);}
}
function openList(items){
  listData=items.slice().sort((x,y)=>x.nr-y.nr);
  listTitle.textContent=items[0]?items[0].place:'Dossiers';
  listSearch.value=''; renderList(); listp.classList.add('open');
}
document.getElementById('listClose').onclick=()=>listp.classList.remove('open');
listSearch.addEventListener('input',renderList);

function apply(){
  syncY();
  let yf=+yfrom.value, yt=+yto.value; if(yf>yt){[yf,yt]=[yt,yf];}
  const q=qEl.value.trim().toLowerCase();
  const showAfg=afgEl.checked;
  const okOk=resOk.checked, okPog=resPog.checked;
  const shOpen=opOpen.checked, shRestr=opRestr.checked;
  cluster.clearLayers();
  let n=0;
  const keep=[];
  for(const m of markers){
    const p=m._p;
    if(!catState[p.cat]) continue;
    if(p.res==='poging' ? !okPog : !okOk) continue;
    if(p.openb ? !shRestr : !shOpen) continue;
    if(!showAfg && p.afg) continue;
    if(!steunTog.checked && p.steun) continue;
    if(p.y!=null && (p.y<yf || p.y>yt)) continue;
    if(q){
      const hay=(p.desc+' '+p.place+' '+p.nr+' '+(p.year||'')).toLowerCase();
      if(!hay.includes(q)) continue;
    }
    keep.push(m); n++;
  }
  cluster.addLayers(keep);
  document.getElementById('cnt').textContent=n.toLocaleString('nl');
  document.getElementById('cntsub').textContent = n===markers.length? '' : `(van ${markers.length.toLocaleString('nl')})`;
  listp.classList.remove('open');
  // mark collapsed sections that have an active (unchecked) filter
  document.querySelectorAll('.acc').forEach(d=>{
    const any=[...d.querySelectorAll('input[type=checkbox]')].some(i=>!i.checked);
    d.classList.toggle('filtered', any);
  });
}

catBox.addEventListener('change',e=>{const c=e.target.dataset.cat; if(c){
  catState[c]=e.target.checked;
  e.target.closest('.chip').classList.toggle('off',!e.target.checked);
  apply();
}});
[yfrom,yto].forEach(s=>s.addEventListener('input',apply));
qEl.addEventListener('input',apply);
afgEl.addEventListener('change',apply);
resOk.addEventListener('change',apply);
resPog.addEventListener('change',apply);
opOpen.addEventListener('change',apply);
opRestr.addEventListener('change',apply);
steunTog.addEventListener('change',apply);
document.getElementById('collapseBtn').onclick=()=>{
  const p=document.getElementById('panel'); p.classList.toggle('collapsed');
  document.getElementById('collapseBtn').textContent = p.classList.contains('collapsed')?'▸':'▾';
};
apply();
// "Zoom op alles"-knop (ook buitenlandse reddingen)
const zoomAll=L.control({position:'topright'});
zoomAll.onAdd=function(){
  const d=L.DomUtil.create('div','leaflet-bar');
  d.innerHTML='<a href="#" title="Toon alle markers" style="width:auto;padding:0 8px;font-size:12px">Alles in beeld</a>';
  L.DomEvent.on(d,'click',L.DomEvent.stop).on(d,'click',()=>{
    const shown=cluster.getLayers().map(m=>[m._p.lat,m._p.lon]);
    if(shown.length) map.fitBounds(L.latLngBounds(shown).pad(0.08));
  });
  return d;
};
zoomAll.addTo(map);
</script>
</body>
</html>"""

note_html = (f'<div class="noteband">{html.escape(note)}</div>') if note else ""
def odict(dct): return json.dumps({c: dct[c] for c in CAT_ORDER}, ensure_ascii=False)
h=(TPL.replace("__DATA__", data_json).replace("__YMIN__", str(ymin))
      .replace("__YMAX__", str(ymax)).replace("__NOTE__", note_html)
      .replace("__CATS__", odict(CAT_LABEL)).replace("__CATSFULL__", odict(CAT_FULL))
      .replace("__COL__", odict(CAT_COL)).replace("__EMO__", odict(CAT_EMO)))
open(out, "w", encoding="utf-8").write(h)
print(f"geschreven: {out}")
print(f"dossiers in bereik: {n_range}; met minstens 1 plaats geplot: {n_placed}; markers (plaats-punten): {len(points)}")
print(f"jaarbereik: {ymin}-{ymax}")
