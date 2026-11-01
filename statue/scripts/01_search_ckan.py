"""Ricerca CKAN su dati.comune.milano.it. Uso: python -I -X utf8 01_search_ckan.py <out.json>"""
import sys, json, urllib.request, urllib.parse, time
KW = ["monumenti","monumento","statue","statua","opere d'arte","arte pubblica","lapidi","lapide","targhe","patrimonio artistico",
      "sculture","scultura","memoriale","fontane","busto","cippi","arredo urbano","street art","murales","opere pubbliche d'arte","patrimonio culturale","beni culturali","ricordo","caduti"]
out = sys.argv[1]
allp = {}
for k in KW:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=200&q=" + urllib.parse.quote(k)
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/0.3 (research)"}), timeout=90))
    n = d["result"]["count"]
    for p in d["result"]["results"]:
        allp.setdefault(p["name"], {"title": p["title"], "license": p.get("license_id"), "modified": p.get("metadata_modified"), "notes": (p.get("notes") or "")[:400],
            "res": [(r["format"], r.get("size"), r["url"]) for r in p["resources"]], "hits": []})["hits"].append(k)
    print(k, n)
    time.sleep(1)
json.dump(allp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(allp), "dataset")
