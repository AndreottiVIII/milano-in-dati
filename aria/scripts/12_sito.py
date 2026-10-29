# Fase 2, passo 5: dati piccoli per la pagina docs/aria/
# uso: python -I scripts/12_sito.py pulito ../docs/aria/data
import pandas as pd, numpy as np, os, sys, json, shutil
pul,out=sys.argv[1:3]
os.makedirs(out,exist_ok=True)
R=pd.read_csv(os.path.join(pul,"riepilogo_annuale.csv"),dtype={"id_stazione":str})
S=pd.read_csv(os.path.join(pul,"stazioni_storia.csv"),dtype={"id_stazione_arpa":str})
SE=pd.read_csv(os.path.join(pul,"stazioni_sensori.csv"),dtype=str)
P=pd.read_csv(os.path.join(pul,"peggiori_2021_2025.csv"),dtype={"id_stazione":str})
T=pd.read_csv(os.path.join(pul,"prima_dopo_areaC_areaB.csv"),dtype={"id_stazione":str})
CV=pd.read_csv(os.path.join(pul,"covid_finestra_per_anno.csv"),dtype={"id_stazione":str})
CVV=pd.read_csv(os.path.join(pul,"covid_2020_vs_2017_2019.csv"),dtype={"id_stazione":str})
def nn(x):
    return None if (x is None or (isinstance(x,float) and np.isnan(x))) else x

# ---------- stazioni
NOMEPC={"NO2":"NO2","PM10":"PM10","PM25":"PM2.5","O3":"ozono","CO":"CO","C6H6":"benzene"}
st=[]
for _,r in S.iterrows():
    sid=r.id_stazione_arpa
    inq=[]
    for pc in ["PM10","PM25","NO2","O3","CO","C6H6"]:
        g=R[(R.id_stazione==sid)&(R.inquinante==pc)&(R.statistica!="max_orario")]
        if len(g)==0: continue
        ok=g[g.anno_ok_75==1]
        inq.append(dict(p=NOMEPC[pc],da=int(g.anno.min()),a=int(g.anno.max()),anni_ok=int(len(ok)),
                        anni_ok_da=int(ok.anno.min()) if len(ok) else None,anni_ok_a=int(ok.anno.max()) if len(ok) else None))
    altri=SE[(SE.id_stazione_arpa==sid)&(SE.nel_file_pulito=="no")].tipo.unique().tolist()
    st.append(dict(id=sid,id_comune=int(r.id_comune),nome=r.nome,posizione=r.posizione,lat=r.lat_arpa,lng=r.lng_arpa,
        stato=r.stato_2026,primo_dato=r.primo_dato_arpa,ultimo_dato=r.ultimo_dato_arpa,fine_comune=nn(r.fine_comune) or "",fine_registro_arpa=nn(r.fine_registro_arpa) or "",
        sostituzione=nn(r.sostituzione) or "",cambio=int(r.cambio_stazione),dist_coord_m=int(r.distanza_coordinate_m),
        inquinanti=inq,altri_sensori=altri,note=r.note))
json.dump(st,open(os.path.join(out,"stazioni.json"),"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))

# ---------- annuali per inquinante
CFG=[("PM10","media_giornaliera","PM10","µg/m³","media annua",40,15,"PM10",50,"giorni con media giornaliera > 50 µg/m³","media_giornaliera"),
     ("PM25","media_giornaliera","PM2.5","µg/m³","media annua",25,5,None,None,None,None),
     ("NO2","media_giornaliera","NO2 (biossido di azoto)","µg/m³","media annua",40,10,"NO2",200,"giorni con almeno un'ora > 200 µg/m³","max_orario"),
     ("O3","max_8h","Ozono","µg/m³","media annua del massimo giornaliero su 8 ore",None,None,"O3",120,"giorni con massimo su 8 ore > 120 µg/m³","max_8h"),
     ("CO","max_8h","Monossido di carbonio","mg/m³","media annua del massimo giornaliero su 8 ore",None,None,"CO",10,"giorni con massimo su 8 ore > 10 mg/m³","max_8h"),
     ("C6H6","media_giornaliera","Benzene","µg/m³","media annua",5,None,None,None,None,None)]
ann={}
for pc,stat,tit,unit,desc,ue,who,_,thr,thrdesc,thrstat in CFG:
    g=R[(R.inquinante==pc)&(R.statistica==stat)]
    stz={}
    for sid,h in g.groupby("id_stazione"):
        h=h.sort_values("anno")
        # giorni sopra soglia
        if thrstat:
            hh=R[(R.inquinante==pc)&(R.statistica==thrstat)&(R.id_stazione==sid)].set_index("anno")
        rows=[]
        for _,r in h.iterrows():
            sopra=None
            if thrstat and r.anno in hh.index:
                sopra=nn(hh.loc[r.anno,"giorni_sopra_soglia"])
                sopra=int(sopra) if sopra is not None else None
            rows.append([int(r.anno),round(r.media_annua,1),int(round(r.completezza_pct)),int(r.anno_ok_75),sopra,int(r.anno_parziale),int(r.giorni_da_comune)])
        stz[sid]=rows
    ann[pc]=dict(titolo=tit,unita=unit,descr=desc,limite_ue=ue,who=who,soglia=thr,soglia_descr=thrdesc,stazioni=stz)
json.dump(ann,open(os.path.join(out,"annuale.json"),"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))

# ---------- peggiori
pj={}
for pc,stat,tit,unit,desc,ue,who,_,thr,thrdesc,thrstat in CFG:
    g=P[(P.inquinante==pc)&(P.statistica==stat)].sort_values("posizione")
    pj[pc]=[dict(id=r.id_stazione,nome=r.stazione,media=r.media_dei_5_anni,anni=r.anni,n=int(r.anni_validi),sopra=nn(r.get("giorni_sopra_soglia_media_annua"))) for _,r in g.iterrows()]
json.dump(pj,open(os.path.join(out,"peggiori.json"),"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))

# ---------- prima/dopo
ZC={"Milano centro":"Milano, dentro Area C (Senato, Verziere)","Milano fuori Area C":"Milano, fuori Area C","fuori Milano (controllo)":"Fuori Milano (controllo)"}
def zona_b(z): return "Fuori Milano (controllo)" if z.startswith("fuori Milano") else "Milano (tutte le stazioni, dentro Area B)"
res={}
for ev,fz in [("Area C",lambda z:ZC[z]),("Area B",zona_b)]:
    t=T[T.evento==ev].copy(); t["Z"]=t.zona.map(fz)
    t=t[t.variazione_pct.notna()]
    reale=t[t.reale==1]; pl=t[t.reale==0]
    righe=[]
    for (pc,z),g in reale.groupby(["inquinante","Z"]):
        pg=pl[(pl.inquinante==pc)&(pl.Z==z)].groupby("anno_ancora").variazione_pct.mean()
        righe.append(dict(inq=pc,zona=z,n=len(g),prima=round(g.media_prima.mean(),1),dopo=round(g.media_dopo.mean(),1),var=round(g.variazione_pct.mean(),1),
            stazioni=", ".join(g.sort_values("stazione").stazione),
            altri_min=round(pg.min(),1) if len(pg) else None,altri_med=round(pg.median(),1) if len(pg) else None,altri_max=round(pg.max(),1) if len(pg) else None,altri_n=len(pg)))
    det=[dict(inq=r.inquinante,staz=r.stazione,zona=(ZC[r.zona] if ev=="Area C" else zona_b(r.zona)),prima=r.media_prima,dopo=r.media_dopo,var=r.variazione_pct,gp=int(r.giorni_prima),gd=int(r.giorni_dopo))
         for _,r in reale.sort_values(["inquinante","zona","stazione"]).iterrows()]
    r0=reale.iloc[0]
    res[ev]=dict(prima=f"{r0.prima_da} / {r0.prima_a}",dopo=f"{r0.dopo_da} / {r0.dopo_a}",gruppi=righe,dettaglio=det)
# covid
cvz=lambda z:"Milano" if not z.startswith("fuori") else "Fuori Milano (controllo)"
CVV["Z"]=CVV.zona.map(cvz)
gr=[]
for (pc,z),g in CVV.groupby(["inquinante","Z"]):
    gr.append(dict(inq=pc,zona=z,n=len(g),ref=round(g.media_2017_2019.mean(),1),m2020=round(g.media_2020.mean(),1),var2020=round(g.variazione_2020_pct.mean(),1),
        var2021=round(g.variazione_2021_pct.mean(),1) if g.variazione_2021_pct.notna().any() else None,stazioni=", ".join(g.sort_values("stazione").stazione)))
det=[dict(inq=r.inquinante,staz=r.stazione,zona=r.Z,ref=r.media_2017_2019,m2020=r.media_2020,var2020=r.variazione_2020_pct,var2021=nn(r.variazione_2021_pct)) for _,r in CVV.sort_values(["inquinante","Z","stazione"]).iterrows()]
# per anno: solo stazioni nel confronto
cvy=[]
sel=CVV[["inquinante","id_stazione"]]
x=CV.merge(sel,on=["inquinante","id_stazione"])
x["Z"]=x.zona.map(cvz)
for (pc,z,anno),g in x[(x.anno>=2015)&(x.anno<=2025)].groupby(["inquinante","Z","anno"]):
    v=g.media.dropna()
    cvy.append(dict(inq=pc,zona=z,anno=int(anno),media=round(v.mean(),1) if len(v) else None,n=len(v)))
res["Covid"]=dict(finestra="9 marzo - 3 maggio",gruppi=gr,dettaglio=det,per_anno=cvy)
json.dump(res,open(os.path.join(out,"prima_dopo.json"),"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))

# file scaricabili (piccoli)
for f in ["riepilogo_annuale.csv","stazioni_storia.csv","stazioni_sensori.csv","problemi.md","prima_dopo_areaC_areaB.csv","covid_2020_vs_2017_2019.csv","peggiori_2021_2025.csv","confronto_fonti.csv"]:
    shutil.copy(os.path.join(pul,f),os.path.join(out,f))
tot=sum(os.path.getsize(os.path.join(out,f)) for f in os.listdir(out))
print("dimensione data/:",round(tot/1e6,2),"MB")
for ev in ("Area C","Area B"):
    print(ev); [print(" ",g) for g in res[ev]["gruppi"]]
print("Covid"); [print(" ",g) for g in gr]
