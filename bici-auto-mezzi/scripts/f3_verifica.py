"""Verifica mezzi: prove di buon senso del motore con tragitti noti (martedi 3/11/2026, 08:00 e 21:00).
Le coordinate sono quelle delle fermate GTFS (cosi si parte e si arriva alla stazione). Gli intervalli attesi sono scritti qui sotto,
ragionati dagli orari veri delle linee (non da Google). Poi due tragitti solo bus in periferia, scelti dal GTFS stesso.
Uso: python -I f3_verifica.py <ABS strand> [etichetta]  -> out/f3_verifica_<etichetta>.json e stampa"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from f2_motore import Motore, xy_of
import f2_parametri as P
S = sys.argv[1]; ET = sys.argv[2] if len(sys.argv) > 2 else 'dopo'
m = Motore(S, verbose=False); g = m.g; nm = g['stop_name']
if ET == 'prima':   # riproduce lo stato PRIMA delle correzioni (solo per il confronto): fermate bus come stazioni, passaggi a piedi vecchi, parametri mezzi della taratura precedente
    old_st = np.zeros(m.ns, bool); old_st[g['f'][g['rtype'] >= 1]] = True; old_st[g['t'][g['rtype'] >= 1]] = True
    z = np.load(S + '/out/_prima_verifica/footpaths_old.npz'); m.fp_ptr, m.fp_to, m.fp_w = z['ptr'], z['to'], z['w']
    m.stop_station = old_st; m.stop_extra = np.where(old_st, 60, 0.0); P.TRANSIT_SLACK_S = 120
def ll(name):
    i = np.where(nm == name)[0][0]; return (float(g['stop_lon'][i]), float(g['stop_lat'][i]))
# (etichetta, partenza, arrivo, atteso mezzi min-max, atteso bici min-max, nota)
T = [('Duomo > Bicocca (M3+M5)', ll('DUOMO M3'), ll('BICOCCA'), (20, 32), (24, 34), 'M3 Duomo-Zara, cambio, M5 Zara-Bicocca'),
     ('Centrale > Rho Fiera (M2+M1 o S)', ll('CENTRALE FS'), ll('RHO FIERAMILANO'), (30, 48), (40, 56), 'M2 o M3+M1, oppure treno'),
     ('Cadorna > Bovisa (Trenord)', ll('Milano Cadorna'), ll('Milano Bovisa Politecnico'), (10, 22), (14, 24), 'treno S/R, 5-8 min di corsa'),
     ('Garibaldi > San Siro Stadio (M5)', ll('GARIBALDI FS'), ll('SAN SIRO STADIO'), (17, 27), (20, 32), 'M5 diretta, circa 15 min'),
     ('Loreto > Cologno Nord (M2)', ll('LORETO M2'), ll('COLOGNO NORD'), (22, 33), (30, 42), 'M2 diretta, circa 19 min'),
     ('Lotto > Lambrate (M5+M2 o M1+M2)', ll('LOTTO M5'), ll('LAMBRATE FS'), (28, 42), (28, 40), 'M5 fino a Garibaldi poi M2, oppure M1+M2 a Loreto')]
T.append(('Sesto Marelli > Cologno Nord (M1+M2, cambio a Loreto)', ll('SESTO MARELLI'), ll('COLOGNO NORD'), (33, 55), (18, 28), 'M1 fino a Loreto, cambio (cambio ufficiale ATM), M2'))
T.append(('Centrale > Rho Fiera (treno Trenord)', ll('Milano Centrale'), ll('Rho Fiera Milano'), (25, 45), (40, 56), 'treno Trenord da Centrale/Garibaldi'))
# due tragitti solo bus in periferia: dalla corsa bus ATM di tipo 3 con due fermate a 3-5 km tra loro, in periferia (>6 km dal Duomo), senza metro/tram/treno entro 800 m dalle due fermate
isbus = g['rtype'] == 3; atm = np.array([f == 'atm' for f in g['stop_feed']])
others = np.zeros(m.ns, bool)
for r in (0, 1, 2):
    k = g['rtype'] == r; others[g['f'][k]] = True; others[g['t'][k]] = True
from scipy.spatial import cKDTree
to = cKDTree(np.c_[m.sx[others], m.sy[others]])
dd = np.hypot(m.sx - m.duomo[0][0], m.sy - m.duomo[1][0])
rng = np.random.RandomState(7)
cand = np.where(isbus[np.minimum(np.arange(len(g['f'])), len(g['f']) - 1)])[0]
bus_pairs = []
idx = np.where((g['rtype'] == 3) & (g['dep'] >= 7 * 3600 + 1800) & (g['dep'] < 8 * 3600))[0]
trips = {}
for i in idx[rng.permutation(len(idx))[:60000]]:
    trips.setdefault(int(g['trip'][i]), []).append(i)
for tr, ii in trips.items():
    if len(bus_pairs) >= 2: break
    a = ii[0]; f0 = int(g['f'][a])
    if dd[f0] < 6000 or not atm[f0] or to.query([m.sx[f0], m.sy[f0]])[0] < 900: continue
    # segue la corsa: connessioni successive della stessa corsa
    pos = np.where(g['trip'] == tr)[0]; pos = pos[np.argsort(g['dep'][pos])]
    for p in pos:
        if g['dep'][p] < g['dep'][a]: continue
        t1 = int(g['t'][p]); dist = np.hypot(m.sx[t1] - m.sx[f0], m.sy[t1] - m.sy[f0])
        if 3000 <= dist <= 5000 and dd[t1] > 5000 and to.query([m.sx[t1], m.sy[t1]])[0] >= 900 and m.stop_ok[f0] and m.stop_ok[t1]:
            ride = (g['arr'][p] - g['dep'][a]) / 60
            bus_pairs.append((f0, t1, ride)); break
for f0, t1, ride in bus_pairs:
    T.append(('Solo bus: %s > %s' % (nm[f0], nm[t1]), (float(g['stop_lon'][f0]), float(g['stop_lat'][f0])), (float(g['stop_lon'][t1]), float(g['stop_lat'][t1])),
              (round(ride), round(ride + 18)), (None, None), 'corsa in orario %.0f min + attesa (fino a una frequenza di 12-15 min) e cammino' % ride))
out = []
for etic, o, d, em, eb, nota in T:
    D = m.dest([d[0]], [d[1]]); row = {'tragitto': etic, 'nota': nota, 'atteso_mezzi': em, 'atteso_bici': eb}
    for b in ('08', '21'):
        r = m.viaggio(o, D, b)
        row['mezzi_' + b] = round(float(r['transit_s'][0]) / 60, 1) if np.isfinite(r['transit_s'][0]) and r['transit_s'][0] < 1e8 else None
        row['bici_' + b] = round(float(r['bike_s'][0]) / 60, 1); row['auto_' + b] = round(float(r['car_s'][0]) / 60, 1)
        row['km_retta'] = round(float(r['straight_m'][0]) / 1000, 1)
    row['ok_mezzi_08'] = row['mezzi_08'] is not None and em[0] <= row['mezzi_08'] <= em[1]
    row['ok_bici_08'] = eb[0] is None or (eb[0] <= row['bici_08'] <= eb[1])
    out.append(row); print(row, flush=True)
json.dump(out, open(S + '/out/f3_verifica_%s.json' % ET, 'w'), ensure_ascii=False, indent=1)
