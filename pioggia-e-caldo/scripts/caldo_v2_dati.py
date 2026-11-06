"""Dati nuovi per la pagina 'Il quartiere piu' caldo' (versione 2).
Uso: python -I -X utf8 caldo_v2_dati.py <cartella pioggia-e-caldo> <cartella docs/caldo/data> <docs/verde/data/nil.geojson>
Scrive (nomi nuovi, nulla viene sovrascritto):
  profilo_24ore.json   temperatura media per ora, estati 2017-2025: stazioni di Milano contro campagna
  quartieri_caldo.json 88 quartieri: indice di calore da satellite, suolo, alberi, verde, distanza dal Duomo, termometro piu vicino
"""
import sys, os, json, math
import pandas as pd, numpy as np
base, out, verde = sys.argv[1], sys.argv[2], sys.argv[3]
URBANE = ['5897', '5909', '5911', '5920', '8162', '2001']
RURALI = ['5917', '2187', '5910', '4066', '17488', '2122', '12716']
T = pd.read_parquet(os.path.join(base, 'pulito', 'intermedi', 'T_orario.parquet'))
T['idsensore'] = T.idsensore.astype(str)
T = T[T.idsensore.isin(URBANE + RURALI)]
T = T[(T.ora.dt.month.isin([6, 7, 8])) & (T.ora.dt.year.between(2017, 2025))]
w = T.pivot_table(index='ora', columns='idsensore', values='t')
ur = w[URBANE]; ru = w[RURALI]
city = ur.where(ur.notna().sum(axis=1) >= 4).mean(axis=1)
camp = ru.where(ru.notna().sum(axis=1) >= 3).mean(axis=1)
d = pd.DataFrame({'c': city, 'r': camp}).dropna()
h = d.groupby(d.index.hour).mean()
prof = {'finestra': '2017-2025, giugno-agosto', 'n_istanti': int(len(d)),
        'ore': [{'h': int(i), 'citta': round(float(r.c), 2), 'campagna': round(float(r.r), 2), 'diff': round(float(r.c - r.r), 2)} for i, r in h.iterrows()],
        'origine': 'pulito/intermedi/T_orario.parquet (ARPA Lombardia, CC0); citta = media di 4+ delle 6 stazioni di Milano, campagna = media di 3+ delle 7 stazioni rurali, stesso istante'}
json.dump(prof, open(os.path.join(out, 'profilo_24ore.json'), 'w', encoding='utf8'), ensure_ascii=False)
# quartieri
G = json.load(open(verde, encoding='utf8'))
st = pd.read_csv(os.path.join(out, 'stazioni.csv'), dtype={'id': str})
st = st[st.classe == 'urbana']
DUOMO = (45.4642, 9.1900)
def km(a, b):
    kx = 111.32 * math.cos(math.radians(45.47)); ky = 110.57
    return math.hypot((a[1] - b[1]) * kx, (a[0] - b[0]) * ky)
def rings(g):
    return g['coordinates'] if g['type'] == 'Polygon' else [r for p in g['coordinates'] for r in p]
def centro(g):
    # baricentro dell'anello esterno piu grande (formula dell'area)
    best = None
    for p in ([g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']):
        r = p[0]; a = cx = cy = 0
        for (x0, y0), (x1, y1) in zip(r, r[1:] + r[:1]):
            c = x0 * y1 - x1 * y0; a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
        if a and (best is None or abs(a) > best[0]): best = (abs(a), cx / (3 * a), cy / (3 * a))
    return best[2], best[1]
Q = []
for f in G['features']:
    p = f['properties']; c = centro(f['geometry'])
    dist = [(km(c, (s.lat, s.lng)), s) for s in st.itertuples()]
    dm, sm = min(dist, key=lambda t: t[0])
    Q.append({'i': p['i'], 'n': p['n'], 'ab': p['ab'], 'cal': p.get('cal'), 'suolo': p.get('suolo'), 'albkm2': p.get('albkm2'),
              'mA': p.get('mA'), 'mB': p.get('mB'), 'duomo': round(km(c, DUOMO), 2), 'st': sm.id, 'dst': round(dm, 2),
              'lat': round(c[0], 5), 'lng': round(c[1], 5)})
def pip(pt, g):
    x, y = pt[1], pt[0]
    for poly in ([g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']):
        r = poly[0]; ins = False
        for (x0, y0), (x1, y1) in zip(r, r[1:] + r[:1]):
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0: ins = not ins
        if ins: return True
    return False
anc = []
for s_ in st.itertuples():
    for f in G['features']:
        if pip((s_.lat, s_.lng), f['geometry']): anc.append({'st': s_.id, 'nil': f['properties']['i']})
json.dump({'ancore': anc, 'origine': 'docs/verde/data/nil.geojson (cal = indice di calore da satellite, luglio 2024, ds2811, CC BY; suolo = suolo consumato 2025 ISPRA, %; albkm2 = alberi per km2, ds2484; mA = metri quadri di parchi e giardini disegnati per abitante, mB = stima completa); distanze calcolate dal baricentro del quartiere',
           'q': Q}, open(os.path.join(out, 'quartieri_caldo.json'), 'w', encoding='utf8'), ensure_ascii=False)
print(len(Q), 'quartieri; senza cal:', sum(1 for q in Q if q['cal'] is None))
print(h.round(1).T.to_string())
