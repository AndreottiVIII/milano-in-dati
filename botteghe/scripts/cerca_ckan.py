"""Cerca nel CKAN del Comune di Milano dataset su attività storiche/botteghe/negozi storici.
Uso: python -I -X utf8 cerca_ckan.py <cartella raw assoluta>"""
import sys, json, urllib.request, urllib.parse, os, time
raw = sys.argv[1]
os.makedirs(raw + "/comune", exist_ok=True)
tutti = {}
for q in ["storiche", "storici", "botteghe", "negozi storici", "locali storici", "attività storiche", "tradizione", "insegne", "artigian", "commercio", "negozi", "NLS"]:
    url = "https://dati.comune.milano.it/api/3/action/package_search?" + urllib.parse.urlencode({"q": q, "rows": 100})
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0"}), timeout=60))["result"]
    print(q, d["count"])
    for p in d["results"]:
        tutti[p["name"]] = {"id": p["id"], "title": p["title"], "modified": p["metadata_modified"], "license": p.get("license_id"), "n_res": len(p["resources"]), "notes": (p.get("notes") or "")[:200]}
    time.sleep(1)
json.dump(tutti, open(raw + "/comune/ricerca_ckan.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
import re
for k, v in tutti.items():
    if re.search(r"stori|bottega|bottegh|tradizion|negozi|commerc|artigian|esercizi", v["title"] + v["notes"], re.I):
        print(k, "|", v["title"], "|", v["modified"][:10], "|", v["license"])
