#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bouw het RGD-inzichtendashboard uit site/data.json (project-niveau, stabiel)."""
import json, os, html
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
SITE = f"{WORK}/../site"
P = json.load(open(f"{SITE}/data.json", encoding="utf-8"))

nproj = len(P)
ntot = nproj                                            # totaal incl. niet-gelokaliseerde (uit rgd_all.json)
try:
    _A = json.load(open(f"{WORK}/rgd_all.json", encoding="utf-8"))
    ntot = sum(1 for p in _A if (p.get("uid") or "").strip() and p.get("stad") != "Geordend per gemeente")
except Exception:
    pass
pct_map = round(100 * nproj / ntot) if ntot else 100
nbl = sum(p["n_bladen"] for p in P)
nplaats = len({p["stad"] for p in P})
nprec = Counter(p.get("prec") for p in P)
op_adres = nprec.get("adres", 0) + nprec.get("straat", 0)
n_micro = sum(p.get("n_micro", 0) for p in P)
pct_orig = round(100 * (nbl - n_micro) / nbl) if nbl else 0
prov = Counter(("Friesland" if p.get("provincie") == "Fryslân" else p.get("provincie"))
               for p in P if p.get("provincie"))
EMO = {"tekening": "📐", "foto": "📷", "bestek": "📄"}
EMC = {p["cat"]: p["emoji"] for p in P}

def esc(s): return html.escape(str(s))
def bars(counter, order=None, emoji=None, maxbars=99, fmt=str):
    items = order or [k for k, _ in counter.most_common()]
    items = items[:maxbars]
    mx = max([counter[k] for k in items] + [1])
    rows = ""
    for k in items:
        v = counter[k]; w = round(100 * v / mx, 1)
        em = (emoji.get(k, "") + " ") if emoji else ""
        rows += (f'<div class="row"><div class="lab">{em}{esc(k)}</div>'
                 f'<div class="track"><div class="fill" style="width:{w}%"></div></div>'
                 f'<div class="val">{fmt(v)}</div></div>')
    return rows

def linechart(order, counter):
    W, H, pl, pr, pt, pb = 840, 180, 40, 14, 16, 28
    iw, ih = W - pl - pr, H - pt - pb
    mx = max([counter[d] for d in order] + [1]); n = len(order)
    X = lambda i: pl + (iw * (i / (n - 1) if n > 1 else 0))
    Y = lambda v: pt + ih - (ih * v / mx)
    pts = [(X(i), Y(counter[d])) for i, d in enumerate(order)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{X(0):.1f},{pt+ih:.1f} " + poly + f" {X(n-1):.1f},{pt+ih:.1f}"
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#0e7490"/>'
                   f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="14" fill="transparent" '
                   f'style="cursor:help" data-tip="{order[i]}–{order[i]+9}: {nl(counter[order[i]])} bouwprojecten"/>'
                   for i, (x, y) in enumerate(pts))
    xl = "".join(f'<text x="{X(i):.1f}" y="{H-8}" font-size="10" fill="#6b7280" text-anchor="middle">{order[i]}</text>' for i in range(0, n, 2))
    grid = (f'<line x1="{pl}" y1="{pt}" x2="{W-pr}" y2="{pt}" stroke="#eef2f4"/>'
            f'<text x="{pl-6}" y="{pt+4}" font-size="10" fill="#94a3b8" text-anchor="end">{mx}</text>'
            f'<line x1="{pl}" y1="{pt+ih}" x2="{W-pr}" y2="{pt+ih}" stroke="#e5e7eb"/>')
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" style="height:auto;display:block">'
            f'{grid}<polygon points="{area}" fill="#0e749020"/>'
            f'<polyline points="{poly}" fill="none" stroke="#0e7490" stroke-width="2.5" stroke-linejoin="round"/>{dots}{xl}</svg>')

cat = Counter(p["cat"] for p in P)
mat = Counter(p["mat"] for p in P)
steden = Counter(p["stad"] for p in P)
dec = Counter((p["jaar_min"] // 10 * 10) for p in P if p.get("jaar_min"))
dec_order = [d for d in range(min(dec) if dec else 1820, (max(dec) if dec else 1940) + 10, 10)]
prec = Counter({"adres": nprec.get("adres", 0), "straat": nprec.get("straat", 0),
                "plaats (terugval)": nprec.get("plaats", 0)})

def nl(n): return f"{n:,}".replace(",", ".")

HTML = f"""<!DOCTYPE html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inzichten — Tekeningenarchief Rijksgebouwendienst</title>
<meta name="description" content="Cijfers en grafieken over het tekeningenarchief van de Rijksgebouwendienst (Nationaal Archief 4.RGD).">
<style>
:root{{--accent:#0e7490;--accent-dark:#155e75;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--bg:#f6f7f5;--card:#fff}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}}
.ptabs{{display:flex;gap:2px;max-width:900px;margin:14px auto 0;padding:4px 6px;background:var(--card);border:1px solid var(--line);border-radius:12px;width:fit-content}}
.ptabs a{{font-size:13px;color:var(--ink);text-decoration:none;padding:6px 12px;border-radius:8px;white-space:nowrap}}
.ptabs a.on{{background:var(--accent);color:#fff}}.ptabs a:not(.on):hover{{background:#eef6f8;color:var(--accent)}}
main{{max-width:900px;margin:0 auto;padding:24px 22px 70px}}
.head{{display:flex;align-items:center;gap:14px;margin:4px 0 18px}}
.logo{{width:52px;height:52px;border-radius:14px;flex:none;display:grid;place-items:center;font-size:26px;background:linear-gradient(135deg,var(--accent),#0891b2);box-shadow:0 2px 10px #0e749033}}
h1{{font-size:25px;margin:0;letter-spacing:-.02em}}.sub{{color:var(--muted);font-size:14px;margin-top:2px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:12px;margin:0 0 8px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}}
.kpi b{{display:block;font-size:26px;color:var(--accent);letter-spacing:-.02em}}.kpi span{{font-size:12.5px;color:var(--muted)}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:16px 0}}
.panel h2{{margin:0 0 12px;font-size:15px;letter-spacing:-.01em}}
.row{{display:grid;grid-template-columns:180px 1fr 54px;align-items:center;gap:10px;margin:5px 0;font-size:13px}}
.lab{{color:#374151;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.track{{background:#eef2f4;border-radius:6px;height:14px;overflow:hidden}}
.fill{{background:linear-gradient(90deg,var(--accent),#0891b2);height:100%;border-radius:6px}}
.val{{text-align:right;color:var(--muted);font-variant-numeric:tabular-nums}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:720px){{.kpis{{grid-template-columns:1fr 1fr}}.two{{grid-template-columns:1fr}}.row{{grid-template-columns:130px 1fr 46px}}}}
.foot{{margin-top:26px;font-size:13px;color:var(--muted)}}.foot a{{color:var(--accent)}}
#tip{{position:fixed;z-index:9999;background:#1f2937;color:#fff;font-size:12px;padding:6px 9px;border-radius:7px;pointer-events:none;opacity:0;transition:opacity .1s;max-width:270px;line-height:1.45;box-shadow:0 6px 18px rgba(0,0,0,.22)}}
.fbk{{position:fixed;bottom:12px;right:12px;z-index:1200;font-size:12px;color:var(--accent);text-decoration:none;background:var(--card);border:1px solid var(--line);padding:6px 12px;border-radius:20px;box-shadow:0 1px 5px rgba(0,0,0,.14)}}
.fbk:hover{{background:#fff;border-color:var(--accent)}}
</style></head><body>
<nav class="ptabs"><a href="../">🗺️ Kaart</a><a href="./" class="on">📊 Inzichten</a><a href="../over/">ℹ️ Over</a><a href="https://archief.alanmoss.nl/" class="ext">← Archiefprojecten</a></nav>
<main>
  <div class="head"><div class="logo">📊</div><div><h1>Inzichten</h1><div class="sub">Tekeningenarchief van de Rijksgebouwendienst · Nationaal Archief 4.RGD</div></div></div>
  <div class="kpis">
    <div class="kpi" style="cursor:help" data-tip="{pct_map}% van alle {nl(ntot)} bouwprojecten kon worden gelokaliseerd · {nl(ntot-nproj)} zonder bruikbare locatie (alleen op inv.nr. te vinden)"><b>{nl(nproj)}</b><span>bouwprojecten op de kaart&nbsp; <span style="color:#94a3b8">&#9432;</span></span></div>
    <div class="kpi"><b>{nl(nbl)}</b><span>tekeningen, foto's &amp; bestekken</span></div>
    <div class="kpi"><b>{nl(nplaats)}</b><span>plaatsen in Nederland</span></div>
    <div class="kpi" style="cursor:help" data-tip="Adres: {nl(nprec.get('adres',0))} · Straat: {nl(nprec.get('straat',0))} · Alleen plaats (terugval): {nl(nprec.get('plaats',0))}"><b>{round(100*op_adres/nproj)}%</b><span>op straat- of adresniveau&nbsp; <span style="color:#94a3b8">&#9432;</span></span></div>
    <div class="kpi" style="cursor:help" data-tip="{pct_orig}% origineel gedigitaliseerd · {100-pct_orig}% alleen op microfilm bewaard"><b>{pct_orig}%</b><span>origineel gedigitaliseerd&nbsp; <span style="color:#94a3b8">&#9432;</span></span></div>
  </div>
  <div class="panel"><h2>Bouwprojecten per functie</h2>{bars(cat, emoji=EMC, fmt=nl)}</div>
  <div class="panel"><h2>Materiaal</h2>{bars(mat, emoji=EMO, fmt=nl)}</div>
  {'<div class="panel"><h2>Bouwprojecten per provincie</h2>' + bars(prov, fmt=nl) + '</div>' if prov else ''}
  <div class="panel"><h2>Per decennium (bouw- of tekeningjaar)</h2>{linechart(dec_order, dec)}</div>
  <div class="foot">Cijfers over de plaats-georganiseerde secties (IB/IIB tekeningen, IC foto's, ID bestekken). Bron: Nationaal Archief 4.RGD (CC0). Onderdeel van de <a href="https://archief.alanmoss.nl/">archiefprojecten</a>.</div>
</main>
<a class="fbk" href="mailto:mossalan@gmail.com?subject=RGD-tekeningenkaart%3A%20feedback%20of%20bugmelding" title="Feedback of een fout melden">✉︎ Feedback</a>
<div id="tip"></div>
<script>
(function(){{
  var tip=document.getElementById('tip');
  function move(e){{var x=e.clientX+14,y=e.clientY+16,w=tip.offsetWidth,h=tip.offsetHeight;
    if(x+w>innerWidth-8)x=e.clientX-w-14; if(y+h>innerHeight-8)y=e.clientY-h-16;
    tip.style.left=x+'px';tip.style.top=y+'px';}}
  document.addEventListener('mouseover',function(e){{
    var t=e.target.closest('[data-tip]');
    if(t){{tip.textContent=t.getAttribute('data-tip');tip.style.opacity=1;move(e);}}
    else{{tip.style.opacity=0;}}
  }});
  document.addEventListener('mousemove',function(e){{if(tip.style.opacity==1)move(e);}});
}})();
</script>
</body></html>"""
os.makedirs(f"{SITE}/inzichten", exist_ok=True)
open(f"{SITE}/inzichten/index.html", "w", encoding="utf-8").write(HTML)
print(f"inzichten geschreven: {nproj} projecten, {nplaats} plaatsen")
