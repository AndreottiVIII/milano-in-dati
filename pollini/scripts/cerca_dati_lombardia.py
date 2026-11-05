"""Cerca pollini/aerobiologia nel catalogo di dati.lombardia.it (API catalogo Socrata) e salva le risposte.
Uso: python -I -X utf8 cerca_dati_lombardia.py <cartella di output assoluta>   (scrive ricerca_catalogo.json)
Il catalogo accetta anche ricerche che pescano dataset di altri portali Socrata (es. FVG): si tiene traccia del dominio."""
import json, sys, os, urllib.request, urllib.parse
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
res = {}
for q in ["pollini", "pollen", "aerobiologia", "aerobiologico", "spore", "polline", "ambrosia", "graminacee", "betulla", "allergeni"]:
    url = "https://www.dati.lombardia.it/api/catalog/v1?limit=50&q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    res[q] = [dict(id=r["resource"]["id"], nome=r["resource"]["name"], dominio=r["metadata"].get("domain"),
                   attribuzione=r["resource"].get("attribution"), aggiornato=r["resource"]["updatedAt"][:10])
              for r in d.get("results", [])]
    print(q, len(res[q]), [x["nome"] + " @" + x["dominio"] for x in res[q]])
json.dump(res, open(os.path.join(out, "ricerca_catalogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
