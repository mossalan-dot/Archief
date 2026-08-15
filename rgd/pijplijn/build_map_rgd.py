#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bouw de RGD-kaart (Leaflet + markercluster). Data wordt EXTERN geladen (data.json).
Argument = 'all' (hele objectenarchief) of één stad."""
import json, os, sys
from collections import Counter
from rgd_categories import categorie

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "all"
ALL = PLACE.lower() == "all"
SITE = f"{WORK}/../site"
P = json.load(open(f"{WORK}/rgd_{'all' if ALL else PLACE.lower().replace(' ','_')}.json", encoding="utf-8"))
P = [p for p in P if p.get("lat") is not None]
for p in P:
    if p.get("mat") == "overig": p["mat"] = "tekening"   # 'overig' materiaal onder tekening
    p["cat"], p["emoji"] = categorie(p.get("titel", ""))  # hercategoriseren met verbeterde trefwoorden
    for k in ("locatie", "gebouw"):                       # vierkante haken (editoriale toevoeging) strippen
        if p.get(k): p[k] = p[k].replace("[", "").replace("]", "").strip()
    p["invnr"] = p["uid"].split("-")[0].split(".")[0]     # afgekort inventarisnummer (1.1-1.48 -> 1)

nbl = sum(x["n_bladen"] for x in P)
EM = {x["cat"]: x["emoji"] for x in P}
SUB = "Nederland · hele objectenarchief" if ALL else f"proef: {PLACE}"
VIEW = "[52.15,5.4],7" if ALL else "[52.37,4.9],13"
json.dump(P, open(f"{SITE}/data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

HTML = r"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tekeningenarchief Rijksgebouwendienst</title>
<meta name="description" content="Bouwtekeningen van de Rijksgebouwendienst (Nationaal Archief 4.RGD, CC0) op de kaart — __SUB__.">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<style>
:root{--accent:#0e7490;--accent-dark:#155e75;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--panel:rgba(255,255,255,.94);--bg:#f6f7f5}
*{box-sizing:border-box}
html,body{margin:0;height:100%;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink)}
#map{position:absolute;inset:0;background:#e8eef0}
.ptabs{position:fixed;top:14px;left:14px;z-index:1200;display:flex;gap:2px;width:330px;max-width:calc(100vw - 28px);
  justify-content:space-between;background:var(--panel);backdrop-filter:blur(8px);
  border:1px solid var(--line);border-radius:12px;padding:4px 6px;box-shadow:0 2px 12px rgba(0,0,0,.1)}
.ptabs a{font-size:12.5px;color:var(--ink);text-decoration:none;padding:6px 9px;border-radius:8px;white-space:nowrap}
.ptabs a.on{background:var(--accent);color:#fff}
.ptabs a:not(.on):hover{background:#eef6f8;color:var(--accent)}
.ptabs a.ext{color:var(--accent)}
#side{position:fixed;top:60px;left:14px;z-index:1100;width:330px;max-width:calc(100vw - 28px);max-height:calc(100vh - 74px);
  overflow-y:auto;overflow-x:hidden;background:var(--panel);backdrop-filter:blur(10px);border:1px solid var(--line);border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.12)}
.phead{display:flex;align-items:center;gap:10px;padding:14px 16px 10px}
.plogo{width:44px;height:44px;border-radius:12px;flex:none;display:grid;place-items:center;font-size:22px;background:linear-gradient(135deg,var(--accent),#0891b2);box-shadow:0 2px 8px #0e749055}
.phead h1{margin:0;font-size:17px;letter-spacing:-.01em}.phead .sub{font-size:12px;color:var(--muted);margin-top:1px}
.pcount{padding:0 16px 8px;font-size:13px}.pcount b{font-size:22px;color:var(--accent)}
.psearch{padding:0 16px 10px}
.psearch input{width:100%;font:inherit;font-size:13px;padding:7px 10px;border:1px solid var(--line);border-radius:9px;background:#fff}
.sec{border-top:1px solid var(--line)}
.sec>summary{list-style:none;cursor:pointer;padding:10px 16px;display:flex;align-items:center}
.sec>summary::-webkit-details-marker{display:none}
.sec>summary::after{content:"+";margin-left:auto;color:var(--muted);font-size:16px;line-height:1}
.sec[open]>summary::after{content:"–"}
.sec.noco>summary{pointer-events:none}.sec.noco>summary::after{content:""}
.sec>summary:hover h2{color:var(--accent)}
.sec h2{margin:0;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.secbody{padding:0 16px 12px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:12px;border:1px solid var(--line);background:#fff;border-radius:20px;padding:4px 10px;cursor:pointer;user-select:none;display:inline-flex;gap:5px;align-items:center}
.chip .n{color:var(--muted);font-variant-numeric:tabular-nums}
.chip.off{opacity:.4}
.chip.on{border-color:var(--accent);background:#f0fafc}
.yr{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-top:4px}
.rangewrap{position:relative;height:24px}
.rtrack{position:absolute;top:10px;left:2px;right:2px;height:4px;background:var(--line);border-radius:3px}
.rfill{position:absolute;top:10px;height:4px;background:var(--accent);border-radius:3px}
.rr{position:absolute;top:0;left:0;width:100%;height:24px;margin:0;background:none;-webkit-appearance:none;appearance:none;pointer-events:none}
.rr::-webkit-slider-thumb{-webkit-appearance:none;pointer-events:auto;width:16px;height:16px;border-radius:50%;background:#fff;border:2px solid var(--accent);cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,.3)}
.rr::-moz-range-thumb{pointer-events:auto;width:15px;height:15px;border-radius:50%;background:#fff;border:2px solid var(--accent);cursor:pointer}
.carou{position:relative;margin:2px 0 4px}
.cnav{position:absolute;top:82px;border:none;background:rgba(255,255,255,.9);border-radius:50%;width:30px;height:30px;font-size:19px;line-height:1;color:var(--ink);cursor:pointer;box-shadow:0 1px 5px rgba(0,0,0,.25)}
.cnav:hover{background:#fff;color:var(--accent)}.cnav.prev{left:6px}.cnav.next{right:6px}
.cbar{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:7px;font-size:11.5px;color:var(--muted)}
.cpill .mf{color:#b45309;font-weight:600}
.ccount{font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
#detail{position:fixed;top:14px;right:14px;z-index:1150;width:346px;max-width:calc(100vw - 28px);max-height:calc(100vh - 28px);
  overflow:auto;background:var(--panel);backdrop-filter:blur(10px);border:1px solid var(--line);border-top:3px solid var(--accent);
  border-radius:16px;box-shadow:0 6px 28px rgba(0,0,0,.18);display:none}
#detail.show{display:block}
.dscan{display:block;width:100%;height:180px;object-fit:cover;background:#eef2f4;border:1px solid var(--line);border-radius:10px;cursor:zoom-in;margin:2px 0 10px}
.dwrap{padding:12px 16px 16px}
.dclose{float:right;border:none;background:none;font-size:20px;color:var(--muted);cursor:pointer;line-height:1}
.dtitle{font-size:16.5px;font-weight:700;margin:0 0 2px;line-height:1.25;color:var(--ink)}
.dloc{font-size:13px;color:var(--muted);margin:0}
.catbadge{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:var(--accent-dark);background:#e6f3f6;border-radius:20px;padding:3px 11px;margin:9px 0 2px}
.dmeta{font-size:12.5px;color:var(--muted);line-height:1.55;margin:9px 0 0}
.dmeta b{color:var(--ink);font-weight:600}
.wdlink{display:inline-block;margin:9px 0 0;font-size:12.5px;color:var(--accent);text-decoration:none}
.wdlink:hover{text-decoration:underline}
.dossbar{display:block;margin-top:10px;background:var(--accent);color:#fff;text-align:center;padding:9px 10px;border-radius:9px;font-weight:700;font-size:12.5px;text-decoration:none}
.dossbar:hover{background:var(--accent-dark)}
.emoji-marker div{font-size:20px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.4));text-align:center;line-height:1}
.credit{position:fixed;left:14px;bottom:8px;z-index:1000;font-size:10px;color:#374151;background:#ffffffcc;padding:2px 7px;border-radius:6px}
.fbk{position:fixed;bottom:12px;right:12px;z-index:1200;font-size:12px;color:var(--accent);text-decoration:none;background:var(--panel);
  border:1px solid var(--line);padding:6px 12px;border-radius:20px;box-shadow:0 1px 5px rgba(0,0,0,.14)}
.fbk:hover{background:#fff;border-color:var(--accent)}
@media(max-width:640px){#side{width:calc(100vw - 28px)}}
</style>
</head>
<body>
<nav class="ptabs"><a href="./" class="on">🗺️ Kaart</a><a href="./inzichten/">📊 Inzichten</a><a href="./over/">ℹ️ Over</a><a href="https://archief.alanmoss.nl/" class="ext" title="Alle archiefprojecten">←</a></nav>
<div id="map"></div>
<div id="side">
  <div class="phead"><div class="plogo">📐</div><div><h1>Tekeningenarchief RGD</h1><div class="sub">__SUB__</div></div></div>
  <div class="pcount"><b id="cnt">…</b> bouwprojecten <span style="color:var(--muted)">· __NBL__ bladen (Nationaal Archief 4.RGD)</span></div>
  <div class="psearch"><input id="q" type="search" placeholder="Zoek op plaats, gebouw of straat…" autocomplete="off"></div>
  <details class="sec"><summary><h2>Materiaal</h2></summary><div class="secbody"><div class="chips" id="matchips"></div></div></details>
  <details class="sec"><summary><h2>Functie</h2></summary><div class="secbody"><div class="chips" id="catchips"></div></div></details>
  <details class="sec"><summary><h2>Soort tekening</h2></summary><div class="secbody"><div class="chips" id="soortchips"></div></div></details>
  <details class="sec noco" open><summary><h2>Periode <span id="yrlab" style="color:var(--muted);text-transform:none;letter-spacing:0"></span></h2></summary>
    <div class="secbody"><div class="rangewrap"><div class="rtrack"></div><div class="rfill" id="rfill"></div>
      <input type="range" id="rmin" class="rr"><input type="range" id="rmax" class="rr"></div>
    <div class="yr"><span id="y0"></span><span id="y1"></span></div></div></details>
</div>
<div id="detail"></div>
<a class="fbk" href="mailto:mossalan@gmail.com?subject=RGD-tekeningenkaart%3A%20feedback%20of%20bugmelding" title="Feedback of een fout melden">✉︎ Feedback</a>
<div class="credit">Kaart © OpenStreetMap-bijdragers · data: Nationaal Archief 4.RGD (CC0)</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const EM = __EM__;
const MAT_EM={tekening:'📐',foto:'📷',bestek:'📄',overig:'📎'};
const esc=s=>(s==null?'':''+s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const map=L.map('map',{preferCanvas:false,zoomControl:false}).setView(__VIEW__);
L.control.zoom({position:'bottomright'}).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{subdomains:'abcd',maxZoom:19,attribution:''}).addTo(map);
const cluster=L.markerClusterGroup({maxClusterRadius:44,spiderfyOnMaxZoom:true,chunkedLoading:true}).addTo(map);
let DATA=[], YMIN=0, YMAX=0, cats=[], soorten=[], mats=[], st={mat:new Set(),cat:new Set(),soort:new Set(),y0:0,y1:0,q:''};
let CUR=null, CSC=[], CIX=0;

function chip(label,em,n,on){return `<span class="chip ${on?'on':'off'}">${em?em+' ':''}${esc(label)} <span class="n">${n}</span></span>`;}
function drawChips(){
  const mm={},cc={},sc={}; DATA.forEach(p=>{mm[p.mat]=(mm[p.mat]||0)+1;cc[p.cat]=(cc[p.cat]||0)+1;sc[p.soort]=(sc[p.soort]||0)+1;});
  document.getElementById('matchips').innerHTML=mats.map(m=>chip(m,MAT_EM[m]||'',mm[m],st.mat.has(m))).join('');
  document.getElementById('catchips').innerHTML=cats.map(c=>chip(c,EM[c],cc[c],st.cat.has(c))).join('');
  document.getElementById('soortchips').innerHTML=soorten.map(s=>chip(s,'',sc[s],st.soort.has(s))).join('');
  document.querySelectorAll('#matchips .chip').forEach((el,i)=>el.onclick=()=>toggle(st.mat,mats,mats[i]));
  document.querySelectorAll('#catchips .chip').forEach((el,i)=>el.onclick=()=>toggle(st.cat,cats,cats[i]));
  document.querySelectorAll('#soortchips .chip').forEach((el,i)=>el.onclick=()=>toggle(st.soort,soorten,soorten[i]));
}
function toggle(set,all,v){
  if(set.size===1&&set.has(v)) all.forEach(x=>set.add(x));   // stond op solo -> toon weer alles
  else { set.clear(); set.add(v); }                          // toon alleen deze
  drawChips(); render();
}
function match(p){
  if(!st.mat.has(p.mat)||!st.cat.has(p.cat)||!st.soort.has(p.soort)) return false;
  if(!(p.jaar_max==null||p.jaar_max>=st.y0)||!(p.jaar_min==null||p.jaar_min<=st.y1)) return false;
  if(st.q){ const h=((p.stad||'')+' '+(p.gebouw||'')+' '+(p.locatie||'')+' '+(p.titel||'')).toLowerCase(); if(h.indexOf(st.q)<0) return false; }
  return true;
}
function render(){
  cluster.clearLayers(); let n=0; const ms=[];
  DATA.forEach(p=>{ if(!match(p))return; n++;
    const m=L.marker([p.lat,p.lon],{icon:L.divIcon({className:'emoji-marker',html:`<div>${p.emoji}</div>`,iconSize:[24,24],iconAnchor:[12,12]})});
    m.on('click',()=>showDetail(p)); ms.push(m);
  });
  cluster.addLayers(ms);
  document.getElementById('cnt').textContent=n;
}
function showDetail(p){ CUR=p; CSC=p.sheets||[];
  CIX=CSC.findIndex(s=>s.thumb); if(CIX<0)CIX=0;
  renderDetail(); map.setView([p.lat,p.lon],Math.max(map.getZoom(),15),{animate:true}); }
function carouNav(dr){ if(CSC.length){ CIX=(CIX+dr+CSC.length)%CSC.length; renderDetail(); } }
function renderDetail(){
  const p=CUR, d=document.getElementById('detail'); d.className='show';
  const per=(p.jaar_min?(p.jaar_min===p.jaar_max?p.jaar_min:p.jaar_min+'–'+p.jaar_max):'onbekend');
  const na='https://www.nationaalarchief.nl/onderzoeken/archief/4.RGD/invnr/'+encodeURIComponent(p.uid.split('-')[0]);
  const ph="data:image/svg+xml,"+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180"><rect width="100%" height="100%" fill="#eef2f4"/><text x="160" y="116" font-size="64" text-anchor="middle">'+p.emoji+'</text></svg>');
  let carou='';
  if(CSC.length){ const s=CSC[CIX]; const href=s.full||s.handle||na;
    carou=`<div class="carou"><a href="${esc(href)}" target="_blank" rel="noopener" title="Open de scan bij het Nationaal Archief"><img class="dscan" src="${esc(s.thumb||ph)}" loading="lazy" alt="scan ${esc(s.id)}" onerror="this.onerror=null;this.src='${ph}'"></a>`
      +(CSC.length>1?`<button class="cnav prev" onclick="carouNav(-1)">‹</button><button class="cnav next" onclick="carouNav(1)">›</button>`:'')
      +`<div class="cbar"><span class="cpill">blad ${esc(s.id)}${s.micro?' <span class="mf">· microfilm</span>':''}</span><span class="ccount">${CIX+1} / ${CSC.length}</span></div></div>`;
  }
  const n=p.n_bladen, bl=n+' blad'+(n===1?'':'en');
  d.innerHTML=`<div class="dwrap"><button class="dclose" onclick="document.getElementById('detail').className=''">×</button>
    <div class="dtitle">${esc(p.gebouw||p.titel)}</div>
    <div class="dloc">${p.locatie?esc(p.locatie)+', ':''}${esc(p.stad)}</div>
    <div class="catbadge">${p.emoji} ${esc(p.cat)}</div>
    ${carou}
    <div class="dmeta"><b>${esc(per)}</b> · ${esc(p.soort)} · ${bl}${p.n_micro?` · ${p.n_micro} microfilm`:''}${p.schalen&&p.schalen.length?` · schaal ${esc(p.schalen.join(', '))}`:''}</div>
    ${p.wd?`<a class="wdlink" href="${esc(p.wd.url)}" target="_blank" rel="noopener">🔗 Wikidata: ${esc(p.wd.label)} ↗</a>`:''}
    <a class="dossbar" href="${na}" target="_blank" rel="noopener">📄 Inventaris ${esc(p.invnr)} bij het Nationaal Archief</a>
  </div>`;
}
const rmin=document.getElementById('rmin'),rmax=document.getElementById('rmax'),rfill=document.getElementById('rfill');
function ylab(){document.getElementById('yrlab').textContent=(st.y0===YMIN&&st.y1===YMAX)?'':`(${st.y0}–${st.y1})`;}
function rfl(){const sp=(YMAX-YMIN)||1,a=(st.y0-YMIN)/sp*100,b=(st.y1-YMIN)/sp*100;rfill.style.left=a+'%';rfill.style.width=(b-a)+'%';}
function onYear(){st.y0=Math.min(+rmin.value,+rmax.value);st.y1=Math.max(+rmin.value,+rmax.value);ylab();rfl();render();}
document.getElementById('q').oninput=e=>{st.q=e.target.value.trim().toLowerCase();render();};

fetch('./data.json').then(r=>r.json()).then(d=>{
  DATA=d;
  const yrs=DATA.flatMap(p=>[p.jaar_min,p.jaar_max]).filter(Boolean);
  YMIN=Math.min(...yrs); YMAX=Math.max(...yrs);
  const byCnt=k=>{const m={};DATA.forEach(p=>m[p[k]]=(m[p[k]]||0)+1);return Object.keys(m).sort((a,b)=>m[b]-m[a]);};
  mats=byCnt('mat'); cats=byCnt('cat'); soorten=byCnt('soort');
  st.mat=new Set(mats); st.cat=new Set(cats); st.soort=new Set(soorten); st.y0=YMIN; st.y1=YMAX;
  [rmin,rmax].forEach(r=>{r.min=YMIN;r.max=YMAX;r.step=1;}); rmin.value=YMIN; rmax.value=YMAX;
  document.getElementById('y0').textContent=YMIN; document.getElementById('y1').textContent=YMAX;
  rmin.oninput=onYear; rmax.oninput=onYear; rfl();
  drawChips(); render();
});
</script>
</body>
</html>"""
HTML = (HTML.replace("__EM__", json.dumps(EM, ensure_ascii=False)).replace("__VIEW__", VIEW)
            .replace("__SUB__", SUB).replace("__NBL__", f"{nbl:,}".replace(",", ".")))
open(f"{SITE}/index.html", "w", encoding="utf-8").write(HTML)
print(f"geschreven: {SITE}/index.html + data.json  ({len(P)} projecten met coord, {nbl} bladen)")
