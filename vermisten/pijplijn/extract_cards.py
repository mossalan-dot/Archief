#!/usr/bin/env python3
"""extract_cards.py — lees de klapperkaarten gestructureerd uit (OCR + veldherkenning).

De kaarten zijn voorgedrukte formulieren (model 8328-'49). De sleutelvelden zijn
getypt en dus goed leesbaar; enkele velden (ouders, echtgeno(o)t(e)) zijn met de
hand geschreven. Een vision-taalmodel leest de hele kaart in één keer en levert de
velden als JSON — betrouwbaarder dan losse OCR omdat het de formulierindeling kent.

Per scan uit klapper_manifest.json wordt één record geschreven naar kaarten.jsonl.
Het script is resumable (reeds verwerkte scan_id's worden overgeslagen) en cachet
de afbeeldingen in scans/.

Backend: Anthropic Messages API (ANTHROPIC_API_KEY). Model instelbaar met --model.
Een andere backend (bv. lokale HTR/Tesseract) kan door extract_one() te vervangen.

Gebruik:
    export ANTHROPIC_API_KEY=...
    python3 extract_cards.py --manifest klapper_manifest.json --limit 50
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
SCANDIR = HERE / "scans"
OUT = HERE / "kaarten.jsonl"

VELDEN = [
    "naam", "voornamen", "geboren_datum", "geboren_plaats", "beroep",
    "vader_naam", "vader_voornamen", "moeder_naam", "moeder_voornamen",
    "gehuwd_met_naam", "gehuwd_met_voornamen", "huwelijk_ontbonden",
    "woonplaats_adres", "staatscourant", "dossiernr",
]

PROMPT = f"""Dit is een voorgedrukte indexkaart (model 8328-'49) uit de klapper van de
Nederlandse "Commissie tot het doen van Aangifte van Overlijden van Vermisten".
Lees de kaart en geef UITSLUITEND een JSON-object met deze sleutels:
{", ".join(VELDEN)}, "leeg", "onzeker".

Regels:
- Neem waarden exact over zoals ze op de kaart staan (getypt of handgeschreven).
- Ontbreekt een veld, gebruik "" (lege string).
- "dossiernr": het getal rechtsboven onder "Dossier nr" (alleen cijfers).
- "geboren_datum": zoals gedrukt (bv. "11.9.1941"); "geboren_plaats": na "te".
- "vader_*"/"moeder_*": de namen achter "Zoon/Dochter van ... en van ...".
- "huwelijk_ontbonden": datum of teken bij "Huwelijk ontbonden op/door O.S.A.N.", anders "".
- "staatscourant": de datum bij "Staatscourant".
- "leeg": true als de kaart leeg is of een tussenblad/scheidingskaart zonder persoon.
- "onzeker": lijst van sleutelnamen die je niet zeker kon lezen (mag leeg zijn).
Geef alleen de JSON, geen toelichting."""


def fetch_image(url, dest: Path, tries=4):
    if dest.exists() and dest.stat().st_size > 0:
        return dest.read_bytes()
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                data = r.read()
            dest.write_bytes(data)
            return data
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 ** i)
    raise last


def extract_one(img_bytes, model):
    """Vraag het vision-model om de velden. Vereist het anthropic-pakket + API-key."""
    import anthropic  # pip install anthropic

    client = anthropic.Anthropic()
    b64 = base64.standard_b64encode(img_bytes).decode()
    msg = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                 "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": PROMPT},
            ],
        }],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.split("```")[1].lstrip("json").strip()
    return json.loads(text)


def done_ids(path: Path):
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(json.loads(line)["scan_id"])
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(HERE / "klapper_manifest.json"))
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--limit", type=int, default=0, help="max aantal kaarten (0=alle)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Zet ANTHROPIC_API_KEY in de omgeving.")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    SCANDIR.mkdir(exist_ok=True)
    out_path = Path(args.out)
    seen = done_ids(out_path)
    todo = [m for m in manifest if m["scan_id"] not in seen]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} kaarten te lezen ({len(seen)} al gedaan)")

    with out_path.open("a", encoding="utf-8") as fh:
        for i, m in enumerate(todo, 1):
            try:
                img = fetch_image(m["scan_url"], SCANDIR / f"{m['scan_id']}.jpg")
                fields = extract_one(img, args.model)
            except Exception as e:  # noqa: BLE001
                print(f"  [{i}] {m['scan_id']}: FOUT {e}")
                continue
            rec = {k: m[k] for k in ("scan_id", "invnr", "alfabetvak", "volgorde",
                                     "scan_url", "thumb_url", "invnr_url")}
            rec.update({k: fields.get(k, "") for k in VELDEN})
            rec["leeg"] = bool(fields.get("leeg"))
            rec["onzeker"] = fields.get("onzeker", [])
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(todo)}")
    print(f"klaar -> {out_path}")


if __name__ == "__main__":
    main()
