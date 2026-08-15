#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bouw het RGD-inzichtendashboard uit site/data.json (project-niveau, stabiel)."""
import json, os, html
from collections import Counter

WORK = os.path.dirname(os.path.abspath(__file__))
SITE = f"{WORK}/../site"
P = json.load(open(f"{SITE}/data.json", encoding="utf-8"))

nproj = len(P)
nbl = sum(p["n_bladen"] for p in P)
nplaats = len({p["stad"] for p in P})
nprec = Counter(p.get("prec") for p in P)
op_adres = nprec.get("adres", 0) + nprec.get("straat", 0)
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
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 8px}}
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
</style></head><body>
<nav class="ptabs"><a href="../">🗺️ Kaart</a><a href="./" class="on">📊 Inzichten</a><a href="../over/">ℹ️ Over</a><a href="https://archief.alanmoss.nl/" class="ext">← Archiefprojecten</a></nav>
<main>
  <div class="head"><div class="logo">📊</div><div><h1>Inzichten</h1><div class="sub">Tekeningenarchief van de Rijksgebouwendienst · Nationaal Archief 4.RGD</div></div></div>
  <div class="kpis">
    <div class="kpi"><b>{nl(nproj)}</b><span>bouwprojecten op de kaart</span></div>
    <div class="kpi"><b>{nl(nbl)}</b><span>tekeningen, foto's &amp; bestekken</span></div>
    <div class="kpi"><b>{nl(nplaats)}</b><span>plaatsen in Nederland</span></div>
    <div class="kpi"><b>{round(100*op_adres/nproj)}%</b><span>op straat- of adresniveau</span></div>
  </div>
  <div class="panel"><h2>Bouwprojecten per functie</h2>{bars(cat, emoji=EMC, fmt=nl)}</div>
  <div class="two">
    <div class="panel"><h2>Materiaal</h2>{bars(mat, emoji=EMO, fmt=nl)}</div>
    <div class="panel"><h2>Locatieprecisie</h2>{bars(prec, order=['adres','straat','plaats (terugval)'], fmt=nl)}</div>
  </div>
  <div class="panel"><h2>Per decennium (bouw- of tekeningjaar)</h2>{bars(dec, order=dec_order, fmt=nl)}</div>
  <div class="panel"><h2>Meeste bouwprojecten per plaats (top 15)</h2>{bars(steden, maxbars=15, fmt=nl)}</div>
  <div class="foot">Cijfers over de plaats-georganiseerde secties (IB/IIB tekeningen, IC foto's, ID bestekken). Bron: Nationaal Archief 4.RGD (CC0). Onderdeel van de <a href="https://archief.alanmoss.nl/">archiefprojecten</a>.</div>
</main></body></html>"""
os.makedirs(f"{SITE}/inzichten", exist_ok=True)
open(f"{SITE}/inzichten/index.html", "w", encoding="utf-8").write(HTML)
print(f"inzichten geschreven: {nproj} projecten, {nplaats} plaatsen")
