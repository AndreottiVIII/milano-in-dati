# Fase 2, passo 4: prima/dopo (Area C, Area B, Covid). Solo numeri, nessuna stima causale.
# uso: python -I scripts/11_prima_dopo.py pulito
import pandas as pd, numpy as np, os, sys, json
pul=sys.argv[1]
D=pd.read_csv(os.path.join(pul,"aria_giornaliera.csv"),dtype={"id_stazione":str},parse_dates=["data"])
K=pd.read_csv(os.path.join(pul,"controlli_giornaliera.csv"),dtype={"id_stazione":str},parse_dates=["data"])
D=D[D.statistica=="media_giornaliera"]
D["gruppo"]=np.where(D.id_stazione.isin(["548","528"]),"centro (dentro Area C)","Milano fuori Area C")
D["zona"]=np.where(D.id_stazione.isin(["548","528"]),"Milano centro","Milano fuori Area C")
K["zona"]="fuori Milano (controllo)"
K["stazione"]=K.stazione.str.replace("Pioltello Limito","Pioltello").str.replace("Magenta v. F. Turati","Magenta").str.replace("Sesto San Giovanni v. Cesare da Sesto","Sesto San Giovanni").str.replace("Cinisello Balsamo v.Lincoln","Cinisello Balsamo").str.replace("Rho via Buon Ges�","Rho").str.replace(r"Rho via Buon.*","Rho",regex=True)
ALL=pd.concat([D[["data","id_stazione","stazione","inquinante","valore","zona"]],K[["data","id_stazione","stazione","inquinante","valore","zona"]]],ignore_index=True)
ALL=ALL[ALL.inquinante.isin(["NO2","PM10","PM25"])]
SOGLIA=0.75
def media(g,a,b):
    w=g[(g.data>=a)&(g.data<=b)]
    ng=(pd.Timestamp(b)-pd.Timestamp(a)).days+1
    return (w.valore.mean() if len(w)>=SOGLIA*ng else np.nan), len(w), ng

def confronto(evento,anchor,mesi=12,placebo_anni=()):
    """12 mesi prima vs 12 mesi dopo la data 'anchor'"""
    righe=[]
    for anno in [anchor.year]+list(placebo_anni):
        an=pd.Timestamp(anno,anchor.month,anchor.day)
        a0=an-pd.DateOffset(months=mesi); a1=an-pd.Timedelta(days=1); b0=an; b1=an+pd.DateOffset(months=mesi)-pd.Timedelta(days=1)
        for (pc,sid,st,zona),g in ALL.groupby(["inquinante","id_stazione","stazione","zona"]):
            m0,n0,t0=media(g,a0,a1); m1,n1,t1=media(g,b0,b1)
            righe.append(dict(evento=evento,reale=int(anno==anchor.year),anno_ancora=anno,inquinante=pc,id_stazione=sid,stazione=st,zona=zona,
                prima_da=a0.date(),prima_a=a1.date(),dopo_da=b0.date(),dopo_a=b1.date(),media_prima=round(m0,1) if m0==m0 else np.nan,giorni_prima=n0,
                media_dopo=round(m1,1) if m1==m1 else np.nan,giorni_dopo=n1,
                variazione_pct=round(100*(m1-m0)/m0,1) if m0==m0 and m1==m1 else np.nan))
    return pd.DataFrame(righe)
AC=confronto("Area C",pd.Timestamp(2012,1,16),placebo_anni=[a for a in range(2009,2020) if a!=2012])
AB=confronto("Area B",pd.Timestamp(2019,2,25),placebo_anni=[2013,2014,2015,2016,2017,2018,2021,2022,2023])
# per l'Area B i confronti 'placebo' 2021+ non sono possibili con 12 mesi dopo fino a 2025: ok (dati fino a ott. 2026)
# Covid: finestra 9 marzo - 3 maggio, tutti gli anni
righe=[]
for anno in range(2012,2026):
    a,b=pd.Timestamp(anno,3,9),pd.Timestamp(anno,5,3)
    for (pc,sid,st,zona),g in ALL.groupby(["inquinante","id_stazione","stazione","zona"]):
        m,n,t=media(g,a,b)
        righe.append(dict(evento="Covid",anno=anno,inquinante=pc,id_stazione=sid,stazione=st,zona=zona,media=round(m,1) if m==m else np.nan,giorni=n,giorni_finestra=t))
CV=pd.DataFrame(righe)
# variazione 2020 su media 2017-2019 stessa finestra (stazioni con almeno 2 anni validi su 3)
cv=[]
for (pc,sid,st,zona),g in CV.groupby(["inquinante","id_stazione","stazione","zona"]):
    gg=g.set_index("anno").media
    ref=gg.loc[[2017,2018,2019]].dropna()
    if len(ref)>=2 and gg.get(2020)==gg.get(2020) and gg.get(2020) is not None:
        cv.append(dict(inquinante=pc,id_stazione=sid,stazione=st,zona=zona,media_2017_2019=round(ref.mean(),1),anni_ref=len(ref),media_2020=gg[2020],
            variazione_2020_pct=round(100*(gg[2020]-ref.mean())/ref.mean(),1),media_2021=gg.get(2021),
            variazione_2021_pct=round(100*(gg.get(2021)-ref.mean())/ref.mean(),1) if gg.get(2021)==gg.get(2021) else np.nan))
CVV=pd.DataFrame(cv)
pd.concat([AC,AB]).to_csv(os.path.join(pul,"prima_dopo_areaC_areaB.csv"),index=False)
CV.to_csv(os.path.join(pul,"covid_finestra_per_anno.csv"),index=False)
CVV.to_csv(os.path.join(pul,"covid_2020_vs_2017_2019.csv"),index=False)
pd.set_option("display.width",250)
def sintesi(T,titolo):
    print("\n==",titolo)
    t=T[T.variazione_pct.notna()]
    g=t.groupby(["reale","anno_ancora","inquinante","zona"]).agg(n_stazioni=("stazione","size"),variaz_media=("variazione_pct","mean")).round(1).reset_index()
    print(g[g.reale==1].to_string())
    pl=g[g.reale==0].groupby(["inquinante","zona"]).variaz_media.agg(["min","median","max","count"]).round(1)
    print("altri anni (stessa data):\n",pl.to_string())
sintesi(AC,"Area C"); sintesi(AB,"Area B")
print(CVV.to_string())
print(CVV.groupby(["inquinante","zona"]).agg(n=("stazione","size"),v2020=("variazione_2020_pct","mean"),v2021=("variazione_2021_pct","mean")).round(1))
