#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bouw de voorbeelddossier-pagina (self-contained) — inv.nr. 3622.

Toont één compleet Carnegie-dossier van dichtbij: de ijsredding op de Oude Waal
bij Nijmegen (28 januari 1933) door Johannes B.J. Jooren. De pagina laat de
verschillende *soorten* documenten in een dossier zien — aanvraag, politie-
onderzoek, bestuurlijk advies en het besluit — met per soort een korte duiding
en een transcriptie van de kernpassage. De scans staan in ./dossier/ en worden
als data-URI ingesloten, zodat de pagina één zelfstandig bestand blijft (net als
kaart.html en stats.html).
"""
import base64, os

WORK = os.path.dirname(os.path.abspath(__file__))
IMGDIR = f"{WORK}/dossier"
OUT = f"{WORK}/dossier.html"
NR = 3622
NA = f"https://www.nationaalarchief.nl/onderzoeken/archief/2.19.364/invnr/{NR}"


def datauri(name):
    with open(f"{IMGDIR}/{name}.jpg", "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def scan(name, alt):
    return (f'<button class="scan" type="button" aria-label="Vergroot: {alt}">'
            f'<img loading="lazy" src="{datauri(name)}" alt="{alt}"></button>')


# ---- de vier documentsoorten in dit dossier (chronologisch) ------------------
DOCS = [
    dict(
        eyebrow="1 · De aanvraag &middot; handgeschreven &middot; 2 februari 1933",
        title="De redder schrijft zelf het Fonds aan",
        scans=[scan("p07", "Handgeschreven brief van J.B.J. Jooren, pagina 1"),
               scan("p08", "Handgeschreven brief van J.B.J. Jooren, pagina 2")],
        duiding=(
            "Een dossier begint vaak met een <b>ego-document</b>: de redder — of een "
            "familielid, buurman of plaatselijke krant — meldt de daad zelf aan. Het is "
            "de meest persoonlijke, maar ook de meest subjectieve bron. Jooren beschrijft "
            "de redding in eigen woorden en voegt er een <b>verzoek</b> aan toe: hij is sinds "
            "maart 1932 werkloos en kan zijn bij de redding bedorven kostuum niet vervangen. "
            "Zo'n aanvraag laat zien wat de kale inventarisregel nooit prijsgeeft — de "
            "beweegredenen en de armoede erachter."),
        quote=("Zaterdag 28 Januari 1933, des middags streeks 3 u. 30 stond ik op de Oude "
               "Waal, in de gemeente Ubbergen&#8211;Beek, bij Nijmegen&hellip; toen plotseling "
               "twee meisjes het wak niet opmerkten&hellip; Ik kon nog juist mijn winterjas "
               "uittrekken, mijn hoed afgooien en sprong direct in 't wak."),
        qsrc="&mdash; uit de aanvraagbrief van J.B.J. Jooren"),
    dict(
        eyebrow="2 · Het onderzoek &middot; politierapport &middot; 16 februari 1933",
        title="De politie hoort vier getuigen",
        scans=[scan("p01", "Politierapport, pagina 1"),
               scan("p02", "Politierapport, pagina 2"),
               scan("p03", "Politierapport, pagina 3"),
               scan("p04", "Politierapport, pagina 4")],
        grid=True,
        duiding=(
            "Het Fonds nam een aanvraag niet op gezag aan. Het vroeg de <b>plaatselijke "
            "politie</b> om een onderzoek, en inspecteur Johannes Meijberg hoorde vier "
            "getuigen onder een ambtelijk rapport: de redder zelf, de <b>twee geredde "
            "vrouwen</b> &mdash; Wilhelmina van Gelder (25) en Mientje Stevens (20) &mdash; en "
            "omstander Johannes Ham, die vanaf het ijs een stok toestak. Dit "
            "verificatiestuk is doorgaans de <b>rijkste bron</b> van het dossier: namen, "
            "leeftijden, adressen, beroepen en het precieze verloop, van meerdere kanten "
            "bevestigd. Het legt ook menselijke wrijving vast &mdash; getuige Ham vond het "
            "&lsquo;onsympathiek&rsquo; dat Jooren zelf om een beloning had geschreven."),
        quote=("Ter voldoening aan een daartoe gedaan verzoek van den heer Secretaris van "
               "het Carnegie Heldenfonds&hellip; heb ik, Johannes Meijberg, Inspecteur van "
               "Politie&hellip; een onderzoek ingesteld en daarbij gehoord&hellip;"),
        qsrc="&mdash; openingszin van het politierapport"),
    dict(
        eyebrow="3 · Het advies &middot; brief burgemeester &middot; 9 maart 1933",
        title="De burgemeester stuurt door en beveelt aan",
        scans=[scan("p06", "Brief van het Gemeentebestuur van Nijmegen, 9 maart 1933")],
        duiding=(
            "Tussen aanvrager en Fonds zit vaak een <b>bestuurlijke schakel</b>. Het "
            "gemeentebestuur van Nijmegen zendt het politierapport door aan het Bestuur van "
            "het Carnegie Heldenfonds in Den Haag &mdash; met twee bijlagen &mdash; en spreekt "
            "een <b>positief advies</b> uit. Zulke doorzendbrieven tonen hoe de erkenning "
            "van een reddingsdaad langs de officiële weg liep: van straat naar politie, naar "
            "gemeentehuis, naar het landelijke Fonds."),
        quote=("Op grond van het daarin medegedeelde komt het mij voor, dat er voor het "
               "Fonds aanleiding bestaat eene belooning of eene vergoeding voor geleden "
               "schade toe te kennen."),
        qsrc="&mdash; de Burgemeester van Nijmegen aan het Carnegie Heldenfonds"),
    dict(
        eyebrow="4 · Het besluit &middot; brief Carnegie Heldenfonds &middot; 13 mei 1933",
        title="Het Fonds kent ƒ 50 toe",
        scans=[scan("p10", "Besluit van het Carnegie Heldenfonds, 13 mei 1933")],
        duiding=(
            "Het <b>uitkomststuk</b>: het bestuur van het Fonds besluit wat wordt "
            "toegekend &mdash; een medaille, een oorkonde, geld, of een combinatie. Jooren "
            "had in het rapport laten weten &lsquo;liever een gratificatie in geld dan een "
            "medaille&rsquo; te ontvangen; het Fonds kent hem <b>&#402;&nbsp;50</b> toe als "
            "beloning &eacute;n schadevergoeding, per postwissel en via de burgemeester "
            "uitbetaald. Van redding tot uitkering verliep <b>ruim drie maanden</b>."),
        quote=("&hellip;heeft het Bestuur van het Carnegie Heldenfonds de eer U mede te "
               "deelen, dat het besloten heeft aan J.B.J. Jooren voor de door hem verrichte "
               "redding een bedrag van &#402;&nbsp;50,&#8212; toe te kennen als belooning en "
               "schadevergoeding."),
        qsrc="&mdash; het besluit van het Bestuur, Den Haag"),
]

# ---- tijdlijn ---------------------------------------------------------------
TIMELINE = [
    ("28 jan 1933", "De redding", "Twee schaatssters zakken door een wak in de Oude Waal; Jooren springt na."),
    ("2 feb 1933", "De aanvraag", "Jooren schrijft het Fonds zelf aan om een tegemoetkoming."),
    ("16 feb 1933", "Het onderzoek", "De politie hoort vier getuigen en stelt een rapport op."),
    ("9 mrt 1933", "Het advies", "De burgemeester zendt door en beveelt een beloning aan."),
    ("13 mei 1933", "Het besluit", "Het Fonds kent ƒ 50 toe als beloning en schadevergoeding."),
]

# ---- feiten -----------------------------------------------------------------
FACTS = [
    ("Redder", "Johannes B.J. Jooren (39), ziekenverpleger &mdash; werkloos sinds maart 1932, Smidstraat 44, Nijmegen"),
    ("Geredden", "Wilhelmina M.J. van Gelder (25) en Wilhelmina C. &lsquo;Mientje&rsquo; Stevens (20), Van&nbsp;Langeveldstraat, Nijmegen"),
    ("Wat", "Twee schaatssters zakten door het ijs bij een wak"),
    ("Waar", "De Oude Waal, gemeente Ubbergen (Beek bij Nijmegen)"),
    ("Wanneer", "Zaterdag 28 januari 1933, omstreeks 15.30 uur"),
    ("Hulp", "Omstander Johannes A. Ham (38, huisschilder) reikte vanaf het ijs een stok toe"),
    ("Afloop", "Beide vrouwen gered; Jooren zelf ook uit het water geholpen"),
    ("Beloning", "&#402;&nbsp;50 als beloning &eacute;n schadevergoeding (13 mei 1933)"),
]

timeline_html = "".join(
    f'<li><span class="tl-date">{d}</span><span class="tl-title">{t}</span>'
    f'<span class="tl-txt">{x}</span></li>' for d, t, x in TIMELINE)
facts_html = "".join(f"<div class=\"fact\"><dt>{k}</dt><dd>{v}</dd></div>" for k, v in FACTS)


def doc_html(d):
    cls = "scans grid" if d.get("grid") else "scans"
    scans = f'<div class="{cls}">' + "".join(d["scans"]) + "</div>"
    return (f'<section class="doc">'
            f'<div class="doc-eyebrow">{d["eyebrow"]}</div>'
            f'<h2>{d["title"]}</h2>'
            f'<p class="duiding">{d["duiding"]}</p>'
            f'{scans}'
            f'<blockquote class="quote">&bdquo;{d["quote"]}&rdquo;'
            f'<span class="qsrc">{d["qsrc"]}</span></blockquote>'
            f'</section>')


docs_html = "".join(doc_html(d) for d in DOCS)

HTML = f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carnegie Heldenfonds &mdash; een dossier van dichtbij</title>
<meta name="description" content="Eén compleet Carnegie-dossier van dichtbij: de ijsredding op de Oude Waal bij Nijmegen (1933), met de verschillende soorten documenten &mdash; aanvraag, politieonderzoek, advies en besluit &mdash; toegelicht.">
<style>
  :root{{
    --bg:#f6f7f5; --card:#ffffff; --ink:#171717; --muted:#6b7280; --line:#e7e7e4;
    --accent:#0e7490; --cream1:#faf6ea; --cream2:#f6efe0; --creamln:#ece0c8;
    --shadow:0 1px 3px #0000000f,0 8px 24px #00000010;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased}}
  a{{color:var(--accent)}}
  .wrap{{max-width:900px;margin:0 auto;padding:22px 20px 60px}}
  header{{display:flex;align-items:center;gap:14px;margin-bottom:6px;flex-wrap:wrap}}
  .logo{{width:44px;height:44px;border-radius:11px;display:grid;place-items:center;font-size:24px;flex:none;
    background:linear-gradient(135deg,#0e7490,#0891b2);box-shadow:0 2px 8px #0e749055}}
  h1{{font-size:23px;margin:0;letter-spacing:-.02em}}
  header .sub{{color:var(--muted);font-size:13px;margin:2px 0 0}}
  .nav{{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}}
  .nav a{{font-size:13px;font-weight:600;text-decoration:none;background:#fff;border:1px solid var(--line);
    padding:8px 13px;border-radius:10px;white-space:nowrap;color:var(--accent)}}
  .nav a:hover{{border-color:#cbd5e1}}
  .lead{{color:#374151;font-size:15.5px;line-height:1.6;margin:16px 0 8px}}
  .lead .nr{{font-variant-numeric:tabular-nums}}
  /* samenvattingskaart (crème) */
  .case{{background:linear-gradient(135deg,var(--cream1),var(--cream2));border:1px solid var(--creamln);
    border-radius:20px;padding:20px 22px;margin:20px 0 26px}}
  .case .lbl{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#a07d3c;margin:0 0 8px}}
  .case h2{{font-size:19px;margin:0 0 8px;letter-spacing:-.01em}}
  .case p.story{{margin:0 0 16px;font-size:14.5px;line-height:1.6;color:#3a3320}}
  .facts{{display:grid;grid-template-columns:1fr 1fr;gap:2px 26px;margin:0}}
  .fact{{display:flex;gap:10px;padding:7px 0;border-top:1px solid #e7dcc4}}
  .fact dt{{flex:none;width:78px;font-size:12px;font-weight:700;color:#8a6d33;padding-top:1px}}
  .fact dd{{margin:0;font-size:13.5px;line-height:1.4;color:#2f2a1c}}
  .case .nalink{{display:inline-block;margin-top:14px;font-size:13px;font-weight:600;color:var(--accent);text-decoration:none}}
  .case .nalink:hover{{text-decoration:underline}}
  /* tijdlijn */
  .tl-lbl{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 12px}}
  ol.timeline{{list-style:none;margin:0 0 30px;padding:0;display:grid;
    grid-template-columns:repeat(5,1fr);gap:12px;counter-reset:t}}
  ol.timeline li{{position:relative;background:var(--card);border:1px solid var(--line);border-radius:14px;
    padding:26px 13px 13px;box-shadow:var(--shadow)}}
  ol.timeline li::before{{counter-increment:t;content:counter(t);position:absolute;top:-11px;left:13px;
    width:23px;height:23px;border-radius:50%;background:var(--accent);color:#fff;font-size:12px;font-weight:700;
    display:grid;place-items:center;box-shadow:0 2px 6px #0e749055}}
  .tl-date{{display:block;font-size:11.5px;font-weight:700;color:var(--accent);font-variant-numeric:tabular-nums}}
  .tl-title{{display:block;font-size:14px;font-weight:700;margin:3px 0 4px;letter-spacing:-.01em}}
  .tl-txt{{display:block;font-size:12px;color:var(--muted);line-height:1.4}}
  /* documentsecties */
  .doc{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 22px 22px;
    box-shadow:var(--shadow);margin:0 0 20px}}
  .doc-eyebrow{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--accent);margin:0 0 6px}}
  .doc h2{{font-size:18px;margin:0 0 10px;letter-spacing:-.01em}}
  .duiding{{font-size:14.5px;line-height:1.62;color:#374151;margin:0 0 16px}}
  .scans{{display:flex;gap:14px;flex-wrap:wrap;margin:0 0 16px}}
  .scans.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
  .scan{{padding:0;border:1px solid var(--line);background:#fff;border-radius:10px;overflow:hidden;cursor:zoom-in;
    box-shadow:var(--shadow);display:block;flex:1;min-width:180px;transition:transform .15s,box-shadow .15s}}
  .scans:not(.grid) .scan{{max-width:340px}}
  .scan:hover{{transform:translateY(-2px);box-shadow:0 10px 26px #0000001c;border-color:#cbd5e1}}
  .scan img{{display:block;width:100%;height:auto}}
  .quote{{margin:0;border-left:3px solid var(--creamln);background:linear-gradient(135deg,var(--cream1),var(--cream2));
    border-radius:0 12px 12px 0;padding:14px 18px;font-size:14.5px;line-height:1.6;color:#3a3320;font-style:italic}}
  .quote .qsrc{{display:block;margin-top:8px;font-size:12px;font-style:normal;color:#8a6d33;font-weight:600}}
  /* afsluiting */
  .close{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 22px;
    box-shadow:var(--shadow);margin:6px 0 0}}
  .close h2{{font-size:17px;margin:0 0 10px;letter-spacing:-.01em}}
  .close p{{font-size:14.5px;line-height:1.62;color:#374151;margin:0 0 10px}}
  .close .cta{{display:inline-flex;gap:8px;flex-wrap:wrap;margin-top:6px}}
  .close .cta a{{font-size:13.5px;font-weight:600;text-decoration:none;background:#f0fafc;border:1px solid #cfe8ee;
    color:var(--accent);padding:8px 13px;border-radius:10px}}
  .close .cta a:hover{{border-color:var(--accent)}}
  footer{{color:var(--muted);font-size:12px;margin-top:30px;line-height:1.6;border-top:1px solid var(--line);padding-top:16px}}
  footer .fnav{{margin-bottom:10px;font-weight:600}}
  footer .fnav a{{text-decoration:none}}
  /* lightbox */
  #lb{{position:fixed;inset:0;background:#0b0b0bde;display:none;place-items:center;z-index:100;padding:20px;cursor:zoom-out}}
  #lb.on{{display:grid}}
  #lb img{{max-width:100%;max-height:100%;border-radius:6px;box-shadow:0 10px 50px #000a}}
  #lb .x{{position:fixed;top:14px;right:18px;color:#fff;font-size:30px;background:none;border:none;cursor:pointer;line-height:1}}
  @media(max-width:760px){{
    ol.timeline{{grid-template-columns:1fr 1fr}}
    .facts{{grid-template-columns:1fr}}
    .scans.grid{{grid-template-columns:1fr 1fr}}
  }}
  @media(max-width:480px){{ol.timeline{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">&#128507;</div>
    <div>
      <h1>Een dossier van dichtbij</h1>
      <p class="sub">Carnegie Heldenfonds &middot; voorbeelddossier inv.nr. <span class="nr">{NR}</span></p>
    </div>
    <nav class="nav">
      <a href="../stats">&#128202; Inzichten</a>
      <a href="../over">&#8505;&#65039; Over</a>
      <a href="../">&#8592; Kaart</a>
    </nav>
  </header>

  <p class="lead">Op de kaart en in de <a href="../stats">inzichten</a> is elke redding teruggebracht
  tot &eacute;&eacute;n regel. Maar achter zo'n regel zit een heel dossier. Hier openen we er &eacute;&eacute;n
  helemaal: <b>inv.nr. <span class="nr">{NR}</span></b> &mdash; de ijsredding op de Oude Waal bij Nijmegen,
  begin 1933. Het toont de <b>verschillende soorten documenten</b> waaruit een Carnegie-dossier is opgebouwd,
  en hoe de erkenning van een reddingsdaad in zijn werk ging.</p>

  <div class="case">
    <p class="lbl">De zaak in het kort</p>
    <h2>Twee schaatssters door het ijs &mdash; en een werkloze verpleger die nasprong</h2>
    <p class="story">Op een drukke schaatsmiddag in januari 1933 zakken twee jonge vrouwen bij een wak
    door het ijs van de Oude Waal. Ziekenverpleger Johannes Jooren &mdash; toevallig toeschouwer, en al een
    jaar zonder werk &mdash; trekt zijn jas uit en springt na. Met hulp van een omstander die vanaf het ijs
    een stok toereikt, haalt hij beide vrouwen levend uit het water. Zijn beste kostuum is bedorven. Ruim
    drie maanden later kent het Carnegie Heldenfonds hem &#402;&nbsp;50 toe.</p>
    <dl class="facts">{facts_html}</dl>
    <a class="nalink" href="{NA}" target="_blank" rel="noopener">Bekijk het dossier bij het Nationaal Archief &#8599;</a>
  </div>

  <p class="tl-lbl">Van redding tot beloning &mdash; in vijf stappen</p>
  <ol class="timeline">{timeline_html}</ol>

  {docs_html}

  <div class="close">
    <h2>Van dossier naar &eacute;&eacute;n regel</h2>
    <p>De interactieve kaart en de statistieken vatten elk van de <b>9.628</b> dossiers samen tot een
    gestructureerde regel: &lsquo;<i>Jooren redde in 1933 te Ubbergen twee schaatssters uit een wak</i>&rsquo;.
    Dat maakt het mogelijk bijna een eeuw reddingsgeschiedenis in &eacute;&eacute;n oogopslag te overzien.</p>
    <p>Maar dit ene dossier laat ook de <b>grens</b> van die samenvatting zien. De aanvraag, het
    getuigenverhoor, het advies en het besluit bevatten wat geen enkele dataregel vangt: de werkloosheid en
    armoede achter de daad, de precieze toedracht van vier kanten bevestigd, en zelfs de menselijke wrijving
    &mdash; een getuige die het &lsquo;onsympathiek&rsquo; vond dat de redder zelf om geld vroeg. Het dossier
    is de bron; de dataregel is de samenvatting.</p>
    <div class="cta">
      <a href="../">&#128506;&#65039; Verken de kaart</a>
      <a href="../stats">&#128202; Bekijk de inzichten</a>
      <a href="{NA}" target="_blank" rel="noopener">&#128196; Dit dossier bij het Nationaal Archief &#8599;</a>
    </div>
  </div>

  <footer>
    <div class="fnav">
      <a href="../">&#8592; naar de kaart</a> &nbsp;&middot;&nbsp;
      <a href="../stats">&#128202; Inzichten &amp; statistiek</a> &nbsp;&middot;&nbsp;
      <a href="../over">&#8505;&#65039; Over</a>
    </div>
    Bron: Nationaal Archief, <b>Stichting Carnegie Heldenfonds Nederland &mdash; Persoonsdossiers, 1903-1987</b>
    (toegang 2.19.364), inv.nr. {NR}. Scans en transcripties uit het originele dossier; spelling van de
    documenten ongewijzigd overgenomen.
  </footer>
</div>

<div id="lb"><button class="x" aria-label="Sluiten">&times;</button><img alt=""></div>
<script>
(function(){{
  var lb=document.getElementById('lb'), lbimg=lb.querySelector('img');
  document.querySelectorAll('.scan').forEach(function(b){{
    b.addEventListener('click',function(){{lbimg.src=b.querySelector('img').src;lb.classList.add('on');}});
  }});
  function close(){{lb.classList.remove('on');lbimg.src='';}}
  lb.addEventListener('click',close);
  document.addEventListener('keydown',function(e){{if(e.key==='Escape')close();}});
}})();
</script>
<script>window.goatcounter={{path:function(p){{return location.host+p}}}}</script>
<script data-goatcounter="https://stats.alanmoss.nl/count" async src="https://stats.alanmoss.nl/count.js"></script>
</body>
</html>"""

open(OUT, "w", encoding="utf-8").write(HTML)
print("geschreven:", OUT, "| bytes", len(HTML), "(~", len(HTML) // 1024, "KB )")
print("documentsoorten:", len(DOCS), "| tijdlijn-stappen:", len(TIMELINE))
