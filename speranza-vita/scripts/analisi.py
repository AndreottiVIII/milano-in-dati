"""Fase 1 - passo 2: standardizzazione indiretta (SMR) e speranza di vita stimata per NIL.
Uso: python -I -X utf8 analisi.py <speranza-vita_dir> <milano-in-dati_dir>   (percorsi assoluti, si puo' rilanciare)
Metodo (spiegato anche in NOTE.md):
 - Decessi per NIL x sesso x anno: Comune di Milano (ds137 + ds1940); NON hanno l'eta' per NIL.
 - Tassi per eta' della citta' (22 classi ISTAT) = decessi ISTAT di Milano / anni-persona del registro (ds27), per finestra e sesso.
 - Attesi del NIL = somma sulle classi (tasso citta' x anni-persona del NIL), riscalati in modo che gli attesi totali = decessi osservati totali del Comune.
 - SMR = osservati / attesi (1 = come la media della citta'). Intervallo al 95%: Poisson esatto (Garwood) sugli osservati.
 - Speranza di vita stimata: tavola abbreviata della citta' con tassi moltiplicati per l'SMR del NIL (stessa distanza proporzionale a tutte le eta').
 - Anni-persona dell'anno y = media dei residenti al 31/12 di y-1 e y (per il 2012: solo 31/12/2012, il registro ha un salto 2011->2012).
"""
import sys, os, math
import numpy as np, pandas as pd
from scipy.stats import chi2, spearmanr
SV, P = sys.argv[1], sys.argv[2]
PU = os.path.join(SV, "pulito")
dn = pd.read_csv(os.path.join(PU, "decessi_nil_anno_genere.csv"))
pp = pd.read_csv(os.path.join(PU, "residenti_nil_anno_cl_genere.csv"))
ci = pd.read_csv(os.path.join(PU, "decessi_citta_anno_cl_sesso.csv"))
ana = pd.read_csv(os.path.join(P, "popolazione", "pulito", "nil_anagrafica.csv"))
inc = pd.read_csv(os.path.join(P, "quartieri-che-cambiano", "out", "indicatori_nil.csv"))[["id_nil", "reddito_2024", "quota_civici_cap_instabili"]]
ids = list(ana.id_nil)
CL = list(range(22))
W = [1, 4] + [5] * 19 + [None]

pop = {}
for r in pp.itertuples():
    pop[(r.anno, r.id_nil, r.sesso, r.cl_eta)] = r.residenti
def P31(a, i, s):
    return np.array([pop.get((a, i, s, c), 0) for c in CL], float)
def PY(y, i, s):
    return P31(y, i, s) if y == 2012 else (P31(y - 1, i, s) + P31(y, i, s)) / 2
PYc = {(y, i, s): PY(y, i, s) for y in range(2012, 2025) for i in ids for s in "MF"}
OBS = {(r.anno, r.id_nil, r.sesso): r.decessi for r in dn.itertuples()}
ISD = {(r.anno, r.cl_eta, r.sesso): r.decessi for r in ci.itertuples()}

def e0_of(m, sesso):
    l = 1.0; e = 0.0
    for c in CL:
        mc = m[c]
        if c == 21:
            e += l / mc; break
        n = W[c]
        if c == 0:
            a = (0.045 + 2.684 * mc) if sesso == "M" else (0.053 + 2.8 * mc)
        elif c == 1:
            a = (1.651 - 2.816 * m[0]) if sesso == "M" else (1.522 - 1.518 * m[0])
        else:
            a = n / 2
        q = min(n * mc / (1 + (n - a) * mc), 1.0)
        d = l * q
        e += n * (l - d) + a * d
        l -= d
    return e

def garwood(O, E):
    lo = 0.0 if O == 0 else chi2.ppf(0.025, 2 * O) / 2 / E
    hi = chi2.ppf(0.975, 2 * (O + 1)) / 2 / E
    return lo, hi

WIN = {"2012-2015": range(2012, 2016), "2016-2019": range(2016, 2020), "2012-2019": range(2012, 2020),
       "2022-2024": range(2022, 2025), "2020": [2020], "2021": [2021]}
res = []; city = []; lt_city = {}
for wn, yrs in WIN.items():
    yrs = list(yrs)
    mc = {}; ECL = {}; OC = {}; pyCL = {}
    for s in "MF":
        pyCL[s] = sum(PYc[(y, i, s)] for y in yrs for i in ids)
        dd = np.array([sum(ISD.get((y, c, s), 0) for y in yrs) for c in CL], float)
        m = dd / pyCL[s]
        E = {i: sum((m * PYc[(y, i, s)]).sum() for y in yrs) for i in ids}
        O = {i: sum(OBS.get((y, i, s), 0) for y in yrs) for i in ids}
        k = sum(O.values()) / sum(E.values())
        ECL[s] = {i: E[i] * k for i in ids}; OC[s] = O
        mc[s] = m * k
        city.append(dict(finestra=wn, sesso=s, e0_citta=e0_of(mc[s], s), decessi=sum(O.values()), fattore_Comune_su_ISTAT=k))
    mT = (mc["M"] * pyCL["M"] + mc["F"] * pyCL["F"]) / (pyCL["M"] + pyCL["F"])
    lt_city[wn] = {"M": mc["M"], "F": mc["F"], "T": mT}
    city.append(dict(finestra=wn, sesso="T", e0_citta=e0_of(mT, "F"), decessi=sum(sum(OC[s].values()) for s in "MF"), fattore_Comune_su_ISTAT=np.nan))
    for i in ids:
        ra = {s: (OC[s][i], ECL[s][i]) for s in "MF"}
        ra["T"] = (ra["M"][0] + ra["F"][0], ra["M"][1] + ra["F"][1])
        pyi = sum(PYc[(y, i, s)].sum() for y in yrs for s in "MF") / len(yrs)
        for s in "MFT":
            O, E = ra[s]
            if E <= 0: continue
            smr = O / E; lo, hi = garwood(O, E)
            sx = "F" if s == "T" else s
            m0 = lt_city[wn][s]
            res.append(dict(finestra=wn, id_nil=i, sesso=s, osservati=O, attesi=E, smr=smr, smr_lo=lo, smr_hi=hi,
                            e0=e0_of(m0 * smr, sx), e0_lo=e0_of(m0 * hi, sx), e0_hi=e0_of(m0 * max(lo, 1e-3), sx), residenti_medi=pyi))
R = pd.DataFrame(res).merge(ana[["id_nil", "nil", "municipio_prevalente"]], on="id_nil")
R["e0_citta"] = [e0_of(lt_city[f][s], "F" if s == "T" else s) for f, s in zip(R.finestra, R.sesso)]
R["e0_diff"] = R.e0 - R.e0_citta

def shrink(g):
    g = g.copy(); x = g[g.residenti_medi >= 3000]
    var = x.smr.var(ddof=1); noise = (x.smr / x.attesi).mean()
    tau2 = max(var - noise, 1e-6); a = 1 / tau2
    g["smr_shrunk"] = (a + g.osservati) / (a + g.attesi)
    g["tau"] = math.sqrt(tau2)
    return g
R = pd.concat([shrink(g) for _, g in R.groupby(["finestra", "sesso"])], ignore_index=True)
R["e0_shrunk"] = [e0_of(lt_city[f][s] * v, "F" if s == "T" else s) for f, s, v in zip(R.finestra, R.sesso, R.smr_shrunk)]

# bandiere: poche persone, molti ultraottantacinquenni (possibili case di riposo: ipotesi, non verificata)
rows = []
tot24 = {a: sum((P31(a, i, "M") + P31(a, i, "F")) for i in ids) for a in (2019, 2024)}
c85 = {a: tot24[a][18:].sum() / tot24[a].sum() for a in tot24}
for i in ids:
    r = dict(id_nil=i)
    for a in (2019, 2024):
        v = P31(a, i, "M") + P31(a, i, "F")
        r[f"residenti_{a}"] = v.sum(); r[f"quota_85piu_{a}"] = v[18:].sum() / v.sum() if v.sum() else np.nan
    rows.append(dict(r, quota_85piu_citta_2024=c85[2024], quota_85piu_citta_2019=c85[2019]))
fl = pd.DataFrame(rows)
fl["rapporto_85piu_2024"] = fl.quota_85piu_2024 / fl.quota_85piu_citta_2024
fl["piccolo_sotto_3000"] = fl.residenti_2024 < 3000
fl["molti_85piu"] = fl.rapporto_85piu_2024 >= 1.5
R = R.merge(fl[["id_nil", "piccolo_sotto_3000", "molti_85piu", "rapporto_85piu_2024"]], on="id_nil").merge(inc, on="id_nil")
R.to_csv(os.path.join(PU, "nil_smr_e0.csv"), index=False, float_format="%.5g")
pd.DataFrame(city).to_csv(os.path.join(PU, "citta_e0_finestre.csv"), index=False, float_format="%.5g")
fl.to_csv(os.path.join(PU, "nil_bandiere_residenze.csv"), index=False, float_format="%.5g")
print("tau per finestra/sesso:", R.groupby(["finestra", "sesso"]).tau.first().round(3).to_dict())

# quintili di reddito (pesati per residenti; NIL con >= 3.000 residenti)
e = R[(R.finestra == "2012-2019") & (R.sesso == "T")][["id_nil", "nil", "reddito_2024", "residenti_medi", "piccolo_sotto_3000"]].copy()
e = e[~e.piccolo_sotto_3000].sort_values("reddito_2024")
e["cum"] = e.residenti_medi.cumsum() / e.residenti_medi.sum()
e["quintile"] = np.minimum(np.ceil(e.cum * 5 - 1e-9), 5).astype(int)
Q = dict(zip(e.id_nil, e.quintile))
grp = []
for wn in WIN:
    sub = R[R.finestra == wn]
    for q in range(1, 6):
        for s in "MFT":
            x = sub[(sub.sesso == s) & sub.id_nil.isin([i for i, v in Q.items() if v == q])]
            O, E = x.osservati.sum(), x.attesi.sum()
            smr = O / E; lo, hi = garwood(O, E); m0 = lt_city[wn][s]; sx = "F" if s == "T" else s
            grp.append(dict(finestra=wn, quintile=q, sesso=s, n_nil=len(x), residenti=x.residenti_medi.sum(), osservati=O, attesi=E,
                            smr=smr, smr_lo=lo, smr_hi=hi, e0=e0_of(m0 * smr, sx), e0_lo=e0_of(m0 * hi, sx), e0_hi=e0_of(m0 * max(lo, 1e-3), sx),
                            reddito_min=x.reddito_2024.min(), reddito_max=x.reddito_2024.max()))
G = pd.DataFrame(grp); G.to_csv(os.path.join(PU, "gruppi_reddito.csv"), index=False, float_format="%.5g")
e[["id_nil", "nil", "quintile", "reddito_2024"]].to_csv(os.path.join(PU, "quintili_reddito_nil.csv"), index=False)

cor = []
for wn in WIN:
    for s in "MFT":
        x = R[(R.finestra == wn) & (R.sesso == s) & ~R.piccolo_sotto_3000].dropna(subset=["reddito_2024"])
        rho, p = spearmanr(x.reddito_2024, x.smr)
        rng = np.random.default_rng(1); bs = []
        for _ in range(2000):
            j = rng.integers(0, len(x), len(x)); bs.append(spearmanr(x.reddito_2024.values[j], x.smr.values[j])[0])
        cor.append(dict(finestra=wn, sesso=s, n_nil=len(x), spearman=rho, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
C = pd.DataFrame(cor); C.to_csv(os.path.join(PU, "correlazione_reddito_smr.csv"), index=False, float_format="%.4g")

# citta' anno per anno: e0 con decessi ISTAT / registro, e confronto con BES (provincia)
yr = []
for y in range(2012, 2025):
    row = dict(anno=y)
    for s in "MF":
        py = sum(PYc[(y, i, s)] for i in ids)
        row["e0_" + s] = e0_of(np.array([ISD.get((y, c, s), 0) for c in CL], float) / py, s)
    pT = sum(sum(PYc[(y, i, s)] for i in ids) for s in "MF")
    dd = np.array([ISD.get((y, c, "M"), 0) + ISD.get((y, c, "F"), 0) for c in CL], float)
    row["e0_T"] = e0_of(dd / pT, "F"); row["decessi_istat"] = dd.sum(); row["residenti_py"] = pT.sum()
    row["decessi_comune"] = sum(OBS.get((y, i, s), 0) for i in ids for s in "MF")
    yr.append(row)
Y = pd.DataFrame(yr)
bes = pd.read_csv(os.path.join(P, "benessere", "pulito", "bes_lungo.csv"), low_memory=False)
bes = bes[(bes.codice == "01SAL001") & bes.territorio.isin(["Milano", "Lombardia", "Italia"]) & (bes.edizione == bes.edizione.max())]
bp = bes.pivot_table(index="anno", columns=["territorio", "sesso"], values="valore")
bp.columns = [f"bes_{a}_{b}" for a, b in bp.columns]
bp = bp.reset_index(); bp.to_csv(os.path.join(PU, "bes_e0_milano_lombardia_italia.csv"), index=False)
Y = Y.merge(bp, on="anno", how="left")
Y.to_csv(os.path.join(PU, "citta_e0_annuale.csv"), index=False, float_format="%.5g")
pd.set_option("display.width", 250)
print(Y.round(2).to_string())
print(pd.DataFrame(city).round(3).to_string())
print(G[G.sesso == "T"].round(3).to_string())
print(C.to_string())
