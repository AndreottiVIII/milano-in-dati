"""Scarica (con pause) le fonti "una tantum": robots.txt e mappa del Comitato, note legali, due voci di it.wikipedia (wikitext via API), Overpass (OSM), Wikidata SPARQL.
Uso: python -I -X utf8 scarica_fonti.py <raw_dir_assoluto>   (i file scaricati sono dati non fidati: restano in raw/, mai eseguiti)"""
import sys, os, time, urllib.request, urllib.parse
raw = sys.argv[1]
UA = {"User-Agent": "milano-in-dati research (milano-in-dati)"}


def get(url, out, data=None, headers=None):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    h = dict(UA); h.update(headers or {})
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None, headers=h)
    b = urllib.request.urlopen(req, timeout=180).read()
    open(out, "wb").write(b); print(out, len(b), flush=True); time.sleep(1.2)


W = "https://www.pietredinciampomilano.it/"
get(W + "robots.txt", os.path.join(raw, "web", "robots.txt"))
get(W + "la-mappa-delle-pietre/", os.path.join(raw, "web", "la-mappa-delle-pietre.html"))
get(W + "?page_id=1378", os.path.join(raw, "web", "legali.html"))
for t, f in [("Pietre_d'inciampo_a_Milano", "Pietre_dinciampo_a_Milano.json"), ("Pietre_d'inciampo_nel_centro_storico_di_Milano", "Pietre_dinciampo_nel_centro_storico_di_Milano.json")]:
    get("https://it.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content|timestamp|ids&rvslots=main&format=json&formatversion=2&titles=" + urllib.parse.quote(t), os.path.join(raw, "wikipedia", f))
get("https://overpass-api.de/api/interpreter", os.path.join(raw, "osm", "overpass_stolperstein_milano.json"),
    data={"data": '[out:json][timeout:120];(node["memorial:type"="stolperstein"](45.38,9.04,45.57,9.32);node["memorial"="stolperstein"](45.38,9.04,45.57,9.32););out body;'})
q = ('SELECT ?s ?sLabel ?coord WHERE { SERVICE wikibase:box { ?s wdt:P625 ?coord . bd:serviceParam wikibase:cornerSouthWest "Point(9.04 45.38)"^^geo:wktLiteral . '
     'bd:serviceParam wikibase:cornerNorthEast "Point(9.32 45.57)"^^geo:wktLiteral . } ?s wdt:P31 wd:Q26703203 . SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }')
get("https://query.wikidata.org/sparql", os.path.join(raw, "wikidata", "stolpersteine_milano.json"), data={"query": q}, headers={"Accept": "application/sparql-results+json"})
