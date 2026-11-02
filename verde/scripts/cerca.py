"""Cerca nel catalogo CKAN del Comune i dataset sul verde (nomi e date). Uso: python -I -X utf8 cerca.py <raw_dir>"""
import sys, os, json, urllib.request, urllib.parse
raw = sys.argv[1]
os.makedirs(raw, exist_ok=True)
out = {}
for q in ["verde", "parchi", "giardini", "aree verdi", "verde pubblico", "aree gioco", "aree cani", "orti", "bosco", "forestazione", "spazi verdi", "verde urbano", "ds89"]:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=100&q=" + urllib.parse.quote(q)
    d = json.load(urllib.request.urlopen(url, timeout=60))["result"]["results"]
    for x in d:
        out[x["name"]] = {"title": x["title"], "modified": x.get("metadata_modified"), "license": x.get("license_id"),
                          "res": [[r["format"], r.get("size"), r["url"], r.get("last_modified")] for r in x["resources"]]}
json.dump(out, open(os.path.join(raw, "search_verde.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in sorted(out.items()):
    print(k, "|", v["title"], "|", (v["modified"] or "")[:10])
