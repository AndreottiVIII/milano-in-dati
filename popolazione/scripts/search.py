"""Ricerca CKAN su dati.comune.milano.it. Uso: python -I -X utf8 search.py <out.json>  (percorso assoluto)"""
import sys, json, urllib.request, urllib.parse, time
KW = ["residenti","cittadinanza","età","eta","NIL","iscrizioni","cancellazioni","immigrati","emigrati","trasferimenti","centenari","popolazione","stranieri","anagrafe","movimento migratorio","residenza","nati","morti","quartiere"]
out = sys.argv[1]
allp = {}
for k in KW:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=300&q=" + urllib.parse.quote(k)
    req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0 (ricerca open data)"})
    d = json.load(urllib.request.urlopen(req, timeout=90))
    n = d["result"]["count"]
    for p in d["result"]["results"]:
        allp.setdefault(p["name"], {"title": p["title"], "license": p.get("license_id"), "modified": p.get("metadata_modified"), "notes": (p.get("notes") or "")[:400], "res": [(r["format"], r.get("size"), r["url"], r.get("name")) for r in p["resources"]], "hits": []})["hits"].append(k)
    print(k, n, flush=True)
    time.sleep(1)
json.dump(allp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(allp), "dataset")
