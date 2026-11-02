"""Controlli di robustezza per una coppia di variabili di quartiere. Importato da 05 e 06."""
import os

import numpy as np
import pandas as pd
from scipy import stats

from comune import OUT, SEED

A = pd.read_csv(os.path.join(OUT, "nil_tabella.csv"), index_col=0)
V = pd.read_csv(os.path.join(OUT, "nil_vicini.csv"))
ids = list(A.index)
pos = {i: k for k, i in enumerate(ids)}
W0 = np.zeros((len(ids), len(ids)))
for a, b in V.values:
    if a in pos and b in pos:
        W0[pos[a], pos[b]] = W0[pos[b], pos[a]] = 1
XY = np.column_stack([A.lon.values * 77.9, A.lat.values * 111.2])
DD = np.sqrt(((XY[:, None] - XY[None]) ** 2).sum(-1))
CTRL = ["dist_duomo_km", "reddito", "eta_media", "densita_kmq"]
FORTI = ["laureati", "prezzo", "q_stranieri", "log_residenti"]
RNG = np.random.default_rng(SEED)


def rk(v):
    return stats.rankdata(v)


def qmat(mask, ctrl, extra=None):
    C = [np.ones(mask.sum())]
    for c in ctrl:
        r = rk(A[c].values[mask])
        r = (r - r.mean()) / r.std()
        C.append(r)
        if c == "dist_duomo_km":
            C.append(r ** 2 - (r ** 2).mean())
    if extra is not None:
        C.append(extra[mask])
    return np.linalg.qr(np.column_stack(C))[0]


def parz(x, y, ctrl, mask=None, extra=None):
    """Spearman parziale; x, y array allineati ad A."""
    ok = ~np.isnan(x) & ~np.isnan(y)
    for c in ctrl:
        ok &= A[c].notna().values
    if mask is not None:
        ok &= mask
    Q = qmat(ok, ctrl, extra)
    rx, ry = rk(x[ok]), rk(y[ok])
    ex = rx - Q @ (Q.T @ rx)
    ey = ry - Q @ (Q.T @ ry)
    r = (ex @ ey) / np.sqrt((ex @ ex) * (ey @ ey))
    df = ok.sum() - Q.shape[1] - 1
    t = r * np.sqrt(df / max(1 - r ** 2, 1e-12))
    return r, 2 * stats.t.sf(abs(t), df), int(ok.sum()), ex, ey, ok


def Wm(ok):
    idx = np.where(ok)[0]
    W = W0[np.ix_(idx, idx)].copy()
    Ds = DD[np.ix_(idx, idx)]
    for i in range(len(idx)):
        if W[i].sum() < 2:
            o = np.argsort(Ds[i])[1:3]
            W[i, o] = W[o, i] = 1
    return W


def moran(z, W):
    z = z - z.mean()
    return len(z) / W.sum() * (z @ W @ z) / (z @ z)


def msr(ex, ey, W, n=9999):
    N = len(ex)
    H = np.eye(N) - 1 / N
    lam, U = np.linalg.eigh(H @ ((W + W.T) / 2) @ H)
    U = U[:, np.abs(U.T @ np.ones(N)) < 1e-6]
    c = U.T @ ex
    ey2 = ey - ey.mean()
    obs = (ex @ ey2) / np.sqrt((ex @ ex) * (ey2 @ ey2))
    seg = RNG.choice([-1.0, 1.0], size=(n, len(c)))
    sur = (seg * c) @ U.T
    sur = sur - sur.mean(axis=1, keepdims=True)
    r = (sur @ ey2) / np.sqrt((sur ** 2).sum(1) * (ey2 @ ey2))
    return (1 + np.sum(np.abs(r) >= abs(obs) - 1e-12)) / (n + 1)


def mem(ok, k=6):
    """Primi k autovettori spaziali (MEM): filtrano la struttura geografica liscia."""
    W = Wm(ok)
    N = ok.sum()
    H = np.eye(N) - 1 / N
    lam, U = np.linalg.eigh(H @ ((W + W.T) / 2) @ H)
    o = np.argsort(lam)[::-1][:k]
    return U[:, o]


def scheda(a, b, x=None, y=None, alt=None, ctrl=None):
    """Tutti i controlli per la coppia (a, b). alt = lista di coppie alternative (a2, b2)."""
    x = A[a].values.astype(float) if x is None else x
    y = A[b].values.astype(float) if y is None else y
    ctrl = [c for c in (ctrl or CTRL) if c not in (a, b)]
    r, p, n, ex, ey, ok = parz(x, y, ctrl)
    W = Wm(ok)
    out = dict(a=a, b=b, n=n, rho_grezzo=stats.spearmanr(x[ok], y[ok])[0], rho_parz=r, p_parz=p, moran_ex=moran(ex, W), moran_ey=moran(ey, W))
    res = ey - (ex @ ey) / (ex @ ex) * ex
    out["moran_res"] = moran(res, W)
    out["p_msr"] = max(msr(ex, ey, W), msr(ey, ex, W))
    # effetto in unità naturali: differenza di y fra x al 25esimo e 75esimo percentile, a parità di controlli (OLS)
    Q = qmat(ok, ctrl)
    xr, yr = x[ok], y[ok]
    ex2 = xr - Q @ (Q.T @ xr)
    ey2 = yr - Q @ (Q.T @ yr)
    slope = (ex2 @ ey2) / (ex2 @ ex2)
    q1, q3 = np.percentile(xr, [25, 75])
    out.update(x_q1=q1, x_q3=q3, slope=slope, effetto_iqr=slope * (q3 - q1), y_mediana=float(np.median(yr)))
    # terzili a parità di controlli: media grezza
    t = pd.qcut(pd.Series(xr).rank(method="first"), 3, labels=False)
    out["y_terzo_basso"] = float(yr[t == 0].mean())
    out["y_terzo_alto"] = float(yr[t == 2].mean())
    # togliendo i 5 NIL più influenti
    infl = np.abs(ex * ey)
    drop = np.argsort(infl)[-5:]
    m2 = ok.copy()
    m2[np.where(ok)[0][drop]] = False
    out["rho_senza5"] = parz(x, y, ctrl, m2)[0]
    out["nil_influenti"] = "; ".join(A.nil.values[np.where(ok)[0][drop]][::-1])
    # lascia fuori un municipio alla volta
    mr = []
    for m in sorted(A.municipio.dropna().unique()):
        mr.append(parz(x, y, ctrl, (A.municipio != m).values)[0])
    out["rho_loo_min"] = float(np.min(np.abs(mr)) * np.sign(r))
    out["rho_loo_max"] = float(np.max(np.abs(mr)) * np.sign(r))
    # dentro il municipio
    M = pd.get_dummies(A.municipio.values[ok], drop_first=True).values.astype(float)
    Qm = np.linalg.qr(np.column_stack([np.ones(ok.sum()), M]))[0]
    e1, e2 = ex - Qm @ (Qm.T @ ex), ey - Qm @ (Qm.T @ ey)
    out["rho_entro_municipio"] = (e1 @ e2) / np.sqrt((e1 @ e1) * (e2 @ e2))
    # controlli forti
    cf = [c for c in ctrl + FORTI if c not in (a, b)]
    r2, p2, *_ = parz(x, y, cf)
    out["rho_forti"], out["p_forti"] = r2, p2
    # filtro spaziale MEM
    Fm = mem(ok)
    Qs = np.linalg.qr(np.column_stack([Q, Fm]))[0]
    rx, ry = rk(xr), rk(yr)
    e1, e2 = rx - Qs @ (Qs.T @ rx), ry - Qs @ (Qs.T @ ry)
    out["rho_mem"] = (e1 @ e2) / np.sqrt((e1 @ e1) * (e2 @ e2))
    # solo NIL con almeno 7.000 residenti
    m3 = (A.residenti_2024 >= 7000).values
    out["rho_ge7000"] = parz(x, y, ctrl, m3)[0]
    # senza controlli di reddito CAP: si usa il prezzo... e senza prezzo si usano i laureati
    c4 = [c if c != "reddito" else "laureati" for c in ctrl]
    if not ({a, b} & {"laureati"}):
        out["rho_laureati_al_posto_reddito"] = parz(x, y, c4)[0]
    # bootstrap
    idx = np.where(ok)[0]
    bs = []
    for _ in range(1000):
        s = RNG.choice(idx, len(idx))
        rr1, rr2 = rk(x[s]), rk(y[s])
        C = [np.ones(len(s))]
        for c in ctrl:
            q = rk(A[c].values[s])
            q = (q - q.mean()) / max(q.std(), 1e-9)
            C.append(q)
            if c == "dist_duomo_km":
                C.append(q ** 2 - (q ** 2).mean())
        Qb = np.linalg.qr(np.column_stack(C))[0]
        e1, e2 = rr1 - Qb @ (Qb.T @ rr1), rr2 - Qb @ (Qb.T @ rr2)
        bs.append((e1 @ e2) / np.sqrt((e1 @ e1) * (e2 @ e2)))
    out["ic95_lo"], out["ic95_hi"] = np.percentile(bs, [2.5, 97.5])
    return out
