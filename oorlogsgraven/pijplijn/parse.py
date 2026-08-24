#!/usr/bin/env python3
"""Oorlogsgravenstichting-kaart (ogs.alanmoss.nl) — stap 1: aggregatie.
Leest de verrijkte CSV en produceert de geocoding-targetlijst + ruwe aggregaten
voor twee lagen: Herkomst (geboorteplaats) en Waar omgekomen (overlijdensplaats).
"""
import csv, json, os, re
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Users/alan/Downloads/NT00446_OORLOGSGRAVEN_verrijkt.csv"

# plaatsen die geen kaartpunt zijn -> 'niet op de kaart'
VAAG = re.compile(r"onbekend|^omg\.|midden-europa|oceaan|zee\b|nabij|a[/ ]?b\b|^\?|volle zee|op transport|onderweg", re.I)

def norm(p):
    p = (p or "").strip()
    return p

def naam(r):
    parts = [r["prs_voornamen"].strip() or r["prs_initialen"].strip(),
             r["prs_tussenvoegsel"].strip(), r["prs_achternaam"].strip()]
    return " ".join(x for x in parts if x)

def main():
    herkomst = Counter(); overlijden = Counter()
    vaag_h = Counter(); vaag_o = Counter()
    persons = []
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    for i, r in enumerate(rows):
        gp = norm(r["prs_geboorteplaats"]); op = norm(r["prs_overlijdensplaats"])
        if gp:
            (vaag_h if VAAG.search(gp) else herkomst)[gp] += 1
        if op:
            (vaag_o if VAAG.search(op) else overlijden)[op] += 1
        persons.append({
            "n": naam(r),
            "gd": r["prs_geboortedatum"] if not r["prs_geboortedatum"].startswith("0000") else "",
            "gp": gp,
            "od": r["prs_overlijdensdatum"] if not r["prs_overlijdensdatum"].startswith("0000") else "",
            "op": op,
            "nat": r["prs_nationaliteit"].strip(),
            "inv": r["vwz_inventarisnummer"],
            "url": r["oorlogsgravenstichting_url"],
        })
    # geocoding-targets: alle niet-vage plaatsen uit beide lagen, met totaaltelling
    targets = Counter()
    for p, c in herkomst.items(): targets[p] += c
    for p, c in overlijden.items(): targets[p] += c
    json.dump(dict(targets), open(HERE + "/geocode_targets.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"herkomst": dict(herkomst), "overlijden": dict(overlijden),
               "vaag_herkomst": dict(vaag_h), "vaag_overlijden": dict(vaag_o)},
              open(HERE + "/aggregaten.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(persons, open(HERE + "/persons.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"personen: {len(persons)}")
    print(f"herkomst: {len(herkomst)} plaatsen / {sum(herkomst.values())} personen (+{sum(vaag_h.values())} vaag)")
    print(f"overlijden: {len(overlijden)} plaatsen / {sum(overlijden.values())} personen (+{sum(vaag_o.values())} vaag)")
    print(f"unieke geocoding-targets: {len(targets)}")
    print("top-10 vage overlijdensplaatsen:", vaag_o.most_common(10))

if __name__ == "__main__":
    main()
