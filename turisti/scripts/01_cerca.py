"""Cerca nei cataloghi aperti (CKAN Comune di Milano, Socrata Regione Lombardia).
uso: python -I -X utf8 01_cerca.py <cartella raw/ricerche assoluta>
Pausa 2 s tra richieste. Salva i risultati in JSON e stampa un elenco."""
import sys, json, time, urllib.request, urllib.parse, os
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "milano-in-dati research (turisti fase 1)"}
def get(u):
    r = urllib.request.Request(u, headers=UA)
    with urllib.request.urlopen(r, timeout=60) as f:
        return json.load(f)
kw = ["turismo", "arrivi", "presenze", "nazionalità", "provenienza", "imposta di soggiorno",
      "turisti", "strutture ricettive", "flussi turistici", "movimento clienti", "paese di residenza"]
res = {}
for q in kw:
    u = "https://dati.comune.milano.it/api/3/action/package_search?" + urllib.parse.urlencode({"q": q, "rows": 100})
    d = get(u)["result"]
    for p in d["results"]:
        res[p["name"]] = {"title": p["title"], "modified": p.get("metadata_modified"), "license": p.get("license_id"),
                          "res": [(r["format"], r["url"]) for r in p["resources"]]}
    print("CKAN", q, d["count"])
    time.sleep(2)
json.dump(res, open(os.path.join(out, "ckan_milano_turismo.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in sorted(res.items()):
    print(k, "|", v["title"], "|", v["modified"][:10], "|", v["license"])
lom = {}
for q in ["turismo", "paese di provenienza", "flussi turistici", "movimento turistico", "arrivi presenze", "nazionalità turisti", "strutture ricettive"]:
    u = "https://dati.lombardia.it/api/catalog/v1?" + urllib.parse.urlencode({"q": q, "limit": 50, "only": "datasets"})
    d = get(u)
    for r in d["results"]:
        m = r["resource"]
        lom[m["id"]] = {"name": m["name"], "updated": (m.get("updatedAt") or "")[:10], "desc": (m.get("description") or "")[:300]}
    print("LOM", q, d.get("resultSetSize"))
    time.sleep(2)
json.dump(lom, open(os.path.join(out, "lombardia_turismo.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in sorted(lom.items(), key=lambda x: x[1]["name"]):
    print(k, "|", v["name"], "|", v["updated"])
