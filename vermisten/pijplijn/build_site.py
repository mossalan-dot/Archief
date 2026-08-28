#!/usr/bin/env python3
"""build_site.py — voeg kaartrecords + manifest + dossiermap samen tot site-data.

Leest de uitgelezen kaarten (kaarten.jsonl of --records), verrijkt elk record met
de scan-URL's uit het manifest en met de verwijzing naar het onderliggende
persoonsdossier (dossiernr -> inv.nr in serie A, via dossiermap.json), en schrijft
site/kaarten.json dat de statische zoekpagina client-side inlaadt.

Gebruik:
    python3 build_site.py --records kaarten.sample.jsonl \
        --manifest klapper_manifest.sample.json
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.parent / "site"
NA = "https://www.nationaalarchief.nl/onderzoeken/archief/2.09.34.02"


def normalize_date(raw):
    """'20-11-86' -> ('1886-11-20', True); '11.9.1941' -> ('1941-09-11', True).

    Datums staan verbatim op de kaart (dag-maand-jaar, scheidingsteken . of -).
    Tweecijferige jaren: de geregistreerden zijn vermisten/overledenen uit
    1940-1945, dus geboren t/m ~1945. Heuristiek: jj 00-45 -> 19jj, jj 46-99 ->
    18jj. Geeft (iso, zeker); zeker=False als het jaar tweecijferig (dus geraden)
    of onparseerbaar is. De verbatim waarde blijft altijd behouden."""
    s = (raw or "").strip()
    m = re.match(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})\s*$", s)
    if not m:
        return "", False
    d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
    if not (1 <= d <= 31 and 1 <= mo <= 12):
        return "", False
    zeker = len(y) == 4
    yr = int(y)
    if not zeker:
        yr = 1900 + yr if yr <= 45 else 1800 + yr
    return f"{yr:04d}-{mo:02d}-{d:02d}", zeker


def load_jsonl(path: Path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def aangifte_gedaan(staatscourant, aantekening):
    """Is er aangifte van overlijden gedaan? Dan hoort het dossier in serie A1.1.
    Signaal: een echte Staatscourant-datum, of een aanwezige overlijdensakte."""
    sc = str(staatscourant).strip().lower()
    if sc and "onvindbaar" not in sc:
        return True
    return "acte" in str(aantekening).lower() or "overleden" in str(aantekening).lower()


def resolve_dossier(dossiernr, staatscourant, aantekening, intervallen):
    """dossiernr -> onderliggend inv.nr. Bij overlap A1.1/A1.2 wint A1.1 zodra er
    aangifte van overlijden is gedaan."""
    if not str(dossiernr).isdigit():
        return None
    nr = int(dossiernr)
    hits = [x for x in intervallen if x["lo"] <= nr <= x["hi"]]
    if not hits:
        return None
    prefer = "A1.1" if aangifte_gedaan(staatscourant, aantekening) else "A1.2"
    hits.sort(key=lambda x: (x["serie"] != prefer, x["serie"]))
    return hits[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", default=str(HERE / "kaarten.jsonl"))
    ap.add_argument("--manifest", default=str(HERE / "klapper_manifest.json"))
    ap.add_argument("--dossiermap", default=str(HERE / "dossiermap.json"))
    args = ap.parse_args()

    records = load_jsonl(Path(args.records))
    manifest = {m["scan_id"]: m for m in json.loads(Path(args.manifest).read_text("utf-8"))}
    intervallen = json.loads(Path(args.dossiermap).read_text("utf-8"))["intervallen"]

    out = []
    gekoppeld = 0
    for r in records:
        if r.get("leeg"):
            continue
        m = manifest.get(r["scan_id"], {})
        rec = {
            "naam": r.get("naam", ""),
            "voornamen": r.get("voornamen", ""),
            "geboren_datum": r.get("geboren_datum", ""),
            "geboren_plaats": r.get("geboren_plaats", ""),
            "geboren_iso": "",  # ingevuld na normalisatie
            "beroep": r.get("beroep", ""),
            "vader": " ".join(x for x in (r.get("vader_voornamen", ""), r.get("vader_naam", "")) if x),
            "moeder": " ".join(x for x in (r.get("moeder_voornamen", ""), r.get("moeder_naam", "")) if x),
            "gehuwd_met": " ".join(x for x in (r.get("gehuwd_met_voornamen", ""), r.get("gehuwd_met_naam", "")) if x),
            "adres": r.get("woonplaats_adres", ""),
            "staatscourant": r.get("staatscourant", ""),
            "aantekening": r.get("aantekening", ""),
            "dossiernr": r.get("dossiernr", ""),
            "invnr_klapper": m.get("invnr"),
            "alfabetvak": m.get("alfabetvak", ""),
            "kaart_scan": m.get("scan_url", ""),
            "kaart_thumb": m.get("thumb_url", ""),
            "onzeker": r.get("onzeker", []),
        }
        iso, zeker = normalize_date(rec["geboren_datum"])
        rec["geboren_iso"] = iso
        if iso and not zeker and "geboren_datum" not in rec["onzeker"]:
            # jaar tweecijferig op de kaart -> eeuw is geschat
            rec["onzeker"] = rec["onzeker"] + ["geboren_datum (eeuw geschat)"]
        d = resolve_dossier(rec["dossiernr"], rec["staatscourant"], rec["aantekening"], intervallen)
        if d:
            rec["dossier_invnr"] = d["invnr"]
            rec["dossier_serie"] = d["serie"]
            rec["dossier_url"] = d["url"]
            gekoppeld += 1
        out.append(rec)

    out.sort(key=lambda r: (r["naam"].lower(), r["voornamen"].lower()))
    SITE.mkdir(exist_ok=True)
    payload = {
        "toegang": "2.09.34.02",
        "titel": "Commissie tot het doen van Aangifte van Overlijden van Vermisten — VP-dossiers",
        "bron": NA,
        "aantal": len(out),
        "gekoppeld_aan_dossier": gekoppeld,
        "kaarten": out,
    }
    (SITE / "kaarten.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), "utf-8")
    print(f"{len(out)} kaarten -> site/kaarten.json ({gekoppeld} gekoppeld aan een dossier-inv.nr)")


if __name__ == "__main__":
    main()
