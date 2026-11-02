"""Analisi delle serie di città.
A. Mensile: tolgo trend e stagionalità, sbianco con AR(1), incrocio con anticipi e ritardi da -6 a +6 mesi, BH.
   Due versioni: con e senza marzo 2020 - dicembre 2021. Sopravvive solo chi regge senza Covid.
B. Annuale: differenze dei logaritmi; ritardi -1, 0, +1; BH; senza gli anni toccati dal Covid (2020, 2021, 2022).
C. Rotture: dove si spezza ogni serie (segmentazione con penalità BIC) e se le date coincidono più del caso.
D. Esperimenti naturali: confronto con gli stessi mesi degli anni prima (Linate 2019, Area B 2019, Expo 2015, M4, Olimpiadi, energia 2022).
E. Giornaliero: modelli di Poisson o log-lineari per morti, aria, Area C con meteo, calendario.
Uscite: out/tempo_*.csv"""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats

from comune import OUT, SEED, bh, path, rd

M = pd.read_csv(os.path.join(OUT, "tempo_mese.csv"), index_col=0)
M.index = pd.PeriodIndex(M.index, freq="M")
Y = pd.read_csv(os.path.join(OUT, "tempo_anno.csv"), index_col=0)
G = pd.read_csv(os.path.join(OUT, "tempo_giorno.csv"), index_col=0, parse_dates=True)
COVID = (M.index >= pd.Period("2020-03", "M")) & (M.index <= pd.Period("2021-12", "M"))
# Gruppi: due serie dello stesso gruppo non si contano come scoperta
GRUPPO = {"morti": "morti", "attesi_morti": "morti", "tmedia": "meteo", "tmax": "meteo", "pioggia_mm": "meteo", "giorni_pioggia": "meteo", "pm10": "aria", "no2": "aria", "o3": "aria",
          "areac": "areac", "areac_vecchia": "areac", "pax_linate": "aero", "pax_malpensa": "aero", "pax_bergamo": "aero", "presenze": "tur", "arrivi": "tur", "presenze_estero_prov": "tur",
          "prestiti": "bib", "musei_civici": "musei", "benzina": "prezzi", "gasolio": "prezzi", "ipc_elettricita": "prezzi", "ipc_gas": "prezzi", "ipc_generale_milano": "prezzi",
          "denunce_maltrattamenti": "reati", "denunce_stalking": "reati", "detenuti_milano": "carceri", "wiki_estero": "wiki", "wiki_italiano": "wiki", "compravendite": "case"}
LOG = {c for c in M.columns if c not in ("tmedia", "tmax", "pioggia_mm", "giorni_pioggia")}
TEST_M = [c for c in M.columns if c not in ("attesi_morti", "compravendite", "gasolio", "arrivi", "o3") and M[c].notna().sum() >= 60]


def destagiona(s, mask_extra=None, trend_anni=3):
    """Toglie stagionalità (mesi) e trend (spline lineare a tratti con nodi ogni trend_anni). La stima ignora Covid e mask_extra."""
    s = s.copy().astype(float)
    if s.name in LOG:
        s = np.log(s.where(s > 0))
    idx = s.dropna().index
    if len(idx) < 24:
        return s * np.nan
    t = np.array([(p.year - idx[0].year) * 12 + p.month - idx[0].month for p in idx], float)
    X = [np.ones(len(idx)), t]
    k = trend_anni * 12
    for kn in np.arange(k, t.max() - 6, k):
        X.append(np.maximum(t - kn, 0))
    for m_ in range(2, 13):
        X.append(np.array([p.month == m_ for p in idx], float))
    X = np.column_stack(X)
    fit = ~((idx >= pd.Period("2020-03", "M")) & (idx <= pd.Period("2021-12", "M")))
    if mask_extra is not None:
        fit &= ~np.isin(idx.astype(str), mask_extra)
    b, *_ = np.linalg.lstsq(X[fit], s.loc[idx].values[fit], rcond=None)
    r = pd.Series(s.loc[idx].values - X @ b, index=idx)
    return r.reindex(s.index)


LINATE = [str(p) for p in pd.period_range("2019-07", "2019-11", freq="M")]
R = pd.DataFrame({c: destagiona(M[c], LINATE if c.startswith("pax_") else None) for c in TEST_M})
R.to_csv(os.path.join(OUT, "tempo_mese_residui.csv"), encoding="utf-8-sig")


def ar1(x):
    """Residui AR(1) su una serie con buchi."""
    x = x.copy()
    a, b = x.values[:-1], x.values[1:]
    ok = ~np.isnan(a) & ~np.isnan(b)
    if ok.sum() < 20:
        return x, 0.0
    phi = np.corrcoef(a[ok], b[ok])[0, 1]
    o = pd.Series(np.r_[np.nan, b - phi * a], index=x.index)
    return o, phi


W = {}
PHI = {}
for c in R:
    W[c], PHI[c] = ar1(R[c])
LAGS = range(-6, 7)
righe = []
CL = np.array(COVID)
for i, a in enumerate(TEST_M):
    for b in TEST_M[i + 1:]:
        if GRUPPO.get(a) == GRUPPO.get(b):
            continue
        for L in LAGS:
            # L>0: a anticipa b di L mesi
            x = W[a].shift(L)
            y = W[b]
            for nome, escl in [("tutti", np.zeros(len(CL), bool)), ("senza_covid", CL)]:
                # esclude anche i mesi spostati nel periodo Covid
                ok = x.notna().values & y.notna().values & ~escl
                if nome == "senza_covid":
                    ok &= ~pd.Series(CL, index=x.index).shift(L).fillna(False).astype(bool).values
                n = ok.sum()
                if n < 48:
                    continue
                r, p = stats.spearmanr(x.values[ok], y.values[ok])
                righe.append(dict(a=a, b=b, lag=L, versione=nome, n=n, r=r, p=p))
L_ = pd.DataFrame(righe)
L_["q"] = np.nan
for v in ["tutti", "senza_covid"]:
    k = L_.versione == v
    L_.loc[k, "q"] = bh(L_.loc[k, "p"].values)
P = L_.pivot_table(index=["a", "b", "lag"], columns="versione", values=["r", "q", "n"]).reset_index()
P.columns = ["_".join([str(x) for x in c if x]) for c in P.columns]
P.to_csv(os.path.join(OUT, "tempo_lag_mese_tutti.csv"), index=False, encoding="utf-8-sig")
S = P[(P.q_senza_covid < 0.05)].sort_values("q_senza_covid")
S.to_csv(os.path.join(OUT, "tempo_lag_mese_sopravvissuti.csv"), index=False, encoding="utf-8-sig")
print("A. MENSILE: test", len(L_), "sopravvissuti senza covid q<0,05:", len(S))
print(S.round(3).to_string())
dt = P[(P.q_tutti < 0.05) & ~(P.q_senza_covid < 0.05)]
dt.to_csv(os.path.join(OUT, "tempo_lag_mese_morti_senza_covid.csv"), index=False, encoding="utf-8-sig")
print("Passano solo col Covid:", len(dt))
print(dt.round(3).head(25).to_string())

# ---- B annuale
TA = [c for c in Y.columns if Y[c].notna().sum() >= 12 and c != "sfratti_eseguiti"]
D_ = np.log(Y[TA].where(Y[TA] > 0)).diff()
# le serie non positive o con percentuali restano differenze semplici
for c in ["tmedia", "pioggia_mm", "quota_civili"]:
    if c in Y:
        D_[c] = Y[c].diff()
GR_Y = {"morti": "m", "tmedia": "meteo", "pioggia_mm": "meteo", "pm10": "aria", "no2": "aria", "incidenti": "inc", "feriti": "inc", "morti_strada": "inc", "incidenti_pedoni": "inc", "incidenti_bici": "inc", "incidenti_moto": "inc",
        "nati": "nat", "nati_x1000_donne": "nat", "matrimoni": "mat", "quota_civili": "mat", "rifiuti_t": "rif", "rifiuti_kg_ab": "rif", "presenze_anno": "tur", "pax_linate": "aero", "pax_malpensa": "aero", "pax_bergamo": "aero",
        "musei_statali": "mus", "musei_civici": "mus", "ipc_generale": "prz", "ipc_affitti": "prz", "ipc_ristoranti": "prz", "ipc_alberghi": "prz", "prezzo_case_reale": "case", "affitto_case_reale": "case", "compravendite": "case",
        "imprese_attive": "imp", "imprese_iscrizioni": "imp", "imprese_cessazioni": "imp", "sfratti_emessi": "sf", "auto_x1000": "auto", "moto_x1000": "auto", "immatricolazioni": "auto", "metro_pax": "metro", "bici_noleggi": "bici", "prestiti_anno": "bib"}
for c in TA:
    if c.startswith("denunce"):
        GR_Y[c] = "reati"
ESCL_Y = [2020, 2021, 2022]
righe = []
for i, a in enumerate(TA):
    for b in TA[i + 1:]:
        if GR_Y.get(a) == GR_Y.get(b):
            continue
        for L in (-1, 0, 1):
            x = D_[a].shift(L)
            d = pd.concat([x, D_[b]], axis=1, keys=["x", "y"]).dropna()
            n0 = len(d)
            if n0 < 9:
                continue
            r0 = stats.spearmanr(d.x, d.y)[0]
            d2 = d[~d.index.isin(ESCL_Y) & ~d.index.isin([e + L for e in ESCL_Y])]
            if len(d2) < 8:
                continue
            r2, p2 = stats.spearmanr(d2.x, d2.y)
            righe.append(dict(a=a, b=b, lag=L, n_tutti=n0, r_tutti=r0, n=len(d2), r=r2, p=p2))
LY = pd.DataFrame(righe)
LY["q"] = bh(LY.p.values)
LY.sort_values("p").to_csv(os.path.join(OUT, "tempo_lag_anno.csv"), index=False, encoding="utf-8-sig")
print("\nB. ANNUALE: test", len(LY), "q<0,05:", (LY.q < 0.05).sum(), "q<0,10:", (LY.q < 0.10).sum())
print(LY.sort_values("p").head(25).round(3).to_string())


# ---- C rotture
def rotture(x, min_seg=12, max_r=4):
    """Segmentazione binaria su cambio di media con penalità BIC. Restituisce gli indici delle rotture."""
    x = x.dropna()
    n = len(x)
    v = x.values
    if n < 2 * min_seg:
        return []
    sigma2 = np.var(np.diff(v)) / 2
    if sigma2 <= 0:
        return []
    pen = 3 * np.log(n) * sigma2

    def cost(a, b):
        s = v[a:b]
        return ((s - s.mean()) ** 2).sum()

    segs = [(0, n)]
    out = []
    for _ in range(max_r):
        best = None
        for a, b in segs:
            if b - a < 2 * min_seg:
                continue
            c0 = cost(a, b)
            for k in range(a + min_seg, b - min_seg + 1):
                g = c0 - cost(a, k) - cost(k, b)
                if best is None or g > best[0]:
                    best = (g, k, a, b)
        if best is None or best[0] < pen:
            break
        out.append(best[1])
        segs.remove((best[2], best[3]))
        segs += [(best[2], best[1]), (best[1], best[3])]
    return [x.index[k] for k in sorted(out)]


BR = []
for c in TEST_M + ["compravendite"]:
    s = M[c].copy()
    if c in LOG:
        s = np.log(s.where(s > 0))
    # solo stagionalità: la rottura è un salto di livello
    idx = s.dropna().index
    dm = pd.get_dummies([p.month for p in idx]).values.astype(float)
    fit = ~((idx >= pd.Period("2020-03", "M")) & (idx <= pd.Period("2021-12", "M")))
    b_, *_ = np.linalg.lstsq(dm[fit], s.loc[idx].values[fit], rcond=None)
    z = pd.Series(s.loc[idx].values - dm @ b_, index=idx)
    # versione senza Covid: mesi tolti e serie ricucita
    z2 = z[fit]
    for tag, zz in [("con_covid", z), ("senza_covid", z2)]:
        for p in rotture(zz):
            BR.append(dict(serie=c, gruppo=GRUPPO.get(c, c), versione=tag, data=str(p)))
BRd = pd.DataFrame(BR)
BRd.to_csv(os.path.join(OUT, "tempo_rotture_mese.csv"), index=False, encoding="utf-8-sig")
print("\nC. ROTTURE (senza Covid)")
print(BRd[BRd.versione == "senza_covid"].groupby("data").serie.apply(lambda s: ", ".join(s)).to_string())
# coincidenza: quante coppie di serie di gruppi diversi hanno rotture entro 3 mesi rispetto a date rimescolate
b2 = BRd[(BRd.versione == "senza_covid") & (BRd.data < "2020-03") | (BRd.versione == "senza_covid") & (BRd.data > "2021-12")].copy()
b2["t"] = b2.data.map(lambda d: pd.Period(d, "M").ordinal)


def n_coinc(t, gr):
    c = 0
    for i in range(len(t)):
        for j in range(i + 1, len(t)):
            if gr[i] != gr[j] and abs(t[i] - t[j]) <= 3:
                c += 1
    return c


rng = np.random.default_rng(SEED)
obs = n_coinc(b2.t.values, b2.gruppo.values)
sim = []
for _ in range(2000):
    tt = []
    for c in b2.serie.values:
        v = M[c].dropna().index
        tt.append(v[rng.integers(12, len(v) - 12)].ordinal)
    sim.append(n_coinc(np.array(tt), b2.gruppo.values))
print("coppie di rotture coincidenti entro 3 mesi:", obs, "attese col caso:", np.mean(sim), "p =", np.mean(np.array(sim) >= obs))
json.dump({"osservate": int(obs), "attese": float(np.mean(sim)), "p": float(np.mean(np.array(sim) >= obs))}, open(os.path.join(OUT, "tempo_rotture_coincidenze.json"), "w"))


# ---- D esperimenti naturali
def effetto(serie, ini, fin, anni_prima=3, logaritmo=True, controllo=None):
    """Confronto dei mesi [ini,fin] con gli stessi mesi dei anni_prima anni precedenti. Se c'è controllo, differenza con la stessa variazione del controllo."""
    s = M[serie].dropna()
    if logaritmo:
        s = np.log(s.where(s > 0))
    pr = pd.period_range(ini, fin, freq="M")
    post, pre, diffs = [], [], []
    for p in pr:
        if p not in s.index:
            continue
        pv = [s.get(p - 12 * a) for a in range(1, anni_prima + 1) if (p - 12 * a) in s.index]
        pv = [x for x in pv if x is not None and not np.isnan(x)]
        if len(pv) == 0:
            continue
        diffs.append(s[p] - np.mean(pv))
    if not diffs:
        return dict(serie=serie, ini=ini, fin=fin, n_mesi=0, effetto_pct=np.nan)
    e = np.mean(diffs)
    # errore: variazione della stessa finestra in anni senza evento (placebo)
    placebo = []
    for sh in range(1, 8):
        dd = []
        for p in pr:
            p0 = p - 12 * sh
            if p0 in s.index:
                pv = [s.get(p0 - 12 * a) for a in range(1, anni_prima + 1) if (p0 - 12 * a) in s.index]
                pv = [x for x in pv if x is not None and not np.isnan(x)]
                if pv:
                    dd.append(s[p0] - np.mean(pv))
        if dd and not (pd.Period(ini, "M") - 12 * sh >= pd.Period("2020-01", "M") and pd.Period(ini, "M") - 12 * sh <= pd.Period("2022-12", "M")):
            placebo.append(np.mean(dd))
    return dict(serie=serie, ini=ini, fin=fin, n_mesi=len(diffs), effetto_pct=(np.exp(e) - 1) * 100 if logaritmo else e, placebo_sd_pct=np.std(placebo) * 100 if len(placebo) >= 3 else np.nan, n_placebo=len(placebo))


EV = [
    ("Chiusura Linate 2019", "2019-08", "2019-10", ["pax_linate", "pax_malpensa", "pax_bergamo", "presenze", "pm10", "no2", "morti", "prestiti"]),
    ("Area B da febbraio 2019", "2019-03", "2020-02", ["areac", "pm10", "no2", "pax_linate", "prestiti"]),
    ("Expo mag-ott 2015", "2015-05", "2015-10", ["presenze_estero_prov", "pax_malpensa", "pax_linate", "pax_bergamo", "musei_civici", "pm10", "no2", "prestiti", "wiki_estero", "morti"]),
    ("Dopo Expo mag-ott 2016", "2016-05", "2016-10", ["presenze_estero_prov", "musei_civici", "pax_malpensa", "pax_linate", "prestiti"]),
    ("M4 fino a Linate dic 2022-giu 2023", "2022-12", "2023-06", ["pax_linate", "areac", "no2", "pm10"]),
    ("M4 completa nov 2024-ott 2025", "2024-11", "2025-10", ["pax_linate", "pm10", "no2", "prestiti", "presenze"]),
    ("Energia: mar-dic 2022", "2022-03", "2022-12", ["areac", "prestiti", "pax_linate", "morti", "pm10", "no2", "presenze"]),
    ("Olimpiadi feb 2026", "2026-02", "2026-02", ["pax_linate", "pax_malpensa", "pax_bergamo", "prestiti", "morti", "pm10", "no2", "wiki_estero", "wiki_italiano"]),
    ("Olimpiadi feb-mar 2026", "2026-02", "2026-03", ["pax_linate", "pax_malpensa", "pax_bergamo", "prestiti", "wiki_estero", "wiki_italiano"]),
]
rig = []
for nome, ini, fin, sl in EV:
    for s_ in sl:
        r = effetto(s_, ini, fin, logaritmo=s_ in LOG)
        r["evento"] = nome
        rig.append(r)
E = pd.DataFrame(rig)
E["z"] = E.effetto_pct / E.placebo_sd_pct
E.to_csv(os.path.join(OUT, "tempo_esperimenti_naturali.csv"), index=False, encoding="utf-8-sig")
print("\nD. ESPERIMENTI NATURALI")
print(E[["evento", "serie", "n_mesi", "effetto_pct", "placebo_sd_pct", "n_placebo", "z"]].round(2).to_string())


# ---- E giornaliero
def poisson_irls(y, X, it=30):
    b = np.zeros(X.shape[1])
    b[0] = np.log(y.mean())
    for _ in range(it):
        eta = X @ b
        mu = np.exp(eta)
        z = eta + (y - mu) / mu
        w = mu
        XtW = X.T * w
        b2 = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(b2 - b)) < 1e-8:
            b = b2
            break
        b = b2
    mu = np.exp(X @ b)
    phi = ((y - mu) ** 2 / mu).sum() / (len(y) - X.shape[1])
    cov = np.linalg.inv((X.T * mu) @ X) * phi
    return b, np.sqrt(np.diag(cov)), phi


def calendario(d):
    """Giorno della settimana, anno, stagione fine (armoniche)."""
    doy = d.dayofyear.values / 365.25
    Xc = [np.ones(len(d))]
    for k in (1, 2, 3, 4):
        Xc += [np.sin(2 * np.pi * k * doy), np.cos(2 * np.pi * k * doy)]
    for w in range(1, 7):
        Xc.append((d.dayofweek == w).astype(float))
    for a in sorted(set(d.year))[1:]:
        Xc.append((d.year == a).astype(float))
    return Xc


G2 = G.copy()
G2["pm10_01"] = (G2.pm10 + G2.pm10.shift(1)) / 2
G2["no2_01"] = (G2.no2 + G2.no2.shift(1)) / 2
G2["t0_3"] = G2.tmedia.rolling(4, min_periods=3).mean()
G2["t4_14"] = G2.tmedia.shift(4).rolling(11, min_periods=9).mean()
G2["caldo"] = np.maximum(G2.t0_3 - 24, 0)
G2["freddo"] = np.maximum(8 - G2.t4_14, 0)
G2["pioggia_si"] = (G2.pioggia_mm >= 1).astype(float).where(G2.pioggia_mm.notna())
festivi = set()
for a in range(2005, 2027):
    for m_, d_ in [(1, 1), (1, 6), (4, 25), (5, 1), (6, 2), (8, 15), (11, 1), (12, 7), (12, 8), (12, 25), (12, 26)]:
        festivi.add(pd.Timestamp(a, m_, d_))
G2["festivo"] = G2.index.isin(festivi).astype(float)
res = []


def modello(y, reg_, sub=None, famiglia="poisson", nome=""):
    d = G2.dropna(subset=[y] + reg_)
    if sub is not None:
        d = d[sub(d)]
    X = np.column_stack(calendario(d.index) + [d.festivo.values] + [d[c].values for c in reg_])
    X = X[:, X.std(axis=0) + (np.arange(X.shape[1]) == 0) > 0]
    k = len(reg_)
    if famiglia == "poisson":
        b, se, phi = poisson_irls(d[y].values.astype(float), X)
    else:
        v = np.log(d[y].values)
        b, *_ = np.linalg.lstsq(X, v, rcond=None)
        e = v - X @ b
        # errori robusti all'autocorrelazione: Newey-West 7 giorni
        XtXi = np.linalg.inv(X.T @ X)
        S0 = (X * e[:, None]).T @ (X * e[:, None])
        for l in range(1, 8):
            w = 1 - l / 8
            G_ = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
            S0 += w * (G_ + G_.T)
        se = np.sqrt(np.diag(XtXi @ S0 @ XtXi))
    for i, c in enumerate(reg_):
        j = -k + i
        res.append(dict(modello=nome, y=y, variabile=c, n=len(d), coef=b[j], se=se[j], z=b[j] / se[j], effetto_pct_per_unita=(np.exp(b[j]) - 1) * 100))


noncovid = lambda d: ~((d.index >= "2020-02-15") & (d.index <= "2021-12-31"))
modello("morti", ["caldo", "freddo", "pm10_01"], noncovid, nome="morti ~ caldo, freddo, PM10 (senza Covid)")
modello("morti", ["caldo", "freddo", "no2_01"], noncovid, nome="morti ~ caldo, freddo, NO2 (senza Covid)")
modello("morti", ["caldo", "freddo", "pm10_01"], None, nome="morti ~ PM10 (con Covid)")
modello("morti", ["caldo", "freddo", "pm10_01", "pioggia_si"], noncovid, nome="morti ~ + pioggia (senza Covid)")
fer = lambda d: (d.index.dayofweek < 5) & (d.festivo == 0) & (d.index.month != 8) & noncovid(d)
modello("areac", ["pioggia_si", "t0_3"], fer, "log", "ingressi Area C feriali ~ pioggia, temperatura")
modello("areac", ["pioggia_si", "tmedia"], lambda d: (d.index.dayofweek >= 5) & noncovid(d), "log", "ingressi Area C sabato-domenica ~ pioggia, temperatura")
modello("areac_vecchia", ["pioggia_si", "t0_3"], lambda d: (d.index.dayofweek < 5) & (d.festivo == 0) & (d.index.month != 8), "log", "Area C serie vecchia 2012-2015 feriali ~ pioggia")
modello("no2", ["pioggia_si", "tmedia"], noncovid, "log", "NO2 ~ pioggia, temperatura")
modello("pm10", ["pioggia_si", "tmedia"], noncovid, "log", "PM10 ~ pioggia, temperatura")
EG = pd.DataFrame(res)
EG.to_csv(os.path.join(OUT, "tempo_giornaliero_modelli.csv"), index=False, encoding="utf-8-sig")
print("\nE. GIORNALIERO")
print(EG.round(4).to_string())
# Giorno della settimana dei morti e mese: anomalie
d = G2.dropna(subset=["morti"])
d = d[noncovid(d)]
print((d.groupby(d.index.dayofweek).morti.mean() / d.morti.mean()).round(4).to_string())
print("dopo festività 26-31 dic vs novembre:", d[(d.index.month == 12) & (d.index.day >= 26)].morti.mean(), d[(d.index.month == 11)].morti.mean(), d[(d.index.month == 1) & (d.index.day <= 15)].morti.mean())
