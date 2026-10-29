import sys, json, time, requests, os
qfile, outdir = sys.argv[1:3]
os.makedirs(outdir, exist_ok=True)
qids = [x.strip() for x in open(qfile) if x.strip().startswith('Q')]
UA = {"User-Agent": "milano-in-dati/0.1 (davide.caniatti@gmail.com; street-name research)", "Accept":"application/sparql-results+json"}
B = 150
TEMPL = """SELECT ?item ?itemLabel ?itemDescription
 (GROUP_CONCAT(DISTINCT STR(?p31); separator="|") AS ?p31s)
 (GROUP_CONCAT(DISTINCT ?p31L; separator="|") AS ?p31Ls)
 (GROUP_CONCAT(DISTINCT STR(?sex); separator="|") AS ?sexs)
 (GROUP_CONCAT(DISTINCT ?occL; separator="|") AS ?occs)
 (MIN(YEAR(?b)) AS ?birth) (MIN(YEAR(?d)) AS ?death)
 (GROUP_CONCAT(DISTINCT STR(?cit); separator="|") AS ?cits)
WHERE {
 VALUES ?item { %s }
 OPTIONAL { ?item wdt:P31 ?p31 . ?p31 rdfs:label ?p31L FILTER(lang(?p31L)="en") }
 OPTIONAL { ?item wdt:P21 ?sex }
 OPTIONAL { ?item wdt:P106 ?occ . ?occ rdfs:label ?occL FILTER(lang(?occL)="it") }
 OPTIONAL { ?item wdt:P569 ?b }
 OPTIONAL { ?item wdt:P570 ?d }
 OPTIONAL { ?item wdt:P27 ?cit }
 SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
} GROUP BY ?item ?itemLabel ?itemDescription"""
for i in range(0, len(qids), B):
    fn = f"{outdir}/batch_{i//B:03d}.json"
    if os.path.exists(fn): continue
    vals = ' '.join('wd:'+q for q in qids[i:i+B])
    for att in range(5):
        try:
            r = requests.post("https://query.wikidata.org/sparql", data={"query": TEMPL % vals}, headers=UA, timeout=180)
            if r.status_code == 200:
                open(fn,'wb').write(r.content); print(fn, len(r.content), flush=True); break
            print('status', r.status_code, r.text[:200], flush=True)
        except Exception as e:
            print('err', e, flush=True)
        time.sleep(30*(att+1))
    else:
        print('FAILED batch', i); sys.exit(1)
    time.sleep(5)
