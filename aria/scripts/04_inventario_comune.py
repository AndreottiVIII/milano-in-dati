import pandas as pd, glob, sys, os, re
src=sys.argv[1]; out=sys.argv[2]
fs=sorted(glob.glob(os.path.join(src,"*datoariagiornostazione*.csv")))
parts=[]
for f in fs:
    d=pd.read_csv(f,sep=";",dtype=str); d["file"]=os.path.basename(f); parts.append(d)
d=pd.concat(parts,ignore_index=True)
print("righe",len(d),"colonne",list(d.columns))
raw=d.valore.copy()
d["v"]=pd.to_numeric(d.valore.str.replace(",","."),errors="coerce")
print("valori non numerici non vuoti:",d[d.v.isna()&d.valore.notna()].valore.unique()[:20])
print("virgola decimale:",d.valore.str.contains(",",na=False).sum(),"negativi:",(d.v<0).sum(),"zeri:",(d.v==0).sum())
print("duplicati (staz,data,inq):",d.duplicated(["stazione_id","data","inquinante"]).sum())
d["data"]=pd.to_datetime(d.data)
d["anno"]=d.data.dt.year
rows=[]
for (s,i),g in d.groupby(["stazione_id","inquinante"]):
    gv=g[g.v.notna()].sort_values("data")
    if len(gv)==0:
        rows.append(dict(stazione_id=s,inquinante=i,righe=len(g),validi=0)); continue
    gaps=gv.data.diff().dt.days
    rows.append(dict(stazione_id=s,inquinante=i,righe=len(g),validi=len(gv),vuoti=len(g)-len(gv),
        prima=gv.data.min().date(),ultima=gv.data.max().date(),
        anni_con_dati=",".join(map(str,sorted(gv.anno.unique()))),
        max_buco_giorni=int(gaps.max()) if gaps.notna().any() else 0,
        max_val=gv.v.max(),min_val=gv.v.min()))
inv=pd.DataFrame(rows); inv["stazione_id"]=inv.stazione_id.astype(int); inv=inv.sort_values(["stazione_id","inquinante"])
inv.to_csv(out,index=False,encoding="utf-8"); print(inv.to_string())
# copertura annuale: validi per stazione/inquinante/anno
cov=d[d.v.notna()].groupby(["stazione_id","inquinante","anno"]).size().unstack(fill_value=0)
cov.to_csv(out.replace(".csv","_per_anno.csv"),encoding="utf-8")
# date per anno: primo e ultimo giorno presenti nel file
print(d.groupby("anno").data.agg(["min","max","nunique"]))
