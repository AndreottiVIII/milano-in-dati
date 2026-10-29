import requests, json, sys, time
H={"User-Agent":"milano-in-dati/1.0 (research; davide.caniatti@gmail.com)"}
out=sys.argv[1]
res={}
for q in ["Rilevazione qualità aria","qualità aria","Stazioni monitoraggio inquinanti","inquinanti aria"]:
    start=0
    while True:
        r=requests.get("https://dati.comune.milano.it/api/3/action/package_search",params={"q":q,"rows":100,"start":start},headers=H,timeout=60)
        r.raise_for_status()
        j=r.json()["result"]
        for p in j["results"]:
            res[p["name"]]=p
        start+=100
        if start>=j["count"]: break
        time.sleep(1)
json.dump(res,open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for n,p in sorted(res.items()):
    print(n,"|",p["title"],"|",len(p["resources"]),"|",p.get("license_id"))
