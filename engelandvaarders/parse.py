#!/usr/bin/env python3
"""Parse NT00464 Engelandvaarders CSV -> people.json + unieke plaatsen om te geocoden."""
import csv, re, json, sys
from collections import OrderedDict

SRC = "bron.csv"

def clean_seg(seg):
    """Split a route segment into (camp, place, country)."""
    seg = seg.strip()
    camp = None
    m = re.match(r'^\[([^\]]*)\]\s*(.*)$', seg)
    if m:
        camp = m.group(1).strip()
        seg = m.group(2).strip()
    # place (country)
    m = re.match(r'^(.*?)\s*\(([^)]+)\)\s*$', seg)
    if m:
        return camp, m.group(1).strip(), m.group(2).strip()
    return camp, seg, None

def parse_route(s):
    if not s.strip():
        return []
    out = []
    for raw in s.split(' - '):
        raw = raw.strip()
        if not raw:
            continue
        camp, place, country = clean_seg(raw)
        if not place and not camp:
            continue
        out.append({"camp": camp, "place": place, "country": country})
    return out

def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    people = []
    places = OrderedDict()  # key -> {name, country}

    def reg(name, country):
        if not name:
            return None
        key = f"{name}|{country or ''}"
        if key not in places:
            places[key] = {"name": name, "country": country or ""}
        return key

    for r in rows:
        route = parse_route(r["locaties_route"])
        for seg in route:
            seg["key"] = reg(seg["place"], seg["country"])
        # herkomst voor stippellijn: land_van_vertrek als land, geboorteplaats als stip
        na_link = r["vwz_scan"].strip()
        if not na_link:
            for i in range(1, 11):
                if r.get(f"scan_{i}", "").strip():
                    na_link = r[f"scan_{i}"].strip(); break
        vertrek_land = r["land_van_vertrek"].strip()
        vertrek_key = reg(vertrek_land, vertrek_land) if vertrek_land else None
        geb_key = reg(r["geboorteplaats"].strip(), r["geboorteland"].strip()) if r["geboorteplaats"].strip() else None

        people.append({
            "id": r["id"],
            "naam": " ".join(x for x in [r["voornamen"], r["tussenvoegsels"], r["achternaam"]] if x.strip()).strip(),
            "roepnaam": r["roepnaam"].strip(),
            "geslacht": r["geslacht"].strip(),
            "geboortejaar": r["geboortejaar"].strip(),
            "geboorteplaats": r["geboorteplaats"].strip(),
            "geboorte_key": geb_key,
            "woonplaats": r["woonplaats"].strip(),
            "beroep": r["beroep"].strip(),
            "godsdienst": r["godsdienst"].strip(),
            "politiek": r["politiekerichting"].strip(),
            "land_vertrek": vertrek_land,
            "vertrek_key": vertrek_key,
            "datumvertr": r["datumvertr"].strip(),
            "datumaank": r["datumaank"].strip(),
            "hoofdroute": r["hoofdroute"].strip(),
            "landen_op_route": r["landen_op_route"].strip(),
            "route": route,
            "heeft_route": len(route) > 0,
            "link": r["externe_link"].strip(),
            "na_link": na_link,
            "record_link": ("https://www.nationaalarchief.nl/onderzoeken/index/nt00464/" + r["GUID"].strip()) if r.get("GUID", "").strip() else "",
        })

    json.dump(people, open("people.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(list(places.items()), open("places_todo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with_route = sum(1 for p in people if p["heeft_route"])
    print(f"personen: {len(people)}  met route: {with_route}  zonder: {len(people)-with_route}")
    print(f"unieke plaatsen te geocoden: {len(places)}")

if __name__ == "__main__":
    main()
