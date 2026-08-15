#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bouw de self-contained RGD-kaart (Leaflet + markercluster) uit rgd_<stad>.json."""
import json, os, sys
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
OUT = sys.argv[2] if len(sys.argv) > 2 else f"{WORK}/../site/index.html"
P = json.load(open(f"{WORK}/rgd_{PLACE.lower().replace(' ','_')}.json", encoding="utf-8"))

nbl = sum(x["n_bladen"] for x in P)
cats = [c for c, _ in Counter(x["cat"] for x in P).most_common()]
EM = {x["cat"]: x["emoji"] for x in P}
DATA = json.dumps(P, ensure_ascii=False, separators=(",", ":"))

HTML = r"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tekeningenarchief Rijksgebouwendienst — __PLACE__</title>
<meta name="description" content="Bouwtekeningen van de Rijksgebouwendienst (Nationaal Archief 4.RGD) op de kaart — proef: __PLACE__.">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<style>
:root{--accent:#0e7490;--accent-dark:#155e75;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--panel:rgba(255,255,255,.94);--bg:#f6f7f5}
*{box-sizing:border-box}
html,body{margin:0;height:100%;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink)}
#map{position:absolute;inset:0;background:#e8eef0}
.ptabs{position:fixed;top:14px;left:14px;z-index:1200;display:flex;gap:2px;background:var(--panel);backdrop-filter:blur(8px);
  border:1px solid var(--line);border-radius:12px;padding:4px 6px;box-shadow:0 2px 12px rgba(0,0,0,.1);max-width:calc(100vw - 28px)}
.ptabs a{font-size:13px;color:var(--ink);text-decoration:none;padding:6px 11px;border-radius:8px;white-space:nowrap}
.ptabs a.on{background:var(--accent);color:#fff}
.ptabs a:not(.on):hover{background:#eef6f8;color:var(--accent)}
.ptabs a.ext{color:var(--accent)}
#side{position:fixed;top:60px;left:14px;z-index:1100;width:330px;max-width:calc(100vw - 28px);max-height:calc(100vh - 74px);
  overflow:auto;background:var(--panel);backdrop-filter:blur(10px);border:1px solid var(--line);border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.12)}
.phead{display:flex;align-items:center;gap:10px;padding:14px 16px 10px}
.plogo{width:44px;height:44px;border-radius:12px;flex:none;display:grid;place-items:center;font-size:22px;background:linear-gradient(135deg,var(--accent),#0891b2);box-shadow:0 2px 8px #0e749055}
.phead h1{margin:0;font-size:17px;letter-spacing:-.01em}.phead .sub{font-size:12px;color:var(--muted);margin-top:1px}
.pcount{padding:0 16px 8px;font-size:13px}.pcount b{font-size:22px;color:var(--accent)}
.sec{padding:10px 16px;border-top:1px solid var(--line)}
.sec h2{margin:0 0 8px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:12px;border:1px solid var(--line);background:#fff;border-radius:20px;padding:4px 10px;cursor:pointer;user-select:none;display:inline-flex;gap:5px;align-items:center}
.chip .n{color:var(--muted);font-variant-numeric:tabular-nums}
.chip.off{opacity:.4}
.chip.on{border-color:var(--accent);background:#f0fafc}
.yr{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted)}
input[type=range]{flex:1;accent-color:var(--accent)}
#detail{position:fixed;top:14px;right:14px;z-index:1150;width:346px;max-width:calc(100vw - 28px);max-height:calc(100vh - 28px);
  overflow:auto;background:var(--panel);backdrop-filter:blur(10px);border:1px solid var(--line);border-top:3px solid var(--accent);
  border-radius:16px;box-shadow:0 6px 28px rgba(0,0,0,.18);display:none}
#detail.show{display:block}
.dscan{display:block;width:100%;height:180px;object-fit:cover;background:#eef2f4;border:1px solid var(--line);border-radius:10px;cursor:zoom-in;margin:2px 0 10px}
.dwrap{padding:12px 16px 16px}
.dclose{float:right;border:none;background:none;font-size:20px;color:var(--muted);cursor:pointer;line-height:1}
.dcat{font-size:11px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.05em}
.dtitle{font-size:16px;font-weight:700;margin:2px 0 6px;line-height:1.25}
.dmeta{font-size:12.5px;color:#374151;line-height:1.6}
.dmeta b{color:var(--ink)}
.badge{display:inline-block;font-size:10.5px;font-weight:600;padding:1px 7px;border-radius:20px;background:#eef2f4;color:#374151;margin-left:4px}
.badge.mf{background:#fef3c7;color:#92400e}
.dsheets{margin:10px 0 0;border-top:1px solid var(--line)}
.sh{display:flex;gap:8px;align-items:baseline;padding:6px 0;border-bottom:1px solid #f1f5f9;font-size:12.5px}
.sh a{color:var(--accent);text-decoration:none;font-weight:600;white-space:nowrap}
.sh a:hover{text-decoration:underline}
.sh .sc{color:var(--muted);font-size:11px}
.nalink{display:inline-block;margin-top:8px;font-size:12.5px;color:var(--accent);text-decoration:none}
.emoji-marker div{font-size:20px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.4));text-align:center;line-height:1}
.credit{position:fixed;left:14px;bottom:8px;z-index:1000;font-size:10px;color:#374151;background:#ffffffcc;padding:2px 7px;border-radius:6px}
.fbk{position:fixed;bottom:12px;right:12px;z-index:1200;font-size:12px;color:var(--accent);text-decoration:none;background:var(--panel);
  border:1px solid var(--line);padding:6px 12px;border-radius:20px;box-shadow:0 1px 5px rgba(0,0,0,.14)}
.fbk:hover{background:#fff;border-color:var(--accent)}
@media(max-width:640px){#side{width:calc(100vw - 28px)}}
</style>
</head>
<body>
<nav class="ptabs"><a href="./" class="on">🗺️ Kaart</a><a href="https://archief.alanmoss.nl/" class="ext">← Archiefprojecten</a></nav>
<div id="map"></div>
<div id="side">
  <div class="phead"><div class="plogo">📐</div><div><h1>Tekeningenarchief RGD</h1><div class="sub">Rijksgebouwendienst · Nationaal Archief 4.RGD</div></div></div>
  <div class="pcount"><b id="cnt">__NP__</b> bouwprojecten <span style="color:var(--muted)">· __NBL__ bladen · proef: __PLACE__</span></div>
  <div class="sec"><h2>Functie</h2><div class="chips" id="catchips"></div></div>
  <div class="sec"><h2>Soort tekening</h2><div class="chips" id="soortchips"></div></div>
  <div class="sec"><h2>Periode <span id="yrlab" style="color:var(--muted)"></span></h2>
    <div class="yr"><span id="y0"></span><input type="range" id="rmin"><input type="range" id="rmax"><span id="y1"></span></div></div>
</div>
<div id="detail"></div>
<a class="fbk" href="mailto:mossalan@gmail.com?subject=RGD-tekeningenkaart%3A%20feedback%20of%20bugmelding" title="Feedback of een fout melden">✉︎ Feedback</a>
<div class="credit">Kaart © OpenStreetMap-bijdragers · data: Nationaal Archief 4.RGD (CC0)</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const DATA = __DATA__;
const EM = __EM__;
const esc=s=>(s==null?'':''+s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const map=L.map('map',{preferCanvas:false,zoomControl:false}).setView([52.37,4.9],13);
L.control.zoom({position:'bottomright'}).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{subdomains:'abcd',maxZoom:19,attribution:''}).addTo(map);
const cluster=L.markerClusterGroup({maxClusterRadius:38,spiderfyOnMaxZoom:true}).addTo(map);
const yrs=DATA.flatMap(p=>[p.jaar_min,p.jaar_max]).filter(Boolean);
const YMIN=Math.min(...yrs), YMAX=Math.max(...yrs);
const cats=[...new Set(DATA.map(p=>p.cat))];
const soorten=[...new Set(DATA.map(p=>p.soort))];
const st={cat:new Set(cats),soort:new Set(soorten),y0:YMIN,y1:YMAX};

function chip(label,em,n,on){return `<span class="chip ${on?'on':'off'}">${em?em+' ':''}${esc(label)} <span class="n">${n}</span></span>`;}
function drawChips(){
  const cc={},sc={}; DATA.forEach(p=>{cc[p.cat]=(cc[p.cat]||0)+1;sc[p.soort]=(sc[p.soort]||0)+1;});
  document.getElementById('catchips').innerHTML=cats.map(c=>chip(c,EM[c],cc[c],st.cat.has(c))).join('');
  document.getElementById('soortchips').innerHTML=soorten.map(s=>chip(s,'',sc[s],st.soort.has(s))).join('');
  document.querySelectorAll('#catchips .chip').forEach((el,i)=>el.onclick=()=>toggle(st.cat,cats[i]));
  document.querySelectorAll('#soortchips .chip').forEach((el,i)=>el.onclick=()=>toggle(st.soort,soorten[i]));
}
function toggle(set,v){ set.has(v)?set.delete(v):set.add(v); if(set.size===0)DATA.forEach(()=>{}),set.add(v); drawChips(); render(); }
function match(p){ return st.cat.has(p.cat)&&st.soort.has(p.soort)&&(p.jaar_max==null||p.jaar_max>=st.y0)&&(p.jaar_min==null||p.jaar_min<=st.y1); }

function render(){
  cluster.clearLayers(); let n=0;
  DATA.forEach(p=>{ if(!match(p))return; n++;
    const m=L.marker([p.lat,p.lon],{icon:L.divIcon({className:'emoji-marker',html:`<div>${p.emoji}</div>`,iconSize:[24,24],iconAnchor:[12,12]})});
    m.on('click',()=>showDetail(p)); cluster.addLayer(m);
  });
  document.getElementById('cnt').textContent=n;
}
function showDetail(p){
  const d=document.getElementById('detail'); d.className='show';
  const per=(p.jaar_min?(p.jaar_min===p.jaar_max?p.jaar_min:p.jaar_min+'–'+p.jaar_max):'onbekend');
  const na='https://www.nationaalarchief.nl/onderzoeken/archief/4.RGD/invnr/'+encodeURIComponent(p.uid.split('-')[0]);
  const scan=p.thumb?`<a href="${p.scan_full||p.thumb}" target="_blank" rel="noopener" title="Open de scan bij het Nationaal Archief"><img class="dscan" src="${esc(p.thumb)}" loading="lazy" alt="voorbeeldscan"></a>`:'';
  const sheets=p.sheets.map(s=>`<div class="sh"><a href="${s.handle||na}" target="_blank" rel="noopener">${esc(s.id)} ↗</a>`
    +`<span>${esc(s.title||'Tekening')}${s.year?' · '+s.year:''}</span>`
    +`<span class="sc">${s.scale?esc(s.scale):''}${s.micro?' <span class="badge mf">microfilm</span>':''}</span></div>`).join('');
  d.innerHTML=`<div class="dwrap"><button class="dclose" onclick="document.getElementById('detail').className=''">×</button>
    <div class="dcat">${p.emoji} ${esc(p.cat)}</div><div class="dtitle">${esc(p.gebouw||p.titel)}</div>
    ${scan}
    <div class="dmeta">${p.locatie?'<b>'+esc(p.locatie)+'</b>, ':''}${esc(p.stad)}
      <span class="badge">${esc(p.prec)}</span><br>
      <b>Periode:</b> ${per} &nbsp; <b>Soort:</b> ${esc(p.soort)}<br>
      <b>${p.n_bladen}</b> bladen${p.n_micro?` · ${p.n_micro} alleen microfilm`:''}${p.schalen&&p.schalen.length?`<br><b>Schaal:</b> ${esc(p.schalen.join(', '))}`:''}</div>
    <div class="dsheets">${sheets}</div>
    <a class="nalink" href="${na}" target="_blank" rel="noopener">Open het bouwproject bij het Nationaal Archief →</a></div>`;
  map.setView([p.lat,p.lon],Math.max(map.getZoom(),15),{animate:true});
}
// year sliders
const rmin=document.getElementById('rmin'),rmax=document.getElementById('rmax');
[rmin,rmax].forEach(r=>{r.min=YMIN;r.max=YMAX;});rmin.value=YMIN;rmax.value=YMAX;
document.getElementById('y0').textContent=YMIN;document.getElementById('y1').textContent=YMAX;
function ylab(){document.getElementById('yrlab').textContent=(st.y0===YMIN&&st.y1===YMAX)?'':`(${st.y0}–${st.y1})`;}
function onYear(){st.y0=Math.min(+rmin.value,+rmax.value);st.y1=Math.max(+rmin.value,+rmax.value);ylab();render();}
rmin.oninput=onYear;rmax.oninput=onYear;
drawChips();render();
</script>
</body>
</html>"""
HTML = (HTML.replace("__DATA__", DATA).replace("__EM__", json.dumps(EM, ensure_ascii=False))
            .replace("__PLACE__", PLACE).replace("__NP__", str(len(P))).replace("__NBL__", f"{nbl:,}".replace(",", ".")))
open(OUT, "w", encoding="utf-8").write(HTML)
print(f"geschreven: {OUT}  ({len(P)} projecten, {nbl} bladen)")
