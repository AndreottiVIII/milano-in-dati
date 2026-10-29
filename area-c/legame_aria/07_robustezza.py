# Passo 7: robustezza: la stessa stima (ingressi per 10.000, con giorno della settimana, mese, anno e meteo) per ogni coppia di stazioni.
# uso: python -I 07_robustezza.py <cartella legame_aria>
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
cart = sys.argv[1]
P = carica(os.path.join(cart, "pannello_giornaliero.csv")); P["ingressi10k"] = P.ingressi / 10000.0
covid = (P.index >= "2020-03-09") & (P.index <= "2021-06-08")
P["normale"] = ~(covid | (P.index.month == 8) | ((P.index.month == 12) & (P.index.day >= 24)) | ((P.index.month == 1) & (P.index.day <= 6)))
L = P[(P.lavorativo == 1) & P.ingressi.notna() & P.normale].copy()
METEO = ["vento_B", "vento_B2", "pioggia_si", "temp_B", "vento_B_ieri", "pioggia_si_ieri"]
X0 = pd.concat([L[["ingressi10k"]], dummies(L, ["dow"]), dummies(L, ["mese"]), dummies(L, ["anno"]), L[METEO]], axis=1)
righe = []
for i in ["Senato", "Verziere"]:
    for o in ["Marche", "Liguria", "Pascal", "controllo"]:
        col_o = "NO2m_controllo" if o == "controllo" else f"NO2m_{o}"
        y = L[f"NO2m_{i}"] - L[col_o]
        res, n, G = ols_cluster(y, X0, L.sett)
        c, se = res.loc["ingressi10k", "coef"], res.loc["ingressi10k", "se"]
        righe.append(dict(dentro=i, fuori=("5 stazioni fuori Milano" if o == "controllo" else o), n=n, effetto_per_10mila_ingressi=round(c, 3),
                          ci95_basso=round(c - 1.96 * se, 3), ci95_alto=round(c + 1.96 * se, 3), dev_std_differenza=round(y.std(), 2)))
R = pd.DataFrame(righe); R.to_csv(os.path.join(cart, "robustezza_coppie.csv"), sep=";", index=False); print(R.to_string())
