import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from scipy.sparse.csgraph import dijkstra
from f2_motore import Motore, xy_of
import f2_parametri as P
S = sys.argv[1]
d = pd.read_csv(S + '/tragitti_prova.csv', sep=';', decimal=',', encoding='utf-8-sig')
m = Motore(S, verbose=False); b = m.b
for n in [int(a) for a in sys.argv[2:]]:
    r = d[d.n == n].iloc[0]
    ox, oy = xy_of(r.lon_partenza, r.lat_partenza); dx, dy = xy_of(r.lon_arrivo, r.lat_arrivo)
    so, sn = m._snap(m.tb, ox[0], oy[0]); de, dn = m._snap(m.tb, dx[0], dy[0])
    dist, pred = dijkstra(m.Gb, directed=True, indices=so, return_predecessors=True)
    path = [de]
    while path[-1] != so: path.append(pred[path[-1]])
    path = path[::-1]
    tot_len = tot_pen = 0; ninf = 0; nsig = 0; nmc = 0; tcls = {}
    for u, v in zip(path[:-1], path[1:]):
        k = np.where(b['indices'][b['indptr'][u]:b['indptr'][u + 1]] == v)[0][0] + b['indptr'][u]
        tot_len += b['len'][k]; tot_pen += b['pen'][k]; nsig += b['sigp'][k]; nmc += b['mcross'][k]
        ninf += b['len'][k] if b['infra'][k] else 0
    print(n, 'straight', r.km_in_linea_retta, 'bike_s', dist[de], 'min', round(dist[de]/60,1), 'len km', round(tot_len/1000,2), 'pen s', tot_pen, 'sig', round(nsig,1), 'mcross', nmc, 'infra km', round(ninf/1000,2), 'snap', round(sn), round(dn), 'google', r.google_bici_min)
