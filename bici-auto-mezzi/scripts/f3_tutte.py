"""Fase 3: tutte le coppie cella -> cella (o origini con nome -> tutte le celle), 3 fasce orarie.
Uso: python -I f3_tutte.py <ABS strand> celle <k> <K>   (processo k di K, origini i % K == k)
     python -I f3_tutte.py <ABS strand> nomi
-> out/f3_celle_<k>.npz / out/f3_nomi.npz.  Tempi in secondi/2 (uint16, 65535 = non raggiungibile)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from f2_motore import Motore
import f2_parametri as P
S = sys.argv[1]; modo = sys.argv[2]
m = Motore(S, verbose=False)
z = np.load(S + '/out/celle.npz'); D = m.dest(z['lon'], z['lat'])
if modo == 'celle':
    k, K = int(sys.argv[3]), int(sys.argv[4]); idx = np.arange(len(z['lon']))[k::K]
    pts = [(z['lon'][i], z['lat'][i]) for i in idx]; fn = S + '/out/f3_celle_%d.npz' % k
else:
    from f3_origini import ORIGINI
    idx = np.arange(len(ORIGINI)); pts = [(lo, la) for _, lo, la in ORIGINI]; fn = S + '/out/f3_nomi.npz'
def q(a):
    a = np.asarray(a, float) / 2
    return np.where(np.isfinite(a), np.minimum(np.round(a), 65534), 65535).astype(np.uint16)
n = len(idx); nd = len(z['lon'])
out = {'idx': idx, 'bike': np.zeros((n, nd), np.uint16), 'walk': np.zeros((n, nd), np.uint16), 'straight': np.zeros((n, nd), np.float32),
       'cdrive': np.zeros((n, 3, nd), np.uint16), 'tr': np.zeros((n, 3, nd), np.uint16), 'areac': np.zeros((n, 3, nd), bool), 'dlen': np.zeros((n, 3, nd), np.float32)}
t0 = time.time()
for j, p in enumerate(pts):
    for b, band in enumerate(P.BANDS):
        r = m.viaggio(p, D, band)
        if b == 0:
            out['bike'][j] = q(r['bike_s']); out['walk'][j] = q(r['walk_s']); out['straight'][j] = r['straight_m']
        out['cdrive'][j, b] = q(r['car_drive_s']); out['tr'][j, b] = q(r['transit_s']); out['areac'][j, b] = r['areac']; out['dlen'][j, b] = r['car_len_m']
    if j % 50 == 0: print(modo, j, '/', n, round(time.time() - t0), 's', flush=True)
out['park'] = D.park_s.astype(np.float32); out['zona'] = D.zona
np.savez_compressed(fn, **out)
print('fatto', fn, round(time.time() - t0), 's', flush=True)
