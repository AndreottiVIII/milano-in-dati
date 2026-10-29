import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, collections
from f2_motore import *
from f2_geocode import Geocoder
S = sys.argv[1]
m = Motore(S, verbose=False); g = Geocoder(S)
a = g.indirizzo(sys.argv[2])[0]; b = g.indirizzo(sys.argv[3])[0]
D = m.dest([b[0]], [b[1]]); ox, oy = xy_of(*a); o = (float(ox[0]), float(oy[0]))
n, sn = m._snap(m.tb, *o)
dist, pred = dijkstra(m.Gb, directed=True, indices=n, return_predecessors=True)
v = D.b_node[0]; path = [v]
while pred[v] >= 0: v = pred[v]; path.append(v)
path = path[::-1]; c = m.b; ip, ix = c['indptr'], c['indices']
kk = np.array([np.where(ix[ip[p]:ip[p+1]] == q)[0][0] + ip[p] for p, q in zip(path[:-1], path[1:])])
ln = c['len'][kk]; t = c['t0'][kk]; pen = c['pen'][kk]
ride = t - pen; spd = ln / np.maximum(ride, 1e-3) * 3.6
print('tempo totale', t.sum()/60, 'min; lunghezza', ln.sum()/1000, 'km; penalita', pen.sum()/60, 'min; semafori eq', c['sigp'][kk].sum(), 'incroci maggiori', c['mcross'][kk].sum())
bins = [(0,6,'<6 (a mano)'),(6,11,'6-11'),(11,13.5,'11-13.5'),(13.5,16,'>=13.5')]
for lo,hi,nm in bins:
    mk = (spd>=lo)&(spd<hi); print(nm, round(ln[mk].sum()/1000,2),'km', round(ride[mk].sum()/60,1),'min')
print('velocita media di marcia (senza penalita)', ln.sum()/ride.sum()*3.6)
