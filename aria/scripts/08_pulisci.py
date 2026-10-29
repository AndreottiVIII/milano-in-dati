# Fase 2, passo 1: dati ARPA orari -> valori giornalieri ufficiali; Comune solo dove ARPA manca.
# uso: python -I scripts/08_pulisci.py raw pulito
import pandas as pd, numpy as np, glob, os, sys
raw, out = sys.argv[1], sys.argv[2]
MIN_ORE = 18          # 75% di 24 ore
POLL = {"Biossido di Azoto":"NO2","PM10 (SM2005)":"PM10","Particelle sospese PM2.5":"PM25",
        "Ozono":"O3","Monossido di Carbonio":"CO","Benzene":"C6H6"}
UNITA = {"NO2":"ug/m3","PM10":"ug/m3","PM25":"ug/m3","O3":"ug/m3","CO":"mg/m3","C6H6":"ug/m3"}
NOMI = {"501":"Marche","502":"Juvara","503":"Zavattari","528":"Verziere","539":"Liguria",
        "547":"Parco Lambro","548":"Senato","549":"Abbiategrasso","705":"Pascal"}
CAMBIO = {"502","705"}  # Juvara chiusa 11/06/2007, sostituita da Pascal (circa 925 m)
COM2ARPA = {1:"549",2:"705",3:"539",4:"501",5:"547",6:"548",7:"528",8:"503",9:"502"}

reg = pd.read_csv(os.path.join(raw,"arpa","ib47-atvt_stazioni_tutte.csv"),dtype=str)

def leggi_sensore(base, sid):
    parti=[]
    for f in sorted(glob.glob(os.path.join(base,"*_*",f"sensore_{sid}.csv"))):
        if "NRT" in f: continue   # tempo quasi reale, senza campo stato: non validato, doppione degli ultimi giorni
        d=pd.read_csv(f,dtype={"idsensore":str,"stato":str},usecols=["data","valore","stato"])
        if len(d): parti.append(d)
    if not parti: return None
    d=pd.concat(parti,ignore_index=True)
    d["t"]=pd.to_datetime(d.data).dt.round("h")
    nraw=len(d)
    valido=(d.stato=="VA")&(d.valore!=-9999)&d.valore.notna()&(d.valore>=0)
    ninv=int((~valido).sum())
    d=d[valido].drop_duplicates("t").sort_values("t")
    return d.set_index("t").valore.astype(float), nraw, ninv

def giornalieri(s, pc):
    """restituisce DataFrame: data, statistica, valore, n"""
    righe=[]
    orario = s.index.hour.nunique()>1
    if not orario:   # PM: valore giornaliero con data del giorno stesso
        d=pd.DataFrame({"data":s.index.normalize(),"valore":s.values,"n":1})
        righe.append(d.assign(statistica="media_giornaliera")[["data","statistica","valore","n"]])
        return pd.concat(righe), False
    day=(s.index-pd.Timedelta(hours=1)).normalize()   # ora "a fine ora": 24:00 appartiene al giorno prima
    g=s.groupby(day)
    n=g.size(); ok=n>=MIN_ORE
    mean=g.mean(); mx=g.max()
    if pc in ("NO2","C6H6"):
        righe.append(pd.DataFrame({"data":mean[ok].index,"statistica":"media_giornaliera","valore":mean[ok].values,"n":n[ok].values}))
    if pc=="NO2":
        righe.append(pd.DataFrame({"data":mx[ok].index,"statistica":"max_orario","valore":mx[ok].values,"n":n[ok].values}))
    if pc in ("O3","CO"):
        s2=s.reindex(pd.date_range(s.index.min(),s.index.max(),freq="h"))
        r=s2.rolling(8,min_periods=6).mean()           # finestra di 8 ore che finisce all'ora indicata
        dd=(r.index-pd.Timedelta(hours=1)).normalize()
        gg=r.groupby(dd); nn=gg.count(); mx8=gg.max(); ok8=nn>=MIN_ORE
        righe.append(pd.DataFrame({"data":mx8[ok8].index,"statistica":"max_8h","valore":mx8[ok8].values,"n":nn[ok8].values}))
    return pd.concat(righe), True

def elabora(base, sensori, log):
    tutte=[]
    for _,r in sensori.iterrows():
        res=leggi_sensore(base,r.idsensore)
        if res is None:
            log.append(dict(idsensore=r.idsensore,stazione=r.idstazione,righe=0)); continue
        s,nraw,ninv=res
        if len(s)==0: continue
        pc=POLL[r.nometiposensore]
        d,orario=giornalieri(s,pc)
        d["id_stazione"]=r.idstazione; d["inquinante"]=pc; d["idsensore"]=r.idsensore
        tutte.append(d)
        log.append(dict(idsensore=r.idsensore,stazione=r.idstazione,inquinante=pc,righe=nraw,non_validi=ninv,orario=orario,giorni=len(d)))
    return pd.concat(tutte,ignore_index=True)

# ---- ARPA Milano
sens=reg[(reg.comune.str.upper()=="MILANO")&reg.nometiposensore.isin(POLL)].copy()
log=[]
A=elabora(os.path.join(raw,"arpa"),sens,log)
pd.DataFrame(log).to_csv(os.path.join(out,"_log_sensori.csv"),index=False)
key=["id_stazione","inquinante","statistica","data"]
dup=A.duplicated(key,keep=False)
print("duplicati ARPA stessa chiave (piu' sensori):",int(dup.sum()))
A=A.groupby(key,as_index=False).agg(valore=("valore","mean"),n=("n","max"),idsensore=("idsensore","first"))
A["fonte"]="ARPA"
print("ARPA giorni:",len(A))

# ---- Comune
STAT_COM={"NO2":"max_orario","PM10":"media_giornaliera","PM25":"media_giornaliera","CO_8h":"max_8h","C6H6":"media_giornaliera"}
PC_COM={"NO2":"NO2","PM10":"PM10","PM25":"PM25","CO_8h":"CO","C6H6":"C6H6"}
c=pd.concat([pd.read_csv(f,sep=";",dtype=str) for f in sorted(glob.glob(os.path.join(raw,"comune","*datoaria*.csv")))],ignore_index=True)
c["v"]=pd.to_numeric(c.valore,errors="coerce"); c["data"]=pd.to_datetime(c.data)
c=c[c.v.notna()]
c=c.drop_duplicates(["stazione_id","data","inquinante"])
zeri=c[(c.v==0)]
print("Comune zeri:",zeri.groupby("inquinante").size().to_dict())
c=c[c.inquinante.isin(STAT_COM)].copy()
c=c[~((c.v==0)&c.inquinante.isin(["PM10","PM25"]))]   # PM a zero: implausibile
c["id_stazione"]=c.stazione_id.astype(int).map(COM2ARPA)
c["inquinante_n"]=c.inquinante.map(PC_COM); c["statistica"]=c.inquinante.map(STAT_COM)
c["data"]=c.data-pd.Timedelta(days=1)       # TRAPPOLA: data Comune = giorno della misura + 1
C=c.drop(columns="valore").rename(columns={"v":"valore"})[["id_stazione","inquinante_n","statistica","data","valore"]].rename(columns={"inquinante_n":"inquinante"})
C["fonte"]="Comune"; C["n"]=np.nan; C["idsensore"]=""

# confronto dove ci sono entrambe (controllo del metodo)
j=A.merge(C,on=key,suffixes=("_a","_c"))
j["d"]=(j.valore_a-j.valore_c).abs()
j["tol"]=(j.d<=0.05*j.valore_a.abs()+0.5)
j["e1"]=(j.d<=1)
cmp=j.groupby(["inquinante","statistica"]).agg(giorni=("d","size"),entro_1=("e1","mean"),entro_5pc_piu_0_5=("tol","mean"),mediana_diff=("d","median")).reset_index().round(3)
cmp.to_csv(os.path.join(out,"confronto_fonti.csv"),index=False); print(cmp.to_string())

# riempimento: solo dove ARPA manca
A_k=A.set_index(key).index
mask=~C.set_index(key).index.isin(A_k)
Cf=C[mask].copy()
print("Comune: giorni usati per riempire:",len(Cf),"su",len(C),"; scartati perche' ARPA c'e':",len(C)-len(Cf))
print(Cf.groupby(["inquinante","statistica"]).size())

D=pd.concat([A,Cf],ignore_index=True)
D["stazione"]=D.id_stazione.map(NOMI)
D["unita"]=D.inquinante.map(UNITA)
def flag(r):
    f=[]
    if r.id_stazione in CAMBIO: f.append("cambio_stazione")
    if r.fonte=="Comune":
        f.append("da_comune_data_spostata_-1g")
        if r.inquinante=="C6H6": f.append("indicatore_da_verificare")
    return ";".join(f)
D["flag"]=[flag(r) for r in D.itertuples()]
D["valore"]=D.valore.round(3)
D=D.rename(columns={"n":"n_valori"})
D=D.sort_values(["inquinante","statistica","id_stazione","data"])
D["data"]=D.data.dt.strftime("%Y-%m-%d")
cols=["data","id_stazione","stazione","inquinante","statistica","valore","unita","n_valori","fonte","flag"]
D[cols].to_csv(os.path.join(out,"aria_giornaliera.csv"),index=False,encoding="utf-8")
print("scritto aria_giornaliera.csv",len(D),"righe")
print(D.groupby(["inquinante","statistica","fonte"]).size())

# ---- controlli (fuori Milano), stesso trattamento
ctrl=os.path.join(raw,"arpa_controllo")
if os.path.exists(os.path.join(ctrl,"nicp-bhqi_corrente","sensore_5532.csv")):
    cs=reg[reg.idsensore.isin(["5534","6908","5549","6912","5507","5517","5532"])].copy()
    lg=[]; K=elabora(ctrl,cs,lg)
    K=K[(K.statistica=="media_giornaliera")]
    nm=cs.drop_duplicates("idstazione").set_index("idstazione").nomestazione.to_dict()
    K["stazione"]=K.id_stazione.map(nm); K["unita"]="ug/m3"; K["fonte"]="ARPA"
    K["data"]=K.data.dt.strftime("%Y-%m-%d"); K["valore"]=K.valore.round(3)
    K.rename(columns={"n":"n_valori"})[["data","id_stazione","stazione","inquinante","statistica","valore","unita","n_valori","fonte"]].sort_values(["inquinante","id_stazione","data"]).to_csv(os.path.join(out,"controlli_giornaliera.csv"),index=False)
    print("controlli:",len(K))
else:
    print("controlli non ancora scaricati")
