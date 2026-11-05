"""Wikidata (CC0): statue, monumenti, memoriali, sculture, lapidi, arte pubblica a Milano.
Due ricerche: (A) P131* = Milano; (B) coordinate nel rettangolo di Milano. Uso: python -I -X utf8 03_wikidata_items.py <cartella_raw_wikidata>"""
import sys, os, time, json, requests
out = sys.argv[1]
UA = {"User-Agent": "milano-in-dati/0.3 (milano-in-dati; research on statues and monuments in Milan)", "Accept": "application/sparql-results+json"}
CLS = "wd:Q179700 wd:Q4989906 wd:Q5003624 wd:Q860861 wd:Q721747 wd:Q557141"
SEL = """SELECT ?item ?itemLabel ?itemDescription ?cls ?clsLabel ?coord ?inc ?depicts ?creator ?creatorLabel ?commem ?main ?loc ?locLabel WHERE {
  %s
  ?item wdt:P31/wdt:P279* ?cls . VALUES ?cls { %s }
  OPTIONAL { ?item wdt:P625 ?coord }
  OPTIONAL { ?item wdt:P571 ?inc }
  OPTIONAL { ?item wdt:P180 ?depicts }
  OPTIONAL { ?item wdt:P170 ?creator }
  OPTIONAL { ?item wdt:P547 ?commem }
  OPTIONAL { ?item wdt:P921 ?main }
  OPTIONAL { ?item wdt:P131 ?loc }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}"""
Q = {
 "A_p131": SEL % ("?item wdt:P131* wd:Q490 .", CLS),
 "B_box": SEL % ('SERVICE wikibase:box { ?item wdt:P625 ?c . bd:serviceParam wikibase:cornerSouthWest "Point(9.04 45.38)"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point(9.29 45.55)"^^geo:wktLiteral . }', CLS),
}
for name, q in Q.items():
    fn = os.path.join(out, name + ".json")
    for att in range(6):
        try:
            r = requests.post("https://query.wikidata.org/sparql", data={"query": q}, headers=UA, timeout=300)
            print(name, r.status_code, len(r.content))
            if r.status_code == 200:
                open(fn, "wb").write(r.content); break
            else:
                print(r.text[:300])
        except Exception as e:
            print("err", e)
        time.sleep(20 * (att + 1))
    time.sleep(5)
