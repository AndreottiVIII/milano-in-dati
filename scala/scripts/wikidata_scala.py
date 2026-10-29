"""Opere con prima rappresentazione alla Scala (Wikidata, CC0). Uso: python -I wikidata_scala.py <cartella_raw_wikidata>"""
import sys, os, json, time, requests
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)", "Accept": "application/sparql-results+json"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
Q = {
"premiere_p4647": """
SELECT ?work ?workLabel ?workDescription ?date ?instLabel ?composerLabel ?librettistLabel ?genreLabel ?placeLabel WHERE {
  ?work wdt:P4647 ?place . VALUES ?place { wd:Q5471 }
  OPTIONAL { ?work wdt:P1191 ?date } OPTIONAL { ?work wdt:P31 ?inst }
  OPTIONAL { ?work wdt:P86 ?composer } OPTIONAL { ?work wdt:P87 ?librettist } OPTIONAL { ?work wdt:P136 ?genre }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }""",
"premiere_p276_event": """
SELECT ?item ?itemLabel ?itemDescription ?date ?instLabel WHERE {
  ?item wdt:P276 wd:Q5471 . OPTIONAL { ?item wdt:P585 ?date } OPTIONAL { ?item wdt:P31 ?inst }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }""",
"premiere_location_any": """
SELECT ?work ?workLabel ?date ?instLabel ?composerLabel WHERE {
  ?work wdt:P1191 ?date . ?work wdt:P291|wdt:P276|wdt:P4647 wd:Q5471 .
  OPTIONAL { ?work wdt:P31 ?inst } OPTIONAL { ?work wdt:P86 ?composer }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }""",
}
for k, q in Q.items():
    p = os.path.join(out, k + ".json")
    if os.path.exists(p): continue
    for t in range(4):
        r = requests.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"}, headers=UA, timeout=120)
        if r.status_code in (429, 504): time.sleep(30*(t+1)); continue
        r.raise_for_status(); open(p, "w", encoding="utf8").write(r.text)
        print(k, len(r.json()["results"]["bindings"]), "righe"); break
    time.sleep(5)
