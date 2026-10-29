# Passo 5: prima e dopo l'avvio di Area C (16/1/2012), con i soli dati d'aria 2011-2013, piu' "placebo" negli altri anni.
# uso: python -I 05_prima_dopo_2012.py <cartella milano-in-dati> <cartella legame_aria>
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
base, cart = sys.argv[1], sys.argv[2]
AR = os.path.join(base, "aria", "pulito")
a = pd.read_csv(os.path.join(AR, "aria_giornaliera.csv"), parse_dates=["data"])
c = pd.read_csv(os.path.join(AR, "controlli_giornaliera.csv"), parse_dates=["data"])
def ser(df, nome, inq, stat=None):
    x = df[(df.stazione.str.startswith(nome)) & (df.inquinante == inq)]
    if stat: x = x[x.statistica == stat]
    return x.groupby("data").valore.mean()
W = pd.DataFrame({
    "Senato": ser(a, "Senato", "NO2", "media_giornaliera"), "Verziere": ser(a, "Verziere", "NO2", "media_giornaliera"),
    "Marche": ser(a, "Marche", "NO2", "media_giornaliera"), "Liguria": ser(a, "Liguria", "NO2", "media_giornaliera"),
    "C_Pioltello": ser(c, "Pioltello", "NO2"), "C_Magenta": ser(c, "Magenta", "NO2"), "C_Sesto": ser(c, "Sesto", "NO2"),
    "C_Rho": ser(c, "Rho", "NO2"), "C_Cinisello": ser(c, "Cinisello", "NO2"),
    "PM_Senato": ser(a, "Senato", "PM10"), "PM_Verziere": ser(a, "Verziere", "PM10"), "PM_Pascal": ser(a, "Pascal", "PM10"),
    "PM_C_Magenta": ser(c, "Magenta", "PM10"), "PM_C_Pioltello": ser(c, "Pioltello", "PM10")})
W.index = pd.to_datetime(W.index)
ctr = ["C_Pioltello", "C_Magenta", "C_Sesto", "C_Rho", "C_Cinisello"]
def gr(cols, nmin=None):
    x = W[cols]; nmin = len(cols) if nmin is None else nmin
    return x.mean(axis=1).where(x.notna().sum(axis=1) >= nmin)
D = pd.DataFrame({"in": gr(["Senato", "Verziere"]), "mi": gr(["Marche", "Liguria"]), "ct": gr(ctr, 4),
                  "pin": gr(["PM_Senato", "PM_Verziere"]), "ppa": gr(["PM_Pascal"]), "pct": gr(["PM_C_Magenta", "PM_C_Pioltello"])})
D["D_B"] = D["in"] - D["mi"]; D["D_C"] = D["in"] - D["ct"]
D["R_B"] = np.log(D["in"] / D["mi"]) * 100; D["R_C"] = np.log(D["in"] / D["ct"]) * 100
D["N_B"] = D["mi"]; D["N_C"] = D["ct"]; D["N_in"] = D["in"]
D["P_B"] = D["pin"] - D["ppa"]; D["P_C"] = D["pin"] - D["pct"]
fe = festivi(range(2003, 2021))
D = D[(D.index.dayofweek < 5) & ~D.index.isin(fe)]
D["sett"] = D.index.isocalendar().year.astype(str) + "-" + D.index.isocalendar().week.astype(str).str.zfill(2)
VAR = {"N_in": "NO2 media dentro (Senato, Verziere), ug/m3", "N_B": "NO2 media resto di Milano (Marche, Liguria), ug/m3", "N_C": "NO2 media fuori Milano (5 stazioni), ug/m3",
       "D_B": "NO2 dentro - resto di Milano (ug/m3)", "D_C": "NO2 dentro - fuori Milano (ug/m3)", "R_B": "NO2 dentro/resto di Milano (%)",
       "R_C": "NO2 dentro/fuori Milano (%)", "P_B": "PM10 dentro - Pascal (ug/m3)", "P_C": "PM10 dentro - fuori Milano (ug/m3)"}
def confronto(y0):
    """12 mesi che iniziano il 16/1 dell'anno y0 contro i 12 mesi seguenti. Restituisce dict variabile -> (media prima, media dopo, diff, se, n1, n2)"""
    a0, a1, b1 = pd.Timestamp(y0, 1, 16), pd.Timestamp(y0 + 1, 1, 16), pd.Timestamp(y0 + 2, 1, 16)
    S = D[(D.index >= a0) & (D.index < b1)].copy(); S["dopo"] = (S.index >= a1).astype(float)
    dw = dummies(S.assign(dw=S.index.dayofweek), ["dw"])
    res = {}
    for v in VAR:
        y = S[v]
        n1 = int(y[S.dopo == 0].notna().sum()); n2 = int(y[S.dopo == 1].notna().sum())
        if n1 < 100 or n2 < 100: continue
        r, n, G = ols_cluster(y, pd.concat([S[["dopo"]], dw], axis=1), S.sett)
        res[v] = (y[S.dopo == 0].mean(), y[S.dopo == 1].mean(), r.loc["dopo", "coef"], r.loc["dopo", "se"], n1, n2)
    return res
righe = []
for y0 in range(2005, 2019):
    res = confronto(y0)
    for v, (m0, m1, d, se, n1, n2) in res.items():
        righe.append(dict(prima_dal=f"16/1/{y0}", dopo_dal=f"16/1/{y0+1}", reale=(y0 == 2011), variabile=v, descrizione=VAR[v],
                          media_prima=round(m0, 2), media_dopo=round(m1, 2), differenza=round(d, 3), ci95_basso=round(d - 1.96 * se, 3),
                          ci95_alto=round(d + 1.96 * se, 3), differenza_percento=round(100 * d / m0, 1) if v in ("N_in", "N_B", "N_C") else np.nan,
                          giorni_prima=n1, giorni_dopo=n2))
R = pd.DataFrame(righe)
R.to_csv(os.path.join(cart, "prima_dopo_2012.csv"), sep=";", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
print(R[R.variabile.isin(["N_in", "N_B", "N_C", "D_B", "D_C", "R_B", "R_C", "P_B", "P_C"])].pivot_table(index="prima_dal", columns="variabile", values="differenza", sort=False).round(2).to_string())
r = R[R.reale]
print(r[["variabile", "media_prima", "media_dopo", "differenza", "ci95_basso", "ci95_alto", "differenza_percento", "giorni_prima", "giorni_dopo"]].to_string())
# posizione del cambio reale tra i cambi "placebo"
pl = R[~R.reale]
out = []
for v in ["D_B", "D_C", "R_B", "R_C", "P_B", "P_C"]:
    x = pl[pl.variabile == v].differenza; real = r[r.variabile == v].differenza.iloc[0]
    out.append(dict(variabile=v, descrizione=VAR[v], cambio_2012=real, placebo_n=len(x), placebo_media=round(x.mean(), 3), placebo_dev_std=round(x.std(), 3),
                    placebo_min=x.min(), placebo_max=x.max(), quanti_placebo_piu_estremi=int((x.abs() >= abs(real)).sum())))
pd.DataFrame(out).to_csv(os.path.join(cart, "prima_dopo_2012_placebo.csv"), sep=";", index=False)
print(pd.DataFrame(out).to_string())
D.reset_index().rename(columns={"index": "data"}).to_csv(os.path.join(cart, "pannello_2005_2019.csv"), sep=";", index=False, float_format="%.3f")

# ---- stessa stima con il meteo di Milano Lambrate (unico vento/pioggia/temperatura disponibili per il 2011-2014 in citta')
me = pd.read_csv(os.path.join(cart, "meteo_giornaliero.csv"), sep=";", parse_dates=["data"]).set_index("data")
D2 = D.join(me[["vento_Lambrate", "pioggia_Lambrate", "temperatura_Lambrate"]], how="left")
D2["v"] = D2.vento_Lambrate; D2["v2"] = D2.v ** 2; D2["p"] = (D2.pioggia_Lambrate >= 1).astype(float).where(D2.pioggia_Lambrate.notna()); D2["t"] = D2.temperatura_Lambrate
rows = []
for y0 in (2011,):
    a0, a1, b1 = pd.Timestamp(y0, 1, 16), pd.Timestamp(y0 + 1, 1, 16), pd.Timestamp(y0 + 2, 1, 16)
    S = D2[(D2.index >= a0) & (D2.index < b1)].copy(); S["dopo"] = (S.index >= a1).astype(float)
    S = S[S[["v", "p", "t"]].notna().all(axis=1)]          # stessi giorni con e senza meteo
    dw = dummies(S.assign(dw=S.index.dayofweek), ["dw"])
    for v in VAR:
        y = S[v]
        if y.notna().sum() < 100: continue
        r0, n0, G0 = ols_cluster(y, pd.concat([S[["dopo"]], dw], axis=1), S.sett)
        r1, n1, G1 = ols_cluster(y, pd.concat([S[["dopo", "v", "v2", "p", "t"]], dw], axis=1), S.sett)
        rows.append(dict(variabile=v, descrizione=VAR[v], senza_meteo=round(r0.loc["dopo", "coef"], 3), senza_ci_basso=round(r0.loc["dopo", "coef"] - 1.96 * r0.loc["dopo", "se"], 3),
                         senza_ci_alto=round(r0.loc["dopo", "coef"] + 1.96 * r0.loc["dopo", "se"], 3), senza_n=n0,
                         con_meteo=round(r1.loc["dopo", "coef"], 3), con_ci_basso=round(r1.loc["dopo", "coef"] - 1.96 * r1.loc["dopo", "se"], 3),
                         con_ci_alto=round(r1.loc["dopo", "coef"] + 1.96 * r1.loc["dopo", "se"], 3), con_n=n1))
M2 = pd.DataFrame(rows); M2.to_csv(os.path.join(cart, "prima_dopo_2012_con_meteo.csv"), sep=";", index=False)
print(M2.to_string())

# ---- medie mensili dei feriali 7/2010 - 6/2013 (per vedere se c'e' un gradino a gennaio 2012 o altro)
mm = D.loc["2010-07":"2013-06"].groupby(pd.Grouper(freq="MS"))[["N_in", "N_B", "N_C", "D_B", "D_C", "R_B", "P_B", "P_C"]].mean().round(2)
mm.index = mm.index.strftime("%Y-%m"); mm.to_csv(os.path.join(cart, "prima_dopo_2012_mensile.csv"), sep=";", index_label="mese")
