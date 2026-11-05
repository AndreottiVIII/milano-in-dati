"""Ricerca CKAN dati.comune.milano.it con piu' parole chiave. Uso: python -I -X utf8 cerca_comune.py <costo-vita assoluto>"""
import sys, os, json, urllib.request, urllib.parse, time, datetime
base = sys.argv[1]
H = {"User-Agent": "milano-in-dati/1.0"}
Q = ["prezzi al consumo", "indice NIC", "NIC", "prezzi medi", "rilevazione prezzi", "osservatorio prezzi", "tariffe", "prezzo", "inflazione",
     "costo della vita", "canoni di locazione", "affitti", "ATM biglietto", "tariffe trasporto", "retribuzioni", "stipendi", "carburante", "benzina", "energia elettrica", "pane", "caffe"]
found = {}
for q in Q:
    start = 0
    while True:
        u = "https://dati.comune.milano.it/api/3/action/package_search?rows=100&start=%d&q=%s" % (start, urllib.parse.quote(q))
        d = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60).read())["result"]
        for p in d["results"]:
            found[p["name"]] = p
        start += 100
        if start >= d["count"]: break
        time.sleep(1)
    print(q, d["count"], len(found)); time.sleep(1)
json.dump({"data_ricerca": str(datetime.date.today()), "pacchetti": found}, open(os.path.join(base, "raw", "comune_search_all.json"), "w", encoding="utf-8"), ensure_ascii=False)
