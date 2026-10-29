"""Fase 3: sensibilita alla velocita della bici. Ricalcola SOLO la bici per tutte le coppie con due ipotesi piu lente.
Uso: python -I f3_sens.py <ABS strand> <k> <K>  -> out/f3_sens_<k>.npz (secondi/2, uint16; scenari: 0 = media, 1 = lenta)"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from f2_motore import Motore
import f2_parametri as P
S = sys.argv[1]; k, K = int(sys.argv[2]), int(sys.argv[3])
SCEN = [dict(v=(17, 15, 14, 10, 5, 10), sig_s=8, mc_s=4), dict(v=(15, 13, 12, 10, 5, 10), sig_s=15, mc_s=8)]
m = Motore(S, verbose=False)
z = np.load(S + '/out/celle.npz'); D = m.dest(z['lon'], z['lat'])
idx = np.arange(len(z['lon']))[k::K]
out = np.zeros((len(idx), 2, len(z['lon'])), np.uint16)
from f2_motore import xy_of
t0 = time.time()
for s, sc in enumerate(SCEN):
    m.set_bike(**sc)
    for j, i in enumerate(idx):
        x, y = xy_of(z['lon'][i], z['lat'][i])
        b = (m.bici((float(x[0]), float(y[0])), D) + P.BIKE_FIXED_S) / 2
        out[j, s] = np.where(np.isfinite(b), np.minimum(np.round(b), 65534), 65535).astype(np.uint16)
    print('scenario', s, round(time.time() - t0), 's', flush=True)
np.savez_compressed(S + '/out/f3_sens_%d.npz' % k, idx=idx, bike=out)
print('fatto')
