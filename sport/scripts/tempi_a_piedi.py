"""Sport v2: minuti a piedi al luogo piu' vicino per quartiere e per citta' (stesso metodo di sport/scripts/analisi.py).
Uso: python -I -X utf8 calcola.py <ABS sport> <ABS citta-15-minuti>  -> data/sport_tempi.json"""
import sys, json
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse import load_npz, csr_matrix
from scipy.sparse.csgraph import dijkstra
S, C = sys.argv[1].rstrip('\/'), sys.argv[2].rstrip('\/'); O = C + '/out/'
SPEED = 4.5/3.6; LIM = 3200.0; MAXSNAP = 150.0
P = pd.read_csv(S + '/pulito/siti.csv', dtype={'ID_NIL': 'Int64'})
nil = pd.read_csv(O + 'nil_punteggi.csv')[['ID_NIL', 'NIL_nome', 'residenti_2025']]; nil['ID_NIL'] = nil.ID_NIL.astype(int)
imp = P.livello == 'impianto'
com = P.gestione.isin(['milanosport', 'comune_concessione', 'comune_da_verificare'])
GRP = {'piscine': imp & P.piscina, 'palestre': imp & P.palestra, 'campi': P.campo, 'tutti': imp,
       'comunali': imp & com, 'milanosport': P.gestione == 'milanosport', 'piscine_comunali': imp & P.piscina & com,
       'piscine_altro': imp & P.piscina & ~com}
G = load_npz(O + 'grafo_pedonale_csr.npz'); nd = np.load(O + 'grafo_pedonale_nodi.npz'); N = G.shape[0]
tree = cKDTree(np.c_[nd['x'], nd['y']])
c = pd.read_csv(O + 'civici_tempi.csv', usecols=['IDMASTER', 'ID_NIL', 'RESIDENZIALE', 'x', 'y', 'snap_m'])
c['node'] = tree.query(np.c_[c.x.values, c.y.values])[1]
dist, nodes = tree.query(np.c_[P.x.values, P.y.values]); P['node'] = nodes; P['snap_m'] = dist
indptr = G.indptr; ind = G.indices; dat = G.data
base_r = np.repeat(np.arange(N), np.diff(indptr))
def minutes(sub):
    sub = sub[sub.snap_m <= MAXSNAP]
    best = pd.DataFrame({'n': sub.node.values, 's': sub.snap_m.values}).groupby('n', as_index=False).s.min()
    A = csr_matrix((np.r_[dat, best.s.values + 0.01], (np.r_[base_r, np.full(len(best), N)], np.r_[ind, best.n.values])), shape=(N + 1, N + 1))
    dn = dijkstra(A, directed=True, indices=N, limit=LIM)[:N]
    dm = dn[c.node.values] + c.snap_m.values
    return np.round(np.where(dm > LIM + MAXSNAP, np.nan, dm / SPEED / 60.0), 2)
res = c[(c.RESIDENZIALE == 1) & c.ID_NIL.notna()].copy(); res['ID_NIL'] = res.ID_NIL.astype(int)
pop = nil.set_index('ID_NIL').residenti_2025
res['peso'] = res.ID_NIL.map(pop) / res.ID_NIL.map(res.groupby('ID_NIL').size()); res = res[res.peso.notna()]
def wmed(v, w):
    o = np.argsort(v); cw = np.cumsum(w[o]); return float(v[o][np.searchsorted(cw, cw[-1]/2)])
OUT = {'residenti': int(res.peso.sum()), 'citta': {}, 'nil': {}}
for g, m in GRP.items():
    t = pd.Series(minutes(P[m]), index=c.index).loc[res.index].fillna(99).values
    w = res.peso.values; tot = w.sum()
    OUT['citta'][g] = {'b5': float(w[t <= 5].sum()/tot), 'b10': float(w[t <= 10].sum()/tot), 'b15': float(w[t <= 15].sum()/tot), 'med': round(wmed(t, w), 1), 'n': int(m.sum())}
    if g in ('piscine', 'palestre', 'campi'):
        for nid, d in res.assign(t=t).groupby('ID_NIL'):
            OUT['nil'].setdefault(int(nid), {})[g] = round(wmed(d.t.values, d.peso.values), 1)
json.dump(OUT, open('data/sport_tempi.json', 'w', encoding='utf-8'), separators=(',', ':'))
print(json.dumps(OUT['citta'], indent=1)); print(len(OUT['nil']))
