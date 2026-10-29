import requests, pandas as pd, sys, os, time
H={"User-Agent":"milano-in-dati/1.0 (research; davide.caniatti@gmail.com)"}
S="https://www.dati.lombardia.it/resource/%s.csv"
st=pd.read_csv(sys.argv[1],dtype=str)
out=sys.argv[2]
sens=sorted(st[st.comune.str.upper()=="MILANO"].idsensore.unique())
print(len(sens),"sensori Milano",flush=True)
DS={"evzn-32bs":"fino1999","cthp-zqrr":"2000-2009","nr8w-tj77":"2010-2017","g2hp-ar79":"dal2018","nicp-bhqi":"corrente","ykhg-b8rs":"NRT"}
def get(url,params):
    for a in range(6):
        try:
            r=requests.get(url,params=params,headers=H,timeout=300)
            if r.status_code in (429,502,503,504):
                time.sleep(20*(a+1)); continue
            r.raise_for_status(); return r.content
        except Exception as e:
            print("err",e,flush=True); time.sleep(10*(a+1))
    raise RuntimeError("fail")
for did,lab in DS.items():
    d=os.path.join(out,f"{did}_{lab}"); os.makedirs(d,exist_ok=True)
    for s in sens:
        fn=os.path.join(d,f"sensore_{s}.csv")
        if os.path.exists(fn): continue
        parts=[]; off=0; first=True
        while True:
            c=get(S%did,{"$where":f"idsensore='{s}'","$order":"data","$limit":50000,"$offset":off})
            lines=c.decode("utf-8").splitlines()
            n=len(lines)-1
            if first: parts.append("\n".join(lines)); first=False
            elif n>0: parts.append("\n".join(lines[1:]))
            if n<50000: break
            off+=50000; time.sleep(0.5)
        open(fn+".tmp","w",encoding="utf-8").write("\n".join(parts)+"\n"); os.replace(fn+".tmp",fn)
        print(did,s,off+n,flush=True); time.sleep(0.5)
print("done",flush=True)
