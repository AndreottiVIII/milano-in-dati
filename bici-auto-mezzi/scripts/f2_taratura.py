"""Taratura della velocita dell'auto: un fattore per fascia in modo che il tempo medio ogni 10 km sul percorso
(viaggi con percorso 6-14 km, origini e destinazioni a caso tra le celle) coincida con l'obiettivo.
Obiettivi (minuti ogni 10 km): 08:00 = 38.7 (TomTom Traffic Index Milano 2025, ora di punta mattina 38m43s);
12:00 e 21:00 = ipotesi (27 e 21 min), da verificare con Google Maps.
Uso: python -I f2_taratura.py <ABS strand>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from f2_motore import Motore, xy_of
import f2_parametri as P
S = sys.argv[1]
TARGET = {'08': 38.7, '12': 27.0, '21': 21.0}
m = Motore(S, verbose=False)
z = np.load(S + '/out/celle.npz'); D = m.dest(z['lon'], z['lat'])
rng = np.random.default_rng(7); org = rng.choice(len(z['lon']), 100, replace=False)
scale = list(P.CAR_SCALE)
def measure(b):
    band = P.BANDS[b]; T = L = 0.0; n = 0
    m.set_car(scale)
    for i in org:
        o = (z['x'][i], z['y'][i])
        drive, dlen, ch = m.auto(o, D, band)
        ok = np.isfinite(drive) & (dlen > 6000) & (dlen < 14000)
        T += drive[ok].sum(); L += dlen[ok].sum(); n += int(ok.sum())
    return T / 60 / (L / 10000), L / 1000 / (T / 3600), n
for b in range(3):
    for it in range(5):
        mi, kmh, n = measure(b)
        print(P.BANDS[b], 'iter', it, 'scala', round(scale[b], 3), 'min/10km', round(mi, 1), 'km/h', round(kmh, 1), 'coppie', n, flush=True)
        if abs(mi - TARGET[P.BANDS[b]]) < 0.4: break
        scale[b] *= (mi / TARGET[P.BANDS[b]]) ** 0.85
json.dump({'CAR_SCALE': scale, 'obiettivi_min_per_10km': TARGET}, open(S + '/out/taratura_auto.json', 'w'), indent=1)
print('CAR_SCALE =', tuple(round(x, 3) for x in scale))
