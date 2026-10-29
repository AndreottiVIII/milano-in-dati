# Passo 2: ingressi giornalieri vs differenza dentro-fuori (giorni lavorativi 1/9/2016 - 30/11/2024).
# uso: python -I 02_regressioni.py <cartella legame_aria>
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
cart = sys.argv[1]
P = carica(os.path.join(cart, "pannello_giornaliero.csv"))
P["ingressi10k"] = P.ingressi / 10000.0
P["ing_piu7"] = P.ingressi10k.shift(-7, freq="D").reindex(P.index)   # placebo: ingressi di 7 giorni dopo (stesso giorno della settimana)
P["ing_meno7"] = P.ingressi10k.shift(7, freq="D").reindex(P.index)
for o in ["R_NO2m_B", "R_NO2m_C"]:
    P[o] = P[o] * 100   # differenza in log x 100 = percentuale (dentro rispetto a fuori)
covid = (P.index >= "2020-03-09") & (P.index <= "2021-06-08")
agosto = P.index.month == 8
natale = ((P.index.month == 12) & (P.index.day >= 24)) | ((P.index.month == 1) & (P.index.day <= 6))
P["normale"] = ~(covid | agosto | natale)
L = P[(P.lavorativo == 1) & P.ingressi.notna()].copy()
OUT = {"D_NO2m_B": "NO2 media, dentro - resto di Milano (ug/m3)", "D_NO2m_C": "NO2 media, dentro - fuori Milano (ug/m3)",
       "D_NO2x_B": "NO2 massimo orario, dentro - resto di Milano (ug/m3)", "R_NO2m_B": "NO2 media, dentro/resto di Milano (% )",
       "R_NO2m_C": "NO2 media, dentro/fuori Milano (%)", "D_PM10_B": "PM10, dentro - Pascal (ug/m3)", "D_PM10_C": "PM10, dentro - fuori Milano (ug/m3)",
       "D_PM25_B": "PM2.5, Senato - Pascal (ug/m3)", "D_BC_Pascal": "Black Carbon, Senato - Pascal (ug/m3), solo 9/2016-12/2017",
       "D_BC_Marche": "Black Carbon, Senato - Marche (ug/m3), solo 11/2020-11/2024"}
dow = dummies(L, ["dow"]); mese = dummies(L, ["mese"]); anno = dummies(L, ["anno"])
METEO = ["vento_B", "vento_B2", "pioggia_si", "temp_B", "vento_B_ieri", "pioggia_si_ieri"]
righe = []; resid_sc = {}
for nome_camp, camp in [("tutti i feriali", L.index == L.index), ("feriali normali (senza agosto, Natale, Covid)", L.normale.values)]:
    S = L[camp]
    for o, desc in OUT.items():
        y = S[o]
        if y.notna().sum() < 60: continue
        specs = {"1 solo ingressi": S[["ingressi10k"]],
                 "2 + giorno della settimana + mese": pd.concat([S[["ingressi10k"]], dow.loc[S.index], mese.loc[S.index]], axis=1),
                 "3 + anno (solo variazioni dentro lo stesso anno)": pd.concat([S[["ingressi10k"]], dow.loc[S.index], mese.loc[S.index], anno.loc[S.index]], axis=1),
                 "4 + meteo (vento, pioggia, temperatura di Brera, anche del giorno prima)": pd.concat([S[["ingressi10k"]], dow.loc[S.index], mese.loc[S.index], anno.loc[S.index], S[METEO]], axis=1)}
        rho, lo, hi, n = spearman_boot(S.ingressi10k, y, S.sett)
        Xr = pd.concat([dow.loc[S.index], mese.loc[S.index], anno.loc[S.index]], axis=1)
        ry = residualizza(y, Xr); rx = residualizza(S.ingressi10k, Xr)
        rho2, lo2, hi2, n2 = spearman_boot(rx, ry, S.sett)
        Xr2 = pd.concat([Xr, S[METEO]], axis=1)
        ry3 = residualizza(y, Xr2); rx3 = residualizza(S.ingressi10k, Xr2)
        rho3, lo3, hi3, n3 = spearman_boot(rx3, ry3, S.sett)
        for sn, X in specs.items():
            Xs = X.loc[:, ~(X.nunique() < 2)]
            res, nn, G = ols_cluster(y, Xs, S.sett)
            c, se = res.loc["ingressi10k", "coef"], res.loc["ingressi10k", "se"]
            l, h = ci95(c, se)
            righe.append(dict(campione=nome_camp, variabile=o, descrizione=desc, specifica=sn, n=nn, settimane=G,
                              effetto_per_10mila_ingressi=round(c, 4), ci95_basso=round(l, 4), ci95_alto=round(h, 4),
                              spearman_grezzo=round(rho, 3), sp_ci_basso=round(lo, 3), sp_ci_alto=round(hi, 3),
                              spearman_dopo_aver_tolto_giorno_mese_anno=round(rho2, 3), sp2_ci_basso=round(lo2, 3), sp2_ci_alto=round(hi2, 3),
                              spearman_dopo_aver_tolto_anche_meteo=round(rho3, 3), sp3_ci_basso=round(lo3, 3), sp3_ci_alto=round(hi3, 3),
                              ingressi_media=round(S.ingressi.mean()), ingressi_dev_std=round(S.ingressi.std()),
                              dev_std_differenza=round(y.std(), 3)))
        # placebo (specifica 3): ingressi di 7 giorni prima e dopo al posto di quelli del giorno
        for pn, pc in [("placebo: ingressi di 7 giorni dopo", "ing_piu7"), ("placebo: ingressi di 7 giorni prima", "ing_meno7")]:
            X = pd.concat([S[[pc]], dow.loc[S.index], mese.loc[S.index], anno.loc[S.index]], axis=1)
            X = X.loc[:, ~(X.nunique() < 2)]
            res, nn, G = ols_cluster(y, X, S.sett)
            c, se = res.loc[pc, "coef"], res.loc[pc, "se"]; l, h = ci95(c, se)
            righe.append(dict(campione=nome_camp, variabile=o, descrizione=desc, specifica="3 " + pn, n=nn, settimane=G,
                              effetto_per_10mila_ingressi=round(c, 4), ci95_basso=round(l, 4), ci95_alto=round(h, 4)))
R = pd.DataFrame(righe)
R.to_csv(os.path.join(cart, "regressioni.csv"), sep=";", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
v = R[R.specifica.str.startswith(("1", "2", "3", "4")) & ~R.specifica.str.contains("placebo")].copy()
print(v[["campione", "variabile", "specifica", "n", "effetto_per_10mila_ingressi", "ci95_basso", "ci95_alto", "spearman_grezzo", "spearman_dopo_aver_tolto_giorno_mese_anno"]].to_string())

# dati per il grafico a nuvola di punti (feriali normali, NO2 media dentro - resto di Milano)
S = L[L.normale & L.D_NO2m_B.notna()]
sc = S[["ingressi", "D_NO2m_B", "anno"]].copy(); sc["ingressi"] = sc.ingressi.round(-2).astype(int); sc["D_NO2m_B"] = sc.D_NO2m_B.round(1)
sc.reset_index().to_csv(os.path.join(cart, "scatter_NO2_B.csv"), sep=";", index=False)
