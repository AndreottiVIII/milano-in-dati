import sys, json, time, urllib.request, urllib.parse
out = sys.argv[1]; res = {}
for q in ["pendolari","popolazione presente","city users","spostamenti casa lavoro","pronto soccorso aggressioni","vigili","polizia locale interventi","furti biciclette","violenza donne","stranieri presenti"]:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=30&q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (milano-in-dati research)"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=60))
        res[q] = [(p["name"], p["title"], p.get("metadata_modified")) for p in d["result"]["results"]]
    except Exception as e:
        res[q] = str(e)
    time.sleep(2)
json.dump(res, open(out,"w",encoding="utf8"), ensure_ascii=False, indent=1)
for q,v in res.items():
    print("==",q)
    if isinstance(v,list):
        for x in v[:10]: print("  ",x[0][:60],"|",x[1][:100])
