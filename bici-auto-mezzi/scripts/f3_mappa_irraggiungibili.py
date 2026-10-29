"""Verifica mezzi: mappa dei quadrati (250 m) senza nessuna fermata entro 800 m a piedi, divisi per tipo.
Uso: python -I f3_mappa_irraggiungibili.py <ABS strand> -> out/mappa_irraggiungibili.png, out/irraggiungibili.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from f2_motore import Motore
S = sys.argv[1]
m = Motore(S, verbose=False); z = np.load(S + '/out/celle.npz'); D = m.dest(z['lon'], z['lat'])
un = np.diff(D.eg_ptr) == 0
w = m.w; t = cKDTree(np.c_[w['x'], w['y']])
dens = np.array([len(t.query_ball_point([D.x[i], D.y[i]], 180)) for i in range(len(D.x))])
snap = D.w_snap
cat = np.where(~un, 0, np.where(snap > 100, 1, np.where(dens >= 60, 3, 2)))
nome = {0: 'con fermata', 1: 'senza fermata: a piu di 100 m da ogni strada o sentiero (parchi, campi, scali ferroviari)', 2: 'senza fermata: poche strade attorno', 3: 'senza fermata: strade fitte ma nessuna fermata entro 800 m'}
col = {0: '#dddddd', 1: '#009E73', 2: '#E69F00', 3: '#D55E00'}
fig, ax = plt.subplots(figsize=(9, 9))
for k in (0, 1, 2, 3):
    s = cat == k; ax.scatter(D.x[s], D.y[s], s=9 if k else 4, c=col[k], marker='s', label='%s (%d)' % (nome[k], s.sum()), linewidths=0)
used = np.zeros(m.ns, bool); used[m.g['f']] = True; used[m.g['t']] = True
sx, sy = m.sx[used], m.sy[used]; inb = (sx > D.x.min() - 3000) & (sx < D.x.max() + 3000) & (sy > D.y.min() - 3000) & (sy < D.y.max() + 3000)
ax.scatter(sx[inb], sy[inb], s=1, c='#0072B2', alpha=.5, label='fermate')
ax.set_aspect('equal'); ax.legend(loc='lower left', fontsize=7); ax.set_title('Quadrati senza nessuna fermata entro 800 m a piedi (%d su %d)' % (un.sum(), len(un)))
ax.set_xticks([]); ax.set_yticks([]); fig.tight_layout(); fig.savefig(S + '/out/mappa_irraggiungibili.png', dpi=130)
dk = D.dist_duomo_km
out = {'totale': int(len(un)), 'senza_fermata': int(un.sum()), 'per_tipo': {nome[k]: int((cat == k).sum()) for k in (1, 2, 3)},
       'per_distanza_duomo_pct': {'%d-%d km' % (a, b): round(100 * float(un[(dk >= a) & (dk < b)].mean()), 1) for a, b in [(0, 3), (3, 5), (5, 7), (7, 9), (9, 20)]},
       'mediana_km_dal_duomo_senza_fermata': round(float(np.median(dk[un])), 1)}
json.dump(out, open(S + '/out/irraggiungibili.json', 'w'), ensure_ascii=False, indent=1); print(out)
