# Funzioni comuni (regressione con errori standard "a grappoli" per settimana, Spearman con intervallo, ecc.).
# Nessuna dipendenza da statsmodels: solo numpy, pandas, scipy.
import numpy as np, pandas as pd
from scipy import stats

def carica(path):
    P = pd.read_csv(path, sep=";", parse_dates=["data"]).set_index("data")
    P["sett"] = P.index.isocalendar().year.astype(str) + "-" + P.index.isocalendar().week.astype(str).str.zfill(2)
    return P

def dummies(df, cols):
    return pd.get_dummies(df[cols].astype(str), drop_first=True, dtype=float)

def ols_cluster(y, X, groups):
    """OLS con errori standard robusti a grappoli (gruppo = settimana), correzione per pochi gruppi.
    y: Series, X: DataFrame (senza costante, la aggiunge). Restituisce Series coef, se, n, gruppi."""
    X = X.copy(); X.insert(0, "const", 1.0)
    ok = y.notna() & X.notna().all(axis=1)
    y = y[ok].values.astype(float); Xv = X[ok].values.astype(float); g = pd.Series(groups[ok].values)
    n, k = Xv.shape
    XtXi = np.linalg.pinv(Xv.T @ Xv)
    b = XtXi @ Xv.T @ y
    e = y - Xv @ b
    meat = np.zeros((k, k)); G = g.nunique()
    for _, idx in g.groupby(g).groups.items():
        s = Xv[idx].T @ e[idx]
        meat += np.outer(s, s)
    corr = (G / (G - 1)) * ((n - 1) / (n - k))
    V = corr * XtXi @ meat @ XtXi
    se = np.sqrt(np.maximum(np.diag(V), 0))
    return pd.DataFrame({"coef": b, "se": se}, index=X.columns), n, G

def ci95(coef, se):
    return coef - 1.96 * se, coef + 1.96 * se

def residualizza(s, X):
    """toglie da s l'effetto lineare delle colonne X (con costante)"""
    ok = s.notna() & X.notna().all(axis=1)
    Xv = np.column_stack([np.ones(ok.sum()), X[ok].values.astype(float)])
    b = np.linalg.pinv(Xv) @ s[ok].values
    r = pd.Series(np.nan, index=s.index)
    r[ok] = s[ok].values - Xv @ b
    return r

def spearman_boot(x, y, groups, B=1000, seed=1):
    """Spearman con intervallo al 95% (bootstrap a blocchi: si ricampionano le settimane intere)."""
    ok = x.notna() & y.notna()
    x = x[ok]; y = y[ok]; g = groups[ok]
    rho, p = stats.spearmanr(x, y)
    rng = np.random.default_rng(seed)
    gl = g.unique(); idx = {k: np.where(g.values == k)[0] for k in gl}
    r = []
    for _ in range(B):
        ch = rng.choice(gl, len(gl))
        ii = np.concatenate([idx[k] for k in ch])
        r.append(stats.spearmanr(x.values[ii], y.values[ii])[0])
    return rho, np.percentile(r, 2.5), np.percentile(r, 97.5), len(x)

def pasqua(anno):
    a = anno % 19; b = anno // 100; c = anno % 100
    d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i = c // 4; k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    mese = (h + l - 7 * m + 114) // 31; giorno = ((h + l - 7 * m + 114) % 31) + 1
    return pd.Timestamp(anno, mese, giorno)

def festivi(anni):
    s = set()
    for y in anni:
        for m, d in [(1, 1), (1, 6), (4, 25), (5, 1), (6, 2), (8, 15), (11, 1), (12, 7), (12, 8), (12, 25), (12, 26)]:
            s.add(pd.Timestamp(y, m, d))
        s.add(pasqua(y) + pd.Timedelta(days=1))
    return s
