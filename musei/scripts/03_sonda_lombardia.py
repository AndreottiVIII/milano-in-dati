"""Cerca nel catalogo Socrata di Regione Lombardia dataset su musei e visitatori.
uso: python -I -X utf8 03_sonda_lombardia.py <cartella raw/ricerche assoluta>"""
import sys, json, time, urllib.request, urllib.parse, os
out = sys.argv[1]
UA = {"User-Agent": "milano-in-dati research (musei fase 1)"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as f:
        return json.load(f)
lom = {}
for q in ["musei", "visitatori musei", "musei riconosciuti", "museo", "istituti culturali"]:
    d = get("https://dati.lombardia.it/api/catalog/v1?" + urllib.parse.urlencode({"q": q, "limit": 50, "only": "datasets"}))
    for r in d["results"]:
        m = r["resource"]
        lom[m["id"]] = {"name": m["name"], "updated": (m.get("updatedAt") or "")[:10], "desc": (m.get("description") or "")[:300]}
    print("LOM", q, d.get("resultSetSize")); time.sleep(2)
json.dump(lom, open(os.path.join(out, "lombardia_musei.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in sorted(lom.items(), key=lambda x: x[1]["name"]):
    print(k, "|", v["name"], "|", v["updated"])
