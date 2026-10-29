import sys, json, time, requests
out = sys.argv[1]
UA = {"User-Agent": "milano-in-dati/1.0 (davide.caniatti@gmail.com; research on political violence in Milan)", "Accept": "application/sparql-results+json"}
Q1 = """
SELECT ?item ?itemLabel ?itemLabelEn ?date ?cls ?clsLabel ?coord ?deaths ?inj ?itwiki ?enwiki ?place ?placeLabel WHERE {
  ?item wdt:P31 ?cls .
  ?cls wdt:P279* ?top . VALUES ?top { wd:Q2223653 wd:Q1190554 wd:Q3199915 wd:Q356405 wd:Q217004 wd:Q168983 wd:Q132821 wd:Q49776 wd:Q2334719 wd:Q1139665 wd:Q645883 wd:Q1656682 wd:Q1385351 wd:Q1415764 wd:Q5446649 wd:Q55235283 }
  { ?item wdt:P276 ?place } UNION { ?item wdt:P131 ?place } UNION { ?item wdt:P17 wd:Q38 . ?item wdt:P625 ?c0 . BIND(wd:Q490 AS ?place) FILTER(false) }
  ?place wdt:P131* wd:Q490 .
  OPTIONAL { ?item wdt:P585 ?d1 } OPTIONAL { ?item wdt:P580 ?d2 }
  BIND(COALESCE(?d1,?d2) AS ?date)
  FILTER(!BOUND(?date) || ?date >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
  OPTIONAL { ?item wdt:P625 ?coord } OPTIONAL { ?item wdt:P1120 ?deaths } OPTIONAL { ?item wdt:P1339 ?inj }
  OPTIONAL { ?itwiki schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> }
  OPTIONAL { ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}
"""
def run(q, name):
    for i in range(4):
        r = requests.post("https://query.wikidata.org/sparql", data={"query": q}, headers=UA, timeout=180)
        if r.status_code == 200:
            open(f"{out}/{name}.json", "w", encoding="utf-8").write(r.text)
            print(name, len(r.json()["results"]["bindings"])); return
        print(name, r.status_code, r.text[:300]); time.sleep(10*(i+1))
run(Q1, "eventi_milano")
