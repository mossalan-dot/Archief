#!/usr/bin/env python3
"""dossiermap.py — bouw de opzoektabel dossiernummer -> inventarisnummer.

De kaarten in de klapper (serie B) noemen een "Dossier nr". De onderliggende
persoonsdossiers staan in serie A, gegroepeerd per inventarisnummer in blokken:

    A1.1  inv.nr 1-592    dossiers 1-118139        (aangifte van overlijden gedaan)
    A1.2  inv.nr 593-613  dossiers (aparte reeksen) (geen aangifte gedaan)

Elk inv.nr beschrijft in zijn titel het dossiernummer-bereik ("27201-27400").
Dit script leest die bereiken uit de EAD-inventaris en schrijft een
interval-tabel + directe deeplinks naar het Nationaal Archief.

Uitvoer: dossiermap.json
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TOEGANG = "2.09.34.02"
EAD = Path(__file__).with_name(f"{TOEGANG}.ead.xml")
OUT = Path(__file__).with_name("dossiermap.json")

NA = "https://www.nationaalarchief.nl/onderzoeken/archief"


def text(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def load_ead(path: Path):
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<!DOCTYPE.*?>", "", raw, flags=re.S)  # geen DTD-fetch
    return ET.fromstring(raw)


def parse_range(title: str):
    """'27201-27400' -> (27201, 27400); '650' -> (650, 650)."""
    m = re.match(r"^\s*(\d+)\s*[-–]\s*(\d+)\s*$", title)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"^\s*(\d+)\s*$", title)
    if m:
        return int(m.group(1)), int(m.group(1))
    return None


def collect(root):
    """Loop alle serie-A inv.nrs af en verzamel (invnr, lo, hi, serie, handle)."""
    intervals = []
    for c in root.iter("c"):
        did = c.find("did")
        if did is None or c.get("level") != "file":
            continue
        unitid = did.find("unitid")
        if unitid is None:
            continue
        invnr = text(unitid)
        if not invnr.isdigit():
            continue
        invnr_i = int(invnr)
        # serie A = inv.nr 1..613; serie B (klapper) = 614..744
        if invnr_i > 613:
            continue
        rng = parse_range(text(did.find("unittitle")))
        if not rng:
            continue
        serie = "A1.1" if invnr_i <= 592 else "A1.2"
        handle = ""
        for u in did.findall("unitid"):
            if u.get("type") == "handle":
                handle = text(u)
        intervals.append(
            {
                "invnr": invnr_i,
                "lo": rng[0],
                "hi": rng[1],
                "serie": serie,
                "handle": handle,
                "url": f"{NA}/{TOEGANG}/invnr/{invnr_i}",
            }
        )
    return intervals


def main():
    if not EAD.exists():
        sys.exit(f"EAD niet gevonden: {EAD}\nDownload: {NA}/{TOEGANG}/download/xml")
    root = load_ead(EAD)
    intervals = collect(root)
    intervals.sort(key=lambda x: (x["serie"], x["lo"]))

    a11 = [x for x in intervals if x["serie"] == "A1.1"]
    a12 = [x for x in intervals if x["serie"] == "A1.2"]
    out = {
        "toegang": TOEGANG,
        "bron": f"{NA}/{TOEGANG}",
        "toelichting": (
            "Zoek een dossiernummer op in 'intervallen'. Het eerste blok waarvan "
            "lo<=nr<=hi bevat het dossier. Serie A1.1 = aangifte van overlijden "
            "gedaan (Staatscourant-datum ingevuld); serie A1.2 = geen aangifte gedaan. "
            "Bij twijfel wijst een ingevulde Staatscourant-datum op A1.1."
        ),
        "intervallen": intervals,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"A1.1: {len(a11)} inv.nrs, dossiers {a11[0]['lo']}-{a11[-1]['hi']}")
    print(f"A1.2: {len(a12)} inv.nrs")
    # zelftest op de twee bekende voorbeeldkaarten
    for nr in (27293, 29870):
        hit = next((x for x in a11 if x["lo"] <= nr <= x["hi"]), None)
        print(f"  dossier {nr} -> inv.nr {hit['invnr'] if hit else '?'}  ({hit['url'] if hit else ''})")
    print(f"geschreven: {OUT}")


if __name__ == "__main__":
    main()
