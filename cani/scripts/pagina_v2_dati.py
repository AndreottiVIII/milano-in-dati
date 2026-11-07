"""Dati nuovi per la pagina Cani (versione 2).
Calcola, sulla stessa rete pedonale della pagina "La citta dei 15 minuti" (4,5 km/h, tetto 3.200 m),
i minuti a piedi da ogni civico residenziale all'area cani del Comune (ds52, 423 aree) piu vicina,
e quale area e la piu vicina. Aggrega per quartiere (NIL) pesando i residenti ds205 2024.
Uso: python -I -X utf8 pagina_v2_dati.py <ABS citta-15-minuti> <ABS docs/cani>
Scrive in <docs/cani>/data/: quartieri_cani_v2.geojson, aree_punti_v2.json, cammino_cani_v2.json (nomi nuovi, nessun file vecchio toccato)."""
import sys, json
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse import load_npz, csr_matrix
from scipy.sparse.csgraph import dijkstra

S, DOC = sys.argv[1], sys.argv[2]
O = S + '/out/'
DD = DOC + '/data/'
SPEED = 4.5 / 3.6
LIM = 3200.0
MAXSNAP = 150.0
G = load_npz(O + 'grafo_pedonale_csr.npz')
nd = np.load(O + 'grafo_pedonale_nodi.npz')
N = G.shape[0]
tree = cKDTree(np.c_[nd['x'], nd['y']])
c = pd.read_csv(O + 'civici_tempi.csv', dtype={'CAP': str})
c = c[(c.RESIDENZIALE == 1) & c.ID_NIL.notna()].copy()
c['ID_NIL'] = c.ID_NIL.astype(int)
c['node'] = tree.query(np.c_[c.x.values, c.y.values])[1]
sv = pd.read_csv(O + 'extra_servizi_puliti.csv')
sv = sv[(sv.tipo == 'cani') & (sv['sub'] == 'Comune')].reset_index(drop=True)
assert len(sv) == 423, len(sv)

# abbina ogni area del servizio a una area del file del sito (stesso punto)
AF = json.load(open(DD + 'aree.geojson', encoding='utf-8'))['features']
ap = pd.DataFrame([dict(f['properties']) for f in AF])
kt = cKDTree(np.c_[ap.x.values, ap.y.values])
d, ix = kt.query(np.c_[sv.lon.values, sv.lat.values])
assert d.max() < 0.0005, d.max()
sv['aid'] = ap.i.values[ix]
assert sv.aid.nunique() == 423

# rete con nodo virtuale: un arco per ogni area, di peso = distanza di aggancio
ind = G.indices
ptr = G.indptr
dat = G.data
r = np.r_[np.repeat(np.arange(N), np.diff(ptr)), np.full(len(sv), N)]
cc = np.r_[ind, sv.node.values]
vv = np.r_[dat, sv.snap_m.values + 0.01]
A = csr_matrix((vv, (r, cc)), shape=(N + 1, N + 1))
dist, pred = dijkstra(A, directed=True, indices=N, limit=LIM, return_predecessors=True)
dist = dist[:N]
pred = pred[:N]

# nodo di ingresso: risalire i predecessori fino a quello che parte dal nodo virtuale
root = np.arange(N)
for _ in range(10000):
    p = pred[root]
    mv = (p != N) & (p >= 0)
    if not mv.any():
        break
    root = np.where(mv, p, root)
sv2 = sv.sort_values('snap_m').drop_duplicates('node')
n2a = dict(zip(sv2.node, sv2.aid))
dm = dist[c.node.values] + c.snap_m.values
c['min'] = np.round(np.where(dm > LIM + MAXSNAP, np.nan, dm / SPEED / 60), 2)
c['aid'] = [n2a.get(int(root[n])) if np.isfinite(dist[n]) else None for n in c.node.values]

# pesi: residenti ds205 2024 del quartiere divisi tra i suoi civici residenziali
NF = json.load(open(DD + 'nil.geojson', encoding='utf-8'))
nilp = {f['properties']['i']: f['properties'] for f in NF['features']}
cnt = c.groupby('ID_NIL').size()
c['peso'] = [nilp[i]['ab'] / cnt[i] if i in nilp else np.nan for i in c.ID_NIL]
c = c[c.peso.notna()].copy()


def wmed(v, w):
    o = np.argsort(v)
    cw = np.cumsum(w[o])
    return float(v[o][np.searchsorted(cw, cw[-1] / 2)])


v_ = c['min'].fillna(99).values
w = c.peso.values
tot = w.sum()
R = {'residenti_pesati': round(float(tot)), 'civici': int(len(c)), 'mediana_min': round(wmed(v_, w), 1),
     'media_min': round(float((v_ * w).sum() / tot), 1)}
cuts = [(0, 3), (3, 5), (5, 10), (10, 15), (15, 999)]
R['classi'] = [{'da': a, 'a': b, 'quota': round(float(w[(v_ >= a) & (v_ < b)].sum() / tot), 4)} for a, b in cuts]
R['entro'] = {str(m): round(float(w[v_ <= m].sum() / tot), 4) for m in (3, 5, 10, 15)}
R['curva'] = [round(float(w[v_ <= m].sum() / tot), 3) for m in range(0, 21)]
R['senza_tempo'] = round(float(w[np.isnan(c['min'].values)].sum() / tot), 5)

res = {}
for i, g in c.groupby('ID_NIL'):
    v = g['min'].fillna(99).values
    ww = g.peso.values
    if ww.sum() <= 0:
        continue
    m = g.dropna(subset=['aid']).groupby('aid').peso.sum().sort_values(ascending=False)
    res[int(i)] = {'med': round(wmed(v, ww), 1), 'q5': round(float(ww[v <= 5].sum() / ww.sum()), 3),
                   'q10': round(float(ww[v <= 10].sum() / ww.sum()), 3),
                   'cu': [round(float(ww[v <= m].sum() / ww.sum()), 3) for m in range(0, 21)],
                   'near': int(m.index[0]) if len(m) else None,
                   'near_q': round(float(m.iloc[0] / ww.sum()), 2) if len(m) else None}
areaprop = {int(p.i): p for p in ap.itertuples()}
nilname = {i: nilp[i]['n'] for i in nilp}
big = [p for p in nilp.values() if p['cl'] == 1]
pv = sorted(round(p['p'] / 10, 2) for p in big)
nb = len(pv)
R['soglie_classi_per_10mila'] = [pv[nb // 4 - 1], pv[nb // 2 - 1], pv[3 * nb // 4 - 1]]
feats = []
for f in NF['features']:
    p = f['properties']
    i = p['i']
    o = res.get(i, {})
    q = {'i': i, 'n': p['n'], 'mu': p['mun'], 'ab': p['ab'], 'km2': p['km2'], 'a': p['a'], 'mq': p['mq'],
         'big': 1 if p['cl'] == 1 else 0}
    q['p10'] = round(p['p'] / 10, 2) if p['cl'] == 1 else None
    q['ak'] = round(p['a'] / p['km2'], 1)
    if o:
        q['med'] = o['med']
        q['q5'] = o['q5']
        q['q10'] = o['q10']
        q['cu'] = o['cu']
        if o['near'] is not None:
            ar = areaprop[o['near']]
            q['nl'] = ar.l
            q['nm'] = int(ar.mq)
            q['nn'] = nilname.get(ar.n, '')
            q['nq'] = o['near_q']
    feats.append({'type': 'Feature', 'geometry': f['geometry'], 'properties': q})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(DD + 'quartieri_cani_v2.geojson', 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))
pts = [[int(p.i), p.l, int(p.mq), int(p.n), int(p.m), round(p.x, 5), round(p.y, 5), (None if pd.isna(p.a) else int(p.a))] for p in ap.itertuples()]
json.dump({'campi': ['id', 'nome', 'mq', 'nil', 'municipio', 'lon', 'lat', 'anno_scheda'], 'aree': pts},
          open(DD + 'aree_punti_v2.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(R, open(DD + 'cammino_cani_v2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
