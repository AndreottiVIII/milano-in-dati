"""Fase 1 - passo 4: stesso metodo di analisi.py, ma per i 9 Municipi (decessi ufficiali per municipio + residenti ds29 del Comune).
Uso: python -I -X utf8 municipi.py <speranza-vita_dir> <milano-in-dati_dir>   (percorsi assoluti, si puo' rilanciare)
Scrive pulito/municipi_smr_e0.csv. Metodo e finestre identici a analisi.py (importato come testo: qui ripetuto in modo autonomo).
"""
import sys, os
import numpy as np, pandas as pd
from scipy.stats import chi2
SV, P = sys.argv[1], sys.argv[2]
PU = os.path.join(SV, "pulito")
ci = pd.read_csv(os.path.join(PU, "decessi_citta_anno_cl_sesso.csv"))
ISD = {(r.anno, r.cl_eta, r.sesso): r.decessi for r in ci.itertuples()}
d29 = pd.read_csv(os.path.join(P, "popolazione", "raw", "comune_ds29", "unzip", "ds29_pop_sto_zona.csv"), sep=";", dtype={"Eta": str})
d29["eta"] = d29.Eta.str.replace("100 e più", "100").astype(int)
d29["cl"] = np.where(d29.eta == 0, 0, np.where(d29.eta <= 4, 1, np.where(d29.eta >= 100, 21, d29.eta // 5 + 1)))
d29["s"] = np.where(d29.Genere == "Maschi", "M", "F")
pop = d29.groupby(["Anno", "Municipio", "s", "cl"]).Residenti.sum().to_dict()
def p31(a, i, s): return np.array([pop.get((a, i, s, c), 0) for c in range(22)], float)
def py(y, i, s): return p31(y, i, s) if y == 2012 else (p31(y - 1, i, s) + p31(y, i, s)) / 2
a = pd.read_csv(os.path.join(SV, "raw", "comune_ds131", "ds131-popolazione-residenti-decessi-municipio.csv"), sep=";", encoding="utf-8-sig").rename(columns={"Numerosita": "n"})
b = pd.read_csv(os.path.join(SV, "raw", "comune_ds1937", "ds1937_popolazione-residenti-decessi-zona.csv"), sep=";", encoding="utf-8-sig").rename(columns={"Numerosità": "n"})
dd = pd.concat([a, b]).dropna(subset=["Municipio"])
dd["s"] = np.where(dd.Genere == "Maschi", "M", "F")
OBS = dd.groupby(["Anno_evento", "Municipio", "s"]).n.sum().to_dict()
MUN = list(range(1, 10))
def e0_of(m, sesso):
    W = [1, 4] + [5] * 19; l = 1.0; e = 0.0
    for c in range(22):
        if c == 21: e += l / m[c]; break
        n = W[c]
        a_ = (0.045 + 2.684 * m[0] if sesso == "M" else 0.053 + 2.8 * m[0]) if c == 0 else ((1.651 - 2.816 * m[0] if sesso == "M" else 1.522 - 1.518 * m[0]) if c == 1 else n / 2)
        q = min(n * m[c] / (1 + (n - a_) * m[c]), 1.0); dth = l * q
        e += n * (l - dth) + a_ * dth; l -= dth
    return e
def gw(O, E):
    return (0.0 if O == 0 else chi2.ppf(0.025, 2 * O) / 2 / E), chi2.ppf(0.975, 2 * (O + 1)) / 2 / E
WIN = {"2013-2019": range(2013, 2020), "2022-2024": range(2022, 2025)}
rows = []
for wn, yrs in WIN.items():
    yrs = list(yrs); mc = {}; pyc = {}; Ec = {}; Oc = {}
    for s in "MF":
        pyc[s] = sum(py(y, i, s) for y in yrs for i in MUN)
        dth = np.array([sum(ISD.get((y, c, s), 0) for y in yrs) for c in range(22)], float)
        m = dth / pyc[s]
        E = {i: sum((m * py(y, i, s)).sum() for y in yrs) for i in MUN}
        O = {i: sum(OBS.get((y, i, s), 0) for y in yrs) for i in MUN}
        k = sum(O.values()) / sum(E.values())
        mc[s] = m * k; Ec[s] = {i: E[i] * k for i in MUN}; Oc[s] = O
    mc["T"] = (mc["M"] * pyc["M"] + mc["F"] * pyc["F"]) / (pyc["M"] + pyc["F"])
    for i in MUN:
        for s in "MFT":
            O = Oc["M"][i] + Oc["F"][i] if s == "T" else Oc[s][i]
            E = Ec["M"][i] + Ec["F"][i] if s == "T" else Ec[s][i]
            lo, hi = gw(O, E); sx = "F" if s == "T" else s
            res = np.mean([py(y, i, "M").sum() + py(y, i, "F").sum() for y in yrs])
            rows.append(dict(finestra=wn, municipio=i, sesso=s, osservati=O, attesi=E, smr=O / E, smr_lo=lo, smr_hi=hi,
                             e0=e0_of(mc[s] * O / E, sx), e0_lo=e0_of(mc[s] * hi, sx), e0_hi=e0_of(mc[s] * lo, sx), residenti_medi=res))
M = pd.DataFrame(rows)
# reddito medio dei NIL del municipio, pesato (indicativo): non si fa, i NIL non coincidono coi municipi
M.to_csv(os.path.join(PU, "municipi_smr_e0.csv"), index=False, float_format="%.5g")
pd.set_option("display.width", 200)
print(M[M.sesso == "T"].round(3).to_string())
print(M[M.sesso == "M"][["finestra", "municipio", "smr", "e0"]].round(2).to_string())
