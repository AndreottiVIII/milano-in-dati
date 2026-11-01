"""Passo 1: elenco degli elementi Wikidata situati (P131 transitivo) nel Comune di Milano (Q490) con coordinate.
Uso: python -I -X utf8 01_wikidata_luoghi.py <cartella luoghi-cercati assoluta>
Scrive raw/wikidata_items_classi.json (righe item/coord/classe/etichette) e raw/wikidata_classi.json.
Fonte: query.wikidata.org (SPARQL), dati CC0."""
import sys, os, json, time, requests
UA="MilanoInDati/1.0 (https://github.com/AndreottiVIII/milano-in-dati)"
base=sys.argv[1]; raw=os.path.join(base,"raw")
def sparql(q):
    for i in range(5):
        r=requests.post("https://query.wikidata.org/sparql",data={"query":q},headers={"User-Agent":UA,"Accept":"application/sparql-results+json"},timeout=170)
        if r.ok: return r.json()["results"]["bindings"]
        print("retry",r.status_code,r.text[:200]); time.sleep(10*(i+1))
    raise SystemExit("sparql fallita")
q="""SELECT ?item ?itemLabel_it ?itemLabel_en ?coord ?cls ?clsLabel_en ?clsLabel_it WHERE {
  ?item wdt:P131* wd:Q490 . ?item wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P31 ?cls . OPTIONAL { ?cls rdfs:label ?clsLabel_en FILTER(lang(?clsLabel_en)="en") } OPTIONAL { ?cls rdfs:label ?clsLabel_it FILTER(lang(?clsLabel_it)="it") } }
  OPTIONAL { ?item rdfs:label ?itemLabel_it FILTER(lang(?itemLabel_it)="it") }
  OPTIONAL { ?item rdfs:label ?itemLabel_en FILTER(lang(?itemLabel_en)="en") }
}"""
rows=sparql(q)
out=[{k:v["value"] for k,v in b.items()} for b in rows]
json.dump({"scaricato":time.strftime("%Y-%m-%d"),"query":q,"righe":out},open(os.path.join(raw,"wikidata_items_classi.json"),"w",encoding="utf8"),ensure_ascii=False)
print(len(out),"righe;",len({o['item'] for o in out}),"elementi")
