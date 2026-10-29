"""Mappa "chi vince" da un punto. Uso: python -I f2_mappa.py <ABS strand> <lon> <lat> <fascia 08|12|21> <nome>"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from f2_motore import Motore
S = sys.argv[1]; lon = float(sys.argv[2]); lat = float(sys.argv[3]); band = sys.argv[4]; nome = sys.argv[5]
m = Motore(S, verbose=False)
z = np.load(S + '/out/celle.npz'); t = time.time()
D = m.dest(z['lon'], z['lat']); t1 = time.time() - t
t = time.time(); r = m.viaggio((lon, lat), D, band); t2 = time.time() - t
print('destinazioni', round(t1, 1), 's; origine->tutte le celle', round(t2, 1), 's')
T = np.c_[r['bike_s'], r['car_s'], r['transit_s']] / 60
w = np.argmin(T, axis=1); fin = np.isfinite(T).any(axis=1)
print('quote vittorie: bici %.1f%% auto %.1f%% mezzi %.1f%%' % tuple(100 * np.mean(w[fin] == k) for k in range(3)))
print('mediane min: bici', np.nanmedian(T[:,0]), 'auto', np.nanmedian(T[:,1]), 'mezzi', np.nanmedian(T[np.isfinite(T[:,2]),2]), 'celle senza mezzi', int((~np.isfinite(T[:,2])).sum()))
col = np.array(['#2a9d8f', '#e76f51', '#264653'])
fig, ax = plt.subplots(figsize=(8, 9))
ax.scatter(z['x'], z['y'], c=col[w], s=14, marker='s', linewidths=0)
ox, oy = np.array([lon]), np.array([lat])
from f2_motore import xy_of
a, b = xy_of(lon, lat); ax.plot(a, b, 'k*', ms=14)
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('%s, martedi ore %s:00 - chi arriva prima' % (nome, band))
for c_, l in zip(col, ['bici', 'auto (con parcheggio)', 'mezzi pubblici']): ax.plot([], [], 's', color=c_, label=l)
ax.legend(loc='lower left')
fig.savefig(S + '/out/mappa_%s_%s.png' % (nome, band), dpi=110, bbox_inches='tight')
