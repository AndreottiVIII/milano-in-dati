"""Funzioni comuni della verifica indipendente. Nessuna dipendenza da incroci-esplorativi/."""
import json, math, os
import numpy as np, pandas as pd
from scipy import stats

R = r'C:\Users\davide\Desktop\ClaudeTower\milano-in-dati'
OUT = os.path.join(R, 'incroci-esplorativi', 'verifica', 'out')
DUOMO = (45.4642, 9.1900)
SEED = 20261102
ELEZ_POL = ['comunali_consiglio_2016-06-05', 'camera_2018-03-04', 'senato_2018-03-04', 'regionali_consiglio_2018-03-04',
            'europee_2019-05-26', 'comunali_consiglio_2021-10-03', 'camera_2022-09-25', 'senato_2022-09-25',
            'regionali_consiglio_2023-02-12', 'europee_2024-06-08']
# elezioni "principali" (senato e regionali restano a parte per non contare due volte)
ELEZ_MAIN = ['comunali_consiglio_2016-06-05', 'camera_2018-03-04', 'europee_2019-05-26', 'comunali_consiglio_2021-10-03',
             'camera_2022-09-25', 'regionali_consiglio_2023-02-12', 'europee_2024-06-08']
SX = ['Sinistra', 'Centrosinistra']
DX = ['Centrodestra', 'Lega', 'Destra']


def p(*a):
    return os.path.join(R, *a)


def _ring_cent(ring):
    # baricentro e area (coordinate proiettate semplici in km)
    x = np.array([c[0] for c in ring]); y = np.array([c[1] for c in ring])
    cr = x[:-1] * y[1:] - x[1:] * y[:-1]
    A = cr.sum() / 2
    if abs(A) < 1e-12:
        return x.mean(), y.mean(), 0.0
    return ((x[:-1] + x[1:]) * cr).sum() / (6 * A), ((y[:-1] + y[1:]) * cr).sum() / (6 * A), abs(A)


def geometrie():
    g = json.load(open(p('docs', 'elezioni', 'data', 'nil.geojson'), encoding='utf8'))
    rows = []
    kx = 111.32 * math.cos(math.radians(DUOMO[0])); ky = 110.57
    for f in g['features']:
        pr = f['properties']
        idn = pr['n']
        geom = f['geometry']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        sx = sy = sa = 0.0
        for poly in polys:
            ring = [((c[0] - DUOMO[1]) * kx, (c[1] - DUOMO[0]) * ky) for c in poly[0]]
            cx, cy, a = _ring_cent(ring)
            sx += cx * a; sy += cy * a; sa += a
        rows.append(dict(id_nil=int(idn), cx=sx / sa, cy=sy / sa, area_geo=sa, dist_duomo=math.hypot(sx / sa, sy / sa)))
    return pd.DataFrame(rows)


def base():
    """Tabella NIL: residenti, età, densità, distanza, reddito, laureati."""
    e = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv'))
    e24 = e[e.anno == 2024].copy()
    b = e24[['id_nil', 'nil', 'residenti', 'eta_media', 'q_65p', 'q_80p', 'q_90p', 'quota_stranieri', 'area_km2', 'densita_ab_km2']].copy()
    b = b.merge(geometrie(), on='id_nil', how='left')
    q = pd.read_csv(p('quartieri-che-cambiano', 'out', 'indicatori_nil.csv'))
    b = b.merge(q[['id_nil', 'reddito_2024', 'quota_civici_cap_instabili', 'prezzo_2026_reale', 'affitto_2026_reale']], on='id_nil', how='left')
    c = pd.read_csv(p('censimenti', 'pulito', 'indicatori_NIL.csv'))
    for an in [1991, 2001, 2011, 2021, 2023]:
        s = c[c.anno == an].set_index('nil')
        b[f'laur_{an}'] = b.id_nil.map(s.quota_laureati_su_residenti)
        b[f'laurb_{an}'] = b.id_nil.map(s.quota_laureati_su_base)
        b[f'pop_{an}'] = b.id_nil.map(s['pop'])
    s = c[c.anno == 2023].set_index('nil')
    b['fam_comp_2023'] = b.id_nil.map(s.famiglie_comp_medio_approx)
    b['municipio'] = b.id_nil.map(s.municipio_prevalente)
    return b


def nil3000(b=None, soglia=3000):
    if b is None:
        b = base()
    return b[b.residenti >= soglia].copy()


_idx = None
def indice():
    global _idx
    if _idx is None:
        _idx = json.load(open(p('docs', 'elezioni', 'data', 'index.json'), encoding='utf8'))
    return _idx


def elezione(eid, fonte='json'):
    """Quote per famiglia, votanti/elettori per NIL da docs/elezioni/data/nil/<id>.json."""
    idx = indice()
    meta = [x for x in idx['elezioni'] if x['id'] == eid][0]
    fam = meta['fam']; par = meta['par']
    d = json.load(open(p('docs', 'elezioni', 'data', 'nil', eid + '.json'), encoding='utf8'))
    rows = []
    for k, v in d['p'].items():
        r = dict(id_nil=int(k), e=v.get('e', np.nan), vt=v.get('vt', np.nan), ns=v.get('ns', np.nan))
        vv = v['v']
        tot = sum(vv)
        for f in fam:
            r[f] = 0.0
        for (nome, fi), x in zip(par, vv):
            r[fam[fi]] += x
        r['tot'] = tot
        r['_v'] = vv
        rows.append(r)
    o = pd.DataFrame(rows)
    for f in fam:
        o['q_' + f] = o[f] / o.tot * 100
    o['aff'] = o.vt / o.e * 100
    o['q_sx'] = sum(o[f] for f in SX if f in o) / o.tot * 100
    o['q_dx'] = sum(o[f] for f in DX if f in o) / o.tot * 100
    o['q_ce'] = o['Centro'] / o.tot * 100 if 'Centro' in o else np.nan
    o['q_m5'] = o['M5S'] / o.tot * 100 if 'M5S' in o else np.nan
    return o.drop(columns=['_v'])


def rk(x):
    return pd.Series(x).rank(method='average').values


def _res(y, Z):
    if Z is None or Z.shape[1] == 0:
        return y - y.mean()
    A = np.column_stack([np.ones(len(y)), Z])
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    return y - A @ b


def parz(x, y, Z=None):
    """Correlazione parziale sui ranghi. Z = matrice dei controlli (non ancora in ranghi)."""
    rx, ry = rk(x), rk(y)
    if Z is not None and Z.shape[1] > 0:
        rz = np.column_stack([rk(Z[:, j]) for j in range(Z.shape[1])])
    else:
        rz = None
    ex, ey = _res(rx, rz), _res(ry, rz)
    d = np.sqrt((ex ** 2).sum() * (ey ** 2).sum())
    return float((ex * ey).sum() / d) if d > 0 else np.nan


def analisi(df, x, y, ctrl=None, B=2000, top=5, seed=SEED):
    """n, r, IC bootstrap 95%, r senza i 5 NIL più influenti (togliendone uno alla volta)."""
    cols = [x, y] + (list(ctrl) if ctrl else [])
    d = df.dropna(subset=cols)
    X = d[x].values.astype(float); Y = d[y].values.astype(float)
    Z = d[list(ctrl)].values.astype(float) if ctrl else None
    r = parz(X, Y, Z)
    n = len(d)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        bs.append(parz(X[i], Y[i], Z[i] if Z is not None else None))
    bs = np.array(bs)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    # influenza: delta da leave-one-out
    deltas = []
    for j in range(n):
        m = np.ones(n, bool); m[j] = False
        deltas.append(parz(X[m], Y[m], Z[m] if Z is not None else None) - r)
    deltas = np.array(deltas)
    idx_top = np.argsort(-np.abs(deltas))[:top]
    m = np.ones(n, bool); m[idx_top] = False
    r5 = parz(X[m], Y[m], Z[m] if Z is not None else None)
    # versione "avversa": toglie i 5 che più spingono il coefficiente nella sua direzione
    idx_adv = np.argsort(np.sign(r) * deltas)[:top]
    m = np.ones(n, bool); m[idx_adv] = False
    r5a = parz(X[m], Y[m], Z[m] if Z is not None else None)
    nomi = list(d.iloc[idx_top]['nil']) if 'nil' in d else []
    return dict(n=n, r=round(r, 3), lo=round(float(lo), 3), hi=round(float(hi), 3), r_senza5=round(r5, 3), r_senza5_avverso=round(r5a, 3), top5=';'.join(map(str, nomi)))


CTRL = ['dist_duomo', 'reddito_2024', 'eta_media', 'densita_ab_km2']


def fmt(a):
    return f"n={a['n']} r={a['r']:+.3f} [{a['lo']:+.3f},{a['hi']:+.3f}] senza5={a['r_senza5']:+.3f} (avverso {a['r_senza5_avverso']:+.3f})"


def hac_ols(y, X, lags=7):
    """OLS con errori Newey-West. X include la costante. Restituisce beta, se."""
    y = np.asarray(y, float); X = np.asarray(X, float)
    XtX_inv = np.linalg.pinv(X.T @ X)
    b = XtX_inv @ X.T @ y
    u = y - X @ b
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = Xu[L:].T @ Xu[:-L]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    return b, np.sqrt(np.diag(V)), u
