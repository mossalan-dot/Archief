# -*- coding: utf-8 -*-
"""Gedeelde functie-categorisering + soort-tekening voor de RGD-pijplijn.
Volgorde telt: eerste match wint (specifieke gebouwtypen vóór generieke)."""

FUNC = [
    ("politie", "👮", ["politiebureau", "politiepost", "marechaussee", "politie"]),
    ("gevangeniswezen", "🔒", ["huis van bewaring", "gevangenis", "cellenbarak", "strafgevangenis",
                               "rijkswerkinrichting", "tuchthuis", "rijksopvoedingsgesticht", "passantenhuis"]),
    ("rechtspraak", "⚖️", ["rechtbank", "gerechtsgebouw", "paleis van justitie", "kantongerecht", "gerechtshof"]),
    ("post & telegraaf", "✉️", ["post", "telegraaf", "telefoon"]),
    ("militair", "🎖️", ["kazerne", "militair", "marine", "fort", "genie", "arsenaal", "magazijn van oorlog",
                        "wachtgebouw", "geschut", "emplacement", "kruitmagazijn", "exercitie"]),
    ("museum & paleis", "🏛️", ["museum", "paleis", "koninklijk"]),
    ("kerk & religie", "⛪", ["kerk", "kapel", "klooster", "synagoge", "pastorie"]),
    ("onderwijs & wetenschap", "🎓", ["school", "h.b.s", "hbs", "hogere burger", "universiteit", "hogeschool",
                                      "gymnasium", "academie", "laboratorium", "proefstation", "sterrenwacht",
                                      "onderzoekingsinstituut", "kweekschool", "observatorium"]),
    ("zorg", "🏥", ["ziekenhuis", "gasthuis", "sanatorium", "krankzinnig", "kliniek", "veeartsenij", "hospitaal"]),
    ("douane & opslag", "📦", ["entrepot", "pakhuis", "douane", "loods", "magazijn", "invoerrechten",
                              "accijnzen", "grenskantoor", "grenskantoren", "veem"]),
    ("bestuur & financiën", "🏢", ["kantoor", "agentschap", "administratie", "belasting", "financiën", "ministerie",
                                   "rijksgebouw", "gouvernement", "provinciehuis", "provinciaal", "raadhuis",
                                   "stadhuis", "secretarie", "ijkkantoor", "munt", "kadaster", "arbeidsbureau"]),
    ("waterstaat & techniek", "🌊", ["sluis", "gemaal", "brug", "haven", "vuurtoren", "waterleiding",
                                     "duiker", "stuw", "kanaal"]),
    ("landbouw & veeteelt", "🚜", ["proefboerderij", "boerderij", "stal", "abattoir", "slachthuis", "hoeve"]),
    ("woningbouw", "🏠", ["woonhuis", "woning", "villa", "landhuis", "dienstwoning", "ambtswoning",
                          "herenhuis", "wooncomplex"]),
]

def categorie(s):
    low = (s or "").lower()
    for name, em, kws in FUNC:
        if any(k in low for k in kws):
            return name, em
    return "overig", "📐"

def soort_tekening(s):
    low = (s or "").lower()
    if "opmeting" in low: return "opmeting"
    if "bestek" in low or "werktekening" in low: return "bestek & werk"
    if "ontwerp" in low: return "ontwerp"
    if "verbouw" in low or "uitbreiding" in low or "aanbouw" in low: return "verbouw"
    if "situatie" in low or "kadast" in low: return "situatie"
    return "overig"
