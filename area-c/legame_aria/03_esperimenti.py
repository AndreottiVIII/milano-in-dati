# Passo 3: "esperimenti naturali": periodi con pochissimi ingressi (agosto, Natale, ponti, Covid) contro giorni normali vicini.
# uso: python -I 03_esperimenti.py <cartella legame_aria>
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
cart = sys.argv[1]
METEO_ON = len(sys.argv) > 2 and sys.argv[2] == "meteo"
METEO = ["vento_B", "vento_B2", "pioggia_si", "temp_B"]
P = carica(os.path.join(cart, "pannello_giornaliero.csv"))
P["ingressi10k"] = P.ingressi / 10000.0
for o in ["R_NO2m_B", "R_NO2m_C"]: P[o] = P[o] * 100
L = P[(P.lavorativo == 1) & P.ingressi.notna()].copy()
OUT = ["ingressi10k", "D_NO2m_B", "D_NO2m_C", "R_NO2m_B", "R_NO2m_C", "D_NO2x_B", "D_PM10_B", "D_PM10_C", "D_PM25_B", "D_BC_Marche"]
T = pd.Timestamp

def finestra(anni, a, b):   # (mese,giorno) -> intervallo nel stesso anno
    return [(T(y, *a), T(y, *b)) for y in anni]

def sel(L, intervalli):
    m = pd.Series(False, index=L.index)
    for a, b in intervalli: m |= (L.index >= a) & (L.index <= b)
    return m

eventi = []
# 1) agosto: 8-23 agosto contro 27/6-25/7 e 6/9-4/10 dello stesso anno
anni = range(2017, 2025)
eventi.append(dict(nome="Agosto (8-23 agosto)", ev=finestra(anni, (8, 8), (8, 23)),
                   rif=finestra(anni, (6, 27), (7, 25)) + finestra(anni, (9, 6), (10, 4)), per_anno=True,
                   nota="rif.: 27 giu-25 lug e 6 set-4 ott dello stesso anno"))
# 2) Natale: 27/12-5/1 contro 15/11-13/12 e 12/1-9/2
ev = [(T(y, 12, 27), T(y + 1, 1, 5)) for y in range(2016, 2024)]
rf = [(T(y, 11, 15), T(y, 12, 13)) for y in range(2016, 2024)] + [(T(y + 1, 1, 12), T(y + 1, 2, 9)) for y in range(2016, 2024)]
eventi.append(dict(nome="Natale (27 dic-5 gen)", ev=ev, rif=rf, per_anno=True, nota="rif.: 15 nov-13 dic e 12 gen-9 feb"))
# 3) ponti: venerdi dopo festivo di giovedi e lunedi prima di festivo di martedi
fest = set(P.index[(P.lavorativo == 0) & (P.index.dayofweek < 5)])
ponti = [d for d in L.index if (d.dayofweek == 4 and d - pd.Timedelta(days=1) in fest) or (d.dayofweek == 0 and d + pd.Timedelta(days=1) in fest)]
pt = pd.DataFrame(index=L.index); pt["ponte"] = L.index.isin(ponti)
# riferimento: stesso giorno della settimana nelle 3 settimane prima e dopo, se non e' ponte/festivo/agosto/Natale/Covid
# 4) Covid: stesse date nel 2018 e 2019
cov = [("Covid, lockdown stretto (12/3-3/5/2020)", (3, 12), (5, 3), 2020),
       ("Covid, riaperture, Area C sospesa (4/5-14/6/2020)", (5, 4), (6, 14), 2020),
       ("Covid, seconda sospensione (5/11/2020-23/2/2021)", None, None, None),
       ("Covid, Area C con orario ridotto (24/2-8/6/2021)", (2, 24), (6, 8), 2021)]

def stima(S, evcol, extra_cols):
    """differenza media evento-riferimento, tolto l'effetto del giorno della settimana (e dell'anno); errori a grappoli per settimana"""
    res = {}
    base = pd.concat([S[[evcol]], dummies(S, ["dow"])] + extra_cols + ([S[METEO]] if METEO_ON else []), axis=1)
    base = base.loc[:, ~((base.nunique() < 2) & (base.columns != evcol))]
    for o in OUT:
        y = S[o]
        if y[S[evcol] == 1].notna().sum() < 5 or y[S[evcol] == 0].notna().sum() < 10:
            res[o] = None; continue
        r, n, G = ols_cluster(y, base, S.sett)
        c, se = r.loc[evcol, "coef"], r.loc[evcol, "se"]
        res[o] = (c, se, int(((S[evcol] == 1) & y.notna()).sum()), int(((S[evcol] == 0) & y.notna()).sum()))
    return res

righe = []
def aggiungi(nome, nota, res, mean_ev, mean_rif):
    for o, v in res.items():
        if v is None: continue
        c, se, ne, nr = v
        l, h = ci95(c, se)
        righe.append(dict(esperimento=nome, nota=nota, variabile=o, differenza=round(c, 3), ci95_basso=round(l, 3), ci95_alto=round(h, 3),
                          giorni_evento=ne, giorni_riferimento=nr, media_evento=round(mean_ev[o], 3), media_riferimento=round(mean_rif[o], 3)))

for e in eventi:
    m_ev = sel(L, e["ev"]); m_rf = sel(L, e["rif"]) & ~m_ev
    S = L[m_ev | m_rf].copy(); S["evento"] = m_ev[S.index].astype(float)
    S["blocco"] = S.index.year   # una finestra di riferimento per anno
    if e["nome"].startswith("Natale"):
        S["blocco"] = np.where(S.index.month >= 7, S.index.year, S.index.year - 1)
    ex = [dummies(S, ["blocco"])]
    res = stima(S, "evento", ex)
    aggiungi(e["nome"], e["nota"], res, S[S.evento == 1][OUT].mean(), S[S.evento == 0][OUT].mean())
    if e["per_anno"]:
        for b, Sb in S.groupby("blocco"):
            if (Sb.evento == 1).sum() < 3: continue
            res = stima(Sb, "evento", [])
            lab = f"{e['nome']} {b}" + (f"/{b+1}" if e["nome"].startswith("Natale") else "")
            aggiungi(lab, "singolo anno (pochi giorni: intervalli poco affidabili)", res, Sb[Sb.evento == 1][OUT].mean(), Sb[Sb.evento == 0][OUT].mean())

# ponti
m_ev = L.index.isin(ponti)
spec = ~(((L.index.month == 8)) | ((L.index.month == 12) & (L.index.day >= 24)) | ((L.index.month == 1) & (L.index.day <= 6)) | ((L.index >= "2020-03-09") & (L.index <= "2021-06-08")))
rif_idx = []
for d in L.index[m_ev & spec]:
    for k in list(range(-21, 0, 7)) + list(range(7, 22, 7)):
        dd = d + pd.Timedelta(days=k)
        if dd in L.index and dd not in ponti and spec[L.index.get_loc(dd)]: rif_idx.append(dd)
rif_idx = sorted(set(rif_idx))
S = L.loc[sorted(set(rif_idx) | set(L.index[m_ev & spec]))].copy(); S["evento"] = S.index.isin(ponti).astype(float)
S["blocco"] = S.index.year
res = stima(S, "evento", [dummies(S, ["blocco"])])
aggiungi("Ponti (venerdi dopo festivo di giovedi, lunedi prima di festivo di martedi)", "rif.: stesso giorno della settimana, 3 sett. prima e 3 dopo", res, S[S.evento == 1][OUT].mean(), S[S.evento == 0][OUT].mean())

# covid
for nome, a, b, anno in cov:
    if a is None:
        ev = [(T(2020, 11, 5), T(2021, 2, 23))]
        rf = [(T(2018, 11, 5), T(2019, 2, 23)), (T(2019, 11, 5), T(2020, 2, 23))]
    else:
        ev = [(T(anno, *a), T(anno, *b))]
        rf = [(T(2018, *a), T(2018, *b)), (T(2019, *a), T(2019, *b))]
    m_ev = sel(L, ev); m_rf = sel(L, rf)
    S = L[m_ev | m_rf].copy(); S["evento"] = m_ev[S.index].astype(float)
    res = stima(S, "evento", [])
    aggiungi(nome, "rif.: stesse date nel 2018-19 (2019-20 per l'inverno): c'e' anche la tendenza di fondo", res, S[S.evento == 1][OUT].mean(), S[S.evento == 0][OUT].mean())

R = pd.DataFrame(righe)
R.to_csv(os.path.join(cart, "esperimenti_naturali_meteo.csv" if METEO_ON else "esperimenti_naturali.csv"), sep=";", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 500)
for nome in R.esperimento.unique():
    if any(nome.startswith(x) for x in ["Agosto 2", "Natale (27) 2"]): pass
x = R[~R.esperimento.str.contains(r"Agosto \(8-23 agosto\) \d|Natale \(27 dic-5 gen\) \d", regex=True)]
print(x.pivot_table(index="esperimento", columns="variabile", values="differenza", sort=False).round(2).to_string())
print(x[x.variabile.isin(["ingressi10k", "D_NO2m_B", "R_NO2m_B", "D_NO2m_C"])][["esperimento", "variabile", "differenza", "ci95_basso", "ci95_alto", "giorni_evento", "giorni_riferimento"]].to_string())
