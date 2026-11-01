"""Assegna ogni civico a una zona OMI (zonizzazione 2026/1) con punto-in-poligono.
Uso: python -I -X utf8 01_civici_in_zone.py <ABS milano-in-dati> <ABS case-servizi-reddito>
Entrate (sola lettura):
  prezzi-case/raw/geopoi/F205_20261.json            perimetri zone OMI (GEOPOI), regola pari/dispari sugli anelli
  citta-15-minuti/out/civici_tempi.csv              civici: x,y UTM32N, CAP, ID_NIL, punteggio (10 servizi), RESIDENZIALE
  citta-15-minuti/out/civici_tempi_extra.csv        punteggio_20 (20 servizi)
  citta-15-minuti/out/cap_redditi_servizi.csv       imponibile_medio_2024 per CAP
  citta-15-minuti/out/nil_punteggi.csv              residenti_2025 per NIL (peso)
Uscite in out/: zone_geom_utm.geojson (perimetri corretti, UTM), civici_zone.csv, log_01.json
"""
import sys, os, json
from functools import reduce
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import Polygon, Point, mapping
from shapely.validation import make_valid
from shapely import STRtree, points

R, O = sys.argv[1].replace(chr(92), '/').rstrip('/'), sys.argv[2].replace(chr(92), '/').rstrip('/')
TR = Transformer.from_crs(4326, 32632, always_xy=True)
LOG = {}

def geom(feat):
    ps = []
    for ring in feat['geometry']['coordinates']:
        a = np.array(ring, float); x, y = TR.transform(a[:, 0], a[:, 1])
        ps.append(make_valid(Polygon(np.column_stack([x, y]))))
    return reduce(lambda p, q: p.symmetric_difference(q), ps)

d = json.load(open(R + '/prezzi-case/raw/geopoi/F205_20261.json', encoding='utf-8'))
Z = {}
for f in d['dat']['features']:
    c = f['properties']['zona']; g = geom(f)
    Z[c] = Z[c].union(g) if c in Z else g
LOG['n_zone'] = len(Z); LOG['area_totale_km2'] = round(sum(g.area for g in Z.values()) / 1e6, 2)
LOG['codici'] = sorted(Z)
codes = list(Z); polys = [Z[c] for c in codes]
# sovrapposizioni tra zone (controllo)
tree = STRtree(polys); ov = 0.0
for i, p in enumerate(polys):
    for j in tree.query(p):
        if j > i: ov += p.intersection(polys[j]).area
LOG['area_sovrapposta_tra_zone_m2'] = round(ov)
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'zona': c}, 'geometry': mapping(Z[c])} for c in codes]},
          open(O + '/out/zone_geom_utm.geojson', 'w'))

c = pd.read_csv(R + '/citta-15-minuti/out/civici_tempi.csv', usecols=['IDMASTER', 'ID_NIL', 'NIL', 'RESIDENZIALE', 'CAP', 'x', 'y', 'lon', 'lat', 'punteggio'])
e = pd.read_csv(R + '/citta-15-minuti/out/civici_tempi_extra.csv', usecols=['IDMASTER', 'punteggio_20', 'punteggio_extra'])
c = c.merge(e, on='IDMASTER', how='left', validate='1:1')
LOG['n_civici'] = len(c)
# controllo CRS: x,y UTM coincidono con lon/lat trasformati
xx, yy = TR.transform(c.lon.values, c.lat.values)
LOG['controllo_crs_max_scarto_m'] = round(float(np.max(np.hypot(xx - c.x.values, yy - c.y.values))), 2)
pts = points(c.x.values, c.y.values)
zona = np.full(len(c), None, dtype=object); n_multi = 0
# interrogazione: per ogni punto i poligoni che lo contengono
pi, gi = tree.query(pts, predicate='within')
cnt = np.bincount(pi, minlength=len(c))
LOG['civici_in_piu_zone'] = int((cnt > 1).sum()); LOG['civici_in_nessuna_zona_prima_del_riparo'] = int((cnt == 0).sum())
for a, b in zip(pi, gi):
    if zona[a] is None: zona[a] = codes[b]
# civici fuori da ogni zona (sul bordo/lungo i confini): zona piu' vicina se a meno di 50 m, altrimenti NaN
miss = np.where(cnt == 0)[0]; rip = 0
tr2 = tree
for i in miss:
    k = tr2.nearest(pts[i]); dm = pts[i].distance(polys[k])
    if dm <= 50: zona[i] = codes[k]; rip += 1
LOG['civici_fuori_zona_riparati_entro_50m'] = rip
LOG['civici_senza_zona'] = int(sum(z is None for z in zona))
c['zona'] = zona
inc = pd.read_csv(R + '/citta-15-minuti/out/cap_redditi_servizi.csv', usecols=['CAP', 'imponibile_medio_2024'])
c = c.merge(inc, on='CAP', how='left')
LOG['civici_senza_reddito_CAP'] = int(c.imponibile_medio_2024.isna().sum())
nil = pd.read_csv(R + '/citta-15-minuti/out/nil_punteggi.csv', usecols=['ID_NIL', 'residenti_2025'])
c = c.merge(nil, on='ID_NIL', how='left')
res = c.RESIDENZIALE == 1
cnt_nil = c[res].groupby('ID_NIL').size()
c['peso'] = np.where(res, c.residenti_2025 / c.ID_NIL.map(cnt_nil), 0.0)
c['peso'] = c.peso.fillna(0.0)
LOG['residenti_distribuiti'] = round(float(c.peso.sum()))
c.drop(columns=['residenti_2025']).to_csv(O + '/out/civici_zone.csv', index=False)
LOG['civici_per_zona_min_max'] = [int(c.zona.value_counts().min()), int(c.zona.value_counts().max())]
json.dump(LOG, open(O + '/out/log_01.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(LOG, indent=1, ensure_ascii=False))
