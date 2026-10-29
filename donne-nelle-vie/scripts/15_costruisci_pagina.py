"""Fase 2, passo 5: costruisce docs/vie/index.html (numeri e lista incorporati nell'HTML, mappa dal geojson).
Uso: python -I 15_costruisci_pagina.py out_dir(percentuali.json, csv periodi) strade_classificate_arricchite_v2.csv docs_vie_dir"""
import sys, json, html
import pandas as pd

outdir, csv, docs = sys.argv[1:4]
P = json.load(open(f"{outdir}/percentuali.json", encoding='utf8'))
res = {r['scope']: r for r in P['percentuali']}
per = pd.read_csv(f"{outdir}/percentuali_per_periodo.csv")
d = pd.read_csv(csv, dtype=str).fillna('')
W = d[(d.categoria == 'donna') & d.confidenza.isin(['sicuro', 'incerto'])].copy()


def pc(x, dec=1):
    return f"{x * 100:.{dec}f}".replace('.', ',') + '%'


def n(x):
    return f"{int(x):,}".replace(',', '.')


def cell(r, key):
    """key = 'persone' | 'tutte'"""
    if key == 'persone':
        firm, wide = r['quota_donne_su_persone_ferma'], r['quota_donne_su_persone_con_incerti']
        lo, hi = r['quota_donne_su_persone_estremo_basso'], r['quota_donne_su_persone_estremo_alto']
        sub = f"{n(r['donne_sicure'])} donne su {n(r['persone_sicure'])} vie intitolate a persone (certe)"
    else:
        firm, wide = r['quota_donne_su_tutte_le_strade_ferma'], r['quota_donne_su_tutte_le_strade_con_incerti']
        lo, hi = r['quota_donne_su_tutte_le_strade_estremo_basso'], r['quota_donne_su_tutte_le_strade_estremo_alto']
        sub = f"{n(r['donne_sicure'])} donne su {n(r['strade_totali'])} vie in tutto"
    a, b = min(firm, wide), max(firm, wide)
    return (f'<span class="big">{pc(firm)}</span><br><span class="sub">{sub}</span><br>'
            + (f'<span class="rng">contando anche le vie incerte (quasi tutte di uomini): <b>{pc(a)}&ndash;{pc(b)}</b></span>'
               if pc(a) != pc(b) else '<span class="rng">le vie incerte non cambiano questo conto</span>'))


cs, ss = res['con santi'], res['senza santi']
rows_per = ''.join(
    f"<tr><td>{r.periodo}</td><td class='r'>{int(r.donne_sicure)} / {int(r.persone_sicure)}</td><td class='r'>{pc(r.quota_ferma) if r.persone_sicure else '–'}</td>"
    f"<td class='r'>{int(r.donne_con_incerti)} / {int(r.persone_con_incerti)}</td><td class='r'>{pc(r.quota_con_incerti) if r.persone_con_incerti else '–'}</td></tr>"
    for r in per.itertuples())


def years(r):
    a, b = r.nascita, r.morte
    if a or b:
        return f"{a or '?'}&ndash;{b or '?'}"
    return ''


def dt(s):
    return f"{s[:4]}-{s[4:6]}-{s[6:]}" if len(s) == 8 and s not in ('17000101', '19000101') else ''


def esc(s):
    return html.escape(s or '')


lis = []
W = W.sort_values(['confidenza', 'nome'], ascending=[False, True])
for r in W.itertuples():
    flags = []
    if r.santa == '1':
        flags.append('santa')
    if r.gruppo == '1':
        flags.append('gruppo')
    if r.confidenza == 'incerto':
        flags.append('da verificare')
    prof = ', '.join(x.strip() for x in r.professioni.split(',')[:3]) if r.professioni else ''
    lis.append(f"<tr class='{'inc' if r.confidenza == 'incerto' else ''}'><td>{esc(r.nome)}</td><td>{esc(r.persona.split(' | ')[0] if r.confidenza == 'sicuro' else r.persona) or '&ndash;'}</td>"
               f"<td>{years(r)}</td><td>{esc(prof)}</td><td>{dt(r.data_intitolazione)}</td><td>{', '.join(flags)}</td></tr>")
n_ok = int((W.confidenza == 'sicuro').sum())
n_inc = int((W.confidenza == 'incerto').sum())
osm_ts = P.get('osm_timestamp', '2026-10-29T14:21Z')

page = f"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Milano in dati · Le vie intitolate a donne</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>
:root{{--acc:#c2185b;--ink:#111;--bg:#fff;--mut:#666;--line:#ddd}}
*{{box-sizing:border-box}} body{{margin:0;font:16px/1.5 system-ui,Arial,sans-serif;color:var(--ink);background:var(--bg)}}
main{{max-width:980px;margin:0 auto;padding:16px}} h1{{font-size:1.7rem;margin:.6em 0 .2em}} h2{{font-size:1.2rem;margin:1.8em 0 .4em;border-top:2px solid var(--ink);padding-top:.6em}}
table{{border-collapse:collapse;width:100%}} th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}} th{{font-size:.85rem;color:var(--mut);font-weight:600}}
td.r{{text-align:right;white-space:nowrap}} .big{{font-size:2.2rem;font-weight:700;color:var(--acc)}} .sub{{font-size:.85rem;color:var(--mut)}} .rng{{font-size:.95rem}}
.src{{font-size:.8rem;color:var(--mut)}} #map .leaflet-tile-pane{{filter:grayscale(1) brightness(1.08) contrast(.85)}} #map{{height:68vh;min-height:380px;border:1px solid var(--ink)}} tr.inc td{{color:var(--mut)}}
a{{color:var(--acc)}} .legend span{{display:inline-block;width:28px;height:0;border-top:4px solid var(--acc);vertical-align:middle;margin-right:6px}} .legend span.d{{border-top-style:dashed}}
.scroll{{max-height:520px;overflow:auto;border:1px solid var(--line)}} footer{{margin:2.5em 0 1em;font-size:.82rem;color:var(--mut);border-top:1px solid var(--line);padding-top:.8em}}
@media(max-width:640px){{.big{{font-size:1.7rem}} th,td{{padding:5px 4px;font-size:.88rem}}}}
</style></head><body><main>
<h1>Quante vie di Milano sono intitolate a donne?</h1>
<p>Tra le vie e le piazze del Comune di Milano intitolate a una persona, quelle dedicate a una donna sono una piccola parte. Qui sotto il conto, la mappa (colorate solo le vie delle donne) e l&rsquo;elenco.</p>

<h2>Le percentuali</h2>
<table>
<tr><th></th><th>Santi compresi</th><th>Santi esclusi</th></tr>
<tr><td><b>Su 100 vie intitolate a persone</b></td><td>{cell(cs, 'persone')}</td><td>{cell(ss, 'persone')}</td></tr>
<tr><td><b>Su 100 vie in tutto</b></td><td>{cell(cs, 'tutte')}</td><td>{cell(ss, 'tutte')}</td></tr>
</table>
<p class="src"><b>Numero fermo</b> = solo i casi sicuri (persona indicata nel tag OpenStreetMap <code>name:etymology:wikidata</code>, oppure trovata su Wikidata con nome identico; sesso dal campo Wikidata P21). <b>Con i casi incerti</b> = si aggiungono le vie per cui una donna &egrave; solo una possibilit&agrave; (omonimie, nome di battesimo senza conferma, santa o chiesa?). &laquo;Santi esclusi&raquo; toglie dal conto, sia al numeratore sia al denominatore, tutte le vie dedicate a santi e sante. Un gruppo di sole sorelle conta come donne; &laquo;Fratelli&hellip;&raquo; e coppie sono nel totale ma non tra le donne.
Fonte dei numeri: <a href="data/percentuali.json">data/percentuali.json</a> (calcolati da <a href="data/strade_classificate_v2.csv">data/strade_classificate_v2.csv</a>, campi <code>categoria</code>, <code>confidenza</code>, <code>santa</code>, <code>santo</code>). Universo: {n(cs['strade_totali'])} vie e piazze del Comune di Milano (registro civici del Comune, 4.030 codici via, pi&ugrave; {int(cs['strade_totali']) - 4030} vie presenti solo in OpenStreetMap). Dati OSM del {esc(osm_ts[:10])}.</p>

<h2>Quando sono state intitolate</h2>
<table><tr><th>Anno di intitolazione</th><th>donne / persone (certe)</th><th>quota</th><th>con incerti: donne / persone</th><th>quota</th></tr>{rows_per}</table>
<p class="src">Solo per le vie con <code>DATA_INTITOLAZIONE</code> nel registro del Comune (circa il 31% delle vie, mancano soprattutto le vie storiche): numeri piccoli, da leggere con cautela. Fonte: <a href="data/percentuali_per_periodo.csv">data/percentuali_per_periodo.csv</a>, <a href="data/percentuali_per_decennio.csv">per decennio</a>.</p>

<h2>La mappa</h2>
<p class="legend"><span></span>via intitolata a una donna (caso certo) &nbsp; <span class="d"></span>caso da verificare. Clic su una via per vedere la persona.</p>
<div id="map" role="img" aria-label="Mappa di Milano con le vie intitolate a donne"></div>

<h2>Le vie intitolate a donne ({n_ok}{(', ' + str(n_inc) + ' da verificare') if n_inc else ''})</h2>
<div class="scroll"><table><tr><th>Via</th><th>Persona</th><th>Anni</th><th>Professione</th><th>Intitolata il</th><th>Note</th></tr>{''.join(lis)}</table></div>
<p class="src">Fonti: persona e anni da Wikidata (<code>strade_classificate_v2.csv</code>: persona, nascita, morte, professioni); data di intitolazione dal registro del Comune (campo <code>DATA_INTITOLAZIONE</code>, spesso vuoto). I 56 casi dubbi sono stati decisi uno per uno il 29/10/2026: <a href="data/decisioni_davide.csv">elenco delle decisioni (CSV)</a>; tra questi, le vie "Santa Maria…" contano come donna (la Madonna) e Via Donna Prassede come personaggio dei Promessi Sposi.</p>

<footer>
<p><b>Fonti e licenze.</b> Vie, geometrie ed etimologie: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>, licenza ODbL; i dati derivati qui pubblicati (<code>vie_donne.geojson</code>, tabelle CSV) sono quindi anch&rsquo;essi ODbL (condivisione alla pari, con attribuzione). Persone, sesso, date: <a href="https://www.wikidata.org">Wikidata</a>, CC0. Registro dei numeri civici e date di intitolazione: <a href="https://dati.comune.milano.it/dataset/ds634-numeri-civici-coordinate">Comune di Milano, ds634</a>, CC BY. Mappa di base: tessere OpenStreetMap (&copy; OpenStreetMap contributors), rese in grigio.</p>
<p>Confronti: Mapping Diversity (OBC Transeuropa / EDJNet, febbraio 2023) conta per Milano 135 donne su 2.677 vie dedicate a persone (5,0%); un censimento citato dalla stampa nel 2019 ne contava 141 su 4.250 vie. Le differenze di metodo sono spiegate in <code>NOTE.md</code> (sezione Fase 2).</p>
<p>Aggiornato al 29 ottobre 2026. Progetto Milano in dati.</p>
</footer>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
var map = L.map('map').setView([45.4642, 9.19], 12);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}}).addTo(map);
function esc(s) {{ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c) {{ return {{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}}[c]; }}); }}
fetch('data/vie_donne.geojson').then(function(r) {{ return r.json(); }}).then(function(g) {{
  var layer = L.geoJSON(g, {{
    style: function(f) {{ var inc = f.properties.confidenza === 'incerto'; return {{color: '#c2185b', weight: inc ? 3 : 5, opacity: inc ? 0.75 : 1, dashArray: inc ? '6 6' : null}}; }},
    onEachFeature: function(f, l) {{
      var p = f.properties, h = '<b>' + esc(p.nome) + '</b><br>' + (p.persona ? esc(p.persona) : 'persona da verificare');
      if (p.nascita || p.morte) h += ' (' + esc(p.nascita || '?') + '&ndash;' + esc(p.morte || '?') + ')';
      if (p.professione) h += '<br>' + esc(p.professione.split(',').slice(0, 3).join(','));
      if (p.intitolazione && p.intitolazione.length === 8 && p.intitolazione !== '19000101' && p.intitolazione !== '17000101') h += '<br>Intitolata il ' + p.intitolazione.slice(0, 4) + '-' + p.intitolazione.slice(4, 6) + '-' + p.intitolazione.slice(6);
      if (p.confidenza === 'incerto') h += '<br><i>caso da verificare: ' + esc(p.motivo) + '</i>';
      if (p.santa) h += '<br><i>santa</i>';
      if (p.qid) h += '<br><a href="https://www.wikidata.org/wiki/' + esc(p.qid.split(';')[0]) + '" target="_blank" rel="noopener">Wikidata</a>';
      l.bindPopup(h);
    }}
  }}).addTo(map);
}}).catch(function() {{ document.getElementById('map').insertAdjacentHTML('afterend', '<p>Mappa non caricata.</p>'); }});
</script></body></html>"""
open(f"{docs}/index.html", 'w', encoding='utf8').write(page)
print('pagina scritta', len(page) // 1024, 'KB')
