import pandas as pd, numpy as np, glob, os, sys
out=sys.argv[1]
a=pd.read_pickle(os.path.join(out,"_arpa_all.pkl"))
inv=pd.read_csv(os.path.join(out,"inventario_arpa.csv"),dtype={"idsensore":str,"idstazione":str})
a=a.drop_duplicates(["idsensore","t"])  # sovrapposizioni tra archivi
a=a[(a.valore!=-9999)&a.valore.notna()]
a=a.merge(inv[["idsensore","tipo","idstazione"]],on="idsensore")
m_st={1:"549",2:"705",3:"539",4:"501",5:"547",6:"548",7:"528",8:"503",9:"502"}
m_in={"NO2":"Biossido di Azoto","SO2":"Biossido di Zolfo","O3":"Ozono","PM10":"PM10 (SM2005)","PM25":"Particelle sospese PM2.5","C6H6":"Benzene","CO_8h":"Monossido di Carbonio"}
c=pd.concat([pd.read_csv(f,sep=";",dtype=str) for f in sorted(glob.glob("raw/comune/*datoaria*.csv"))],ignore_index=True)
c["data"]=pd.to_datetime(c.data); c["v"]=pd.to_numeric(c.valore,errors="coerce")
c=c[c.v.notna()].drop_duplicates(["stazione_id","data","inquinante"])
rows=[]
for (sid,inq),g in c.groupby(["stazione_id","inquinante"]):
    sid=int(sid)
    ar=a[(a.idstazione==m_st[sid])&(a.tipo==m_in[inq])]
    if inq=="NO2": pass
    if len(ar)==0: rows.append(dict(stazione_id=sid,inquinante=inq,n_comune=len(g),n_arpa_giorni=0)); continue
    ar=ar.copy()
    # ARPA orario: etichetta oraria; ore 1..24 -> giorno = t-1h ; per PM giornalieri t=00:00 del giorno
    hourly=ar.groupby("idsensore").t.apply(lambda x:x.dt.hour.nunique()).max()>1
    if hourly:
        ar["day"]=(ar.t-pd.Timedelta(hours=1)).dt.normalize()
        grp=ar.groupby("day").valore
        d=pd.DataFrame({"mean":grp.mean(),"max":grp.max(),"n":grp.size()})
        d=d[d.n>=18]
        if inq in ("CO_8h","O3"):
            s=ar.sort_values("t").set_index("t").valore.resample("1h").mean().rolling(8,min_periods=6).mean()
            s.index=s.index-pd.Timedelta(hours=1)
            mx=s.groupby(s.index.normalize()).max(); d["max8h"]=mx.reindex(d.index)
    else:
        ar["day"]=ar.t.dt.normalize(); d=ar.groupby("day").valore.mean().to_frame("mean"); d["n"]=1
    d.index=d.index+pd.Timedelta(days=1)   # la data del Comune e' il giorno DOPO la misura ARPA
    j=g.set_index("data").v.rename("comune").to_frame().join(d,how="inner")
    r=dict(stazione_id=sid,inquinante=inq,n_comune=len(g),n_arpa_giorni=len(d),n_giorni_comuni=len(j))
    if len(j):
        for col in [x for x in ["mean","max","max8h"] if x in j]:
            diff=(j.comune-j[col]).abs()
            r[f"uguali_5pc_{col}"]=round((diff<=0.05*j[col].abs()+0.5).mean(),3); r[f"uguali_1_{col}"]=round((diff<=1).mean(),3) ; r[f"mediana_diff_{col}"]=round(diff.median(),3)
        r["corr_mean"]=round(j.comune.corr(j["mean"]),3)
    # giorni solo-Comune e solo-ARPA
    r["solo_comune"]=len(set(g.data)-set(d.index)); r["solo_arpa"]=len(set(d.index)-set(g.data))
    rows.append(r)
res=pd.DataFrame(rows); res.to_csv(os.path.join(out,"confronto_comune_arpa.csv"),index=False)
pd.set_option("display.width",250); print(res.to_string())
