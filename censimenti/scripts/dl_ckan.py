import sys, os, json, time, re, requests
root=sys.argv[1]
UA={"User-Agent":"Mozilla/5.0 (research; davide.caniatti@gmail.com)"}
sel=json.load(open(root+"/raw/comune_ckan/pacchetti_censimento.json",encoding="utf8"))
# extra storici
extra=["ds1494-popolazione-calcolata-nel-comune-di-milano-dal-1880","ds1495-popolazione-censimenti-storici-nati-vivi-residenti-nel-comune-di-milano-dal-1880","ds73-popolazione-residenti-suddivisi-per-genere","ds2918-tassi-natalita-mortalita-dal-1880"]
for n in extra:
    if n not in sel:
        r=requests.get("https://dati.comune.milano.it/api/3/action/package_show",params={"id":n},headers=UA,timeout=60).json()["result"]; sel[n]=r; time.sleep(1)
log=[]
for n,p in sorted(sel.items()):
    d=os.path.join(root,"raw","comune_ckan",n[:60]); os.makedirs(d,exist_ok=True)
    for i,r in enumerate(p["resources"]):
        url=r["url"]; fmt=(r.get("format") or "").lower()
        name=re.sub(r"[^\w.\-]","_",url.rsplit("/",1)[-1])[:100] or f"res{i}.{fmt}"
        fn=os.path.join(d,f"{i:02d}_{name}")
        ok=os.path.exists(fn) and os.path.getsize(fn)>0
        if not ok:
            for att in range(4):
                try:
                    rr=requests.get(url,headers=UA,timeout=180)
                    if rr.status_code==429: time.sleep(60); continue
                    rr.raise_for_status(); open(fn,"wb").write(rr.content); ok=True; break
                except Exception as e:
                    print("err",url,e,flush=True); time.sleep(8*(att+1))
            time.sleep(0.8)
        print("ok" if ok else "FAIL",fn,os.path.getsize(fn) if ok else 0,flush=True)
print("DONE")
