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
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE.parent / "site"
NA = "https://www.nationaalarchief.nl/onderzoeken/archief/2.09.34.02"


def load_jsonl(path: Path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def resolve_dossier(dossiernr, staatscourant, intervallen):
    """dossiernr -> onderliggend inv.nr. Bij overlap A1.1/A1.2 wint A1.1 zodra een
    Staatscourant-datum is ingevuld (dan is er aangifte van overlijden gedaan)."""
    if not str(dossiernr).isdigit():
        return None
    nr = int(dossiernr)
    hits = [x for x in intervallen if x["lo"] <= nr <= x["hi"]]
    if not hits:
        return None
    prefer = "A1.1" if str(staatscourant).strip() else "A1.2"
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
            "beroep": r.get("beroep", ""),
            "vader": " ".join(x for x in (r.get("vader_voornamen", ""), r.get("vader_naam", "")) if x),
            "moeder": " ".join(x for x in (r.get("moeder_voornamen", ""), r.get("moeder_naam", "")) if x),
            "gehuwd_met": " ".join(x for x in (r.get("gehuwd_met_voornamen", ""), r.get("gehuwd_met_naam", "")) if x),
            "adres": r.get("woonplaats_adres", ""),
            "staatscourant": r.get("staatscourant", ""),
            "dossiernr": r.get("dossiernr", ""),
            "invnr_klapper": m.get("invnr"),
            "alfabetvak": m.get("alfabetvak", ""),
            "kaart_scan": m.get("scan_url", ""),
            "kaart_thumb": m.get("thumb_url", ""),
            "onzeker": r.get("onzeker", []),
        }
        d = resolve_dossier(rec["dossiernr"], rec["staatscourant"], intervallen)
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
