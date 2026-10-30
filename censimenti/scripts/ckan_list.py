import sys, json, requests, time, re
root=sys.argv[1]
UA={"User-Agent":"Mozilla/5.0 (research; davide.caniatti@gmail.com)"}
seen={}
for q in ["censimento","censimenti","censimento storico","sezioni di censimento","popolazione legale","censimenti storici","aree di censimento","censuario","ISTAT censimento permanente","popolazione residente censimento"]:
    start=0
    while True:
        r=requests.get("https://dati.comune.milano.it/api/3/action/package_search",params={"q":q,"rows":100,"start":start},headers=UA,timeout=60).json()["result"]
        for p in r["results"]: seen[p["name"]]=p
        start+=100
        if start>=r["count"] or start>=300: break
        time.sleep(1)
    time.sleep(1)
sel={n:p for n,p in seen.items() if re.search(r"censim|censuar|legale|storic|ACE\b|sezion",p["title"],re.I)}
json.dump(sel,open(root+"/raw/comune_ckan/pacchetti.json","w",encoding="utf8"),ensure_ascii=False,indent=1)
for n,p in sorted(sel.items()):
    print(n,"|",p["title"],"|",p.get("license_id"),"|",[ (r["format"],r.get("size")) for r in p["resources"]])
print(len(sel))
