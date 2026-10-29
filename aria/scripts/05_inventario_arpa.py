import pandas as pd, glob, os, sys
src=sys.argv[1]; out=sys.argv[2]
st=pd.read_csv(os.path.join(src,"ib47-atvt_stazioni_tutte.csv"),dtype=str)
st=st[st.comune.str.upper()=="MILANO"].set_index("idsensore")
frames=[]
for f in sorted(glob.glob(os.path.join(src,"*_*","sensore_*.csv"))):
    ds=os.path.basename(os.path.dirname(f))
    d=pd.read_csv(f,dtype={"idsensore":str,"stato":str,"idoperatore":str})
    if len(d)==0: continue
    d["ds"]=ds; frames.append(d)
d=pd.concat(frames,ignore_index=True)
d["t"]=pd.to_datetime(d.data)
print("righe totali",len(d),"per dataset:\n",d.groupby("ds").size())
print("stato:",d.stato.value_counts(dropna=False).to_dict())
print("idoperatore:",d.idoperatore.value_counts(dropna=False).to_dict())
print("valore -9999:",(d.valore==-9999).sum(),"altri negativi:",((d.valore<0)&(d.valore!=-9999)).sum(),"NaN:",d.valore.isna().sum())
print("orari non esatti:",(d.t.dt.minute+d.t.dt.second!=0).sum())
d.to_pickle(os.path.join(out,"_arpa_all.pkl"))
d["ok"]=(d.valore!=-9999)&d.valore.notna()
rows=[]
for s,g in d.groupby("idsensore"):
    g=g.sort_values("t"); gv=g[g.ok]
    dup=g.duplicated(["t"]).sum()
    ds_list=",".join(sorted(g.ds.unique()))
    med=g.t.drop_duplicates().diff().median()
    gaps=gv.t.drop_duplicates().diff().dt.total_seconds()/86400
    r=dict(idsensore=s,tipo=st.loc[s,"nometiposensore"],unita=st.loc[s,"unitamisura"],idstazione=st.loc[s,"idstazione"],stazione=st.loc[s,"nomestazione"],
        storico=st.loc[s,"storico"],datastart_reg=st.loc[s,"datastart"][:10],datastop_reg=(st.loc[s,"datastop"] or "")[:10] if isinstance(st.loc[s,"datastop"],str) else "",
        righe=len(g),validi=len(gv),meno9999=int((~g.ok).sum()),prima=gv.t.min(),ultima=gv.t.max(),passo_mediano=str(med),
        max_buco_giorni=round(gaps.max(),1) if gaps.notna().any() else None,righe_duplicate_t=int(dup),dataset=ds_list,
        stati=",".join(f"{k}:{v}" for k,v in g.stato.value_counts(dropna=False).items()))
    rows.append(r)
inv=pd.DataFrame(rows).sort_values(["idstazione","tipo","idsensore"])
inv.to_csv(os.path.join(out,"inventario_arpa.csv"),index=False,encoding="utf-8")
print(inv.drop(columns=["stati"]).to_string())
# sensori Milano senza nessun dato scaricato
miss=[s for s in st.index if s not in set(inv.idsensore)]
print("sensori senza dati:",miss)
# per anno validi
cov=d[d.ok].assign(anno=lambda x:x.t.dt.year).groupby(["idsensore","anno"]).size().unstack(fill_value=0)
cov.to_csv(os.path.join(out,"inventario_arpa_per_anno.csv"))
