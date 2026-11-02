"""Ultimi controlli prima del REPORT: sezioni condivise e registro elettorale nei risultati sul voto, anomali senza il reddito per CAP, prestiti per quartiere, pioggia di oggi e di domani, pioggia e cucine.
Stampare in out/log_09.txt"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats

from comune import OUT, SEED, path, rd
from robusta import A, CTRL, FORTI, parz

pd.set_option("display.width", 220, "display.max_rows", 100)
rng = np.random.default_rng(SEED)
print("=== 1. SEZIONI CONDIVISE E REGISTRO ELETTORALE")
ni = rd("elezioni/pulito/nil_info.csv").set_index("nil").reindex(A.index)
ec = rd("elezioni/pulito/nil_controllo_popolazione.csv").set_index("id_nil").reindex(A.index)
print("quota civici in sezioni condivise, mediana:", round(ni.quota_civici_condivisi.median(), 3), "NIL fragile:", ec.fragile.astype(str).value_counts().to_dict())
ok = (ni.quota_civici_condivisi <= ni.quota_civici_condivisi.quantile(0.6)).values
PAIRS = [("aff_cam_2022", "smr_22_24"), ("aff_cam_2022", "smr_12_19"), ("laureati", "dx_cam22"), ("laureati", "lega_eur19"), ("reddito", "dx_cam22"), ("gap_occ_mf", "aff_com_2021"), ("gap_occ_mf", "aff_eur_2024"), ("famiglia_media", "sx_eur24"), ("var_laureati_91_23", "sx_cam22")]
rows = []
for a, b in PAIRS:
    ctrl = [c for c in CTRL if c not in (a, b)]
    x, y = A[a].values, A[b].values
    base = parz(x, y, ctrl)[0]
    r1 = parz(x, y, ctrl, ok)
    r2 = parz(x, y, ctrl + ["elettori_su_adulti"])
    rows.append(dict(a=a, b=b, rho=base, rho_sezioni_poco_condivise=r1[0], n_poco_condivise=r1[2], rho_con_controllo_registro=r2[0], p=r2[1]))
print(pd.DataFrame(rows).round(3).to_string())
print("affluenza ricalcolata sugli adulti residenti (votanti stimati / adulti):")
A["aff_su_adulti"] = A.aff_com_2021 * A.elettori_su_adulti
r = parz(A.aff_su_adulti.values, A.smr_22_24.values, CTRL)
print("  aff comunali 2021 su adulti contro SMR 22-24:", round(r[0], 3), "p", round(r[1], 4), "| rho semplice:", round(stats.spearmanr(A.aff_su_adulti, A.smr_22_24)[0], 3), "| prima:", round(parz(A.aff_com_2021.values, A.smr_22_24.values, CTRL)[0], 3))

print("\n=== 2. ANOMALI SENZA IL REDDITO PER CAP (si usa laureati al posto del reddito)")
D = pd.read_csv(os.path.join(OUT, "dizionario.csv")).fillna("")
det = pd.read_csv(os.path.join(OUT, "nil_anomali_dettaglio.csv"))
VA = sorted(det.variabile.unique())
VA = [v for v in VA if v != "laureati"]
C2 = ["dist_duomo_km", "laureati", "eta_media", "densita_kmq"]
Cr = A[C2].rank()
Cr = (Cr - Cr.mean()) / Cr.std()
X = np.column_stack([np.ones(len(A)), Cr.values, Cr.dist_duomo_km.values ** 2])
R = {}
for v in VA:
    y = A[v].rank()
    k = y.notna().values
    b, *_ = np.linalg.lstsq(X[k], y.values[k], rcond=None)
    e = y.values - X @ b
    R[v] = (e - np.nanmean(e)) / np.nanstd(e)
R = pd.DataFrame(R, index=A.index)
q2 = (R.abs() >= 1.5).mean(axis=1).sort_values(ascending=False)
sim = []
for _ in range(500):
    Rs = R.apply(lambda c: pd.Series(rng.permutation(c.values), index=c.index))
    sim.append((Rs.abs() >= 1.5).mean(axis=1).max())
sim = np.array(sim)
an = pd.read_csv(os.path.join(OUT, "nil_anomali.csv"), index_col=0)
T = pd.DataFrame({"nil": A.nil[q2.index], "residenti": A.residenti_2024[q2.index], "quota_con_laureati": q2, "p_max": [(sim >= v).mean() for v in q2], "quota_con_reddito": an.quota_indicatori_forti.reindex(q2.index), "p_con_reddito": an.p_max_quota.reindex(q2.index)})
T.to_csv(os.path.join(OUT, "nil_anomali_due_versioni.csv"), encoding="utf-8-sig")
print(T.head(14).round(3).to_string())
for nome in ["Rogoredo - Santa Giulia", "San Siro", "Bovisa", "Vigentino - Q.re Fatima", "Cimiano - Rottole - Q.re Feltre", "Maggiore - Musocco - Certosa"]:
    i = A.index[A.nil == nome][0]
    d = R.loc[i].sort_values(key=np.abs, ascending=False).head(10)
    print(nome, [f"{k} {A.loc[i, k]:.3g} (med {A[k].median():.3g}, {v:+.1f})" for k, v in d.items()])

print("\n=== 3. PRESTITI PER QUARTIERE (solo NIL con biblioteca: poche righe, fuori dallo screening)")
bi = rd("biblioteche/pulito/nil_biblioteche.csv").set_index("ID_NIL").reindex(A.index)
A["prestiti_x1000"] = bi.prestiti_per_1000_ab_2025_nil_ospitante
A["var_prestiti"] = bi.prestiti_2025_biblioteche_nel_nil / bi.prestiti_2019_biblioteche_nel_nil * 100 - 100
ok2 = A.prestiti_x1000.notna() & (A.prestiti_x1000 > 0)
print("n", ok2.sum(), {k: round(stats.spearmanr(A.prestiti_x1000[ok2], A[k][ok2], nan_policy="omit")[0], 2) for k in ["laureati", "reddito", "q0_14", "eta_media", "dist_duomo_km", "aff_cam_2022"]})
ok3 = A.var_prestiti.notna() & np.isfinite(A.var_prestiti)
print("n", ok3.sum(), "var prestiti 2019-2025", {k: round(stats.spearmanr(A.var_prestiti[ok3], A[k][ok3], nan_policy="omit")[0], 2) for k in ["laureati", "reddito", "var_q20_34", "var_q0_14", "airbnb_x100"]})

print("\n=== 4. PIOGGIA DI OGGI, DI IERI E DI DOMANI SU AUTO E MOTO")
G = pd.read_csv(os.path.join(OUT, "tempo_giorno.csv"), index_col=0, parse_dates=True)
ac = rd("docs/area-c/data/ingressi_giornalieri.csv")
ac["data"] = pd.to_datetime(ac.data)
ac = ac[ac.flag != "nessun_dato"].set_index("data")
d = ac.join(G[["pioggia_mm", "tmedia"]], how="inner")
d["p0"] = (G.pioggia_mm.reindex(d.index) >= 1).astype(float)
d["p_ieri"] = (G.pioggia_mm.shift(1).reindex(d.index) >= 1).astype(float)
d["p_dom"] = (G.pioggia_mm.shift(-1).reindex(d.index) >= 1).astype(float)
d = d[(d.index.dayofweek < 5) & (d.index.month != 8) & ~((d.index >= "2020-02-20") & (d.index <= "2021-12-31")) & ~((d.index.month == 12) & (d.index.day >= 20)) & ~((d.index.month == 1) & (d.index.day <= 7))]
festivi = {(1, 1), (1, 6), (4, 25), (5, 1), (6, 2), (8, 15), (11, 1), (12, 7), (12, 8), (12, 25), (12, 26)}
d = d[[(a.month, a.day) not in festivi for a in d.index]].dropna(subset=["pioggia_mm", "tmedia"])


def nw(y, X, lag=7):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    Xi = np.linalg.pinv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, lag + 1):
        G_ = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
        S += (1 - l / (lag + 1)) * (G_ + G_.T)
    return b, np.sqrt(np.diag(Xi @ S @ Xi))


for c in ["tipo_moto", "tipo_auto", "totale"]:
    q = d[d[c] > 0]
    doy = q.index.dayofyear.values / 365.25
    Xl = [np.ones(len(q)), q.p0.values, q.p_ieri.values, q.p_dom.values, q.tmedia.values]
    for k in (1, 2):
        Xl += [np.sin(2 * np.pi * k * doy), np.cos(2 * np.pi * k * doy)]
    for w in range(1, 5):
        Xl.append((q.index.dayofweek == w).astype(float))
    for a in sorted(set(q.index.year))[1:]:
        Xl.append((q.index.year == a).astype(float))
    X_ = np.column_stack(Xl)
    b, se = nw(np.log(q[c].values), X_)
    print(c, "oggi", round((np.exp(b[1]) - 1) * 100, 1), "z", round(b[1] / se[1], 1), "| ieri", round((np.exp(b[2]) - 1) * 100, 1), "z", round(b[2] / se[2], 1), "| domani", round((np.exp(b[3]) - 1) * 100, 1), "z", round(b[3] / se[3], 1), "| n", len(q), "media", round(q[c].mean()))
print("giorni di pioggia >=1mm tra i feriali considerati:", round(d.p0.mean() * 100, 1), "%; correlazione pioggia oggi-domani:", round(np.corrcoef(d.p0, d.p_dom)[0, 1], 2))
g2 = d.groupby("p0")[["tipo_moto", "tipo_auto", "totale"]].mean().round(0)
print(g2.to_string())
print("quota moto sul totale: asciutto", round((d[d.p0 == 0].tipo_moto / d[d.p0 == 0].totale).mean() * 100, 1), "pioggia", round((d[d.p0 == 1].tipo_moto / d[d.p0 == 1].totale).mean() * 100, 1))

print("\n=== 5. PROVA DIVERSA PER I LEGAMI MENSILI: VARIAZIONE SULLO STESSO MESE DELL'ANNO PRIMA, POI DIFFERENZA COL MESE PRECEDENTE")
M = pd.read_csv(os.path.join(OUT, "tempo_mese.csv"), index_col=0)
M.index = pd.PeriodIndex(M.index, freq="M")
Yo = np.log(M[["presenze", "prestiti", "pax_linate", "pax_malpensa", "pax_bergamo"]]).diff(12)
Yd = Yo.diff()
for a, b in [("presenze", "prestiti"), ("pax_linate", "presenze"), ("pax_malpensa", "presenze"), ("pax_bergamo", "presenze")]:
    for nome, Z in [("su anno prima", Yo), ("e poi differenza mese su mese", Yd)]:
        for ini in ("2023-03", "2024-01"):
            d_ = Z[[a, b]].dropna()
            d_ = d_[d_.index >= pd.Period(ini, "M")]
            if a == "pax_linate":
                d_ = d_[~d_.index.isin(pd.period_range("2019-07", "2020-11", freq="M"))]
            print(a, b, nome, "da", ini, "n", len(d_), "rho", round(stats.spearmanr(d_[a], d_[b])[0], 3), "p", round(stats.spearmanr(d_[a], d_[b])[1], 4))
