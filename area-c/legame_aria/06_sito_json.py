# Passo 6: prepara i dati piccoli per la pagina del sito (docs/area-c/data/legame_aria.json) e il file dei numeri chiave.
# uso: python -I 06_sito_json.py <cartella legame_aria> <file json di uscita>
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
cart, outf = sys.argv[1], sys.argv[2]
def r(x, d=2):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)
P = carica(os.path.join(cart, "pannello_giornaliero.csv"))
covid = (P.index >= "2020-03-09") & (P.index <= "2021-06-08")
normale = ~(covid | (P.index.month == 8) | ((P.index.month == 12) & (P.index.day >= 24)) | ((P.index.month == 1) & (P.index.day <= 6)))
L = P[(P.lavorativo == 1) & P.ingressi.notna()]
S = L[normale[(P.lavorativo == 1) & P.ingressi.notna()] & L.D_NO2m_B.notna()]
# --- nuvola di punti + medie per fasce di ingressi (7 fasce con lo stesso numero di giorni), intervallo con bootstrap sulle settimane
fasce = pd.qcut(S.ingressi, 7, labels=False)
rng = np.random.default_rng(3); bins = []
for f in range(7):
    X = S[fasce == f]; sett = X.sett.unique(); idx = {k: X.D_NO2m_B.values[(X.sett == k).values] for k in sett}
    bm = [np.concatenate([idx[k] for k in rng.choice(sett, len(sett))]).mean() for _ in range(1000)]
    bins.append(dict(x=r(X.ingressi.mean() / 1000, 1), y=r(X.D_NO2m_B.mean()), lo=r(np.percentile(bm, 2.5)), hi=r(np.percentile(bm, 97.5)), n=int(len(X))))
sc = dict(x=[r(v / 1000, 1) for v in S.ingressi], y=[r(v, 1) for v in S.D_NO2m_B], anno=[int(a) for a in S.anno], fasce=bins)
# --- serie mensile
M = pd.read_csv(os.path.join(cart, "tendenza_mensile.csv"), sep=";")
serie = dict(mesi=M.mese.tolist(), ingressi=[r(v / 1000, 1) for v in M.ingressi], D_B=[r(v, 2) for v in M.D_NO2m_B], D_C=[r(v, 2) for v in M.D_NO2m_C])
A = pd.read_csv(os.path.join(cart, "tendenza_annuale.csv"), sep=";")
annuale = A.replace({np.nan: None}).to_dict("records")
corr = pd.read_csv(os.path.join(cart, "tendenza_correlazioni.csv"), sep=";").replace({np.nan: None}).to_dict("records")
# --- esperimenti naturali (media dei giorni dell'evento contro quelli di riferimento)
E0 = pd.read_csv(os.path.join(cart, "esperimenti_naturali.csv"), sep=";"); E1 = pd.read_csv(os.path.join(cart, "esperimenti_naturali_meteo.csv"), sep=";")
VARS = ["ingressi10k", "D_NO2m_B", "R_NO2m_B", "D_NO2m_C", "D_NO2x_B", "D_PM10_B", "D_PM25_B", "D_BC_Marche"]
import re
principali = [e for e in E0.esperimento.unique() if not re.search(r"\d{4}(/\d{4})?$", e)]
def riga(E, nome):
    d = {}
    for v in VARS:
        x = E[(E.esperimento == nome) & (E.variabile == v)]
        if len(x): d[v] = dict(d=r(x.differenza.iloc[0], 2), lo=r(x.ci95_basso.iloc[0], 2), hi=r(x.ci95_alto.iloc[0], 2), ne=int(x.giorni_evento.iloc[0]), nr=int(x.giorni_riferimento.iloc[0]))
    return d
esper = [dict(nome=n, senza=riga(E0, n), con=riga(E1, n), nota=E0[E0.esperimento == n].nota.iloc[0]) for n in principali]
per_anno = {}
for pre in ("Agosto (8-23 agosto)", "Natale (27 dic-5 gen)"):
    per_anno[pre] = [dict(nome=n.replace(pre + " ", ""), ing=riga(E0, n).get("ingressi10k"), DB=riga(E0, n).get("D_NO2m_B"), RB=riga(E0, n).get("R_NO2m_B"), DC=riga(E0, n).get("D_NO2m_C"))
                     for n in E0.esperimento.unique() if n.startswith(pre + " ")]
# --- regressioni (le righe principali)
R = pd.read_csv(os.path.join(cart, "regressioni.csv"), sep=";")
reg = R[~R.specifica.str.contains("placebo")].replace({np.nan: None}).to_dict("records")
plac = R[R.specifica.str.contains("placebo")].replace({np.nan: None}).to_dict("records")
# --- prima/dopo 2012
PD = pd.read_csv(os.path.join(cart, "prima_dopo_2012.csv"), sep=";"); PL = pd.read_csv(os.path.join(cart, "prima_dopo_2012_placebo.csv"), sep=";")
pd2012 = dict(reale=PD[PD.reale].replace({np.nan: None}).to_dict("records"), placebo=PL.replace({np.nan: None}).to_dict("records"),
              placebo_anni=PD[~PD.reale & PD.variabile.isin(["D_B", "D_C", "P_B", "P_C"])][["prima_dal", "variabile", "differenza"]].to_dict("records"),
              con_meteo=pd.read_csv(os.path.join(cart, "prima_dopo_2012_con_meteo.csv"), sep=";").replace({np.nan: None}).to_dict("records"))
cop = pd.read_csv(os.path.join(cart, "copertura.csv"), sep=";").replace({np.nan: None}).to_dict("records")
J = dict(scatter=sc, serie=serie, annuale=annuale, correlazioni=corr, esperimenti=esper, per_anno=per_anno, regressioni=reg, placebo=plac, prima_dopo_2012=pd2012, copertura=cop,
         ingressi_normali=dict(media=r(S.ingressi.mean(), 0), dev_std=r(S.ingressi.std(), 0)))
os.makedirs(os.path.dirname(outf), exist_ok=True)
json.dump(J, open(outf, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("scritto", outf, round(os.path.getsize(outf) / 1024), "KB")
print(esper[0]["nome"], [e["nome"] for e in esper])
print(bins)
