"""Confini delle regioni italiane, semplificati, per la mappa «da dove arrivano».
Fonte: ISTAT, Limiti delle unità amministrative 2021 (generalizzati), CC BY 4.0, già scaricati per la pagina Pendolari.
Legge lo shapefile senza librerie esterne (solo poligoni), riporta le coordinate a longitudine/latitudine con pyproj, semplifica con shapely.
Uso: python -I -X utf8 universita/scripts/03_mappa.py"""
import os, json, struct
from pyproj import Transformer
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely.ops import unary_union
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(R, 'pendolari', 'raw', 'istat_codici', 'x', 'Limiti2021_g', 'Reg2021_g', 'Reg2021_g')
OUT = os.path.join(R, 'docs', 'universita', 'data', 'regioni.geojson')
tr = Transformer.from_crs(32632, 4326, always_xy=True)
# nomi dal dbf
b = open(P + '.dbf', 'rb').read()
n = struct.unpack('<I', b[4:8])[0]; hl = struct.unpack('<H', b[8:10])[0]; rl = struct.unpack('<H', b[10:12])[0]
nomi = []
for i in range(n):
    rec = b[hl + i * rl: hl + (i + 1) * rl]
    nomi.append(rec[1 + 10 + 10: 1 + 10 + 10 + 50].decode('latin-1').strip())
# poligoni dallo shp
s = open(P + '.shp', 'rb').read()
o = 100; geoms = []
while o < len(s):
    num, ln = struct.unpack('>ii', s[o:o + 8]); o += 8
    body = s[o:o + ln * 2]; o += ln * 2
    st = struct.unpack('<i', body[:4])[0]
    if st != 5: geoms.append(None); continue
    npart, npts = struct.unpack('<ii', body[36:44])
    parts = list(struct.unpack('<%di' % npart, body[44:44 + 4 * npart])) + [npts]
    pts = struct.unpack('<%dd' % (2 * npts), body[44 + 4 * npart:44 + 4 * npart + 16 * npts])
    xy = [(pts[2 * k], pts[2 * k + 1]) for k in range(npts)]
    rings = [xy[parts[k]:parts[k + 1]] for k in range(npart)]
    polys = []
    for r in rings:
        ll = [tr.transform(x, y) for x, y in r]
        pg = Polygon(ll)
        # anello esterno = orario nello shapefile; i buchi (antiorari) sono rari qui
        polys.append(pg.buffer(0))
    geoms.append(unary_union(polys))
feats = []
for nome, g in zip(nomi, geoms):
    g = g.simplify(0.02, preserve_topology=True)
    if g.geom_type == 'MultiPolygon':
        g = MultiPolygon([p for p in g.geoms if p.area > 0.01])
    m = mapping(g)
    def rnd(o): return [round(v, 2) for v in o] if isinstance(o[0], float) else [rnd(i) for i in o]
    feats.append({'type': 'Feature', 'properties': {'n': nome}, 'geometry': {'type': m['type'], 'coordinates': rnd(m['coordinates'])}})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({'type': 'FeatureCollection', 'features': feats}, open(OUT, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print(len(feats), os.path.getsize(OUT), nomi)
