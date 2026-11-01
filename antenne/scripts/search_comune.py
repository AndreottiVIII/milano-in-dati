"""Cerca nel CKAN del Comune di Milano. Uso: python -I -X utf8 search_comune.py <out_json>"""
import sys, json, urllib.request, urllib.parse
out = sys.argv[1]
terms = ["antenne", "antenna", "stazioni radio base", "radio base", "piano antenne", "telefonia", "impianti telecomunicazione", "elettromagnetic", "campi elettromagnetici", "radiotelevisivi", "5G", "ARPA", "inquinamento elettromagnetico", "telecomunicazioni", "SRB", "wifi", "banda larga", "fibra"]
res = {}
for t in terms:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=100&q=" + urllib.parse.quote(t)
    req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/antenne"})
    try:
        j = json.load(urllib.request.urlopen(req, timeout=60))["result"]
    except Exception as e:
        print(t, "ERRORE", e); continue
    print(t, j["count"])
    for r in j["results"]:
        res.setdefault(r["name"], {"id": r["name"], "title": r["title"], "notes": (r.get("notes") or "")[:300], "mod": r.get("metadata_modified"), "license": r.get("license_id"), "terms": []})["terms"].append(t)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
