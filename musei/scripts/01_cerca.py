"""Cerca nel CKAN del Comune di Milano i dataset su musei e visitatori.
uso: python -I -X utf8 01_cerca.py <cartella raw/ricerche assoluta>
Pausa 2 s tra richieste."""
import sys, json, time, urllib.request, urllib.parse, os
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "milano-in-dati research (musei fase 1)"}
def get(u):
    r = urllib.request.Request(u, headers=UA)
    with urllib.request.urlopen(r, timeout=60) as f:
        return json.load(f)
kw = ["musei civici visitatori", "ingressi musei", "musei", "visitatori", "museo", "ingressi", "biglietti", "mostre", "cultura"]
res = {}
for q in kw:
    u = "https://dati.comune.milano.it/api/3/action/package_search?" + urllib.parse.urlencode({"q": q, "rows": 100})
    d = get(u)["result"]
    for p in d["results"]:
        res[p["name"]] = {"title": p["title"], "modified": p.get("metadata_modified"), "license": p.get("license_id"),
                          "res": [(r["format"], r["url"]) for r in p["resources"]]}
    print("CKAN", q, d["count"])
    time.sleep(2)
json.dump(res, open(os.path.join(out, "ckan_milano_musei.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in sorted(res.items()):
    print(k, "|", v["title"], "|", v["modified"][:10], "|", v["license"])
