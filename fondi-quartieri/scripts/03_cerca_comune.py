"""Ricerca CKAN su dati.comune.milano.it per il filone fondi-quartieri. Uso: python -I -X utf8 03_cerca_comune.py <out.json>"""
import sys, json, urllib.request, urllib.parse, time
KW = ["PNRR","PINQuA","qualità dell'abitare","periferie","bando periferie","riqualificazione","rigenerazione urbana","piano triennale opere pubbliche","opere pubbliche","programma triennale lavori pubblici","investimenti","cantieri","lavori pubblici","edilizia residenziale pubblica","quartieri","San Siro","Lorenteggio","Gratosoglio","Corvetto","Quarto Oggiaro","Niguarda","fondi europei","PON Metro","finanziamenti","progetti finanziati","contratti di quartiere","manutenzione straordinaria","bilancio investimenti","spesa in conto capitale","edilizia abitativa"]
out = sys.argv[1]
allp = {}
for k in KW:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=200&q=" + urllib.parse.quote(k)
    req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0 (ricerca open data)"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=90))
    except Exception as e:
        print(k, "ERRORE", e); continue
    n = d["result"]["count"]
    for p in d["result"]["results"]:
        allp.setdefault(p["name"], {"title": p["title"], "license": p.get("license_id"), "modified": p.get("metadata_modified"), "notes": (p.get("notes") or "")[:500], "res": [(r["format"], r.get("size"), r["url"]) for r in p["resources"]], "hits": []})["hits"].append(k)
    print(k, n)
    time.sleep(0.5)
json.dump(allp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(allp), "dataset")
