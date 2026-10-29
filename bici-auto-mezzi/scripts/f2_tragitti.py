"""20 tragitti di prova per la taratura (Davide li controlla a mano su Google Maps). Uso: python -I f2_tragitti.py <ABS strand>
-> tragitti_prova.csv (separatore ;, UTF-8 con BOM, aprire con Excel)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from f2_motore import Motore, xy_of
from f2_geocode import Geocoder
import f2_parametri as P
S = sys.argv[1]
T = [  # origine, destinazione, fascia
 ("Piazza Duca d'Aosta, 1", "via Dante, 9", '08'),
 ("via Torino, 21", "Corso di Porta Romana, 100", '12'),
 ("Piazza San Babila, 1", "via Mario Pagano, 47", '21'),
 ("via Dante, 9", "Piazza Leonardo da Vinci, 32", '08'),
 ("Piazza Tre Torri, 1", "Piazza San Babila, 1", '12'),
 ("Piazza dell'Ospedale Maggiore, 3", "Piazza Duca d'Aosta, 1", '08'),
 ("viale Certosa, 22", "via Rombon, 11", '21'),
 ("Piazza dell'Ateneo Nuovo, 1", "Piazza Tre Torri, 1", '08'),
 ("via Giambellino, 100", "Piazza Leonardo da Vinci, 32", '12'),
 ("via delle Forze Armate, 260", "Piazza Duca d'Aosta, 1", '08'),
 ("via Piccolomini, 5", "Piazza Tre Torri, 1", '21'),
 ("via Rombon, 11", "Piazza San Babila, 1", '08'),
 ("via Mecenate, 76", "via Tertulliano, 70", '12'),
 ("via dei Missaglia, 97", "Piazza Duca d'Aosta, 1", '08'),
 ("viale Sarca, 200", "via Giambellino, 100", '12'),
 ("via Giovanni Cimabue, 5", "via Mecenate, 76", '08'),
 ("via Tertulliano, 70", "Piazza dell'Ateneo Nuovo, 1", '21'),
 ("Piazza dell'Ospedale Maggiore, 3", "via dei Missaglia, 97", '08'),
 ("viale Fulvio Testi, 100", "via delle Forze Armate, 260", '21'),
 ("Piazza San Babila, 1", "via Orefici, 2", '12'),
]
g = Geocoder(S); m = Motore(S, verbose=False)
gt = m.g
metro = np.unique(np.r_[gt['f'][gt['rtype'] == 1], gt['t'][gt['rtype'] == 1]])
from scipy.spatial import cKDTree
tm = cKDTree(np.c_[m.sx[metro], m.sy[metro]])
def metro_d(lon, lat):
    x, y = xy_of(lon, lat); return int(round(tm.query([x[0], y[0]])[0]))
rows = []
for i, (a, b, band) in enumerate(T, 1):
    (oa, la), (ob, lb) = g.indirizzo(a), g.indirizzo(b)
    assert oa is not None and ob is not None, (a, b, la, lb)
    D = m.dest([ob[0]], [ob[1]])
    r = m.viaggio(oa, D, band)
    h = int(band)
    rows.append({
        'n': i, 'origine': a + ', Milano', 'destinazione': b + ', Milano', 'giorno': 'martedi 3 novembre 2026', 'ora_partenza': '%02d:00' % h,
        'km_in_linea_retta': round(float(r['straight_m'][0]) / 1000, 1), 'km_percorso_auto': round(float(r['car_len_m'][0]) / 1000, 1),
        'zona_arrivo': {'areac': 'Area C', 'semicentro': 'semicentro', 'periferia': 'periferia'}[D.zona[0]],
        'area_c_auto': ('si' if bool(r['areac'][0]) else 'no') if band != '21' else 'no (dopo le 19:30)',
        'metro_vicino_partenza_m': metro_d(*oa), 'metro_vicino_arrivo_m': metro_d(*ob),
        'stima_bici_min': round((r['bike_s'][0] - P.BIKE_FIXED_S) / 60), 'stima_auto_guida_min': round(r['car_drive_s'][0] / 60),
        'stima_auto_porta_a_porta_min': round(r['car_s'][0] / 60), 'stima_mezzi_min': (round(r['transit_s'][0] / 60) if np.isfinite(r['transit_s'][0]) else ''),
        'stima_a_piedi_min': (round(r['walk_s'][0] / 60) if np.isfinite(r['walk_s'][0]) else ''),
        'google_bici_min': '', 'google_auto_min': '', 'google_mezzi_min': '', 'note_davide': '',
        'lon_partenza': round(oa[0], 5), 'lat_partenza': round(oa[1], 5), 'lon_arrivo': round(ob[0], 5), 'lat_arrivo': round(ob[1], 5),
    })
df = pd.DataFrame(rows)
df.to_csv(S + '/tragitti_prova.csv', sep=';', decimal=',', index=False, encoding='utf-8-sig')
print(df[['n', 'km_in_linea_retta', 'km_percorso_auto', 'zona_arrivo', 'area_c_auto', 'metro_vicino_partenza_m', 'metro_vicino_arrivo_m', 'stima_bici_min', 'stima_auto_guida_min', 'stima_auto_porta_a_porta_min', 'stima_mezzi_min', 'stima_a_piedi_min']].to_string())
