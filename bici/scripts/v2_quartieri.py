"""Prepara i file nuovi per la pagina 'bici' (versione 2): assegna ogni tratto ciclabile e ogni stazione BikeMi al quartiere (NIL).
Uso: python -I -X utf8 v2_quartieri.py <cartella milano-in-dati>
Scrive in docs/bici/data/: quartieri_bici.geojson (confini semplificati + km per tipo + stazioni) e piste_quartieri.json (tratti con anno, tipo, quartiere)."""
import json, sys, os, collections
from shapely.geometry import shape, Point, LineString
from shapely.strtree import STRtree
R = sys.argv[1]
D = os.path.join(R, 'docs', 'bici', 'data')
nil = json.load(open(os.path.join(R, 'docs', 'medici-farmacie', 'data', 'nil.geojson'), encoding='utf8'))
polys = [shape(f['geometry']) for f in nil['features']]
ids = [f['properties']['i'] for f in nil['features']]
tree = STRtree(polys)
def quartiere(pt):
    for k in tree.query(pt, predicate='intersects'):
        return int(k)
    # fuori dai confini: il più vicino entro 300 m (circa)
    k = int(tree.nearest(pt))
    return k if polys[k].distance(pt) < 0.003 else None
cic = json.load(open(os.path.join(D, 'ciclabili.json'), encoding='utf8'))
km = collections.defaultdict(lambda: [0.0]*4)
out = []; fuori = 0.0
def tipo3(t):  # 0 protetta, 1 dipinta, 2 condivisa (pedoni o veicoli)
    return 0 if t == 0 else 1 if t == 1 else 2
for f in cic['features']:
    p = f['properties']; lines = f['geometry']['coordinates']
    pts = [c for ln in lines for c in ln]
    mid = LineString(lines[0]).interpolate(0.5, normalized=True) if len(lines[0]) > 1 else Point(lines[0][0])
    k = quartiere(mid)
    t = tipo3(p['t'])
    if k is None: fuori += p['l']/1000
    else: km[k][t] += p['l']/1000
    enc = [[[round(c[0]*1e5), round(c[1]*1e5)] for c in ln] for ln in lines]
    out.append([t, p['a'], p['o'], -1 if k is None else ids[k], p['l'], enc])
json.dump(out, open(os.path.join(D, 'piste_quartieri.json'), 'w'), separators=(',', ':'))
st = json.load(open(os.path.join(D, 'stazioni.json'), encoding='utf8'))
cm = st['campi']; ix = {c: i for i, c in enumerate(cm)}
cnt = collections.Counter(); sl = collections.Counter(); senza = 0
for r in st['righe']:
    k = quartiere(Point(r[ix['lon']], r[ix['lat']]))
    if k is None: senza += 1; continue
    cnt[k] += 1; sl[k] += r[ix['stalli']] or 0
feats = []
for i, f in enumerate(nil['features']):
    p = f['properties']
    rp = polys[i].representative_point()
    q = {'i': p['i'], 'c': [round(rp.x, 5), round(rp.y, 5)], 'n': p['n'], 'mu': p['mu'], 'k0': round(km[i][0], 3), 'k1': round(km[i][1], 3), 'k2': round(km[i][2], 3), 'st': cnt[i], 'sl': sl[i]}
    feats.append({'type': 'Feature', 'properties': q, 'geometry': f['geometry']})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(D, 'quartieri_bici.geojson'), 'w'), separators=(',', ':'))
print('km fuori quartieri', round(fuori, 2), '| stazioni senza quartiere', senza)
print('km totali assegnati', round(sum(sum(v) for v in km.values()), 1), '| stazioni', sum(cnt.values()))
