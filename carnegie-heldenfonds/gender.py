#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Best-effort gender inference for the first rescuer, Dutch historical names."""
import re

MALE = set("""Johannes Jan Cornelis Willem Hendrik Pieter Jacobus Gerrit Jacob Dirk Petrus
Adrianus Arie Nicolaas Gerardus Wilhelmus Johan Antonius Theodorus Marinus Hendrikus
Franciscus Klaas Albert Leendert Frederik Hermanus Peter Martinus Abraham Adriaan Roelof
Leonardus Albertus Teunis Bastiaan Gijsbert Gijsbertus Bernardus Cornelius Anthonius Karel
Simon Jozef Joseph Josephus Lambertus Lodewijk Rudolf Rutger Sebastiaan Steven Thomas Tobias
Coenraad Cornelis Daniel Egbert Eduard Evert Everhardus Ferdinand Floris Frans Gerard Gerhard
Gerardus Godfried Harm Heinrich Herman Huibert Izaak Jacobus Jelle Jochem Joris Julius Jurjen
Laurentius Lourens Machiel Marius Matthijs Meindert Michiel Nanne Otto Paulus Pieter Reinier
Reinder Rein Sander Siebe Sjoerd Tjeerd Tjipke Willem Wouter Wybe Ale Alle Andries Anne Anton
Barend Bauke Bernard Cornelius Derk Douwe Eelke Folkert Foppe Geert Gooitzen Harmen Hein Hessel
Hidde Hilbrand Hylke Iede Jelte Jentje Johan Kees Koos Krijn Lammert Lieuwe Lubbertus Lubbert
Marten Meint Menno Nico Okke Onno Paul Piet Reinder Rienk Rik Sake Siebren Sikke Sipke Taeke
Teun Thijs Tjalling Uilke Ulbe Watze Wessel Wibren Wichert Wietse Wim Ynze Ype Adrianus Cornelis
Gerben Geurt Hein Hidde Jorrit Klaas Sjoerd Wiebe Age Bernardus Christiaan Christoffel Dominicus
Eugenius Gabriel Guillaume Ignatius Marcus Mattheus Norbertus Servaas Sijbrand Sybren Valentijn
Vincent Xaverius Zacharias Hubert Hubertus Hugo Ignaas Isaac Louis Ludovicus Maarten Melchior
Nicolaes Roelof Theodoor Timon Wolter Zeger Adam Aart Ary Bram Cent Cees Chris Dick Freek Gerlof
Guido Hans Henk Ids Jaap Jarig Job Jelmer Joop Joost Kasper Leen Maarten Marnix Nol Rein Ties Ton""".split())

FEMALE = set("""Maria Johanna Anna Cornelia Wilhelmina Elisabeth Hendrika Geertruida Petronella
Adriana Catharina Margaretha Jacoba Gerarda Antonia Alida Willemina Grietje Aaltje Trijntje
Neeltje Antje Dirkje Jantje Marretje Aagje Sophia Christina Helena Jannetje Klaasje Pietertje
Gesina Hendrikje Berendina Frederika Everdina Janna Aleida Bregje Guurtje Sijtske Ytje Baukje
Rinske Wietske Froukje Tjitske Hiltje Martha Ida Ike Ika Agatha Henriëtte Jeannette Yolanda Betje
Janne Anneke Wilma Ria Corrie Ans Riet Truus Nel Greet Bep Cornelisje Jacomijntje Marchje Sjoukje
Aafke Akke Antje Dieuwke Feikje Fokje Gatske Geeske Hendrikje Iefke Jeltje Klaaske Lolkje Minke
Nieske Renske Saapke Sjoukje Tetje Tjaltje Wypkje Ymkje Aleid Bertha Diena Dina Everdina Fenna
Frederika Geertje Gerritje Grada Hanna Harmke Hendrina Jansje Jozina Lena Lubbertje Marrigje
Metje Reintje Roelofje Stijntje Willemke Aleida Angela Barbera Cecilia Clara Cornelia Dorothea
Emerentia Francina Geertruy Gijsberta Ida Josina Judith Louisa Magdalena Margaretha Petronella
Rosalia Susanna Theodora Ursula Veronica Wilhelmina Adelheid Bernardina Everdiena Gezina Hermina
Reinnera Sibilla Wendelina Adriana Apolonia Cornelia Digna Engeltje Fijtje Geesje Immetje Jaapje
Jannigje Lijntje Maartje Naatje Pleuntje Willempje Ariaantje Neeltje Aagje Ada Alie Coba Fien Greet
Jopie Lien Miep Nellie Rie Sien Sjaan Toos Truus Wies Riek Nol Door Anneke Ike Janne Jeanne Jeannette""".split())

def first_name(desc):
    low = desc.lower()
    if any(low.startswith(w) for w in ('afwijzen','ondersteun','correspondentie','stukken','afwijz','financi','leeg','verzoek')):
        return None, None
    m = re.search(r'\b(redde(?:n)?|poogde(?:n)?|probeerde(?:n)?|bracht(?:en)?|nam(?:en)?|gedroegen|hielp|verrichtte|trok|verloste)\b', desc)
    head = desc[:m.start()] if m else desc.split(',')[0]
    head = head.split(' en ')[0].split(',')[0].strip()
    toks = head.split()
    fn = next((t for t in toks if t[:1].isupper()), None)
    return fn, head

def gender(desc):
    fn, head = first_name(desc)
    if not fn:
        return "onbekend"
    # married-woman form: surname with a hyphen (Aardema-Snijders) -> strong female signal
    hyph = bool(head and re.search(r'[A-Z][a-zäöëé]+-[A-Z][a-zäöëé]+', head))
    clean = fn.strip(".")
    if clean in FEMALE:
        return "vrouw"
    if clean in MALE:
        return "man"
    if re.fullmatch(r'[A-Z]', clean):          # initial only
        return "vrouw" if hyph else "onbekend"
    # ending heuristics (female-leaning Dutch endings)
    if re.search(r'(tje|sje|pje|kje|ke|ien|ine|ette|ienne|a|na|tha|dina)$', clean):
        # a few male exceptions ending in -a/-e
        if clean not in ("Bona","Attila"):
            return "vrouw"
    if hyph:
        return "vrouw"
    return "man" if re.search(r'(us|er|t|k|n|d|s|o|f|m|p|rt)$', clean) else "onbekend"

if __name__ == "__main__":
    import json
    from collections import Counter
    recs = json.load(open("dossiers_raw.json"))
    c = Counter(gender(x["desc"]) for x in recs)
    tot = sum(c.values())
    print("verdeling:", dict(c), "van", tot)
    for g in ("man","vrouw","onbekend"):
        print(f"  {g}: {c[g]} ({100*c[g]/tot:.1f}%)")
    print("\n--- steekproef vrouw ---")
    n=0
    for x in recs:
        if gender(x["desc"])=="vrouw":
            print(" ", x["nr"], x["desc"][:70]); n+=1
        if n>=12: break
    print("\n--- steekproef onbekend ---")
    n=0
    for x in recs:
        if gender(x["desc"])=="onbekend":
            print(" ", x["nr"], x["desc"][:70]); n+=1
        if n>=8: break
