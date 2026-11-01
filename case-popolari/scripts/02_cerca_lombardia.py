"""Ricerca nel catalogo Socrata di dati.lombardia.it. Uso: python -I -X utf8 02_cerca_lombardia.py <out.json>"""
import sys, json, urllib.request, urllib.parse, time, re
KW = ["ALER","alloggi SAP","servizi abitativi pubblici","patrimonio abitativo","edilizia residenziale pubblica","alloggi","piattaforma servizi abitativi","unità abitative","sfitti","case popolari","abitativi","ERP","edilizia sociale","offerta abitativa","assegnazione alloggi","MM spa","condizione abitativa","unità immobiliari","bandi servizi abitativi","canone sociale","servizi abitativi","Osservatorio regionale condizione abitativa","unità di offerta abitativa","domande alloggi","graduatoria","patrimonio immobiliare","SAP","SAT","sfratti","fondo sostegno affitto","contributo affitto"]
seen = {}
for k in KW:
    url = "https://dati.lombardia.it/api/catalog/v1?only=dataset&limit=100&q=" + urllib.parse.quote(k)
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0 (ricerca open data)"}), timeout=60))
    except Exception as e:
        print(k, "ERR", e); continue
    print("##", k, d.get("resultSetSize"))
    for r in d["results"]:
        res = r["resource"]
        seen.setdefault(res["id"], {"name": res["name"], "desc": (res.get("description") or "")[:400], "updated": res.get("data_updated_at"), "license": r["metadata"].get("license") if "metadata" in r else None, "hits": []})["hits"].append(k)
    time.sleep(0.4)
json.dump(seen, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
pat = re.compile(r"aler|abitativ|alloggi|edilizia resid|\berp\b|\bSAP\b|case popolari|sfitt|housing|locazion|canone|affitt", re.I)
for i, v in seen.items():
    if pat.search(v["name"] + " " + v["desc"]):
        print(i, "|", v["name"][:110], "|", (v["updated"] or "")[:10], "|", v["hits"][:3])
