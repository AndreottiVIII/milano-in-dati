"""Cerca nel catalogo Socrata di dati.lombardia.it dataset su negozi/locali/botteghe storici.
Uso: python -I -X utf8 cerca_lombardia.py <cartella raw assoluta>"""
import sys, json, urllib.request, urllib.parse, os, time
raw = sys.argv[1]
os.makedirs(raw + "/lombardia", exist_ok=True)
qs = ["negozi storici", "locali storici", "botteghe storiche", "botteghe artigiane", "attività storiche", "storici", "storica", "insegne storiche", "tradizione", "esercizi commerciali", "negozi", "commercio storico", "locali"]
tutti = {}
for q in qs:
    url = "https://www.dati.lombardia.it/api/catalog/v1?" + urllib.parse.urlencode({"q": q, "limit": 100})
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0"}), timeout=60))
    except Exception as e:
        print("ERR", q, e); continue
    for r in d.get("results", []):
        res = r["resource"]
        tutti[res["id"]] = {"id": res["id"], "name": res["name"], "desc": (res.get("description") or "")[:300], "updatedAt": res.get("updatedAt"), "createdAt": res.get("createdAt"), "type": res.get("type"), "licenza": r.get("metadata", {}).get("license") if isinstance(r.get("metadata"), dict) else None, "q": q}
    print(q, len(d.get("results", [])))
    time.sleep(1)
json.dump(tutti, open(raw + "/lombardia/catalogo_ricerca.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
import re
for i, v in tutti.items():
    if re.search(r"storic|bottegh|tradizion|insegn|negoz|local", v["name"], re.I):
        print(i, "|", v["name"], "|", v["updatedAt"], "|", v["desc"][:120])
