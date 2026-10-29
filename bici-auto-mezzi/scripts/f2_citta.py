"""Mappa generale: N origini a caso (celle) verso tutte le celle, tre fasce. Uso: python -I f2_citta.py <ABS strand> [N]
-> out/citta_coppie.npz"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from f2_motore import Motore
import f2_parametri as P
S = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 300
m = Motore(S, verbose=False)
z = np.load(S + '/out/celle.npz'); D = m.dest(z['lon'], z['lat'])
rng = np.random.default_rng(2026); org = np.sort(rng.choice(len(z['lon']), N, replace=False))
out = {'org': org}
acc = {}
t0 = time.time()
for j, i in enumerate(org):
    for band in P.BANDS:
        r = m.viaggio((z['lon'][i], z['lat'][i]), D, band)
        for k, v in r.items():
            if k in ('walk_s', 'bike_s', 'straight_m') and band != '08': continue
            acc.setdefault((k, band), []).append(np.asarray(v, dtype=np.float32))
    if j % 20 == 0: print(j, round(time.time() - t0), 's', flush=True)
for (k, band), v in acc.items(): out['%s_%s' % (k, band)] = np.stack(v)
np.savez_compressed(S + '/out/citta_coppie.npz', **out)
print('fatto', round(time.time() - t0), 's')
