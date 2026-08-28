#!/usr/bin/env python3
"""harvest_klapper.py — bouw het scan-manifest van de namenklapper (serie B).

Serie B (inv.nr 614-744, "Klapper op de dossiers betreffende vermiste personen")
is de alfabetische kaartenbak. Elk inv.nr dekt een alfabetvak ("Aa - Adelaar")
en verwijst via een METS-manifest naar de losse kaartscans.

Dit script leest de klapper-inv.nrs uit de EAD, haalt per inv.nr het METS op en
schrijft een plat manifest van alle kaartscans:

    {invnr, alfabetvak, volgorde, scan_id, scan_url, thumb_url, invnr_url}

scan_url is direct te downloaden (JPEG); daarop draait extract_cards.py de OCR.

Gebruik:
    python3 harvest_klapper.py                 # alle 131 inv.nrs
    python3 harvest_klapper.py --only 614 615  # alleen deze inv.nrs (steekproef)

Uitvoer: klapper_manifest.json  (kan groot zijn: ~115k scans; staat in .gitignore)
"""
import argparse
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

TOEGANG = "2.09.34.02"
EAD = Path(__file__).with_name(f"{TOEGANG}.ead.xml")
OUT = Path(__file__).with_name("klapper_manifest.json")
NA = "https://www.nationaalarchief.nl/onderzoeken/archief"

METS_NS = {"mets": "http://www.loc.gov/METS/", "xlink": "http://www.w3.org/1999/xlink"}
XLINK = "{http://www.w3.org/1999/xlink}href"


def text(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def load_ead(path: Path):
    raw = re.sub(r"<!DOCTYPE.*?>", "", path.read_text(encoding="utf-8"), flags=re.S)
    return ET.fromstring(raw)


def klapper_invnrs(root):
    """Alle serie-B inv.nrs (614-744) met alfabetvak en METS-uuid."""
    items = []
    for c in root.iter("c"):
        did = c.find("did")
        if did is None or c.get("level") != "file":
            continue
        unitid = did.find("unitid")
        if unitid is None or not text(unitid).isdigit():
            continue
        invnr = int(text(unitid))
        if not (614 <= invnr <= 744):
            continue
        dao = did.find("dao")
        mets_uuid = ""
        if dao is not None and dao.get("role") == "METS":
            mets_uuid = (dao.get(XLINK) or dao.get("href") or "").rsplit("/", 1)[-1]
        items.append(
            {"invnr": invnr, "alfabetvak": text(did.find("unittitle")), "mets_uuid": mets_uuid}
        )
    items.sort(key=lambda x: x["invnr"])
    return items


def fetch(url, tries=4):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 ** i)
    raise last


def scans_from_mets(mets_bytes):
    """Geef de DISPLAY-scans in leesvolgorde terug: [(scan_id, url, thumb_url)]."""
    root = ET.fromstring(mets_bytes)
    # map fileGrp USE -> {fileid: href}
    grp = {}
    for fg in root.findall(".//mets:fileGrp", METS_NS):
        use = fg.get("USE")
        for f in fg.findall("mets:file", METS_NS):
            loc = f.find("mets:FLocat", METS_NS)
            if loc is not None:
                grp.setdefault(use, {})[f.get("ID")] = loc.get(XLINK)
    # DEFAULT = volledige JPEG (api/file/v1/default/{uuid}) — die gebruiken we
    # voor OCR; DISPLAY is een IIIF-tegel-endpoint (info.json), THUMBS de duim.
    full = grp.get("DEFAULT") or grp.get("DISPLAY") or next(iter(grp.values()), {})
    thumbs = grp.get("THUMBS") or {}
    # leesvolgorde uit de structMap; elke pagina-div heeft meerdere fptr's.
    out = []
    for div in root.findall(".//mets:structMap//mets:div", METS_NS):
        fids = [fp.get("FILEID") for fp in div.findall("mets:fptr", METS_NS)]
        url = next((full[f] for f in fids if f in full), None)
        if not url:
            continue
        thumb = next((thumbs[f] for f in fids if f in thumbs), "")
        out.append((url.rsplit("/", 1)[-1], url, thumb))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", type=int, help="beperk tot deze inv.nrs")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    if not EAD.exists():
        sys.exit(f"EAD niet gevonden: {EAD}\nDownload: {NA}/{TOEGANG}/download/xml")
    invnrs = klapper_invnrs(load_ead(EAD))
    if args.only:
        invnrs = [x for x in invnrs if x["invnr"] in set(args.only)]
    print(f"{len(invnrs)} klapper-inv.nrs te verwerken")

    manifest = []
    for it in invnrs:
        if not it["mets_uuid"]:
            print(f"  inv.nr {it['invnr']}: geen METS — overgeslagen")
            continue
        mets_url = f"https://service.archief.nl/gaf/api/mets/v1/{it['mets_uuid']}"
        scans = scans_from_mets(fetch(mets_url))
        for order, (sid, url, thumb) in enumerate(scans, 1):
            manifest.append(
                {
                    "invnr": it["invnr"],
                    "alfabetvak": it["alfabetvak"],
                    "volgorde": order,
                    "scan_id": sid,
                    "scan_url": url,
                    "thumb_url": thumb,
                    "invnr_url": f"{NA}/{TOEGANG}/invnr/{it['invnr']}",
                }
            )
        print(f"  inv.nr {it['invnr']} ({it['alfabetvak']}): {len(scans)} scans")

    Path(args.out).write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n{len(manifest)} scans geschreven -> {args.out}")


if __name__ == "__main__":
    main()
