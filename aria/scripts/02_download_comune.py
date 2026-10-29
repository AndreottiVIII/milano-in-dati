import requests, json, sys, time, os, re
H={"User-Agent":"milano-in-dati/1.0 (research; davide.caniatti@gmail.com)"}
meta=json.load(open(sys.argv[1],encoding="utf-8"))
outdir=sys.argv[2]
os.makedirs(outdir,exist_ok=True)
rows=[]
for n,p in sorted(meta.items()):
    t=p["title"]
    if not (re.search(r"qualit.\s+aria",t) and ("Rilevazione" in t or "Report" in t) or n.startswith("ds484") or n.startswith("ds573")):
        continue
    for r in p["resources"]:
        fmt=r["format"].upper()
        if fmt not in ("CSV","GEOJSON","SHP") : continue
        fn=r["url"].split("/")[-1]
        path=os.path.join(outdir,fn)
        rows.append((n,t,fmt,r["url"],fn,r.get("last_modified"),r.get("size"),p.get("license_id"),p.get("metadata_modified")))
        if os.path.exists(path) and os.path.getsize(path)>0: continue
        for a in range(4):
            try:
                resp=requests.get(r["url"],headers=H,timeout=180)
                if resp.status_code==429:
                    time.sleep(30*(a+1)); continue
                resp.raise_for_status()
                open(path,"wb").write(resp.content); print("ok",fn,len(resp.content),flush=True); break
            except Exception as e:
                print("err",fn,e,flush=True); time.sleep(5*(a+1))
        time.sleep(1.5)
json.dump(rows,open(os.path.join(outdir,"_manifest.json"),"w"),indent=1)
print("done")
