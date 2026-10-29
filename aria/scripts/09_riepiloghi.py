# Fase 2, passo 2: riepiloghi annuali per stazione e inquinante + "dove si respira peggio".
# uso: python -I scripts/09_riepiloghi.py pulito
import pandas as pd, numpy as np, os, sys
out=sys.argv[1]
D=pd.read_csv(os.path.join(out,"aria_giornaliera.csv"),dtype={"id_stazione":str},parse_dates=["data"])
D["anno"]=D.data.dt.year
ULTIMO=D.data.max()                         # ultimo giorno con dati (2026-10-28 circa)
# limiti: (soglia giornaliera, descrizione) ; annuo UE ; annuo OMS 2021
GIORN={("PM10","media_giornaliera"):(50,"giorni con media > 50 ug/m3 (UE: max 35 giorni/anno)"),
       ("NO2","max_orario"):(200,"giorni con almeno un'ora > 200 ug/m3 (UE: max 18 ORE/anno, qui si contano giorni)"),
       ("O3","max_8h"):(120,"giorni con massimo su 8 ore > 120 ug/m3 (obiettivo UE: max 25 giorni/anno, media su 3 anni)"),
       ("CO","max_8h"):(10,"giorni con massimo su 8 ore > 10 mg/m3 (limite UE)")}
ANNUO={("PM10","media_giornaliera"):(40,15),("PM25","media_giornaliera"):(25,5),("NO2","media_giornaliera"):(40,10),("C6H6","media_giornaliera"):(5,None)}
righe=[]
for (st,nome,pc,stat),g in D.groupby(["id_stazione","stazione","inquinante","statistica"]):
    for anno,h in g.groupby("anno"):
        giorni_anno=366 if pd.Timestamp(anno,12,31).dayofyear==366 else 365
        attesi=giorni_anno if anno<ULTIMO.year else (ULTIMO-pd.Timestamp(anno,1,1)).days+1
        n=len(h); comp=100*n/attesi
        r=dict(anno=anno,id_stazione=st,stazione=nome,inquinante=pc,statistica=stat,
               giorni_validi=n,giorni_attesi=attesi,completezza_pct=round(comp,1),
               anno_ok_75=int(comp>=75),anno_parziale=int(anno==ULTIMO.year),
               media_annua=round(h.valore.mean(),2),massimo=round(h.valore.max(),1),
               giorni_da_comune=int((h.fonte=="Comune").sum()),
               cambio_stazione=int(st in ("502","705")))
        if (pc,stat) in GIORN:
            thr=GIORN[(pc,stat)][0]; r["soglia_giornaliera"]=thr; r["giorni_sopra_soglia"]=int((h.valore>thr).sum())
        if (pc,stat) in ANNUO:
            ue,who=ANNUO[(pc,stat)]; r["limite_ue_annuo"]=ue; r["who2021_annuo"]=who
            r["sopra_limite_ue"]=int(r["media_annua"]>ue)
            r["sopra_who2021"]=int(r["media_annua"]>who) if who else np.nan
        righe.append(r)
R=pd.DataFrame(righe).sort_values(["inquinante","statistica","id_stazione","anno"])
R.to_csv(os.path.join(out,"riepilogo_annuale.csv"),index=False,encoding="utf-8")
print("riepilogo",len(R))

# dove si respira peggio: ultimi 5 anni completi 2021-2025, solo anni con >=75% di giorni
W=R[(R.anno.between(2021,2025))&(R.anno_ok_75==1)]
rows=[]
for (pc,stat),g in W.groupby(["inquinante","statistica"]):
    for (st,nome),h in g.groupby(["id_stazione","stazione"]):
        r=dict(inquinante=pc,statistica=stat,id_stazione=st,stazione=nome,anni_validi=len(h),anni=",".join(map(str,h.anno)),
               media_dei_5_anni=round(h.media_annua.mean(),1))
        if "giorni_sopra_soglia" in h and h.giorni_sopra_soglia.notna().any():
            r["giorni_sopra_soglia_media_annua"]=round(h.giorni_sopra_soglia.mean(),1)
        rows.append(r)
P=pd.DataFrame(rows)
P["posizione"]=P.groupby(["inquinante","statistica"]).media_dei_5_anni.rank(ascending=False,method="min").astype(int)
P=P.sort_values(["inquinante","statistica","posizione"])
P.to_csv(os.path.join(out,"peggiori_2021_2025.csv"),index=False)
pd.set_option("display.width",250)
print(P.to_string())
# copertura: stazione x inquinante x anni validi
cov=R[R.statistica.isin(["media_giornaliera","max_8h"])].pivot_table(index=["inquinante","stazione"],columns="anno",values="completezza_pct")
print(cov.round(0).to_string())
