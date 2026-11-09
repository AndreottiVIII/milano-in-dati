"""Minuti a piedi dai civici residenziali all'ospedale e al pronto soccorso piu vicini.
Usa la rete pedonale gia costruita per la pagina "Citta in 15 minuti" (solo lettura; 4,5 km/h).
Uso: python -I -X utf8 05_minuti.py  -> pulito/minuti_nil.csv, pulito/minuti_riepilogo.json"""
import json, pathlib
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.sparse import load_npz, csr_matrix
from scipy.sparse.csgraph import dijkstra
B = pathlib.Path(__file__).resolve().parent.parent
C15 = B.parent / 'citta-15-minuti' / 'out'
SPEED = 4.5/3.6; MAXSNAP = 150.0; LIM = 9000.0
tr = Transformer.from_crs(4326, 32632, always_xy=True)
G = load_npz(C15/'grafo_pedonale_csr.npz'); nd = np.load(C15/'grafo_pedonale_nodi.npz')
gx, gy = nd['x'], nd['y']; N = G.shape[0]; tree = cKDTree(np.c_[gx, gy])
P = json.load(open(B/'pulito/punti.json', encoding='utf-8'))
cv = pd.read_csv(C15/'civici_tempi.csv', usecols=['ID_NIL','NIL','RESIDENZIALE','x','y'])
cv = cv[(cv.RESIDENZIALE > 0) & cv.ID_NIL.notna()].reset_index(drop=True)
d, i = tree.query(np.c_[cv.x, cv.y]); cv['node'] = i; cv['snap'] = d
indptr, ind, dat = G.indptr, G.indices, G.data
def tempi(punti):
    """Un Dijkstra per ogni punto (22 + 32 in tutto): distanza in metri dal punto a ogni civico, e quale e il piu vicino."""
    x, y = tr.transform([p['lon'] for p in punti], [p['lat'] for p in punti])
    dd, nn = tree.query(np.c_[x, y]); assert (dd <= MAXSNAP).all(), [punti[k]['nome'] for k in np.where(dd > MAXSNAP)[0]]
    M = np.full((len(punti), len(cv)), np.inf)
    for k in range(len(punti)):
        r = np.r_[np.repeat(np.arange(N), np.diff(indptr)), [N]]; c = np.r_[ind, [nn[k]]]; v = np.r_[dat, [dd[k] + 0.01]]
        t = dijkstra(csr_matrix((v, (r, c)), shape=(N+1, N+1)), directed=True, indices=N, limit=LIM)[:N]
        M[k] = t[cv.node.values] + cv.snap.values
    return M
res = {}
gruppi = {'osp': P['ospedali'], 'ps_g': [p for p in P['ps'] if p['tipo']=='g'], 'ps_tutti': P['ps']}
for k, pts in gruppi.items():
    M = tempi(pts); best = M.argmin(axis=0)
    cv['m_'+k] = M.min(axis=0)/SPEED/60.0
    cv['p_'+k] = [pts[o]['nome'] for o in best]

nil = pd.read_csv(B.parent/'docs/medici-farmacie/data/nil.csv', sep=';', usecols=['id_nil','quartiere_nil','residenti_2025'])
nil = nil.rename(columns={'id_nil':'ID_NIL'})
out = []
for idn, g in cv.groupby('ID_NIL'):
    r = dict(id=int(idn), n_civici=len(g))
    for k in gruppi:
        r['min_'+k] = round(float(g['m_'+k].median()), 1)
        r['p_'+k] = g['p_'+k].value_counts().index[0]
    out.append(r)
o = pd.DataFrame(out).merge(nil.rename(columns={'ID_NIL':'id'}), on='id', how='right')
o.to_csv(B/'pulito/minuti_nil.csv', index=False, encoding='utf-8')
# riepilogo cittadino pesato per residenti (residenti del quartiere divisi in parti uguali tra i suoi civici)
w = cv.merge(nil, on='ID_NIL'); w['w'] = w.residenti_2025 / w.groupby('ID_NIL').ID_NIL.transform('size')
def q(col, soglia): return float(w.loc[w[col] <= soglia, 'w'].sum() / w.w.sum())
def med(col):
    s = w.sort_values(col); cs = s.w.cumsum() / s.w.sum(); return float(s[col][cs >= .5].iloc[0])
R = {'residenti_considerati': int(w.w.sum()), 'civici': len(cv)}
for k in gruppi:
    bins = [0, 15, 25, 35, 45, 1e9]
    quote = [round(float(w.loc[(w['m_'+k] > bins[j]) & (w['m_'+k] <= bins[j+1]), 'w'].sum() / w.w.sum()), 4) for j in range(5)]
    R[k] = dict(quote=quote, mediana=round(med('m_'+k),1), entro10=round(q('m_'+k,10),3), entro15=round(q('m_'+k,15),3), oltre20=round(1-q('m_'+k,20),3), oltre30=round(1-q('m_'+k,30),3))
json.dump(R, open(B/'pulito/minuti_riepilogo.json','w',encoding='utf-8'), indent=1, ensure_ascii=False)
print(json.dumps(R, indent=1)); print(o.sort_values('min_ps_g').tail(8)[['id','quartiere_nil','min_ps_g','p_ps_g','min_osp']])
print(o.sort_values('min_ps_g').head(5)[['id','quartiere_nil','min_ps_g','p_ps_g']])
