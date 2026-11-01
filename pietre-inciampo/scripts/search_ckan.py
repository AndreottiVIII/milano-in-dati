"""Ricerca CKAN dati.comune.milano.it. Uso: python -I -X utf8 search_ckan.py <out.json>"""
import sys, json, urllib.request, urllib.parse
KW = ["pietre d'inciampo","pietre inciampo","stolpersteine","stolpersteine milano","deportati","deportazione","memoria","shoah","monumenti","lapidi"]
out = sys.argv[1]; allp = {}
for k in KW:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=100&q=" + urllib.parse.quote(k)
    d = json.load(urllib.request.urlopen(url, timeout=90))
    print(k, d["result"]["count"])
    for p in d["result"]["results"]:
        allp.setdefault(p["name"], {"title": p["title"], "license": p.get("license_id"), "modified": p.get("metadata_modified"), "notes": (p.get("notes") or "")[:300], "res": [(r["format"], r.get("size"), r["url"]) for r in p["resources"]], "hits": []})["hits"].append(k)
json.dump(allp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for n,p in allp.items(): print(n,"|",p["title"],"|",p["hits"])
