import sys, json, urllib.request, urllib.parse
out = sys.argv[1]
kw = ["incidenti stradali","incidenti","sinistri","localizzazione incidenti","polizia locale","incidente","infortunistica","georeferenziati incidenti","sicurezza stradale","zone 30","velocità"]
base = "https://dati.comune.milano.it/api/3/action/package_search?rows=100&q="
res = {}
for k in kw:
    try:
        req = urllib.request.Request(base+urllib.parse.quote(k), headers={"User-Agent":"milano-in-dati/1.0"})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        for p in d["result"]["results"]:
            res[p["name"]] = {"title":p.get("title"),"notes":(p.get("notes") or "")[:300],"license":p.get("license_id"),"modified":p.get("metadata_modified"),"res":[(r.get("format"),r.get("url")) for r in p.get("resources",[])]}
        print(k, d["result"]["count"])
    except Exception as e:
        print(k, "ERR", e)
json.dump(res, open(out,"w",encoding="utf8"), ensure_ascii=False, indent=1)
print(len(res))
