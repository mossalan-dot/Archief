#!/usr/bin/env python3
"""Stap 2: geocoding van de plaatsnamen.
GeoNames cities1000 (NL/DE/PL-voorkeur) + een gecureerde lijst voor de
concentratie-/vernietigingskampen en de plaatsen in voormalig Nederlands-Indië.
Schrijft geocode.json = {plaatsnaam: [lat, lon]} en rapporteert dekking naar personen."""
import csv, json, os, re, unicodedata
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

def strip(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"[-]+", " ", s)  # streepjes = spaties (Gross-Rosen == Gross Rosen)

# kampnaam ergens in de string -> coördinaten van het (hoofd)kamp
CAMPS = {
    "neuengamme": (53.4281, 10.2344), "auschwitz": (50.0353, 19.1783),
    "monowitz": (50.0353, 19.1783), "birkenau": (50.0353, 19.1783),
    "gross rosen": (50.9853, 16.2831), "buchenwald": (51.0222, 11.2483),
    "dachau": (48.2694, 11.4342), "mauthausen": (48.2583, 14.5008),
    "sachsenhausen": (52.7658, 13.2631), "oranienburg": (52.7550, 13.2420),
    "ravensbruck": (53.1897, 13.1681), "flossenburg": (49.7342, 12.3572),
    "natzweiler": (48.4569, 7.2564), "stutthof": (54.3278, 18.9436),
    "sobibor": (51.4472, 23.5942), "treblinka": (52.6314, 22.0519),
    "bergen belsen": (52.7575, 9.9075), "theresienstadt": (50.5133, 14.1483),
    "majdanek": (51.2233, 22.6106), "blechhammer": (50.3500, 18.3100),
    "westerbork": (52.9183, 6.6064),
}

# ---- gecureerde coördinaten (exact zoals in de CSV) ----
CURATED = {
    # vernietigings- en concentratiekampen
    "Auschwitz": (50.0353, 19.1783), "Omg. Auschwitz": (50.0353, 19.1783),
    "Omg. van Auschwitz": (50.0353, 19.1783), "Auschwitz-Birkenau": (50.0353, 19.1783),
    "Sobibor": (51.4472, 23.5942), "Sobibór": (51.4472, 23.5942),
    "Bergen-Belsen": (52.7575, 9.9075), "Mauthausen": (48.2583, 14.5008),
    "Neuengamme": (53.4281, 10.2344), "Westerbork": (52.9183, 6.6064),
    "Vught": (51.6403, 5.2842), "Dachau": (48.2694, 11.4342),
    "Buchenwald": (51.0222, 11.2483), "Ravensbrück": (53.1897, 13.1681),
    "Ravensbruck": (53.1897, 13.1681), "Treblinka": (52.6314, 22.0519),
    "Theresienstadt": (50.5133, 14.1483), "Gross-Rosen": (50.9853, 16.2831),
    "Groß-Rosen": (50.9853, 16.2831), "Natzweiler": (48.4569, 7.2564),
    "Flossenbürg": (49.7342, 12.3572), "Flossenburg": (49.7342, 12.3572),
    "Stutthof": (54.3278, 18.9436), "Sachsenhausen": (52.7658, 13.2631),
    "Majdanek": (51.2233, 22.6106), "Lublin": (51.2465, 22.5684),
    "Kamp Amersfoort": (52.1497, 5.3708), "Amersfoort": (52.1561, 5.3878),
    # Nederlands-Indië (historische spelling -> moderne coördinaten)
    "Batavia": (-6.175, 106.827), "Soerabaja": (-7.2575, 112.7521),
    "Bandoeng": (-6.9175, 107.6191), "Semarang": (-6.9667, 110.4167),
    "Tjimahi": (-6.8722, 107.5425), "Ambarawa": (-7.2631, 110.4039),
    "Buitenzorg": (-6.5950, 106.7892), "Medan": (3.5952, 98.6722),
    "Palembang": (-2.9761, 104.7754), "Makassar": (-5.1477, 119.4327),
    "Padang": (-0.9471, 100.4172), "Soerakarta": (-7.5755, 110.8243),
    "Malang": (-7.9666, 112.6326), "Djakarta": (-6.175, 106.827),
    "Tjilatjap": (-7.7279, 109.0154), "Magelang": (-7.4706, 110.2178),
    "Fort de Kock": (-0.3050, 100.3692), "Balikpapan": (-1.2379, 116.8529),
    "Bandjermasin": (-3.3199, 114.5908), "Pontianak": (-0.0263, 109.3425),
    "Menado": (1.4748, 124.8421), "Kediri": (-7.8480, 112.0178),
    "Tjiandjoer": (-6.8201, 107.1385), "Garoet": (-7.2116, 107.9086),
    "Poerwokerto": (-7.4218, 109.2346), "Pekalongan": (-6.8886, 109.6753),
    "Bangkok": (13.7563, 100.5018), "Pakan Baroe": (0.5071, 101.4478),
    "Soengei Geroeng": (-0.72, 100.20),
    "Nagasaki": (32.7503, 129.8779), "Hirohata": (34.80, 134.68),
    "Fukuoka": (33.5904, 130.4017), "Nagoya": (35.1815, 136.9066),
    "Meester-Cornelis": (-6.2247, 106.8706), "Batavia-Antjol": (-6.1230, 106.8370),
    "Banjoebiroe": (-7.2800, 110.4200), "Banjoebiroe, kamp 10": (-7.2800, 110.4200),
    "Bodjonegoro": (-7.1500, 111.8800), "Omgeving Bodjonegoro": (-7.1500, 111.8800),
    "Pajacombo": (-0.2200, 100.6300), "Tandjong Priok": (-6.1050, 106.8800),
    "Tjiandjoer": (-6.8201, 107.1385), "Soekaboemi": (-6.9277, 106.9300),
    "Tasikmalaja": (-7.3506, 108.2172), "Cheribon": (-6.7320, 108.5523),
    "Tjirebon": (-6.7320, 108.5523), "Djokja": (-7.7956, 110.3695),
    "Jogjakarta": (-7.7956, 110.3695), "Djokjakarta": (-7.7956, 110.3695),
    "Blitar": (-8.0983, 112.1681), "Madioen": (-7.6298, 111.5239),
    "Probolinggo": (-7.7543, 113.2159), "Kepandjen": (-8.1300, 112.5700),
    "Ambon": (-3.6954, 128.1814), "Koepang": (-10.1772, 123.6070),
    # Birma-Siam-spoorweg (Thailand/Birma)
    "Chungkai": (14.0100, 99.5100), "Kuie, Thailand": (14.0200, 99.5300),
    "Tamarkan": (14.0417, 99.5117), "Nong Pladoek": (13.9840, 99.8000),
    "Tarsau": (14.3800, 98.9500), "Kanburi": (14.0227, 99.5328),
    "Kanchanaburi": (14.0227, 99.5328), "Wampo": (14.2000, 99.1200),
    "Kuie": (14.0200, 99.5300), "Rintin, Thailand": (14.6000, 98.8000),
    "Takanon, Thailand": (14.7000, 98.6000), "Kinsayok": (14.5000, 98.9000),
    "Kinsayok, Thailand": (14.5000, 98.9000), "Hintok": (14.4500, 98.9500),
    "Loeboek Linggau, kamp Belalau": (-3.3000, 102.8600),
    "Loeboek Linggau": (-3.3000, 102.8600), "Tjiaterstelling": (-6.7500, 107.6500),
    "Banjoebiroe, kamp 11": (-7.2800, 110.4200), "Schoppinitz": (50.2600, 19.0500),
    # lange staart: Duitse (subkamp)plaatsen
    "Kdo. Bobrek": (50.0353, 19.1783), "Kdo. Fürstengrube": (50.0353, 19.1783),
    "Kdo. Weimar": (51.0222, 11.2483), "Kdo. Nordhausen": (51.5340, 10.7620),
    "Tröbitz, Landkreis Finsterwalde": (51.6200, 13.5500),
    "Wöbbelin Landkreis Ludwigslust": (53.3000, 11.4700), "Dorohucza, PL.": (51.1800, 23.0500),
    "Lahde, Landkreis Minden": (52.3500, 8.9500), "Elberfeld": (51.2560, 7.1500),
    "München-Gladbach, Stadtkreis M. Gladbach": (51.1900, 6.4400),
    "München-Gladbach, D.": (51.1900, 6.4400), "Berlijn-Tegel, D.": (52.5900, 13.2900),
    "Salzgitter-Heerte Stadtkreis Salzgitter": (52.1500, 10.3300),
    "Salzgitter-Watenstedt Stadtkreis Salzgitter": (52.1500, 10.3300),
    # lange staart: Nederlands-Indië / Pacific
    "Pematang Siantar": (2.9600, 99.0600), "Kota Radja, NOI": (5.5500, 95.3200),
    "Koeta Radja": (5.5500, 95.3200), "Kota Radja": (5.5500, 95.3200),
    "Long Nawang": (2.5500, 115.4000), "Weltevreden": (-6.1700, 106.8300),
    "Kamp Soemobito": (-7.5500, 112.3000), "Tanimbar-eilanden": (-7.5000, 131.5000),
    "Timor": (-9.5000, 124.5000), "Hainan": (19.2000, 109.7000),
    "Bougainville": (-6.3000, 155.5000), "Kario/Haroekoe": (-3.5800, 128.4500),
    "Si Rengorengo": (2.3000, 99.0000), "Lawe Sigala 2": (3.4000, 97.9000),
    "Hindato, Thailand": (14.5000, 98.9000), "Tamarkan, Thailand": (14.0417, 99.5117),
    # historische exonymen
    "Constantinopel": (41.0082, 28.9784), "Weenen": (48.2082, 16.3738),
    "Koningsbergen": (54.7104, 20.4522), "Dantzig": (54.3520, 18.6466),
    "Lemberg": (49.8397, 24.0297), "Breslau": (51.1079, 17.0385),
    "Praag": (50.0755, 14.4378), "Warschau": (52.2297, 21.0122),
    # --- lange-staart-review (handmatig geplaatst) ---
    # Nederlandse (oud-)gemeenten
    "Schoterland": (52.96, 6.00), "Haskerland": (52.96, 5.80), "Wonseradeel": (53.05, 5.45),
    "Wymbritseradiel": (53.00, 5.65), "Zwollerkerspel": (52.52, 6.12),
    "Ambt-Hardenberg": (52.58, 6.62), "Ambt Hardenberg": (52.58, 6.62),
    "Herwen en Aerdt": (51.87, 6.10), "Hooge en Lage Zwaluwe": (51.70, 4.68),
    "Alphen en Riel": (51.48, 4.96), "Ginneken en Bavel": (51.55, 4.80),
    "Hof van Delft": (52.02, 4.35), "Wijk aan Zee en Duin": (52.49, 4.60),
    "Capelsche Veer": (51.70, 4.95), "Etten en Leur": (51.57, 4.63),
    "Alkemade": (52.20, 4.62), "Bergum": (53.19, 5.99),
    "Hengelo Gld.": (52.005, 6.294), "Hengelo (Gld)": (52.005, 6.294),
    "Hengelo G.": (52.005, 6.294), "Hengelo Gld": (52.005, 6.294),
    # Antillen
    "Curaçao, NA": (12.17, -68.99), "Bonaire, NA": (12.20, -68.26),
    # Nederlands-Indië / Pacific
    "Kalidjati": (-6.53, 107.66), "Bandaneira": (-4.53, 129.90), "Banda Neira": (-4.53, 129.90),
    "Amoerang": (1.18, 124.59), "Madoera": (-7.00, 113.30), "Bangka": (-2.30, 106.10),
    "Larat": (-7.14, 131.78), "Larat-Tanimbar-eilanden": (-7.14, 131.78), "Watidal, Larat": (-7.14, 131.78),
    "Medan-Brastagi": (3.20, 98.51), "Brastagi, kamp Brastagi": (3.20, 98.51),
    "Tanah Grogot": (-1.91, 116.19), "Sanggau Ledo": (0.93, 109.55), "Sario-Menado": (1.47, 124.84),
    "Tretes": (-7.70, 112.63), "Tjibadak": (-6.90, 106.78), "Boemiajoe": (-7.21, 109.01),
    "Hutumuri": (-3.67, 128.28), "Tuhaha": (-3.58, 128.62), "Kampili, kamp": (-5.28, 119.55),
    "Padang Pandjang": (-0.46, 100.40), "Sawahloento, NOI.": (-0.68, 100.78),
    "Pakatto": (-5.30, 119.50), "Tjimahi Centr. Hosp.": (-6.87, 107.54),
    "Cococo, Port. Timor": (-8.90, 125.70), "Port. Timor": (-8.90, 125.70),
    "Palau-eilanden": (7.50, 134.60), "Moji, Japan": (33.94, 130.96),
    "Fukuoka kamp 6, Orio Japan": (33.87, 130.70),
    # Birma-Siam-spoorweg (Thailand)
    "Tarsao": (14.38, 98.95), "Tarsao, Thailand": (14.38, 98.95), "Koedjie": (14.50, 98.90),
    "Koedjie, Thailand": (14.50, 98.90), "Nakompaton": (13.82, 100.06), "Nakompaton, Thailand": (13.82, 100.06),
    "Rintin": (14.60, 98.80), "Takanon": (14.70, 98.60), "Brangkasi": (14.30, 98.90),
    "Brangkasi, Thailand": (14.30, 98.90), "Banggan, Thailand": (14.80, 98.50),
    "Nompladuk I": (13.98, 99.80), "Nompladuk II": (13.98, 99.80), "Nonpladuk II": (13.98, 99.80),
    "Nompladuk I, Thailand": (13.98, 99.80), "Nompladuk II, Thailand": (13.98, 99.80),
    # Duitse plaatsen / (sub)kampen
    "Kdo. Gusen": (48.26, 14.45), "Kdo. Golleschau": (49.75, 18.72), "Gräditz": (50.75, 16.45),
    "Hamborn": (51.49, 6.75), "Bentheim": (52.30, 7.16), "Rheydt, D.": (51.16, 6.44),
    "Oberndorf am Neckar, Landkreis Rottweil": (48.29, 8.57),
    "Walsum, Landkreis Dinslaken": (51.53, 6.68), "Dülken, Landkreis Kempen-Krefeld": (51.25, 6.32),
    "Bienen, Landkreis Rees": (51.83, 6.29), "Salzgitter-Hallendorf Stadtkreis Salzgitter": (52.13, 10.36),
    "Salzgitter-Watenstedt, Stadtkreis Salzgitter": (52.13, 10.36),
    "Salzgitter-Drütte Stadtkreis Salzgitter": (52.13, 10.36),
    "Verden-Aller Landkreis Verden": (52.92, 9.23), "Peres, Landkreis Borna": (51.13, 12.47),
    "Ohrbeck Landkreis Osnabrück": (52.23, 8.10), "Vaihingen Enz, Landkreis Vaihingen": (48.93, 8.96),
    "Bedburg-Hau, Landkreis Kleve": (51.75, 6.20), "Gelsenkirchen-Buer, Stadtkreis Gelsenkirchen": (51.58, 7.10),
    "Neustadt Holstein, Landkreis Oldenburg Holstein": (54.11, 10.82), "Ammendorf, Saalkreis": (51.42, 11.99),
    "Burgsteinfurt": (52.15, 7.35), "Frankfort am Main": (50.11, 8.68),
    "Berlijn-Spandau, D.": (52.54, 13.20), "Tröbitz, Landkreis Luckau": (51.62, 13.55),
    # extra Indië (bevestigd)
    "Kesilir": (-8.45, 114.15), "Soekoen": (-7.99, 112.62), "Patjet": (-7.62, 112.53),
    "Tigaroenggoe": (2.60, 98.90), "Lengkong nabij Jember": (-8.20, 113.70),
    "Si Rengorengo, Kamp 5": (2.30, 99.00), "Si Rengorengo, kamp 5": (2.30, 99.00),
    "Lawe Sigala Sigala": (3.40, 97.90), "Lawe Sigala 2": (3.40, 97.90),
    # correcties van foute geocoderingen (matchten VS/Afrika i.p.v. Indië/Cariben)
    "Oma, eil. Haroekoe": (-3.58, 128.45), "Haria": (-3.60, 128.65),
    "Haria, Saparoea": (-3.60, 128.65), "Saba, NA": (17.63, -63.24),
    "Kema": (1.36, 125.08), "Banda": (-4.53, 129.90), "Neira": (-4.53, 129.90),
    "Deli": (3.58, 98.67), "Paso": (-3.63, 128.25), "Amèt": (-3.58, 128.65),
    "Tepa": (-8.00, 129.50), "Flores": (-8.60, 121.00), "Banka": (-2.30, 106.10),
    "Kuima": (14.50, 98.90), "Kuima, Thailand": (14.50, 98.90), "Mandor": (0.30, 109.27),
    "Minoa": (14.30, 98.90), "Minoa, Thailand": (14.30, 98.90), "New Britain": (-5.50, 151.50),
    # Duitse arbeidsinzet-plaatsen komen uit seed_cache
}
CURATED["Ellecom"] = (52.0139, 6.0947)

def _add(gz, c, base_boost=0, classes=None):
    if len(c) < 15:
        return
    if classes and c[6] not in classes:
        return
    try:
        lat, lon, pop = float(c[4]), float(c[5]), int(c[14] or 0)
    except ValueError:
        return
    cc = c[8]
    pref = {"NL": 3_000_000, "DE": 400_000, "PL": 300_000, "ID": 220_000, "BE": 200_000,
            "FR": 150_000, "GB": 120_000}.get(cc, 0)
    score = pop + pref + base_boost
    names = [c[1], c[2]] + (c[3].split(",") if c[3] else [])
    for nm in names:
        k = strip(nm)
        if k and (k not in gz or score > gz[k][2]):
            gz[k] = (lat, lon, score)

def build_gazetteer():
    gz = {}
    p = os.path.join(HERE, "cities1000.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            _add(gz, line.split("\t"))
    # volledige NL-dump wint (alle woonplaatsen + gemeenten), hoge boost
    p = os.path.join(HERE, "NL.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            _add(gz, line.split("\t"), base_boost=5_000_000, classes={"P", "A"})
    return gz

def main():
    targets = json.load(open(HERE + "/geocode_targets.json", encoding="utf-8"))
    seed = json.load(open(HERE + "/seed_cache.json", encoding="utf-8"))
    gz = build_gazetteer()
    print(f"gazetteer: {len(gz)} namen")
    out = {}
    hit_p = miss_p = 0
    misses = Counter()
    for place, cnt in targets.items():
        coord = None
        k = strip(place)
        if place in CURATED:
            coord = CURATED[place]
        elif place in seed:
            coord = tuple(seed[place])
        elif any(camp in k for camp in CAMPS):  # subcommando -> hoofdkamp
            coord = next(c for camp, c in CAMPS.items() if camp in k)
        else:
            # strip Stadtkreis/Landkreis-suffix, "a/d Ruhr", en alles na komma/haakje
            k2 = re.sub(r"^(kdo\.?|kamp)\s+", "", k)              # Kommando/Kamp <plaats> -> plaats
            k2 = re.sub(r"^stad\s+", "", k2)                      # "Stad Almelo" -> Almelo
            k2 = re.sub(r"\b(stadt|land)?kreis\b.*$", "", k2).strip()
            k2 = re.sub(r"\ba[/ ]?d\b.*$", "", k2).strip()
            k2 = re.sub(r"[,(].*$", "", k2).strip()
            k2 = re.sub(r"\s+[a-z]{1,2}\.?$", "", k2).strip()     # land-afk. "B." "PL." "D." weg
            k2 = re.sub(r"\s+(belgie|belgi|belg|blg|duitsland|frankrijk|engeland|nederland|polen|denemarken|"
                        r"oostenrijk|hongarije|hong|tsjechoslowakije|joegoslavie|italie|zwitserland|noorwegen)\.?$", "", k2).strip()
            if k in gz:
                coord = gz[k][:2]
            elif k2 and k2 in gz:
                coord = gz[k2][:2]
        if coord:
            out[place] = [round(coord[0], 4), round(coord[1], 4)]
            hit_p += cnt
        else:
            miss_p += cnt
            misses[place] = cnt
    json.dump(out, open(HERE + "/geocode.json", "w", encoding="utf-8"), ensure_ascii=False)
    tot = hit_p + miss_p
    print(f"geocoded: {len(out)}/{len(targets)} plaatsen | dekking naar personen: {hit_p}/{tot} = {100*hit_p/tot:.1f}%")
    print("grootste missers (plaats: personen):")
    for p, c in misses.most_common(25):
        print(f"  {c:6}  {p}")
    json.dump(dict(misses.most_common()), open(HERE + "/geocode_misses.json", "w", encoding="utf-8"), ensure_ascii=False)

if __name__ == "__main__":
    main()
