#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gedeelde categorie- en afloop-logica voor kaart, export en dashboard."""
import re

# volgorde/labels/kleuren/emoji — één bron van waarheid (ondersteuning is GEEN aard-categorie
# maar een aparte vlag; de daad van de overleden redder wordt zelf gecategoriseerd)
CAT_ORDER = ["water","zee","ijs","auto","trein","brand","dier","onbekend","overig"]
CAT_LABEL = {"water":"Water","zee":"Zee/kust","ijs":"IJs","auto":"Auto","trein":"Trein/spoor",
             "brand":"Brand","dier":"Op hol/dier","onbekend":"Onvermeld","overig":"Overig"}
CAT_FULL  = {"water":"Binnenwater","zee":"Zee / kust","ijs":"IJs","auto":"Auto te water","trein":"Trein / spoor",
             "brand":"Brand","dier":"Op hol / dier","onbekend":"Aard onvermeld","overig":"Overig"}
CAT_COL   = {"water":"#2563eb","zee":"#0e7490","ijs":"#06b6d4","auto":"#dc2626","trein":"#a16207",
             "brand":"#ea580c","dier":"#7c3aed","onbekend":"#a8a29e","overig":"#6b7280"}
CAT_EMO   = {"water":"🌊","zee":"🚢","ijs":"🧊","auto":"🚗","trein":"🚂","brand":"🔥","dier":"🐴",
             "onbekend":"❔","overig":"🆘"}

# administratieve/steun-dossiers (aan het begin herkenbaar)
STEUN_START = re.compile(r'^\s*(ondersteun|correspondentie|stukken betreffende|'
    r'verzoek (om|voor|tot)\b.{0,60}(steun|ondersteuning|uitkering|toelage|vergoeding)|'
    r'afwijzen van (het )?verzoek\b.{0,60}(ondersteun|steun|financi|uitkering|toelage))')
# geld-/steunverzoek elders in de tekst (nooit 'gratificatie', dat staat in echte reddingen)
STEUN_ANY = re.compile(r'verzoek(t)?\b.{0,20}\b(om|tot)\b.{0,45}(uitkering|toelage|toekenning|ondersteuning|financiële steun|pensioen)', re.I)
# redding wél, maar aard niet gespecificeerd
ONBEKEND = re.compile(r'verrichtte\b.{0,30}redding|gedroegen zich verdienstelijk|betoonde\b.{0,20}moed|'
    r'moedig gedrag|hulp verleend|te hulp gekomen|\ben redding\b|'
    r'een redding\s*($|,|\.| en | gratificatie| aanvraag)', re.I)

def is_steun(desc):
    """Ondersteuning van nabestaanden / administratief steunverzoek (aparte vlag, geen aard)."""
    d = desc.lower()
    return bool(STEUN_START.match(d) or STEUN_ANY.search(d))

def categorize(desc, detail=None):
    d = (desc + " " + (detail or "")).lower()
    if re.search(r'\bijs\b|ijsschots|ijsschol|ijsvlakte|door het ijs|onder het ijs|op het ijs|schaats|wak\b', d):
        return "ijs"
    if re.search(r'auto|voertuig|vrachtwagen|te water geraakte (auto|wagen)|personenauto|bestelbus', d):
        return "auto"
    if re.search(r'\btrein|spoorweg|spoorlijn|spoorbaan|\boverweg|\brails\b|locomotief|het spoor|spoorrails', d):
        return "trein"
    if re.search(r'brand|vuur|vlammen|in brand|brandende', d):
        return "brand"
    if re.search(r'op hol|hol geslagen|hollende?|dolle hond|aangevallen door (?:een )?(?:hond|stier|dier|koe)|'
                 r'\bstier\b|losgebroken', d):
        return "dier"
    if re.search(r'noordzee|waddenzee|zuiderzee|\bzee\b|op zee|schipbreuk|schip\b|vrachtschip|binnenschip|'
                 r'zeeschip|opvarende|coaster|sleepboot|duwbak|scheepsramp|bemanning|reddingb?oot|reddingsboot|'
                 r'\bstrand|branding|\bkust|\bkotter|vissersvaartuig', d):
        return "zee"
    if re.search(r'water|gracht|haven|kanaal|sloot|vaart|rivier|singel|plas|meer|kolk|wiel|dok|dijk|'
                 r'kade|wetering|tocht|boezem|drenkel|verdrink|verdronk|te water', d):
        return "water"
    if ONBEKEND.search(d):
        return "onbekend"
    return "overig"

def outcome(desc):
    d = desc.lower()
    if re.search(r'\bpoog|poging|tevergeefs|kwam(?:en)?\s+(?:daarbij\s+)?om|om het leven|'
                 r'verdronk|verdronken|mocht niet baten|verloor daarbij het leven', d):
        return "poging"
    return "geslaagd"

# --- redder-naam + Delpher-zoekopdracht (gedeeld door kaart-data en export) ---
VERBS = r'\b(redde(?:n)?|poogde(?:n)?|probeerde(?:n)?|bracht(?:en)?|nam(?:en)?|gedroegen|hielp|hielpen|verrichtte)\b'
NONPERSON = ("afwijzen", "ondersteun", "correspondentie", "stukken", "afwijz", "financi", "verzoek")
def extract_person(desc):
    """Naam van de (eerste) redder — voor de krantenzoekopdracht."""
    low = desc.lower()
    if any(low.startswith(w) for w in NONPERSON):
        return None
    m = re.search(VERBS, desc)
    head = desc[:m.start()] if m else desc.split(",")[0]
    head = head.split(" en ")[0].split(",")[0].strip()
    caps = [t for t in head.split() if t[:1].isupper()]
    if len(head) < 4 or len(caps) < 2:
        return None
    return head

import urllib.parse as _u
TUSSEN = {"van","de","der","den","ten","ter","te","op","aan","bij","in","het","'t","'s","vande","vander","uit","la","le","du"}
def delpher_query(who, place=None, detail=None):
    """Gerichte Delpher-URL: '<eerste voornaam> <achternaam>' + plaats + water/straat-detail."""
    if not who:
        return ""
    parts = who.split()
    if not parts:
        return ""
    si = len(parts) - 1
    for i, t in enumerate(parts):
        if t.lower() in TUSSEN:
            si = i; break
    surname = " ".join(parts[si:])
    first = parts[0] if si > 0 else ""
    name = ((first + " ") if first else "") + surname
    q = lambda s: f'"{s}"' if " " in s else s
    query = f'"{name.strip()}"'
    if place:  query += " " + q(place)
    if detail: query += " " + q(detail)
    return "https://www.delpher.nl/nl/kranten/results?query=" + _u.quote(query) + "&coll=ddd"
