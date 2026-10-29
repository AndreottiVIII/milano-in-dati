import sys, json, time, requests
out = sys.argv[1]
UA = {"User-Agent": "milano-in-dati/1.0 (davide.caniatti@gmail.com; research on political violence in Milan)", "Accept": "application/sparql-results+json"}
def run(q, name):
    for i in range(4):
        try:
            r = requests.post("https://query.wikidata.org/sparql", data={"query": q}, headers=UA, timeout=200)
        except Exception as e:
            print(name, "EXC", e); time.sleep(10); continue
        if r.status_code == 200:
            open(f"{out}/{name}.json", "w", encoding="utf-8").write(r.text)
            print(name, len(r.json()["results"]["bindings"]), flush=True); return
        print(name, r.status_code, r.text[:200], flush=True); time.sleep(15*(i+1))
# A: events with a date >=1900 located in Milan (P276 or P131 -> Milan or its subdivisions), any class
QA = """
SELECT ?item ?itemLabel ?cls ?clsLabel ?date ?coord ?deaths ?inj ?itwiki ?enwiki WHERE {
  { ?item wdt:P276 wd:Q490 } UNION { ?item wdt:P131 wd:Q490 }
  ?item wdt:P31 ?cls .
  ?item wdt:P585|wdt:P580 ?date . FILTER(?date >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
  OPTIONAL { ?item wdt:P625 ?coord } OPTIONAL { ?item wdt:P1120 ?deaths } OPTIONAL { ?item wdt:P1339 ?inj }
  OPTIONAL { ?itwiki schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> }
  OPTIONAL { ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}"""
# B: items with a class among subclasses of terrorist attack / massacre / assassination etc, located (P17 Italy) and with location text Milan via P276 chain
QB = """
SELECT ?item ?itemLabel ?cls ?clsLabel ?date ?coord ?deaths ?inj ?itwiki ?enwiki ?place ?placeLabel WHERE {
  VALUES ?top { wd:Q2223653 wd:Q3199915 wd:Q356405 wd:Q217004 wd:Q168983 wd:Q132821 wd:Q49776 }
  ?cls wdt:P279* ?top . ?item wdt:P31 ?cls .
  ?item wdt:P17 wd:Q38 .
  ?item wdt:P585|wdt:P580 ?date . FILTER(?date >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
  OPTIONAL { ?item wdt:P276|wdt:P131 ?place }
  OPTIONAL { ?item wdt:P625 ?coord } OPTIONAL { ?item wdt:P1120 ?deaths } OPTIONAL { ?item wdt:P1339 ?inj }
  OPTIONAL { ?itwiki schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> }
  OPTIONAL { ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}"""
# C: people who died in Milan (place of death in Milan or subdivisions) with manner of death homicide / killed by
QC = """
SELECT ?item ?itemLabel ?dod ?dob ?manner ?mannerLabel ?cod ?codLabel ?pod ?podLabel ?itwiki ?enwiki WHERE {
  ?item wdt:P20 ?pod . ?pod wdt:P131* wd:Q490 .
  ?item wdt:P570 ?dod . FILTER(?dod >= "1900-01-01T00:00:00Z"^^xsd:dateTime)
  { ?item wdt:P1196 ?manner . FILTER(?manner IN (wd:Q149086, wd:Q3739104, wd:Q171558, wd:Q10737, wd:Q1139665)) }
  UNION { ?item wdt:P509 ?cod . FILTER(?cod IN (wd:Q31144, wd:Q132821, wd:Q3739104, wd:Q842338, wd:Q1139665)) }
  OPTIONAL { ?item wdt:P1196 ?manner } OPTIONAL { ?item wdt:P509 ?cod }
  OPTIONAL { ?itwiki schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> }
  OPTIONAL { ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  OPTIONAL { ?item wdt:P569 ?dob }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}"""
for n, q in [("A_eventi_milano", QA), ("B_attentati_italia", QB), ("C_morti_milano", QC)]:
    run(q, n)
