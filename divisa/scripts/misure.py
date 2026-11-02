"""Misure di segregazione (libreria usata dai passi 01-04). Nessun dato qui dentro.
Tutte le misure partono da una matrice di conteggi: righe = unita' (CAP o NIL), colonne = gruppi.
- dissimilarita(a, b): D = meta' della somma di |quota di A nell'unita' - quota di B nell'unita'|; 0 = distribuiti allo stesso modo, 1 = mai nella stessa unita'.
- isolamento(a, t): quota media di gruppo A tra i vicini di una persona di A (Lieberson/Bell).
- theil_H(C): indice di entropia multigruppo (Theil/Reardon-Firebaugh), 0..1.
- rank_order_H(C): indice a ordine di rango (Reardon et al. 2006) su categorie ORDINATE (classi di reddito, anni di eta'); 0..1; non cambia se i redditi
  salgono tutti insieme (l'inflazione non lo muove), perche' guarda i percentili e non le soglie in euro.
- basale(): valore atteso se i gruppi fossero sparsi a caso (stesse dimensioni delle unita', stesse quote totali): le unita' piccole fanno salire gli indici anche senza segregazione.
- bootstrap(): ricampionamento multinomiale dentro ogni unita' (intervallo 2,5-97,5 per cento).
"""
import numpy as np

LN2 = np.log(2.0)


def _ent(p):
    p = np.asarray(p, float)
    with np.errstate(divide='ignore', invalid='ignore'):
        e = -np.where(p > 0, p * np.log(p), 0.0)
    return e


def dissimilarita(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    return 0.5 * np.abs(a / a.sum() - b / b.sum()).sum()


def isolamento(a, t):
    a = np.asarray(a, float); t = np.asarray(t, float)
    ok = t > 0
    return float(((a[ok] / a.sum()) * (a[ok] / t[ok])).sum())


def theil_H(C):
    C = np.asarray(C, float)
    t = C.sum(1); T = t.sum()
    ok = t > 0
    P = C.sum(0) / T
    E = _ent(P).sum()
    if E <= 0:
        return 0.0
    Ei = _ent(C[ok] / t[ok, None]).sum(1)
    return float((t[ok] / T * (E - Ei)).sum() / E)


def _bin_H(low, t):
    """indice di entropia binario tra 'low' e 'resto' per un taglio; low, t: vettori sulle unita'."""
    T = t.sum(); L = low.sum()
    p = L / T
    if p <= 0 or p >= 1:
        return 0.0
    E = _ent(np.array([p, 1 - p])).sum()
    ok = t > 0
    pi = low[ok] / t[ok]
    Ei = _ent(pi) + _ent(1 - pi)
    return float((t[ok] / T * (E - Ei)).sum() / E)


def _e2(p):
    """entropia binaria in base 2, E(p) in [0,1]"""
    return _ent(p) / LN2 + _ent(1 - p) / LN2


GRID = np.linspace(0, 1, 1001)


def rank_order_H(C):
    """C: unita' x categorie ORDINATE (da basso ad alto). Per ogni taglio tra categorie si calcola l'indice di entropia binario H(p);
    poi H(p) e' interpolato in linea retta tra i tagli (e vale 0 in p=0 e p=1) e pesato con E(p): 2 ln2 * integrale E(p) H(p) dp.
    Con poche categorie e' una stima per difetto (non si vede la separazione dentro la categoria)."""
    C = np.asarray(C, float)
    t = C.sum(1); T = t.sum()
    ok = t > 0
    C = C[ok]; t = t[ok]
    cum = np.cumsum(C, axis=1)[:, :-1]               # unita' x (K-1) tagli
    L = cum.sum(0); p = L / T
    good = (p > 1e-9) & (p < 1 - 1e-9)
    if not good.any():
        return 0.0
    cum = cum[:, good]; p = p[good]
    E = _ent(p) + _ent(1 - p)
    pi = cum / t[:, None]
    Ei = _ent(pi) + _ent(1 - pi)
    H = ((t[:, None] / T) * (E[None, :] - Ei)).sum(0) / E
    ps = np.concatenate([[0.0], p, [1.0]]); hs = np.concatenate([[0.0], H, [0.0]])
    o = np.argsort(ps, kind='stable')
    h = np.interp(GRID, ps[o], hs[o])
    w = _e2(GRID)
    return float(np.trapezoid(w * h, GRID) / np.trapezoid(w, GRID))


def basale(C, f, B=100, rng=None):
    """media di f su B riallocazioni casuali (stesse dimensioni delle unita', stesse quote di gruppo nel totale)."""
    rng = rng or np.random.default_rng(12345)
    C = np.asarray(C, float)
    t = C.sum(1).astype(int); P = C.sum(0) / C.sum()
    v = []
    for _ in range(B):
        R = np.array([rng.multinomial(n, P) for n in t])
        v.append(f(R))
    return float(np.mean(v)), float(np.std(v))


def bootstrap(C, f, B=200, rng=None):
    """ricampiona i conteggi di ogni unita' (multinomiale con le quote osservate); ritorna (media, p2.5, p97.5)."""
    rng = rng or np.random.default_rng(54321)
    C = np.asarray(C, float)
    t = C.sum(1).astype(int)
    Pu = np.where(t[:, None] > 0, C / np.maximum(t[:, None], 1), 0)
    v = []
    for _ in range(B):
        R = np.array([rng.multinomial(n, p / p.sum()) if n > 0 else np.zeros_like(p) for n, p in zip(t, Pu)])
        v.append(f(R))
    v = np.array(v)
    return float(v.mean()), float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))
