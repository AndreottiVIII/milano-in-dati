"""Ricerca CKAN su dati.comune.milano.it per parole chiave sulla poverta' educativa.
Uso: python -I -X utf8 search_comune.py <out.json>"""
import sys, json, urllib.request, urllib.parse
KW = ["nido","nidi","asili nido","prima infanzia","0-3","graduatoria","domande iscrizione","lista d'attesa","liste d'attesa","posti nido","ammissioni",
      "mensa","refezione","ristorazione scolastica","tempo pieno","tempo scuola","dispersione scolastica","abbandono scolastico","NEET","invalsi",
      "doposcuola","pre-scuola","educativ","minori","scuola infanzia iscrizioni","iscrizioni scuole","servizi educativi","0-6","sezioni primavera","bambini"]
out = sys.argv[1]
allp = {}
for k in KW:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=100&q=" + urllib.parse.quote(k)
    req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati-research/1.0"})
    d = json.load(urllib.request.urlopen(req, timeout=90))
    for p in d["result"]["results"]:
        allp.setdefault(p["name"], {"title": p["title"], "license": p.get("license_id"), "modified": p.get("metadata_modified"),
            "notes": (p.get("notes") or "")[:400], "res": [(r["format"], r.get("size"), r["url"]) for r in p["resources"]], "hits": []})["hits"].append(k)
    print(k, d["result"]["count"])
json.dump(allp, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(allp), "dataset")
