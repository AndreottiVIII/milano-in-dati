import sys, os, time, json, requests
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "MilanoInDati/1.0 (davide.caniatti@gmail.com; progetto dati aperti)", "Accept": "application/sparql-results+json"}
COLS = """?item ?itemLabel ?itemDescription ?classLabel ?inception ?dissolved ?coord ?address ?streetLabel ?hn ?locLabel ?article"""
OPT = """
  OPTIONAL { ?item wdt:P571 ?inception } OPTIONAL { ?item wdt:P576 ?dissolved }
  OPTIONAL { ?item wdt:P625 ?coord } OPTIONAL { ?item wdt:P6375 ?address }
  OPTIONAL { ?item wdt:P669 ?street } OPTIONAL { ?item wdt:P670 ?hn } OPTIONAL { ?item wdt:P131 ?loc }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }"""
Q = {
"a_cinema_inMilano_P131": "SELECT DISTINCT "+COLS+" WHERE { ?item wdt:P31 ?class . ?class wdt:P279* wd:Q41253 . ?item wdt:P131 wd:Q490 ."+OPT+"}",
"b_cinema_box": "SELECT DISTINCT "+COLS+""" WHERE { SERVICE wikibase:box { ?item wdt:P625 ?coord . bd:serviceParam wikibase:cornerSouthWest "Point(9.05 45.38)"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point(9.31 45.57)"^^geo:wktLiteral . }
  ?item wdt:P31 ?class . ?class wdt:P279* wd:Q41253 ."""+OPT.replace("OPTIONAL { ?item wdt:P625 ?coord } ","")+"}",
"c_teatri_box": "SELECT DISTINCT "+COLS+""" WHERE { SERVICE wikibase:box { ?item wdt:P625 ?coord . bd:serviceParam wikibase:cornerSouthWest "Point(9.05 45.38)"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point(9.31 45.57)"^^geo:wktLiteral . }
  ?item wdt:P31 ?class . ?class wdt:P279* wd:Q24354 ."""+OPT.replace("OPTIONAL { ?item wdt:P625 ?coord } ","")+"}",
}
for name, q in Q.items():
    fn = os.path.join(out, name + ".json")
    if os.path.exists(fn) and os.path.getsize(fn) > 100: print("skip", fn, flush=True); continue
    for att in range(4):
        t=time.time()
        try:
            r = requests.get("https://query.wikidata.org/sparql", params={"query": q}, headers=UA, timeout=70)
            print(name, r.status_code, len(r.content), round(time.time()-t), flush=True)
            if r.status_code == 200:
                open(fn, "wb").write(r.content); break
        except Exception as e: print(name, "err", e, flush=True)
        time.sleep(20 * (att + 1))
    time.sleep(5)
