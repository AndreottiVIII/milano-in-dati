import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, collections
from f2_motore import *
from f2_geocode import Geocoder
S = sys.argv[1]
m = Motore(S, verbose=False); g = Geocoder(S)
a = g.indirizzo(sys.argv[2])[0]; b = g.indirizzo(sys.argv[3])[0]
D = m.dest([b[0]], [b[1]]); ox, oy = xy_of(*a); o = (float(ox[0]), float(oy[0]))
n, sn = m._snap(m.tc, *o, m.car_snap_ids)
dist, pred = dijkstra(m.Gc[0], directed=True, indices=n, return_predecessors=True)
v = D.c_node[0]; path = [v]
while pred[v] >= 0: v = pred[v]; path.append(v)
path = path[::-1]; c = m.c; ip, ix = c['indptr'], c['indices']
byc = collections.Counter(); tt = collections.Counter()
for p, q in zip(path[:-1], path[1:]):
    k = np.where(ix[ip[p]:ip[p+1]] == q)[0][0] + ip[p]
    nm = m.cls_names[c['cls'][k]]; byc[nm] += c['len'][k]; tt[nm] += m.Gc[0].data[k]
print('tempo', dist[D.c_node[0]]/60, 'snap', sn, D.c_snap)
for k in byc: print(k, round(byc[k]/1000,1), 'km', round(tt[k]/60,1), 'min')
xs = c['x'][path]; ys = c['y'][path]
print('punti ogni 25 nodi:', [(round(float(x)), round(float(y))) for x, y in zip(xs[::max(1,len(path)//12)], ys[::max(1,len(path)//12)])])
