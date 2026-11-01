"""Fase 1 - passo 3: controlli di robustezza dell'SMR per NIL (finestra 2012-2019, sessi uniti).
Uso: python -I -X utf8 sensibilita.py <speranza-vita_dir> <milano-in-dati_dir>   (percorsi assoluti, si puo' rilanciare)
 A. Solo residenti con cittadinanza italiana (decessi 'Italiana' / anni-persona dei cittadini 'Italia', ds27 grezzo): l'SMR cambia?
 B. Senza i NIL con segnali di residenza collettiva (Morivione) e senza i NIL con meno di 3.000 residenti.
 C. Quintili di reddito: gap con e senza i NIL segnalati.
 D. Stabilita' tra finestre (correlazione di rango 2012-2015 / 2016-2019 / 2022-2024).
Scrive pulito/sensibilita.json.
"""
import sys, os, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr, chi2
SV, P = sys.argv[1], sys.argv[2]
PU = os.path.join(SV, "pulito")
R = pd.read_csv(os.path.join(PU, "nil_smr_e0.csv"))
dn = pd.read_csv(os.path.join(PU, "decessi_nil_anno_genere.csv"))
ci = pd.read_csv(os.path.join(PU, "decessi_citta_anno_cl_sesso.csv"))
ids = sorted(R.id_nil.unique())
src = os.path.join(P, "popolazione", "raw", "comune_ds27", "unzip", "ds27_pop_sto_quartiere.csv")
df = pd.read_csv(src, sep=";", dtype={"Eta": str, "Cittadinanza": str, "Nil": str})
df["eta"] = df.Eta.str.replace("100 e più", "100").astype(int)
df = df[df.Cittadinanza == "Italia"]
df["cl"] = np.where(df.eta == 0, 0, np.where(df.eta <= 4, 1, np.where(df.eta >= 100, 21, df.eta // 5 + 1)))
df["s"] = np.where(df.Genere == "Maschi", "M", "F")
pit = df.groupby(["Anno", "IdNil", "s", "cl"]).Residenti.sum().to_dict()
def p31(a, i, s): return np.array([pit.get((a, i, s, c), 0) for c in range(22)], float)
def py(y, i, s): return p31(y, i, s) if y == 2012 else (p31(y - 1, i, s) + p31(y, i, s)) / 2
yrs = range(2012, 2020)
ISD = {(r.anno, r.cl_eta, r.sesso): r.decessi for r in ci.itertuples()}
E = {i: 0.0 for i in ids}; O = {i: 0 for i in ids}
for s in "MF":
    PYs = {(y, i): py(y, i, s) for y in yrs for i in ids}
    tot = sum(PYs[k] for k in PYs)
    # tassi: decessi ISTAT di tutta la citta' / anni-persona di tutta la citta' (qui solo italiani al denominatore -> si usa un fattore interno)
    m = np.array([sum(ISD.get((y, c, s), 0) for y in yrs) for c in range(22)], float) / tot
    for i in ids:
        E[i] += sum((m * PYs[(y, i)]).sum() for y in yrs)
        O[i] += int(dn[(dn.id_nil == i) & (dn.sesso == s) & dn.anno.isin(list(yrs))].di_cui_italiani.sum())
k = sum(O.values()) / sum(E.values())
IT = pd.DataFrame({"id_nil": ids, "oss_it": [O[i] for i in ids], "att_it": [E[i] * k for i in ids]})
IT["smr_it"] = IT.oss_it / IT.att_it
M = R[(R.finestra == "2012-2019") & (R.sesso == "T")].merge(IT, on="id_nil")
ok = M[~M.piccolo_sotto_3000]
out = {}
rho = spearmanr(ok.smr, ok.smr_it)[0]
out["A_spearman_smr_tutti_vs_solo_italiani"] = round(float(rho), 3)
out["A_pearson"] = round(float(np.corrcoef(ok.smr, ok.smr_it)[0, 1]), 3)
d = (ok.smr_it - ok.smr)
out["A_differenza_media_smr_italiani_meno_tutti"] = round(float(d.mean()), 4)
out["A_nil_con_maggior_differenza"] = ok.assign(d=d).sort_values("d", key=abs, ascending=False)[["nil", "smr", "smr_it", "d"]].head(6).round(3).to_dict("records")
out["A_spearman_reddito_smr_italiani"] = round(float(spearmanr(ok.reddito_2024, ok.smr_it)[0]), 3)
# B/C: quintili con e senza Morivione
Qf = pd.read_csv(os.path.join(PU, "quintili_reddito_nil.csv"))
G = M[~M.piccolo_sotto_3000].merge(Qf[["id_nil", "quintile"]], on="id_nil")
def quint(g):
    r = {}
    for q in (1, 5):
        x = g[g.quintile == q]; r[q] = x.osservati.sum() / x.attesi.sum()
    return r
a = quint(G); b = quint(G[G.id_nil != 37])
out["C_smr_quintile1_e_5_con_Morivione"] = {k: round(v, 4) for k, v in a.items()}
out["C_smr_quintile1_e_5_senza_Morivione"] = {k: round(v, 4) for k, v in b.items()}
out["B_spearman_reddito_smr_senza_Morivione"] = round(float(spearmanr(G[G.id_nil != 37].reddito_2024, G[G.id_nil != 37].smr)[0]), 3)
# D stabilita' tra finestre
x = R[(R.sesso == "T") & R.finestra.isin(["2012-2015", "2016-2019", "2022-2024"]) & ~R.piccolo_sotto_3000].pivot(index="nil", columns="finestra", values="smr")
out["D_spearman_2012_2015_vs_2022_2024"] = round(float(x.corr(method="spearman").loc["2012-2015", "2022-2024"]), 3)
out["D_spearman_2016_2019_vs_2022_2024"] = round(float(x.corr(method="spearman").loc["2016-2019", "2022-2024"]), 3)
out["D_spearman_2012_2015_vs_2016_2019"] = round(float(x.corr(method="spearman").loc["2012-2015", "2016-2019"]), 3)
# E: quanti NIL (>=3.000 residenti) hanno intervallo che esclude 1
z = R[(R.finestra == "2012-2019") & (R.sesso == "T") & ~R.piccolo_sotto_3000]
out["E_nil_analizzabili"] = int(len(z)); out["E_sotto_la_media_intervallo_esclude_1"] = int((z.smr_hi < 1).sum()); out["E_sopra_la_media_intervallo_esclude_1"] = int((z.smr_lo > 1).sum())
z2 = R[(R.finestra == "2022-2024") & (R.sesso == "T") & ~R.piccolo_sotto_3000]
out["E_2022_2024_sotto"] = int((z2.smr_hi < 1).sum()); out["E_2022_2024_sopra"] = int((z2.smr_lo > 1).sum())
json.dump(out, open(os.path.join(PU, "sensibilita.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
