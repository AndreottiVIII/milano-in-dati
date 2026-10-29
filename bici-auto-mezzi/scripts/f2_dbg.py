import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from f2_motore import *
S = sys.argv[1]
m = Motore(S, verbose=False)
D = m.dest([9.2036], [45.4859])
ox, oy = xy_of(9.1859, 45.4642); o = (float(ox[0]), float(oy[0]))
n, sn = m._snap(m.tb, *o); print('snap origin', sn, 'dest snap', D.b_snap, D.c_snap)
dist, pred = dijkstra(m.Gb, directed=True, indices=n, return_predecessors=True)
v = D.b_node[0]; path = [v]
while pred[v] >= 0: v = pred[v]; path.append(v)
path = path[::-1]
b = m.b; ip = b['indptr']; ix = b['indices']
tot = 0; L = 0; pen = 0
for a, c in zip(path[:-1], path[1:]):
    k = np.where(ix[ip[a]:ip[a+1]] == c)[0][0] + ip[a]
    L += b['len'][k]; tot += b['t0'][k]
print('nodi', len(path), 'lunghezza', L, 'tempo', tot/60, 'min; velocita media', L/tot*3.6)
print('infra share', sum(b['len'][np.where(ix[ip[a]:ip[a+1]] == c)[0][0] + ip[a]] for a,c in zip(path[:-1],path[1:]) if b['infra'][np.where(ix[ip[a]:ip[a+1]] == c)[0][0] + ip[a]]) / L)
nf = np.load(S+'/out/nodi_flag.npz')
no = b['node_old'][path]
print('semafori sul percorso', nf['sig_any'][no].sum(), 'major', nf['major_node'][no].sum())
kk = [np.where(ix[ip[a]:ip[a+1]] == c)[0][0] + ip[a] for a,c in zip(path[:-1],path[1:])]
print('penalita totale min', b['pen'][kk].sum()/60, 'semafori eq', b['sigp'][kk].sum(), 'incroci maggiori', b['mcross'][kk].sum())
