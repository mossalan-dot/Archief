# -*- coding: utf-8 -*-
"""Voeg een periode-harvest toe aan harvest_all.json (dedup op guid)."""
import json,sys,os
NEW=sys.argv[1]; ALL='harvest_all.json'
allv=json.load(open(ALL)) if os.path.exists(ALL) else []
seen={v['guid'] for v in allv}
add=[v for v in json.load(open(NEW)) if v.get('guid') not in seen]
allv+=add
json.dump(allv,open(ALL,'w'),ensure_ascii=False)
print(f"toegevoegd {len(add)} (nieuw) | totaal harvest_all: {len(allv)} folio's")
