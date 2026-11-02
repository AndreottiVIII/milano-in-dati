"""Cerca nei cataloghi aperti (Socrata di Regione Lombardia, CKAN del Comune) dataset su medici, pediatri, farmacie.
Uso: python -I -X utf8 cerca.py <cartella medici-farmacie>   -> scrive raw/ricerca_cataloghi.json
"""
import sys, os, json, time, requests
base = sys.argv[1]
UA = {"User-Agent": "milano-in-dati-ricerca/1.0 (dati aperti; contatto: davide.caniatti@gmail.com)"}
out = {}
for q in ["medici di medicina generale", "pediatri", "pediatra libera scelta", "farmacie", "ambiti carenti", "medici di base", "assistiti", "guardia medica", "massimale"]:
    try:
        r = requests.get("https://www.dati.lombardia.it/api/catalog/v1", params={"q": q, "limit": 25}, headers=UA, timeout=60)
        out["lombardia:" + q] = [{"id": x["resource"]["id"], "name": x["resource"]["name"], "type": x["resource"].get("type"), "updated": x["resource"].get("updatedAt"), "desc": (x["resource"].get("description") or "")[:200], "license": x["metadata"].get("license")} for x in r.json().get("results", [])]
    except Exception as e:
        out["lombardia:" + q] = str(e)
    time.sleep(1)
    try:
        r = requests.get("https://dati.comune.milano.it/api/3/action/package_search", params={"q": q, "rows": 25}, headers=UA, timeout=60)
        out["comune:" + q] = [{"id": x["name"], "title": x["title"], "mod": x.get("metadata_modified")} for x in r.json()["result"]["results"]]
    except Exception as e:
        out["comune:" + q] = str(e)
    time.sleep(1)
json.dump(out, open(os.path.join(base, "raw", "ricerca_cataloghi.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
for k, v in out.items():
    print("==", k)
    if isinstance(v, str): print("  ERRORE", v); continue
    for x in v: print("  ", x["id"], "|", x.get("name") or x.get("title"), "|", x.get("updated") or x.get("mod"))
