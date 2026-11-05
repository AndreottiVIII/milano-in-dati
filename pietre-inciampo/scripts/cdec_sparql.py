"""Scarica da lod.xdams.org/sparql (CDEC, 'Nomi della Shoah') cognome, nome, anno nascita, sesso, sopravvissuto delle persone dati.cdec.it/lod/shoah/person/N.
Finestre di 400 numeri (l'endpoint va in errore 500 oltre OFFSET 9000). SOLO per controllo incrociato dei nomi.
Uso: python -I -X utf8 cdec_sparql.py <out.csv>"""
import sys, json, csv, time, urllib.request, urllib.parse
UA = "milano-in-dati research (milano-in-dati)"
PROPS = {"cognome": "http://xmlns.com/foaf/0.1/familyName", "nome": "http://xmlns.com/foaf/0.1/firstName", "nascita": "http://dati.cdec.it/lod/bio-ext/dateOfBirth",
         "sesso": "http://xmlns.com/foaf/0.1/gender", "sopravvissuto": "http://dati.cdec.it/lod/bio-ext/shoahSurvivor"}
Q = ("SELECT ?s ?p ?o WHERE { ?s ?p ?o . VALUES ?p { %s } BIND(xsd:integer(STRAFTER(STR(?s),'/shoah/person/')) AS ?n) FILTER(STRSTARTS(STR(?s),'http://dati.cdec.it/lod/shoah/person/') && ?n >= %d && ?n < %d) }")
PFX = "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> "
inv = {v: k for k, v in PROPS.items()}


def run(q):
    for t in range(4):
        try:
            req = urllib.request.Request("http://lod.xdams.org/sparql", data=urllib.parse.urlencode({"query": PFX + q}).encode(), headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            return json.load(urllib.request.urlopen(req, timeout=240))["results"]["bindings"]
        except Exception as e:
            print("retry", e, flush=True); time.sleep(6)
    return None


data = {}
vals = " ".join(f"<{u}>" for u in PROPS.values())
step = 400; lo = 0; vuoti = 0
while lo < 30000 and vuoti < 8:
    b = run(Q % (vals, lo, lo + step))
    if b is None:
        print("fallita finestra", lo, flush=True); lo += step; continue
    for x in b:
        data.setdefault(x["s"]["value"], {}).setdefault(inv[x["p"]["value"]], x["o"]["value"])
    print(lo, len(b), len(data), flush=True)
    vuoti = vuoti + 1 if not b else 0
    lo += step; time.sleep(1.2)
with open(sys.argv[1], "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter=";"); w.writerow(["uri"] + list(PROPS))
    for s, v in data.items(): w.writerow([s] + [v.get(k, "") for k in PROPS])
