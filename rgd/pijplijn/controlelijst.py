#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genereer een controlelijst (xlsx) van RGD-bouwprojecten — voor handmatige verrijking.
Markeert wat alleen op stad-niveau (of grover) staat: die hebben een preciezere bron nodig."""
import json, os, sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

WORK = os.path.dirname(os.path.abspath(__file__))
PLACE = sys.argv[1] if len(sys.argv) > 1 else "Amsterdam"
P = json.load(open(f"{WORK}/rgd_{PLACE.lower().replace(' ','_')}.json", encoding="utf-8"))

wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Controlelijst"
cols = ["Inv.nr.", "Gebouw", "Locatie (uit titel)", "Stad", "Categorie", "Soort", "Jaren",
        "Precisie", "Geo-bron", "Gevonden adres", "Bladen", "Actie nodig?", "NA-link"]
ws.append(cols)
head = Font(bold=True, color="FFFFFF"); fill = PatternFill("solid", fgColor="0E7490")
for c in ws[1]: c.font = head; c.fill = fill; c.alignment = Alignment(vertical="center")
warn = PatternFill("solid", fgColor="FEF3C7")

for p in sorted(P, key=lambda x: (x.get("prec") != "plaats", x["uid"])):
    jr = f"{p['jaar_min']}" + (f"–{p['jaar_max']}" if p.get("jaar_max") and p["jaar_max"] != p["jaar_min"] else "") if p.get("jaar_min") else ""
    na = "https://www.nationaalarchief.nl/onderzoeken/archief/4.RGD/invnr/" + p["uid"].split("-")[0]
    actie = "JA — alleen stad" if p.get("prec") == "plaats" else ""
    row = [p["uid"], p.get("gebouw", ""), p.get("locatie") or "", p["stad"], p["cat"], p["soort"], jr,
           p.get("prec", ""), p.get("bron_geo", ""), p.get("geo_naam", ""), p["n_bladen"], actie, na]
    ws.append(row)
    if p.get("prec") == "plaats":
        for c in ws[ws.max_row]: c.fill = warn

widths = [12, 34, 24, 12, 18, 13, 10, 10, 9, 34, 8, 16, 40]
for i, w in enumerate(widths, 1): ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
ws.freeze_panes = "A2"
out = f"{WORK}/RGD-{PLACE}-controlelijst.xlsx"
wb.save(out)
nwarn = sum(1 for p in P if p.get("prec") == "plaats")
print(f"{out}  ({len(P)} rijen, {nwarn} met actie nodig)")
