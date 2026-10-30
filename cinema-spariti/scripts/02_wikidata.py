import sys, os, time, json, requests
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "MilanoInDati/1.0 (davide.caniatti@gmail.com; progetto dati aperti)", "Accept": "application/sparql-results+json"}
Q = {
"cinema_milano": """
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?class ?classLabel ?inception ?dissolved ?coord ?address ?street ?streetLabel ?hn ?locLabel ?capacity ?article ?opening ?closed WHERE {
  ?item wdt:P31/wdt:P279* wd:Q41253 .
  ?item wdt:P131* wd:Q490 .
  ?item wdt:P31 ?class .
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P576 ?dissolved }
  OPTIONAL { ?item wdt:P1619 ?opening }
  OPTIONAL { ?item wdt:P3999 ?closed }
  OPTIONAL { ?item wdt:P625 ?coord }
  OPTIONAL { ?item wdt:P6375 ?address }
  OPTIONAL { ?item wdt:P669 ?street }
  OPTIONAL { ?item wdt:P670 ?hn }
  OPTIONAL { ?item wdt:P131 ?loc }
  OPTIONAL { ?item wdt:P1083 ?capacity }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}""",
"teatri_milano": """
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?class ?classLabel ?inception ?dissolved ?coord ?address ?streetLabel ?hn ?article WHERE {
  ?item wdt:P31/wdt:P279* wd:Q24354 .
  ?item wdt:P131* wd:Q490 .
  ?item wdt:P31 ?class .
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P576 ?dissolved }
  OPTIONAL { ?item wdt:P625 ?coord }
  OPTIONAL { ?item wdt:P6375 ?address }
  OPTIONAL { ?item wdt:P669 ?street }
  OPTIONAL { ?item wdt:P670 ?hn }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}""",
# anche oggetti che furono cinema (ex) con P31 diverso: ex cinema, edifici con 'cinema' nella descrizione
"ex_cinema_descrizione": """
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?classLabel ?inception ?dissolved ?coord ?article WHERE {
  ?item wdt:P131* wd:Q490 .
  ?item rdfs:label|schema:description ?t . FILTER(lang(?t) IN ("it","en") && REGEX(?t, "cinema|cinematograf|movie theat", "i"))
  OPTIONAL { ?item wdt:P31 ?class }
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P576 ?dissolved }
  OPTIONAL { ?item wdt:P625 ?coord }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}""",
}
for name, q in Q.items():
    fn = os.path.join(out, name + ".json")
    if os.path.exists(fn) and os.path.getsize(fn) > 100: print("skip", fn); continue
    for att in range(4):
        r = requests.get("https://query.wikidata.org/sparql", params={"query": q}, headers=UA, timeout=120)
        print(name, r.status_code, len(r.content))
        if r.status_code == 200:
            open(fn, "wb").write(r.content); break
        time.sleep(20 * (att + 1))
    time.sleep(5)
