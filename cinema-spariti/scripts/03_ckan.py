import sys, os, time, json, requests
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "MilanoInDati/1.0 (davide.caniatti@gmail.com; progetto dati aperti)"}
base = "https://dati.comune.milano.it/api/3/action/"
names = ["ds157-cultura-ingressi-spettacoli-manifestazione-1995-2010","ds252-economia-locali-pubblico-spettacolo","ds59-economia-pubblici-esercizi-fuori-piano"]
# anche ricerche aggiuntive
extra = set()
for q in ["cinematografi","multisala","sale cultura","luoghi della cultura","teatro","biblioteche musei cinema"]:
    r = requests.get(base+"package_search", params={"q":q,"rows":30}, headers=UA, timeout=60).json()["result"]
    print(q, r["count"], [p["name"] for p in r["results"]])
    time.sleep(2)
meta = {}
for n in names:
    p = requests.get(base+"package_show", params={"id":n}, headers=UA, timeout=60).json()["result"]
    meta[n] = {"title":p["title"],"license":p.get("license_id"),"modified":p.get("metadata_modified"),"notes":p.get("notes","")[:600],"resources":[(r["name"],r["format"],r["url"]) for r in p["resources"]]}
    d = os.path.join(out, n); os.makedirs(d, exist_ok=True)
    for r in p["resources"]:
        fn = os.path.join(d, os.path.basename(r["url"].split("?")[0]) or "res")
        if os.path.exists(fn): continue
        if r["format"].upper() not in ("CSV","JSON","XLS","XLSX","GEOJSON"): continue
        rr = requests.get(r["url"], headers=UA, timeout=120)
        print(n, r["format"], rr.status_code, len(rr.content)); 
        if rr.status_code==200: open(fn,"wb").write(rr.content)
        time.sleep(2)
json.dump(meta, open(os.path.join(out,"_metadati.json"),"w",encoding="utf8"), ensure_ascii=False, indent=1)
