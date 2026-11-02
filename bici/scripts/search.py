"""Ricerca CKAN su dati.comune.milano.it. Uso: python -I -X utf8 search.py <out.json>"""
import sys, json, urllib.request, urllib.parse
KW = ["bikemi","bike sharing","bike","contabici","conteggio bici","conta bici","piste ciclabili","ciclabil","ciclabile","sharing mobility","sharing","monopattini","biciclette","bicicletta","ciclisti","contatori","flussi","mobilita ciclistica","bici","cycle","vehicle counter","traffico"]
out = sys.argv[1]
allp = {}
for k in KW:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=200&q=" + urllib.parse.quote(k)
    d = json.load(urllib.request.urlopen(url, timeout=90))
    n = d["result"]["count"]
    for p in d["result"]["results"]:
        allp.setdefault(p["name"], {"title": p["title"], "license": p.get("license_id"), "modified": p.get("metadata_modified"), "notes": (p.get("notes") or "")[:300], "res": [(r["format"], r.get("size"), r["url"], r.get("last_modified")) for r in p["resources"]], "hits": []})["hits"].append(k)
    print(k, n)
json.dump(allp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(allp), "dataset")
