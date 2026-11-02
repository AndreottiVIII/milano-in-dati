"""Screening di tutte le coppie di variabili per quartiere.
Passi: Spearman grezzo -> Spearman parziale al netto di distanza dal Duomo (e quadrato), reddito, età media, densità
-> Benjamini-Hochberg sulle coppie NON meccaniche -> Moran sui residui -> permutazioni spaziali (Moran spectral randomization)
-> controlli forti (laureati, prezzo, quota stranieri, log residenti).
Uscite: out/nil_coppie_tutte.csv, out/nil_coppie_sopravvissute.csv, out/nil_imbuto.json, out/nil_moran_variabili.csv"""
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats

from comune import OUT, SEED, bh

A = pd.read_csv(os.path.join(OUT, "nil_tabella.csv"), index_col=0)
D = pd.read_csv(os.path.join(OUT, "dizionario.csv")).fillna("")
V = pd.read_csv(os.path.join(OUT, "nil_vicini.csv"))
META = D.set_index("variabile")
MIN_N = 35
CONTROLLI = ["dist_duomo_km", "reddito", "eta_media", "densita_kmq"]
FORTI = ["laureati", "prezzo", "q_stranieri", "log_residenti"]
ESCLUSE = set(D.variabile[D.controllo == 1])
# Variabili sulla cittadinanza: restano solo come controllo forte, NON entrano nella ricerca di "scoperte" (scelta dichiarata nel REPORT)
SENSIBILI = {"q_stranieri", "var_q_stranieri", "n_eff_cittadinanze", "scuola_gap_cit"}
# elettori_su_adulti misura il registro elettorale (residenti all'estero, stranieri che non votano): è un artefatto, non un fenomeno
SENSIBILI |= {"elettori_su_adulti"}
TEST = [v for v in D.variabile if v not in ESCLUSE and v not in SENSIBILI and A[v].notna().sum() >= MIN_N and A[v].nunique() >= 8]

# ---- concetti: variabili che dicono la stessa cosa o sono costruite l'una dall'altra
CONCETTI = {
    "verde": r"^(alberi_|verde_|indice_verde|calore|suolo_pct|min_parco|c15_parchi|gioco_|orti_|cani_|var_alberi)",
    "soldi_cap": r"^(quota_alti|quota_bassi|var_reddito)",
    "omi": r"^(affitto|var_affitto|var_prezzo|rendimento_lordo)",
    "airbnb": r"^(airbnb_|case_non_occ$)",
    "eta": r"^(q0_14|q65|q80|q20_34|var_q20_34|var_eta_media|var_q0_14|famiglia_media|famiglie_sole|var_bambini|nati_|var_nati)",
    "scuole": r"^(var_alunni|var_bambini|scuola_gap|tempo_pieno|paritarie|nidi_)",
    "stranieri": r"^(var_q_stranieri|n_eff_cittadinanze|scuola_gap_cit)",
    "movimenti": r"^(saldo_|ricambio|var_pop_14)",
    "medici": r"^(medici_x1000|minuti_medico|c15_medici|medici_65)",
    "farmacie": r"^(farmacie|minuti_farmacia)",
    "metro": r"^(dist_metro|c15_metro)",
    "bici": r"^(bikemi|c15_bikemi|ciclabili)",
    "biblio": r"^(distanza_biblioteca|c15_biblioteche)",
    "negozi": r"^(locali_|artigianato|var_locali|c15_vicinato|c15_mercati|c15_supermercati|botteghe_)",
    "cultura": r"^(opere_|murali|targhe_|pietre_|beni_cult|cinema_|film_libri|wiki_|c15_cinema|c15_teatri|c15_librerie|violenza_pol)",
    "suolo_costr": r"^(nuovo_suolo|nuove_case|volume_nuovo|ambiti_rigen|var_pop_14)",
    "incidenti": r"^(incid|morti_x1000|var_incidenti)",
    "antenne": r"^(antenne|var_antenne)",
    "smr": r"^(smr_|var_smr|eccesso_2020)",
    "voto": r"^(aff_|var_aff|sx_|dx_|lega_|destra_|m5s_|var_sx|var_dx|elettori_)",
    "lavoro": r"^(tasso_occ|gap_occ|disocc|studenti_)",
    "edifici": r"^(edifici_|interni_)",
    "lau": r"^(var_laureati|laureati_1991)",
}


def concetti(v):
    return {k for k, r in CONCETTI.items() if re.search(r, v)}


# Coppie meccaniche o quasi (dichiarate una per una, con il motivo)
ESPLICITE = [
    (r"^c15_punteggio$", r"^(distanza_biblioteca|minuti_|min_parco|dist_metro|bikemi|c15_)", "il punteggio contiene quel servizio"),
    (r"^c15_vicinato$", r"^(artigianato|locali_)", "negozi di vicinato e attività alimentari: stesso tessuto commerciale"),
    (r"^saldo_estero", r"^(q0_14|q65|q80|q20_34|famiglia_media|famiglie_sole|studenti_2011)$", "chi arriva dall'estero è giovane e cambia la composizione delle famiglie"),
    (r"^(var_laureati_91_23)$", r"^(laureati_1991)$", "la variazione contiene il livello"),
    (r"^(var_pop_14_25|var_pop_91_11)$", r"^(var_eta_media|var_q20_34|var_q0_14|var_bambini|edifici_post80)$", "crescita di residenti ed età: nuove case, stesso registro"),
    (r"^aler_", r"^(quota_bassi)$", "case popolari e fascia bassa di reddito: stessa geografia del CAP"),
    (r"^airbnb_x100$", r"^(case_non_occ)", "stesso denominatore (abitazioni) e l'annuncio è una casa non occupata"),
    (r"^(locali_x1000|locali_x_kmq)$", r"^cuc_", "le cucine sono calcolate sui locali"),
    (r"^(saldo_|ricambio|var_pop_14)", r"^(var_q20_34|var_eta_media|var_q0_14|var_bambini|var_q_stranieri)$", "chi arriva cambia età e composizione: stesso registro"),
    (r"^(nuove_case|volume_nuovo|nuovo_suolo)", r"^(var_pop_14|saldo_|var_q|var_eta|var_bambini|edifici_post80)", "le nuove case portano nuovi residenti giovani: è il cantiere"),
    (r"^(smr_|eccesso_2020|var_smr)", r"^(q65|q80|var_eta_media)$", "gli attesi dell'SMR dipendono dall'età del quartiere"),
    (r"^(nati_|var_nati)", r"^(q0_14|q20_34|var_q0_14|var_bambini|var_q20_34|famiglia_media)$", "i nati sono i bambini di domani"),
    (r"^(famiglie_sole|famiglia_media)$", r"^(q0_14|q65|q80|q20_34)$", "famiglie piccole ed età"),
    (r"^(incidenti_x_kmq)$", r"^(locali_x_kmq|antenne_x_kmq|bikemi_x_kmq|opere_x_kmq|wiki_views_x_kmq|cinema_storici_x_kmq|volume_nuovo_x_kmq|ciclabili_km_x_kmq|beni_cult_x_kmq|film_libri_x_kmq)$", "conteggi per km2: densità di attività"),
    (r"_x_kmq$", r"_x_kmq$", "conteggi per km2: tutti misurano quanto è fitta la città"),
]


def meccanica(a, b):
    """Restituisce il motivo se la coppia è meccanica, altrimenti stringa vuota."""
    ma, mb = META.loc[a], META.loc[b]
    if ma.fonte_id == mb.fonte_id:
        return "stessa fonte: " + str(ma.fonte_id)
    fam = [{"ds27", "ds27_cit", "ds_flussi", "ds_nati"}, {"censimento", "censimento_edifici"}]
    for f in fam:
        if ma.fonte_id in f and mb.fonte_id in f and (ma.tipo == mb.tipo):
            return "stesso registro: " + str(ma.fonte_id) + "/" + str(mb.fonte_id)
    c = concetti(a) & concetti(b)
    if c:
        return "stesso concetto: " + ",".join(sorted(c))
    for ra, rb, mot in ESPLICITE:
        if (re.search(ra, a) and re.search(rb, b)) or (re.search(ra, b) and re.search(rb, a)):
            return mot
    return ""


# ---- matrice di contiguità, con almeno 2 vicini per punto
ids = list(A.index)
pos = {i: k for k, i in enumerate(ids)}
W0 = np.zeros((len(ids), len(ids)))
for a, b in V.values:
    if a in pos and b in pos:
        W0[pos[a], pos[b]] = W0[pos[b], pos[a]] = 1
xy = np.column_stack([A.lon.values * 77.9, A.lat.values * 111.2])
DD = np.sqrt(((xy[:, None] - xy[None]) ** 2).sum(-1))


def W_mask(mask):
    idx = np.where(mask)[0]
    W = W0[np.ix_(idx, idx)].copy()
    Ds = DD[np.ix_(idx, idx)]
    for i in range(len(idx)):
        if W[i].sum() < 2:
            o = np.argsort(Ds[i])[1:3]
            W[i, o] = W[o, i] = 1
    return W


def moran(x, W):
    z = x - x.mean()
    return len(x) / W.sum() * (z @ W @ z) / (z @ z)


def rk(v):
    return stats.rankdata(v)


CACHE = {}


def preparatore(mask, ctrl):
    """Matrice ortonormale delle variabili di controllo in ranghi, sul sottoinsieme mask (metodo QR)."""
    key = (mask.tobytes(), tuple(ctrl))
    if key not in CACHE:
        C = []
        for c in ctrl:
            r = rk(A[c].values[mask])
            r = (r - r.mean()) / r.std()
            C.append(r)
            if c == "dist_duomo_km":
                C.append(r ** 2 - (r ** 2).mean())
        X = np.column_stack([np.ones(mask.sum())] + C)
        Q, _ = np.linalg.qr(X)
        CACHE[key] = Q
    return CACHE[key]


def parziale(a, b, ctrl):
    x, y = A[a].values, A[b].values
    c_ok = np.all([A[c].notna().values for c in ctrl], axis=0)
    mask = ~np.isnan(x) & ~np.isnan(y) & c_ok
    n = mask.sum()
    if n < MIN_N:
        return np.nan, np.nan, n, None, None, mask
    Q = preparatore(mask, ctrl)
    rx, ry = rk(x[mask]), rk(y[mask])
    ex, ey = rx - Q @ (Q.T @ rx), ry - Q @ (Q.T @ ry)
    if ex.std() < 1e-9 or ey.std() < 1e-9:
        return np.nan, np.nan, n, None, None, mask
    r = (ex @ ey) / np.sqrt((ex @ ex) * (ey @ ey))
    df = n - Q.shape[1] - 2 + 2 - 2  # n - colonne di controllo - 2
    df = n - Q.shape[1] - 1
    t = r * np.sqrt(df / max(1 - r ** 2, 1e-12))
    return r, 2 * stats.t.sf(abs(t), df), n, ex, ey, mask


righe = []
for i, a in enumerate(TEST):
    for b in TEST[i + 1:]:
        ok = A[a].notna() & A[b].notna()
        if ok.sum() < MIN_N:
            continue
        rho, p0 = stats.spearmanr(A.loc[ok, a], A.loc[ok, b])
        r, p, n, *_ = parziale(a, b, CONTROLLI)
        righe.append(dict(a=a, b=b, n_grezzo=int(ok.sum()), rho=rho, p_rho=p0, n=n, rho_parz=r, p_parz=p, meccanica=meccanica(a, b),
                          ta=META.loc[a, "tema"], tb=META.loc[b, "tema"]))
R = pd.DataFrame(righe)
R["q_rho"] = np.nan
R["q_parz"] = np.nan
nm = R.meccanica == ""
R.loc[nm, "q_rho"] = bh(R.loc[nm, "p_rho"].values)
R.loc[nm, "q_parz"] = bh(R.loc[nm, "p_parz"].values)

# ---- stima empirica di quante coppie passerebbero per caso: rimescolo le etichette dei NIL per ogni variabile
rng = np.random.default_rng(SEED)
falsi = []
TN = R[nm]
perm_vars = {v: rng.permutation(len(A)) for v in TEST}
A0 = A.copy()
for it in range(3):
    for v in TEST:
        A[v] = A0[v].values[rng.permutation(len(A))]
    ps = []
    for a, b in zip(TN.a.values, TN.b.values):
        r, p, n, *_ = parziale(a, b, CONTROLLI)
        ps.append(p)
    falsi.append(int(np.nansum(bh(np.array(ps)) < 0.05)))
A = A0
print("coppie sotto q<0,05 con etichette mescolate:", falsi)

# ---- fattori latenti: gli assi generali della città, per vedere cosa resta oltre la struttura comune
PCA_VAR = [v for v in D.variabile if A[v].notna().sum() >= 55 and A[v].nunique() >= 8 and v not in SENSIBILI and v not in ("area_km2",)]
ZP = A[PCA_VAR].rank().apply(lambda c: (c - c.mean()) / c.std()).fillna(0)


def n_fattori():
    """Analisi parallela di Horn: quanti assi superano il rumore."""
    ev = np.linalg.svd(ZP.values, compute_uv=False) ** 2
    g = np.random.default_rng(SEED)
    sim = []
    for _ in range(200):
        Z = np.column_stack([g.permutation(ZP.values[:, j]) for j in range(ZP.shape[1])])
        sim.append(np.linalg.svd(Z, compute_uv=False) ** 2)
    soglia = np.percentile(np.array(sim), 95, axis=0)
    k = 0
    while ev[k] > soglia[k]:
        k += 1
    return k, ev / ev.sum()


KF, QUOTE = n_fattori()
print("fattori sopra il rumore:", KF, "quota varianza:", np.round(QUOTE[:KF + 2], 3))
U, s_, Vt = np.linalg.svd(ZP.values, full_matrices=False)
car = pd.DataFrame(Vt[:KF].T * s_[:KF] / np.sqrt(len(ZP) - 1), index=PCA_VAR, columns=[f"F{i+1}" for i in range(KF)])
car.to_csv(os.path.join(OUT, "nil_fattori_carichi.csv"), encoding="utf-8-sig")
pd.DataFrame(U[:, :KF] * s_[:KF], index=A.index, columns=car.columns).assign(nil=A.nil).to_csv(os.path.join(OUT, "nil_fattori_punteggi.csv"), encoding="utf-8-sig")


def parziale_fattori(a, b, k=None):
    """Parziale al netto dei controlli e dei k assi latenti calcolati SENZA a, b e le variabili dello stesso concetto o fonte."""
    k = KF if k is None else k
    tieni = [v for v in PCA_VAR if v not in (a, b) and meccanica(a, v) == "" and meccanica(b, v) == ""]
    Z = ZP[tieni].values
    U_, s2, _ = np.linalg.svd(Z, full_matrices=False)
    F = U_[:, :k]
    x, y = A[a].values, A[b].values
    mask = ~np.isnan(x) & ~np.isnan(y)
    C = []
    for c in CONTROLLI:
        r = rk(A[c].values[mask])
        r = (r - r.mean()) / r.std()
        C.append(r)
        if c == "dist_duomo_km":
            C.append(r ** 2 - (r ** 2).mean())
    X = np.column_stack([np.ones(mask.sum())] + C + [F[mask]])
    Q = np.linalg.qr(X)[0]
    rx, ry = rk(x[mask]), rk(y[mask])
    ex, ey = rx - Q @ (Q.T @ rx), ry - Q @ (Q.T @ ry)
    r = (ex @ ey) / np.sqrt((ex @ ex) * (ey @ ey))
    df = mask.sum() - Q.shape[1] - 1
    t = r * np.sqrt(df / max(1 - r ** 2, 1e-12))
    return r, 2 * stats.t.sf(abs(t), df)


# ---- permutazioni spaziali sulle coppie sopravvissute
N_SURR = 9999
SP = {}


def msr_p(ex, ey, W, rng):
    """Moran spectral randomization: inverte i segni dei coefficienti sugli autovettori di W, conserva l'autocorrelazione di ex."""
    n = len(ex)
    Ws = (W + W.T) / 2
    H = np.eye(n) - 1 / n
    lam, U = np.linalg.eigh(H @ Ws @ H)
    keep = np.abs(U.T @ np.ones(n)) < 1e-6
    U = U[:, keep]
    c = U.T @ ex
    ey2 = ey - ey.mean()
    obs = (ex @ ey2) / np.sqrt((ex @ ex) * (ey2 @ ey2))
    seg = rng.choice([-1.0, 1.0], size=(N_SURR, len(c)))
    sur = (seg * c) @ U.T
    sur = sur - sur.mean(axis=1, keepdims=True)
    r = (sur @ ey2) / np.sqrt((sur ** 2).sum(1) * (ey2 @ ey2))
    return (1 + np.sum(np.abs(r) >= abs(obs) - 1e-12)) / (N_SURR + 1)


S = R[(R.q_parz < 0.10)].copy()
ext = []
for _, row in S.iterrows():
    r, p, n, ex, ey, mask = parziale(row.a, row.b, CONTROLLI)
    W = W_mask(mask)
    pm = msr_p(ex, ey, W, rng)
    pm2 = msr_p(ey, ex, W, rng)
    # residui della regressione ey ~ ex
    b_ = (ex @ ey) / (ex @ ex)
    res = ey - b_ * ex
    # forti: toglie il controllo se è uno dei due
    forti = [c for c in CONTROLLI + FORTI if c not in (row.a, row.b)]
    r2, p2, n2, *_ = parziale(row.a, row.b, forti)
    # municipio come effetto fisso
    ok = mask.copy()
    M = pd.get_dummies(A.municipio.values[ok], drop_first=True).values.astype(float)
    Q = np.linalg.qr(np.column_stack([np.ones(ok.sum()), M]))[0]
    ex3 = ex - Q @ (Q.T @ ex)
    ey3 = ey - Q @ (Q.T @ ey)
    r3 = (ex3 @ ey3) / np.sqrt((ex3 @ ex3) * (ey3 @ ey3))
    rf, pf = parziale_fattori(row.a, row.b)
    ext.append(dict(a=row.a, b=row.b, rho_fattori=rf, p_fattori=pf, p_msr_x=pm, p_msr_y=pm2, p_msr=max(pm, pm2), moran_x=moran(ex, W), moran_y=moran(ey, W), moran_res=moran(res, W),
                    rho_forte=r2, p_forte=p2, rho_entro_municipio=r3))
S = S.merge(pd.DataFrame(ext), on=["a", "b"])
S["q_msr"] = np.nan
sn = S.meccanica == ""
S.loc[sn, "q_msr"] = bh(S.loc[sn, "p_msr"].values)
R.to_csv(os.path.join(OUT, "nil_coppie_tutte.csv"), index=False, encoding="utf-8-sig")
S = S.sort_values("p_parz")
S.to_csv(os.path.join(OUT, "nil_coppie_q10.csv"), index=False, encoding="utf-8-sig")
surv = S[(S.meccanica == "") & (S.q_parz < 0.05) & (S.q_msr < 0.05) & (S.p_forte < 0.05) & (np.sign(S.rho_forte) == np.sign(S.rho_parz)) & (np.sign(S.rho_entro_municipio) == np.sign(S.rho_parz)) & (S.rho_entro_municipio.abs() > 0.2)]
surv = surv.copy()
surv["specifica"] = (surv.p_fattori < 0.01) & (surv.rho_fattori.abs() >= 0.35) & (np.sign(surv.rho_fattori) == np.sign(surv.rho_parz))
surv.to_csv(os.path.join(OUT, "nil_coppie_sopravvissute.csv"), index=False, encoding="utf-8-sig")
imbuto = {
    "variabili_testate": len(TEST), "coppie": len(R), "coppie_meccaniche_o_stesso_concetto": int((~nm).sum()),
    "coppie_non_meccaniche": int(nm.sum()), "rho_grezzo_ge_0_5_non_mecc": int((R[nm].rho.abs() >= 0.5).sum()), "q_grezzo_lt_05_non_mecc": int((R.q_rho < 0.05).sum()),
    "q_parziale_lt_05": int((R.q_parz < 0.05).sum()), "q_parziale_lt_10": int((R.q_parz < 0.10).sum()),
    "falsi_attesi_con_etichette_mescolate_q05": falsi,
    "passano_msr": int(((S.meccanica == "") & (S.q_parz < 0.05) & (S.q_msr < 0.05)).sum()),
    "passano_controlli_forti": int(((S.meccanica == "") & (S.q_parz < 0.05) & (S.q_msr < 0.05) & (S.p_forte < 0.05)).sum()),
    "sopravvissute_controlli_e_municipio": len(surv), "specifiche_oltre_gli_assi_latenti": int(surv.specifica.sum()), "assi_latenti": int(KF),
}
json.dump(imbuto, open(os.path.join(OUT, "nil_imbuto.json"), "w"), indent=1)
print(json.dumps(imbuto, indent=1))
pd.set_option("display.width", 230, "display.max_rows", 200, "display.max_colwidth", 60)
print(surv[surv.specifica][["a", "b", "n", "rho", "rho_parz", "q_parz", "p_msr", "moran_res", "rho_forte", "rho_entro_municipio", "rho_fattori", "p_fattori"]].round(3).to_string())
