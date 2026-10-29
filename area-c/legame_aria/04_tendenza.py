# Passo 4: tendenza 2016-2024, ingressi contro differenza dentro-fuori (mensile e annuale), solo feriali.
# uso: python -I 04_tendenza.py <cartella legame_aria>
import sys, os, numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
cart = sys.argv[1]
P = carica(os.path.join(cart, "pannello_giornaliero.csv"))
for o in ["R_NO2m_B", "R_NO2m_C"]: P[o] = P[o] * 100
L = P[(P.lavorativo == 1) & P.ingressi.notna() & ~((P.index >= "2020-03-09") & (P.index <= "2021-06-08"))].copy()   # senza il periodo Covid
L["ym"] = L.index.to_period("M")
cols = ["ingressi", "NO2m_dentro", "NO2m_fuoriAC", "NO2m_controllo", "D_NO2m_B", "D_NO2m_C", "R_NO2m_B", "R_NO2m_C", "D_PM10_B", "D_PM10_C"]
M = L.groupby("ym")[cols].mean()
M["giorni_ingressi"] = L.groupby("ym").ingressi.count()
M["giorni_DB"] = L.groupby("ym").D_NO2m_B.count()
M["giorni_DC"] = L.groupby("ym").D_NO2m_C.count()
M.loc[M.giorni_DB < 8, ["D_NO2m_B", "R_NO2m_B"]] = np.nan
M.loc[M.giorni_DC < 8, ["D_NO2m_C", "R_NO2m_C"]] = np.nan
M = M.reindex(pd.period_range("2016-09", "2024-11", freq="M"))   # mesi senza giorni (Covid) restano vuoti: l'asse del tempo resta corretto
M = M.round(3); M.index = M.index.astype(str)
M.to_csv(os.path.join(cart, "tendenza_mensile.csv"), sep=";", index_label="mese")

# annuale: tutti i feriali e solo settembre-novembre (unici mesi presenti in tutti gli anni)
righe = []
for nome, S in [("feriali dell'anno (senza Covid 3/2020-6/2021)", L), ("feriali di settembre-novembre", L[L.index.month.isin([9, 10, 11])])]:
    g = S.groupby("anno")
    A = g[cols].mean(); A["giorni_DB"] = g.D_NO2m_B.count(); A["giorni_DC"] = g.D_NO2m_C.count(); A["giorni_ingressi"] = g.ingressi.count()
    A.insert(0, "campione", nome)
    righe.append(A.reset_index())
A = pd.concat(righe).round(3)
A.to_csv(os.path.join(cart, "tendenza_annuale.csv"), sep=";", index=False)
print(A[["campione", "anno", "ingressi", "NO2m_dentro", "NO2m_fuoriAC", "NO2m_controllo", "D_NO2m_B", "D_NO2m_C", "R_NO2m_B", "R_NO2m_C", "giorni_DB"]].to_string())

# correlazioni di tendenza
out = []
def corr(nome, x, y):
    ok = x.notna() & y.notna()
    if ok.sum() < 5: return
    r, p = stats.spearmanr(x[ok], y[ok])
    out.append(dict(confronto=nome, n=int(ok.sum()), spearman=round(r, 3), p=round(p, 4)))
for dv in ["D_NO2m_B", "D_NO2m_C", "R_NO2m_B", "R_NO2m_C"]:
    corr(f"mensile grezzo: ingressi vs {dv}", M.ingressi, M[dv])
    # tolta la stagione (media del mese dell'anno)
    mm = M.copy(); mm["m"] = [int(i[5:]) for i in mm.index]
    ds = mm[dv] - mm.groupby("m")[dv].transform("mean"); xs = mm.ingressi - mm.groupby("m").ingressi.transform("mean")
    corr(f"mensile senza stagione: ingressi vs {dv}", xs, ds)
    S9 = A[A.campione.str.contains("settembre")].set_index("anno")
    corr(f"annuale (sett-nov): ingressi vs {dv}", S9.ingressi, S9[dv])
    # tendenza lineare: stessa pendenza nel tempo?
t = np.arange(len(M))
for v in ["ingressi", "D_NO2m_B", "D_NO2m_C", "NO2m_dentro", "NO2m_fuoriAC", "NO2m_controllo"]:
    ok = M[v].notna()
    s = stats.linregress(t[ok.values], M[v][ok].values)
    out.append(dict(confronto=f"pendenza lineare mensile di {v} (per anno)", n=int(ok.sum()), spearman=round(s.slope * 12, 3), p=round(s.pvalue, 4)))
pd.DataFrame(out).to_csv(os.path.join(cart, "tendenza_correlazioni.csv"), sep=";", index=False)
print(pd.DataFrame(out).to_string())
