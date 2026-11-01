import sys, json, time, urllib.request, urllib.parse
out = sys.argv[1]
res = {}
for q in ["reati","sicurezza","polizia locale","incidenti","denunce","delitti","criminalità","furti","interventi polizia","sanzioni"]:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=50&q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (milano-in-dati research)"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=60))
        res[q] = [(p["name"], p["title"], p.get("metadata_modified")) for p in d["result"]["results"]]
        print(q, d["result"]["count"])
    except Exception as e:
        res[q] = str(e); print(q, "ERR", e)
    time.sleep(2)
json.dump(res, open(out,"w",encoding="utf8"), ensure_ascii=False, indent=1)
for q,v in res.items():
    print("==",q)
    if isinstance(v,list):
        for x in v[:15]: print("  ",x[0],"|",x[1][:90])
