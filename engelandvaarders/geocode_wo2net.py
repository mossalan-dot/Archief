#!/usr/bin/env python3
"""Geocode de nieuwe plaats-keys uit parse_wo2net (hervatbaar, 1/sec)."""
import json, time, os
from geocode import query
cache=json.load(open('geocache.json',encoding='utf-8'))
todo=[k for k in json.load(open('geocode_todo_wo2net.json',encoding='utf-8')) if k not in cache]
print(f"te geocoden: {len(todo)}")
ok=miss=0
for i,key in enumerate(todo,1):
    name,_,country=key.partition('|')
    r=query(name,country,key)
    cache[key]=r
    if r: ok+=1
    else: miss+=1; print("  MISS",key)
    if i%25==0 or i==len(todo):
        json.dump(cache,open('geocache.json','w',encoding='utf-8'),ensure_ascii=False)
        print(f"  {i}/{len(todo)}  ok={ok} miss={miss}")
    time.sleep(1.1)
json.dump(cache,open('geocache.json','w',encoding='utf-8'),ensure_ascii=False)
print(f"KLAAR: ok={ok} miss={miss} | geocache nu {len(cache)}")
