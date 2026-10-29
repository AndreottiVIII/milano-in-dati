"""Fase 2: prove di sensibilita' (biblioteche con OSM, mercati solo coperti, soglie 10/12/20 minuti).
Uso: python -I f2_sens.py <ABS strand>"""
import sys, glob, json
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.sparse import load_npz, csr_matrix
from scipy.sparse.csgraph import dijkstra
S = sys.argv[1]; R = S + '/raw/comune_milano/'; O = S + '/out/'
SPEED = 4.5 / 3.6
c = pd.read_csv(O + 'civici_tempi.csv', dtype={'CAP': str})
p = pd.read_csv(glob.glob(R + 'pop_cittadinanza_quartiere/estratto/*.csv')[0], sep=';', usecols=['Anno', 'IdNil', 'Residenti'])
p = p[p.Anno == 2025].groupby('IdNil').Residenti.sum()
res = (c.RESIDENZIALE == 1) & c.ID_NIL.notna()
cnt = c[res].groupby('ID_NIL').size()
w = np.where(res, c.ID_NIL.map(p) / c.ID_NIL.map(cnt), 0.0); w = np.nan_to_num(w)
TIPI = ['farmacie', 'medici', 'nidi', 'scuole', 'biblioteche', 'mercati', 'parchi', 'sport', 'poste', 'vicinato']
def share(mask): return float((w * mask).sum() / w.sum())
out = {}
# soglie diverse
for th in [10, 12, 15, 20]:
    sc = (c[['min_' + t for t in TIPI]] <= th).sum(axis=1)
    out[f'soglia_{th}min'] = {'punteggio_medio': round(float((w * sc).sum() / w.sum()), 3), 'quota_tutti_10': round(share(sc == 10), 4),
                              'quota_biblioteche': round(share(c.min_biblioteche <= th), 4), 'quota_parchi': round(share(c.min_parchi <= th), 4), 'quota_poste': round(share(c.min_poste <= th), 4)}
# mercati solo coperti
sc = (c[[('min_mercato_coperto' if t == 'mercati' else 'min_' + t) for t in TIPI]] <= 15).sum(axis=1)
out['mercati_solo_coperti'] = {'quota_mercati_entro15': round(share(c.min_mercato_coperto <= 15), 4), 'punteggio_medio': round(float((w * sc).sum() / w.sum()), 3), 'quota_tutti': round(share(sc == 10), 4)}
# punteggio senza biblioteche (9 tipi)
t9 = [t for t in TIPI if t != 'biblioteche']; sc9 = (c[['min_' + t for t in t9]] <= 15).sum(axis=1)
out['senza_biblioteche_9_tipi'] = {'punteggio_medio': round(float((w * sc9).sum() / w.sum()), 3), 'quota_tutti_9': round(share(sc9 == 9), 4)}
# biblioteche: Sistema bibliotecario + tutte le biblioteche OSM dentro il Comune
G = load_npz(O + 'grafo_pedonale_csr.npz'); nd = np.load(O + 'grafo_pedonale_nodi.npz'); N = G.shape[0]
tree = cKDTree(np.c_[nd['x'], nd['y']]); tr = Transformer.from_crs(4326, 32632, always_xy=True)
sv = pd.read_csv(O + 'servizi_puliti.csv'); sb = sv[sv.tipo == 'biblioteche']
po = pd.read_csv(S + '/raw/osm_poi/osm_poi_milano_estratto.csv'); po = po[(po.tag == 'library') & (po.fascia == 'dentro')]
x, y = tr.transform(po.lon.values, po.lat.values); d, i = tree.query(np.c_[x, y]); ok = d <= 150
nodes = np.r_[sb.node.values, i[ok]]; sn = np.r_[sb.snap_m.values, d[ok]]
best = pd.DataFrame({'n': nodes, 's': sn}).groupby('n', as_index=False).s.min()
r = np.r_[np.repeat(np.arange(N), np.diff(G.indptr)), np.full(len(best), N)]
A = csr_matrix((np.r_[G.data, best.s.values + 0.01], (r, np.r_[G.indices, best.n.values])), shape=(N + 1, N + 1))
dist = dijkstra(A, directed=True, indices=N, limit=3200)[:N]
cs, cn = tree.query(np.c_[c.x.values, c.y.values]); mt = (dist[cn] + cs) / SPEED / 60
out['biblioteche_con_OSM'] = {'punti_Sistema': len(sb), 'punti_OSM_library_dentro_Comune': int(ok.sum()), 'quota_residenti_entro15': round(share(mt <= 15), 4),
                              'quota_residenti_entro15_solo_Sistema': round(share(c.min_biblioteche <= 15), 4)}
sc_o = (c[['min_' + t for t in t9]] <= 15).sum(axis=1) + (mt <= 15)
out['biblioteche_con_OSM']['quota_tutti_10'] = round(share(sc_o == 10), 4)
json.dump(out, open(O + 'sensibilita_fase2.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
