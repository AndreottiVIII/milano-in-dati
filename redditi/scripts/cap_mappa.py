"""Ricostruisce le zone dei 38 CAP di Milano (i confini ufficiali dei CAP non sono pubblicati).
Ogni civico ha il CAP del punto noto piu' vicino (negozi, farmacie, poste, medici con CAP);
si disegna intorno a ogni civico la sua zona (Voronoi), si uniscono le zone dello stesso CAP,
si leviga e si ritaglia sul confine del comune.
Uso: python -I -X utf8 cap_mappa.py <ABS milano-in-dati>
Scrive docs/redditi/data/cap_zone_ricostruite.geojson"""
import sys, json
import numpy as np, pandas as pd, shapely
from shapely.geometry import MultiPoint, Point, shape, mapping
from shapely.ops import voronoi_diagram, unary_union, transform
from shapely import make_valid
from pyproj import Transformer
R = sys.argv[1]
c = pd.read_csv(R + '/citta-15-minuti/out/civici_tempi.csv', usecols=['x', 'y', 'CAP'], dtype={'CAP': str}).drop_duplicates(['x', 'y']).reset_index(drop=True)
g = json.load(open(R + '/citta-15-minuti/raw/comune_milano/confine_comune/confine_comune_milano_layer_0_confine_comune_milano.geojson', encoding='utf-8'))
fw = Transformer.from_crs(4326, 32632, always_xy=True).transform
bw = Transformer.from_crs(32632, 4326, always_xy=True).transform
city = unary_union([make_valid(transform(fw, shape(f['geometry']))) for f in g['features']]).buffer(0)
P = shapely.points(c.x.values, c.y.values)
vor = voronoi_diagram(shapely.multipoints(P), envelope=city.buffer(3000))
cells = list(vor.geoms)
tree = shapely.STRtree(cells)
pi, ci = tree.query(P, predicate='within')
cap_of_cell = {}
for a, b in zip(pi, ci): cap_of_cell[b] = c.CAP[a]
by = {}
for b, cp in cap_of_cell.items(): by.setdefault(cp, []).append(cells[b])
raw = {cp: unary_union(v).intersection(city) for cp, v in by.items()}
# levigatura: chiude i buchi e toglie le isole piccole (< 4 ettari), le zone restano nel confine
sm = {}
for cp, geom in raw.items():
    s = geom.buffer(60).buffer(-120).buffer(60)
    parts = [p for p in (s.geoms if hasattr(s, 'geoms') else [s]) if p.area > 40000]
    big = max(parts, key=lambda p: p.area) if parts else geom
    sm[cp] = unary_union(parts) if parts else big
# elimina sovrapposizioni: chi e' stato levigato cede a chi ha piu' civici nel punto
order = sorted(sm, key=lambda k: -len(by[k]))
taken = None; fin = {}
for cp in order:
    gm = sm[cp] if taken is None else sm[cp].difference(taken)
    fin[cp] = gm; taken = gm if taken is None else taken.union(gm)
# i vuoti rimasti dentro il confine vanno al CAP piu' vicino
gap = city.difference(taken).buffer(1).intersection(city)
for part in (gap.geoms if hasattr(gap, 'geoms') else [gap]):
    if part.area < 1: continue
    near = min(fin, key=lambda k: fin[k].distance(part))
    fin[near] = fin[near].union(part)
feats = []
for cp in sorted(fin):
    gm = fin[cp].simplify(12).buffer(0)
    gm = transform(bw, gm)
    gm = shapely.set_precision(gm, 0.00001)
    feats.append({'type': 'Feature', 'properties': {'cap': cp, 'civici': int((c.CAP == cp).sum())}, 'geometry': mapping(gm)})
out = R + '/docs/redditi/data/cap_zone_ricostruite.geojson'
json.dump({'type': 'FeatureCollection', 'features': feats}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
import os
print(len(feats), 'CAP', os.path.getsize(out) // 1024, 'KB')
