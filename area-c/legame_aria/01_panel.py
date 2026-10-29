# Legame Area C - aria, passo 1: costruisce la tabella giornaliera unica (ingressi + aria + differenze dentro-fuori).
# uso: python -I 01_panel.py <cartella milano-in-dati> <cartella di uscita>
import pandas as pd, numpy as np, glob, os, sys
base, out = sys.argv[1], sys.argv[2]
AC = os.path.join(base, "area-c", "pulito"); AR = os.path.join(base, "aria")
os.makedirs(out, exist_ok=True)

# ---- ingressi e calendario (solo dal 1/9/2016: la serie 2012-2015 ha un altro conteggio e NON si usa)
ing = pd.read_csv(os.path.join(AC, "ingressi_giornalieri.csv"), sep=";", parse_dates=["data"],
                  usecols=["data", "giorno_settimana", "totale", "flag", "tipo_moto", "tipo_auto"])
cal = pd.read_csv(os.path.join(AC, "calendario.csv"), sep=";", parse_dates=["data"])
d = ing.merge(cal.drop(columns=["giorno_settimana"]), on="data")
d["ingressi"] = d.totale.where(d.flag != "nessun_dato")
d = d.set_index("data")

# ---- aria (file pulito, ARPA + Comune dove ARPA manca)
a = pd.read_csv(os.path.join(AR, "pulito", "aria_giornaliera.csv"), parse_dates=["data"])
c = pd.read_csv(os.path.join(AR, "pulito", "controlli_giornaliera.csv"), parse_dates=["data"])
c["stazione"] = c.stazione.str.replace("�", "").str.replace("�", "")
a = a[a.fonte.isin(["ARPA", "Comune"])]

def serie(df, staz, inq, stat):
    x = df[(df.stazione == staz) & (df.inquinante == inq) & (df.statistica == stat)]
    return x.groupby("data").valore.mean()

W = {}
for st in ["Senato", "Verziere", "Marche", "Liguria", "Pascal"]:
    W[f"NO2m_{st}"] = serie(a, st, "NO2", "media_giornaliera")
    W[f"NO2x_{st}"] = serie(a, st, "NO2", "max_orario")
for st in ["Senato", "Verziere", "Marche", "Pascal"]:
    W[f"PM10_{st}"] = serie(a, st, "PM10", "media_giornaliera")
for st in ["Senato", "Marche", "Pascal"]:
    W[f"PM25_{st}"] = serie(a, st, "PM25", "media_giornaliera")
ctrl_no2 = {"Pioltello": "Pioltello Limito", "Magenta": "Magenta v. F. Turati", "Sesto": "Sesto San Giovanni v. Cesare da Sesto",
            "Rho": "Rho via Buon Ges", "Cinisello": "Cinisello Balsamo v.Lincoln"}
for k, v in ctrl_no2.items():
    W[f"NO2m_C_{k}"] = c[c.stazione.str.startswith(v[:12]) & (c.inquinante == "NO2")].groupby("data").valore.mean()
for k in ["Pioltello", "Magenta"]:
    v = ctrl_no2[k]
    W[f"PM10_C_{k}"] = c[c.stazione.str.startswith(v[:12]) & (c.inquinante == "PM10")].groupby("data").valore.mean()
W = pd.DataFrame(W)
W.index = pd.to_datetime(W.index)

# ---- Black Carbon (orario ARPA, fuori dal file pulito): media giornaliera con almeno 18 ore valide
BC = {"Senato": ["20005", "20465"], "Pascal": ["20004", "20581"], "Marche": ["29001", "20455"]}
def leggi_orario(sid):
    parti = []
    for f in sorted(glob.glob(os.path.join(AR, "raw", "arpa", "*_*", f"sensore_{sid}.csv"))):
        if "NRT" in f: continue
        x = pd.read_csv(f, dtype={"stato": str}, usecols=["data", "valore", "stato"])
        if len(x): parti.append(x)
    if not parti: return pd.Series(dtype=float)
    x = pd.concat(parti, ignore_index=True)
    x["t"] = pd.to_datetime(x.data).dt.round("h")
    x = x[(x.stato == "VA") & (x.valore != -9999) & (x.valore >= 0)].drop_duplicates("t").sort_values("t")
    return x.set_index("t").valore.astype(float)
bcd = {}
for st, sids in BC.items():
    s = pd.concat([leggi_orario(i) for i in sids]).sort_index()
    s = s[~s.index.duplicated()]
    day = (s.index - pd.Timedelta(hours=1)).normalize()   # ora "a fine ora"
    g = s.groupby(day)
    n = g.size(); m = g.mean()
    bcd[f"BC_{st}"] = m[n >= 18]
bcd = pd.DataFrame(bcd); bcd.index = pd.to_datetime(bcd.index)
W = W.join(bcd, how="outer")

P = d.join(W, how="left")

# ---- meteo ARPA (Milano Brera; vedi 00_scarica_meteo.py e 00b_meteo_giornaliero.py), se presente
mf = os.path.join(out, "meteo_giornaliero.csv")
if os.path.exists(mf):
    me = pd.read_csv(mf, sep=";", parse_dates=["data"]).set_index("data")
    P = P.join(me, how="left")
    P["vento_B"] = P.vento_Brera; P["pioggia_B"] = P.pioggia_Brera; P["temp_B"] = P.temperatura_Brera
    P["pioggia_si"] = (P.pioggia_B >= 1).astype(float).where(P.pioggia_B.notna())
    P["vento_B2"] = P.vento_B ** 2
    P["vento_B_ieri"] = P.vento_B.shift(1, freq="D").reindex(P.index)
    P["pioggia_si_ieri"] = P.pioggia_si.shift(1, freq="D").reindex(P.index)

# ---- gruppi e differenze (un giorno vale solo se TUTTE le stazioni del gruppo ci sono: composizione costante)
def grp(cols, nmin=None):
    x = P[cols]
    nmin = len(cols) if nmin is None else nmin
    return x.mean(axis=1).where(x.notna().sum(axis=1) >= nmin)
IN = ["Senato", "Verziere"]; OB = ["Marche", "Liguria", "Pascal"]
CT = ["Pioltello", "Magenta", "Sesto", "Rho", "Cinisello"]
P["NO2m_dentro"] = grp([f"NO2m_{s}" for s in IN])
P["NO2m_fuoriAC"] = grp([f"NO2m_{s}" for s in OB])
P["NO2m_controllo"] = grp([f"NO2m_C_{s}" for s in CT], 4)     # almeno 4 stazioni di controllo su 5
P["NO2x_dentro"] = grp([f"NO2x_{s}" for s in IN])
P["NO2x_fuoriAC"] = grp([f"NO2x_{s}" for s in OB])
P["D_NO2m_B"] = P.NO2m_dentro - P.NO2m_fuoriAC     # dentro Area C meno resto di Milano (3 stazioni)
P["D_NO2m_C"] = P.NO2m_dentro - P.NO2m_controllo   # dentro Area C meno fuori Milano (5 stazioni)
P["D_NO2x_B"] = P.NO2x_dentro - P.NO2x_fuoriAC
P["R_NO2m_B"] = np.log(P.NO2m_dentro / P.NO2m_fuoriAC)   # rapporto (in logaritmo), robustezza
P["R_NO2m_C"] = np.log(P.NO2m_dentro / P.NO2m_controllo)
# PM
P["PM10_dentro"] = grp(["PM10_Senato", "PM10_Verziere"])
P["PM10_fuoriAC"] = grp(["PM10_Pascal"])               # Marche PM10 solo dal 2018: per avere una serie lunga si usa Pascal
P["PM10_fuoriAC2"] = grp(["PM10_Pascal", "PM10_Marche"])
P["PM10_controllo"] = grp(["PM10_C_Pioltello", "PM10_C_Magenta"])
P["D_PM10_B"] = P.PM10_dentro - P.PM10_fuoriAC
P["D_PM10_C"] = P.PM10_dentro - P.PM10_controllo
P["D_PM25_B"] = P.PM25_Senato - P.PM25_Pascal
# Black Carbon
P["D_BC_Pascal"] = P.BC_Senato - P.BC_Pascal
P["D_BC_Marche"] = P.BC_Senato - P.BC_Marche
P["anno"] = P.index.year; P["mese"] = P.index.month; P["dow"] = P.index.dayofweek
P.reset_index().to_csv(os.path.join(out, "pannello_giornaliero.csv"), index=False, sep=";", float_format="%.4f")

# ---- copertura: quanti giorni (lavorativi, ingressi presenti) hanno la differenza
L = P[(P.lavorativo == 1) & P.ingressi.notna()]
rows = []
for col in ["D_NO2m_B", "D_NO2m_C", "D_NO2x_B", "D_PM10_B", "D_PM10_C", "D_PM25_B", "D_BC_Pascal", "D_BC_Marche"]:
    x = L[col].dropna()
    rows.append(dict(variabile=col, giorni_lavorativi_con_dato=len(x), primo=x.index.min().date(), ultimo=x.index.max().date(),
                     media=round(x.mean(), 2), dev_std=round(x.std(), 2)))
pd.DataFrame(rows).to_csv(os.path.join(out, "copertura.csv"), index=False, sep=";")
print(pd.DataFrame(rows).to_string())
print("giorni lavorativi con ingressi:", len(L), " tot giorni", len(P))
