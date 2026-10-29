"""Fase 3: taratura di bici, auto e mezzi sui tragitti di prova con valori Google (tragitti_prova.csv + tragitti_prova_2.csv se c'e).
Regole (fisse, cosi si puo rifare con piu tragitti):
 - divisione 70/30 per ora e distanza (f3_lib.carica): 'taratura' per scegliere i parametri, 'controllo' solo per misurare l'errore
 - bici: si prova prima con attesa al semaforo 6 s (attraversamenti 3 s): velocita su strada da 14 a 18 km/h (passo 0,5; ciclabile = strada + 2,
   servizio = strada - 1), la prima per cui il rapporto mediano nostra stima / Google sui tragitti di taratura sta tra 0,95 e 1,05; se nessuna,
   si ripete con semaforo 4 s e poi 2 s; se ancora nessuna, la combinazione piu vicina a 1. Velocita massima 18 km/h su strada (limite di plausibilita)
 - auto: ore 08 invariata (TomTom); 12 e 21 un moltiplicatore comune sulle scale, per rapporto mediano 1 sui tragitti di taratura
   (esclusi i tragitti con meta a meno di 1 km in linea retta: in centro Google fa giri per le zone chiuse)
 - mezzi: griglia margine di cambio (45-180 s) x tempo di accesso a metro/treno (0-120 s); minimizza errore medio |log| + 2 x |log rapporto mediano|
Uso: python -I f3_calibra.py <ABS strand> -> out/f3_taratura.json (parametri, errori prima/dopo; nessun valore di Google)"""
import sys, os, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_lib import *
S = sys.argv[1]
B = Banco(S); d = B.d; N = len(d)
tr = (d.gruppo == 'taratura').values; ho = ~tr; band = d.band.values
G = {'bici': d.google_bici_min.values, 'auto': d.google_auto_min.values, 'mezzi': d.google_mezzi_min.values}
BASE08 = P.CAR_SCALE[0]
F2 = dict(bike=(15, 13, 12, 10, 5, 10), sig=15, mc=8, car=P.CAR_SCALE_F2, slack=45, stat=0)
def setta(bike, sig, mc, car, slack, stat):
    B.m.set_bike(v=bike, sig_s=sig, mc_s=mc); B.m.set_car(car); P.TRANSIT_SLACK_S = slack
    B.m.stop_extra = np.where(B.m.stop_station, stat, 0.0)
    B.D = [B.m.dest([r.lon_arrivo], [r.lat_arrivo]) for r in B.d.itertuples()]
def mediana(est, g, mk):
    ok = mk & np.isfinite(est) & np.isfinite(g)
    return float(np.median(est[ok] / g[ok])) if ok.any() else np.nan
# ---------- bici
cand = []; found = None
for SIG in (6.0, 4.0, 2.0):
    MC = SIG / 2
    for vr in np.arange(14, 18.01, 0.5):
        B.m.set_bike(v=(vr + 2, vr, vr - 1, 10, 5, 10), sig_s=SIG, mc_s=MC)
        r = mediana(B.bici(), G['bici'], tr)
        print('bici strada', vr, 'semaforo', SIG, 'rapporto mediano taratura', round(r, 3), flush=True)
        cand.append((abs(r - 1), SIG, vr))
        if abs(r - 1) <= 0.05: found = (SIG, vr); break
    if found: break
if not found:
    _, SIG, vr = min(cand); found = (SIG, vr)
SIG, VR = found; MC = SIG / 2; BIKE = (VR + 2, VR, VR - 1, 10.0, 5.0, 10.0)
# ---------- auto
fit = tr & (band != '08') & (d.km_in_linea_retta.values >= 1.0) & np.isfinite(G['auto'])
base = list(P.CAR_SCALE_F2); m = 1.0
for it in range(12):
    sc = [BASE08, base[1] * m, base[2] * m]
    B.m.set_car(sc); a = B.auto(); r = np.median(a[fit] / G['auto'][fit])
    print('auto', it, round(m, 3), 'rapporto mediano', round(r, 3), flush=True)
    if abs(r - 1) < 0.015: break
    m *= r ** 0.9
CAR = [round(float(x), 3) for x in sc]
# ---------- mezzi
resm = []
for stat in (0, 60, 90, 120):
    for slack in (45, 90, 120, 180):
        setta(BIKE, SIG, MC, CAR, slack, stat); z = B.mezzi()
        ok = tr & np.isfinite(z) & np.isfinite(G['mezzi'])
        rr = z[ok] / G['mezzi'][ok]
        sc_ = float(np.mean(np.abs(np.log(rr))) + 2 * abs(np.log(np.median(rr))))
        resm.append((sc_, slack, stat)); print('mezzi', slack, stat, round(sc_, 3), flush=True)
_, SLACK, STAT = min(resm)
# ---------- errori prima / dopo
def errtab(est):
    out = {}
    for mod in ('bici', 'auto', 'mezzi'):
        e = {}
        for gr, mk in [('taratura', tr), ('controllo', ho), ('tutti', np.ones(N, bool))]:
            r = errori(est[mod], G[mod], mk); e[gr] = {'rapporto_mediano': round(r[0], 3), 'errore_mediano_pct': round(r[1], 1), 'errore_medio_pct': round(r[2], 1), 'n': r[3]}
        if mod == 'auto':
            for b in P.BANDS:
                r = errori(est[mod], G[mod], band == b); e['ore_' + b] = {'rapporto_mediano': round(r[0], 3), 'errore_mediano_pct': round(r[1], 1), 'n': r[3]}
        out[mod] = e
    return out
res = {}
for nome, args in [('prima', (F2['bike'], F2['sig'], F2['mc'], F2['car'], F2['slack'], F2['stat'])), ('dopo', (BIKE, SIG, MC, CAR, SLACK, STAT))]:
    setta(*args); est = {'bici': B.bici(), 'auto': B.auto(), 'mezzi': B.mezzi()}
    res[nome] = errtab(est)
    for mod in est: print(nome, mod, {k: (v['rapporto_mediano'], v['errore_mediano_pct']) for k, v in res[nome][mod].items()})
J = {'parametri': {'bike_kmh': [float(x) for x in BIKE], 'bike_signal_s': SIG, 'bike_major_cross_s': MC, 'car_scale': CAR,
                   'transit_slack_s': int(SLACK), 'station_access_s': int(STAT)},
     'prima': {'bike_kmh': list(F2['bike']), 'bike_signal_s': F2['sig'], 'bike_major_cross_s': F2['mc'], 'car_scale': list(F2['car']), 'transit_slack_s': F2['slack'], 'station_access_s': F2['stat']},
     'errori': res, 'n_tragitti': N, 'n_taratura': int(tr.sum()), 'n_controllo': int(ho.sum()),
     'n_per_ora': {b: int((band == b).sum()) for b in P.BANDS},
     'n_con_google': {k: int(np.isfinite(v).sum()) for k, v in G.items()},
     'file': sorted(d.file.unique().tolist())}
json.dump(J, open(S + '/out/f3_taratura.json', 'w'), indent=1)
print('PARAMETRI', J['parametri'])
