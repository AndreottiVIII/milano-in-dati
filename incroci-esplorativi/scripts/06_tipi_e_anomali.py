"""Tipi di quartiere (gruppi) e quartieri anomali.
Tipi: clustering gerarchico (Ward) e k-means sugli assi latenti, stabilità con bootstrap (indice di Rand corretto), confronto con municipio, distanza e tipologie del filone quartieri-che-cambiano.
Anomali: per ogni indicatore, residuo rispetto a ciò che reddito, distanza, età e densità prevedono. Si contano i residui forti in DOMINI indipendenti (fonti diverse), non in singole variabili, e si confronta col caso (residui rimescolati).
Uscite: out/nil_tipi.csv, out/nil_tipi_profili.csv, out/nil_anomali.csv, out/nil_anomali_dettaglio.csv"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from comune import OUT, SEED, rd

A = pd.read_csv(os.path.join(OUT, "nil_tabella.csv"), index_col=0)
D = pd.read_csv(os.path.join(OUT, "dizionario.csv")).fillna("")
SENS = {"q_stranieri", "var_q_stranieri", "n_eff_cittadinanze", "scuola_gap_cit", "elettori_su_adulti", "area_km2", "log_residenti", "residenti_2024"}
# una o poche variabili per fonte per non far pesare di più le fonti con molte colonne: peso = 1/radice(variabili del dominio)
V = [v for v in D.variabile if v not in SENS and A[v].notna().sum() >= 55 and A[v].nunique() >= 8 and not v.startswith("cuc_")]
Z = A[V].rank().apply(lambda c: (c - c.mean()) / c.std()).fillna(0)
tema = D.set_index("variabile").tema
pesi = np.array([1 / np.sqrt((tema.loc[V] == tema[v]).sum()) for v in V])
ZW = Z.values * pesi
U, s, Vt = np.linalg.svd(ZW - ZW.mean(0), full_matrices=False)
var = s ** 2 / (s ** 2).sum()
K_AX = 6
F = U[:, :K_AX] * s[:K_AX]
print("varianza assi pesati", np.round(var[:8], 3))
car = pd.DataFrame(Vt[:K_AX].T, index=V, columns=[f"F{i+1}" for i in range(K_AX)])
for f in car:
    o = car[f].sort_values()
    print(f, "NEG", list(o.index[:7]), "POS", list(o.index[-7:]))

rng = np.random.default_rng(SEED)
ris = []
for k in range(3, 11):
    km = KMeans(k, n_init=50, random_state=SEED).fit(F)
    lab = km.labels_
    ari = []
    for _ in range(100):
        i = rng.choice(len(F), len(F))
        km2 = KMeans(k, n_init=5, random_state=int(rng.integers(1e9))).fit(F[i])
        ari.append(adjusted_rand_score(lab, km2.predict(F)))
    ris.append(dict(k=k, silhouette=silhouette_score(F, lab), stabilita_ari=np.mean(ari), ari_p10=np.percentile(ari, 10)))
Rk = pd.DataFrame(ris)
print(Rk.round(3).to_string())
Rk.to_csv(os.path.join(OUT, "nil_tipi_scelta_k.csv"), index=False)
# scelta: il k con stabilità media >= 0,6 e silhouette più alta
ok = Rk[Rk.stabilita_ari >= 0.6]
KK = int(ok.sort_values("silhouette").k.iloc[-1]) if len(ok) else int(Rk.sort_values("stabilita_ari").k.iloc[-1])
KK = max(KK, 4) if len(Rk[(Rk.k >= 4) & (Rk.stabilita_ari >= 0.55)]) else KK
print("k scelto", KK)
km = KMeans(KK, n_init=200, random_state=SEED).fit(F)
lab = km.labels_
W = linkage(F, "ward")
lw = fcluster(W, KK, "maxclust")
print("accordo k-means/Ward ARI:", round(adjusted_rand_score(lab, lw), 3))
q = rd("docs/quartieri-che-cambiano/data/nil.csv").set_index("id_nil").tipologia.reindex(A.index)
print("ARI con municipio", round(adjusted_rand_score(lab, A.municipio.fillna(0)), 3), "con fascia di distanza", round(adjusted_rand_score(lab, pd.qcut(A.dist_duomo_km, KK, labels=False)), 3), "con tipologie quartieri-che-cambiano", round(adjusted_rand_score(lab[q.notna()], q.dropna()), 3))
T = pd.DataFrame({"nil": A.nil, "municipio": A.municipio, "tipo": lab, "tipo_ward": lw, "tipologia_quartieri_che_cambiano": q})
# silhouette per NIL (quanto appartiene al suo gruppo)
from sklearn.metrics import silhouette_samples
T["silhouette"] = silhouette_samples(F, lab)
T.to_csv(os.path.join(OUT, "nil_tipi.csv"), encoding="utf-8-sig")
prof = Z.groupby(lab).mean().T
prof.columns = [f"tipo_{c}" for c in prof.columns]
prof.to_csv(os.path.join(OUT, "nil_tipi_profili.csv"), encoding="utf-8-sig")
mediana = A[V].groupby(lab).median().T
for t in sorted(set(lab)):
    z = prof[f"tipo_{t}"].sort_values()
    mem = T[T.tipo == t].sort_values("silhouette", ascending=False).nil.tolist()
    print(f"\nTIPO {t} n={len(mem)}: {mem}")
    print(" alto:", [f"{k} {v:.1f}" for k, v in z.tail(10).items()][::-1])
    print(" basso:", [f"{k} {v:.1f}" for k, v in z.head(10).items()])
    print(" chiave:", {c: round(float(mediana.loc[c, t]), 1) for c in ["dist_duomo_km", "reddito", "eta_media", "laureati", "prezzo", "densita_kmq", "smr_22_24", "aff_cam_2022", "airbnb_x100"] if c in mediana.index})

# --------------- anomali
CTRL = ["dist_duomo_km", "reddito", "eta_media", "densita_kmq"]
Cr = A[CTRL].rank()
Cr = (Cr - Cr.mean()) / Cr.std()
X = np.column_stack([np.ones(len(A)), Cr.values, Cr.dist_duomo_km.values ** 2])
DOM = {"Soldi": "soldi", "Casa": "casa", "Salute": "salute", "Voto": "voto", "Servizi": "servizi", "Verde": "verde", "Mobilità": "mobilita", "Memoria": "memoria", "Nascite": "famiglie", "Scuola": "famiglie", "Lavoro": "lavoro", "Istruzione": "lavoro", "Movimenti": "movimenti", "Chi ci abita": "famiglie", "Società": "societa", "Cucine": "cucine"}
ESCL = set(CTRL) | SENS | {v for v in D.variabile if D.set_index("variabile").loc[v, "affidabilita"] == "bassa"} | {"lon", "lat"}
VA = [v for v in D.variabile if v not in ESCL and A[v].notna().sum() >= 50 and A[v].nunique() >= 10 and D.set_index("variabile").loc[v, "controllo"] == 0]
R = {}
for v in VA:
    y = A[v].rank()
    ok = y.notna().values
    b, *_ = np.linalg.lstsq(X[ok], y.values[ok], rcond=None)
    e = y.values - X @ b
    R[v] = (e - np.nanmean(e)) / np.nanstd(e)
R = pd.DataFrame(R, index=A.index)


def punteggi(Rr):
    """Per ogni NIL e dominio prende il residuo mediano in valore assoluto del dominio; poi conta i domini con residuo mediano forte."""
    out = {}
    dom_v = {}
    for v in Rr.columns:
        dom_v.setdefault(DOM[tema[v]], []).append(v)
    dm = pd.DataFrame({d: Rr[vs].abs().median(axis=1) for d, vs in dom_v.items()})
    dq = pd.DataFrame({d: (Rr[vs].abs() >= 1.5).mean(axis=1) for d, vs in dom_v.items()})
    return dm, dq


dm, dq = punteggi(R)
tot = pd.DataFrame({"nil": A.nil, "residenti": A.residenti_2024, "quota_indicatori_forti": (R.abs() >= 1.5).mean(axis=1), "indicatori_forti": (R.abs() >= 1.5).sum(axis=1), "indicatori_molto_forti": (R.abs() >= 2.5).sum(axis=1), "domini_con_almeno_30pct_forti": (dq >= 0.3).sum(axis=1), "residuo_medio_abs": R.abs().mean(axis=1)})
# confronto col caso: rimescolo i residui di ciascun indicatore tra i NIL
sim = []
sim_d = []
for _ in range(500):
    Rs = R.apply(lambda c: pd.Series(rng.permutation(c.values), index=c.index))
    sim.append((Rs.abs() >= 1.5).mean(axis=1).max())
    _, dq2 = punteggi(Rs)
    sim_d.append((dq2 >= 0.3).sum(axis=1).max())
tot["p_max_quota"] = [(np.array(sim) >= v).mean() for v in tot.quota_indicatori_forti]
tot["p_max_domini"] = [(np.array(sim_d) >= v).mean() for v in tot.domini_con_almeno_30pct_forti]
tot = tot.sort_values("quota_indicatori_forti", ascending=False)
tot.to_csv(os.path.join(OUT, "nil_anomali.csv"), encoding="utf-8-sig")
pd.set_option("display.width", 220, "display.max_rows", 100)
print(tot.head(15).round(3).to_string())
det = R.stack().rename("residuo_z").reset_index()
det.columns = ["id_nil", "variabile", "residuo_z"]
det["nil"] = det.id_nil.map(A.nil)
det["valore"] = [A.loc[i, v] for i, v in zip(det.id_nil, det.variabile)]
det["mediana_citta"] = det.variabile.map(A[VA].median())
det["tema"] = det.variabile.map(tema)
det.to_csv(os.path.join(OUT, "nil_anomali_dettaglio.csv"), index=False, encoding="utf-8-sig")
for i in tot.index[:12]:
    d = det[(det.id_nil == i) & (det.residuo_z.abs() >= 1.8)].sort_values("residuo_z", key=abs, ascending=False)
    print("\n", A.nil[i], "| reddito", round(A.reddito[i]), "dist", round(A.dist_duomo_km[i], 1), "età", round(A.eta_media[i], 1), "res", int(A.residenti_2024[i]))
    print("   ", [f"{r.variabile}={r.valore:.3g} (mediana {r.mediana_citta:.3g}, z {r.residuo_z:+.1f})" for r in d.head(14).itertuples()])
