"""Ricerca CKAN su dati.comune.milano.it e Socrata su dati.lombardia.it.
Uso: python -I -X utf8 search.py <cartella raw assoluta>"""
import sys, json, urllib.request, urllib.parse, os, time
raw = sys.argv[1]
KW = ["cani","cane","anagrafe canina","animali","razze","aree cani","animali d'affezione","gatti","pet","microchip","canile","sgambatura","zoofilia","veterinari","tutela animali","fauna"]
UA = {"User-Agent": "milano-in-dati/1.0 (ricerca open data, uso personale)"}
def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90))
allp = {}
for k in KW:
    d = get("https://dati.comune.milano.it/api/3/action/package_search?rows=200&q=" + urllib.parse.quote(k))
    for p in d["result"]["results"]:
        e = allp.setdefault(p["name"], {"title": p["title"], "license": p.get("license_id"), "modified": p.get("metadata_modified"), "notes": (p.get("notes") or "")[:300], "res": [(r["format"], r.get("size"), r["url"]) for r in p["resources"]], "hits": []})
        e["hits"].append(k)
    print("comune", k, d["result"]["count"]); time.sleep(1)
json.dump(allp, open(os.path.join(raw, "search_comune.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(allp), "dataset comune")
# Regione Lombardia: catalogo Socrata
lomb = {}
for k in ["cani","anagrafe canina","animali d'affezione","animali","randagismo","canile","microchip","gatti","razze","veterinari","anagrafe regionale animali","animali da compagnia","cuccioli","canina","anagrafe animali"]:
    try:
        d = get("https://www.dati.lombardia.it/api/catalog/v1?limit=100&q=" + urllib.parse.quote(k))
    except Exception as ex:
        print("lomb err", k, ex); continue
    for r in d["results"]:
        res = r["resource"]
        e = lomb.setdefault(res["id"], {"name": res["name"], "type": res.get("type"), "updated": res.get("updatedAt"), "desc": (res.get("description") or "")[:300], "link": r["link"], "hits": []})
        e["hits"].append(k)
    print("lomb", k, d.get("resultSetSize")); time.sleep(1)
json.dump(lomb, open(os.path.join(raw, "search_lombardia.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(lomb), "dataset lombardia")
