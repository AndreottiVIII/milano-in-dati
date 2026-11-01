"""Cerca nel catalogo Socrata di dati.lombardia.it. Uso: python -I -X utf8 search_socrata.py <out_json>"""
import sys, json, urllib.request, urllib.parse
out = sys.argv[1]
terms = ["impianti", "telefonia", "CASTEL", "radiobase", "campi elettromagnetici", "elettromagnetic", "antenne", "radiotelevisivi", "telecomunicazione", "ARPA", "radiazioni", "stazioni radio base", "5G", "inquinamento elettromagnetico", "SRB", "emittenti"]
res = {}
for t in terms:
    url = "https://api.eu.socrata.com/api/catalog/v1?domains=www.dati.lombardia.it&limit=100&q=" + urllib.parse.quote(t)
    req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/antenne (ricerca open data)"})
    try:
        j = json.load(urllib.request.urlopen(req, timeout=60))
    except Exception as e:
        print(t, "ERRORE", e); continue
    for r in j.get("results", []):
        rs = r["resource"]
        res.setdefault(rs["id"], {"id": rs["id"], "name": rs["name"], "desc": (rs.get("description") or "")[:300], "updated": rs.get("data_updated_at"), "type": rs.get("type"), "terms": []})["terms"].append(t)
    print(t, len(j.get("results", [])))
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(res))
