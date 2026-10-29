import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from f2_motore import Motore
from f2_geocode import Geocoder
S = sys.argv[1]; m = Motore(S, verbose=False); g = Geocoder(S)
T = [("Piazza Cadorna, 1", "Piazza Duca d'Aosta, 1", '12'), ("Piazza Gae Aulenti, 1", "via Rogoredo, 20", '12'), ("Piazza Duca d'Aosta, 1", "Piazza Leonardo da Vinci, 32", '12'),
     ("Piazza Leonardo da Vinci, 32", "Piazza Duca d'Aosta, 1", '21'), ("Piazza dell'Ateneo Nuovo, 1", "Piazza Duca d'Aosta, 1", '08')]
for a, b, band in T:
    oa, ob = g.indirizzo(a), g.indirizzo(b)
    if oa[0] is None or ob[0] is None: print('non trovato', a, b, oa, ob); continue
    D = m.dest([ob[0][0]], [ob[0][1]]); t = time.time(); r = m.viaggio(oa[0], D, band)
    print(a, '->', b, band, {k: round(float(v[0]) / 60, 1) if k.endswith('_s') else round(float(v[0]), 0) for k, v in r.items()}, round(time.time() - t, 2), 's')
