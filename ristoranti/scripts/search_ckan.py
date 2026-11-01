"""Ricerca CKAN su dati.comune.milano.it per esercizi pubblici. Uso: python -I -X utf8 search_ckan.py <out.json>"""
import sys, json, urllib.request, urllib.parse, time
KW = ["esercizi pubblici","pubblici esercizi","somministrazione","somministrazione alimenti bevande","ristoranti","ristorazione","bar","dehors","commercio","SUAP","attività commerciali","esercizi commerciali","licenze","locali","pubblico spettacolo","plateatici","occupazione suolo pubblico","pizzerie","negozi","commercio su aree pubbliche","pasti","mense","food","movida","insegne","attività economiche","unità locali","imprese","SCIA","autorizzazioni"]
out = sys.argv[1]
allp = {}
for k in KW:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=200&q=" + urllib.parse.quote(k)
    d = json.load(urllib.request.urlopen(url, timeout=90))
    n = d["result"]["count"]
    for p in d["result"]["results"]:
        allp.setdefault(p["name"], {"title": p["title"], "license": p.get("license_id"), "created": p.get("metadata_created"), "modified": p.get("metadata_modified"), "frequency": next((e["value"] for e in p.get("extras", []) if e["key"] == "frequency"), None), "notes": (p.get("notes") or "")[:300], "res": [(r["format"], r.get("size"), r["url"], r.get("last_modified")) for r in p["resources"]], "hits": []})["hits"].append(k)
    print(k, n)
    time.sleep(0.5)
json.dump(allp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(allp), "dataset")
