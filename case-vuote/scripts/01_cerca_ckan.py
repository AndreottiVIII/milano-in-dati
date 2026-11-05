"""Cerca nel catalogo CKAN del Comune di Milano dataset su abitazioni/alloggi non occupati.
Uso: python -I -X utf8 01_cerca_ckan.py <file_output.json>"""
import sys, json, urllib.request, urllib.parse, time
out = sys.argv[1]
qs = ["abitazioni", "alloggi", "case vuote", "abitazioni non occupate", "alloggi vuoti", "seconde case", "patrimonio edilizio", "abitazioni occupate residenti", "unita immobiliari", "catasto", "TARI utenze domestiche"]
res = {}
for q in qs:
    u = "https://dati.comune.milano.it/api/3/action/package_search?" + urllib.parse.urlencode({"q": q, "rows": 40})
    req = urllib.request.Request(u, headers={"User-Agent": "milano-in-dati research"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    for p in d["result"]["results"]:
        res[p["name"]] = {"title": p["title"], "modified": p.get("metadata_modified"), "license": p.get("license_id"), "notes": (p.get("notes") or "")[:300], "q": q}
    print("==", q, d["result"]["count"])
    time.sleep(2)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in sorted(res.items()):
    print(k, "|", v["title"], "|", (v["modified"] or "")[:10])
