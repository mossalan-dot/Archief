#!/usr/bin/env python3
"""Oorlogsgravenstichting-kaart (ogs.alanmoss.nl) — stap 1: aggregatie.
Leest de verrijkte CSV en produceert de geocoding-targetlijst + ruwe aggregaten
voor twee lagen: Herkomst (geboorteplaats) en Waar omgekomen (overlijdensplaats).
"""
import csv, json, os, re
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/Users/alan/Downloads/NT00446_OORLOGSGRAVEN_verrijkt.csv"

# plaatsen die geen kaartpunt zijn -> 'niet op de kaart' (precies, zodat echte
# plaatsen als Zierikzee/Egmond aan Zee wél geplaatst worden)
VAAG = re.compile(r"onbekend|niets bekend|^omg\.|omgeving|midden-?europa|oost-?europa|"
                  r"\boceaan\b|op zee|volle zee|\bab\b|op transport|onderweg|^\?|"
                  r",? \d+ ?km$|^duitsland$|^rusland$|^engeland$|^frankrijk$|^belgi", re.I)

def norm(p):
    p = (p or "").strip()
    if p in ("?", "onbekende plaats", "Onbekend"):
        return "onbekend"
    return p

def naam(r):
    """Achternaam-eerst, bv. 'Aalten, Karel van'."""
    achter = r["prs_achternaam"].strip()
    voor = r["prs_voornamen"].strip() or r["prs_initialen"].strip()
    tv = r["prs_tussenvoegsel"].strip()
    rest = " ".join(x for x in [voor, tv] if x)
    if achter and rest:
        return f"{achter}, {rest}"
    return achter or rest

def main():
    herkomst = Counter(); overlijden = Counter()
    vaag_h = Counter(); vaag_o = Counter()
    persons = []
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    # dedup: zelfde inventarisnummer = zelfde persoon (A = openbaar dossier 1947,
    # B = correspondentiedossier 1995). Houd A als primair, B-UUID als tweede link.
    from collections import defaultdict as _dd
    byinv = _dd(list)
    for r in rows:
        byinv[r["vwz_inventarisnummer"]].append(r)
    merged = []
    for inv, grp in byinv.items():
        grp.sort(key=lambda r: r["ove_dateofcapture"])   # 1947 (openbaar) eerst
        prim = grp[0]
        prim["_na2"] = grp[1]["vwz_UUID"].strip() if len(grp) > 1 else ""
        merged.append(prim)
    rows = merged
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
            "na": r["vwz_UUID"].strip(),
            "na2": r.get("_na2", ""),
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
