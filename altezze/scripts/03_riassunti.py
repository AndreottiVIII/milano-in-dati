"""Calcola i riassunti pubblicati in docs/altezze/data/ a partire da x_uv.pkl (creato da 01_estrai.py).
Misura di base: UN_VOL_AV, altezza dell'unità volumetrica, in metri. Pianta = area dell'unità vista dall'alto.
Volume = pianta x altezza. Altezza media del costruito di un quartiere = volume / pianta.
Quartieri: stessi confini di docs/negozi/data/nil.geojson (88 NIL). Ogni unità va al quartiere che contiene il suo centro."""
import os, json, pickle, csv, numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from shapely.ops import unary_union
from pyproj import Transformer
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, '..', 'docs', 'altezze', 'data'); os.makedirs(OUT, exist_ok=True)
d = pickle.load(open(os.path.join(R, 'x_uv.pkl'), 'rb'))
nil = json.load(open(os.path.join(R, '..', 'docs', 'negozi', 'data', 'nil.geojson'), encoding='utf-8'))
feat = nil['features']; polys = [shape(f['geometry']) for f in feat]; tree = STRtree(polys)
nomi = [f['properties']['n'] for f in feat]


def assegna(v):
    pts = np.array([Point(x, y) for x, y in zip(v['lon'], v['lat'])], dtype=object)
    ip, ij = tree.query(pts, predicate='within')
    q = np.full(len(pts), -1); q[ip] = ij
    return q


for a in d:
    d[a]['q'] = assegna(d[a])
U = d
H = {}
for a in (2012, 2020):
    v = U[a]; H[a] = {}
    for q in range(len(feat)):
        m = v['q'] == q
        pian = v['area'][m].sum(); vol = (v['area'][m] * v['h'][m]).sum()
        H[a][q] = dict(pianta=float(pian), vol=float(vol), media=float(vol / pian) if pian else None)


def dump(nome, obj):
    json.dump(obj, open(os.path.join(OUT, nome), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), default=float)


# 1. mappa: altezza media 2020 per quartiere
mappa = [dict(i=feat[q]['properties']['i'], n=nomi[q], media=round(H[2020][q]['media'], 1) if H[2020][q]['media'] else None,
              pianta_ha=round(H[2020][q]['pianta'] / 1e4, 1), vol_mm3=round(H[2020][q]['vol'] / 1e6, 3),
              media_2012=round(H[2012][q]['media'], 1) if H[2012][q]['media'] else None) for q in range(len(feat))]
dump('quartieri.json', mappa)
dump('nil.geojson', {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'i': f['properties']['i'], 'n': f['properties']['n']}, 'geometry': f['geometry']} for f in feat]})
# 2. creste: quota di pianta costruita per fascia di altezza (2020), 10 quartieri scelti
BIN = 3; NB = 20
scelti = ['Duomo', 'Brera', 'Porta Garibaldi - Porta Nuova', 'Tre Torri', 'Città studi', 'Lodi - Corvetto', 'Giambellino',
          'Baggio - Q.re degli Olmi - Q.re Valsesia', 'Gratosoglio - Q.re Missaglia - Q.re Terrazze', 'Quintosole']
v = U[2020]; creste = []
for nome in scelti:
    q = nomi.index(nome); m = (v['q'] == q) & (v['h'] > 0.5)
    h = np.minimum(v['h'][m], NB * BIN - 0.001); a = v['area'][m]
    hist = np.bincount((h // BIN).astype(int), weights=a, minlength=NB)
    creste.append(dict(n=nome, q=q, quote=[round(float(x), 4) for x in hist / hist.sum()], media=round(H[2020][q]['media'], 1),
                       oltre30=round(float(a[v['h'][m] >= 30].sum() / a.sum()), 4)))
dump('creste.json', dict(fascia=BIN, creste=creste))
# 3. torri: complessi con unità >= 60 m, uniti se a meno di 40 m
T = Transformer.from_crs(4326, 32632, always_xy=True)
wd = list(csv.DictReader(open(os.path.join(R, 'scripts', 'torri_wikidata.csv'), encoding='utf-8')))
wdp = []
for r in wd:
    x, y = r['c'][6:-1].split(); X, Y = T.transform(float(x), float(y)); wdp.append((r['l'], X, Y))


def complessi(a, soglia, raggio=40):
    v = U[a]; m = v['h'] >= soglia
    x, y = T.transform(v['lon'][m], v['lat'][m]); h = v['h'][m]; lon = v['lon'][m]; lat = v['lat'][m]; qq = v['q'][m]
    pts = [Point(p, q_) for p, q_ in zip(x, y)]
    u = unary_union([p.buffer(raggio) for p in pts])
    parti = list(u.geoms) if hasattr(u, 'geoms') else [u]; ris = []
    for pa in parti:
        ix = [i for i in range(len(x)) if pa.contains(pts[i])]
        j = max(ix, key=lambda i: h[i])
        nome = None; dist = 1e9
        for n_, X, Y in wdp:
            dd = ((X - x[j]) ** 2 + (Y - y[j]) ** 2) ** .5
            if dd < dist: dist, nome = dd, n_
        ris.append(dict(h=round(float(h[j]), 1), lon=round(float(lon[j]), 4), lat=round(float(lat[j]), 4),
                        nome=nome if dist <= 80 else None, q=nomi[qq[j]] if qq[j] >= 0 else None))
    return sorted(ris, key=lambda r: -r['h'])


alti = {a: complessi(a, 60) for a in (2012, 2020)}
c100 = {a: sum(r['h'] >= 100 for r in alti[a]) for a in alti}
for r in alti[2020]:  # nuova = nessun gruppo di torri del 2012 a meno di 80 m
    X, Y = T.transform(r['lon'], r['lat'])
    r['nuova'] = not any(((X - X2) ** 2 + (Y - Y2) ** 2) ** .5 < 80 for X2, Y2 in (T.transform(o['lon'], o['lat']) for o in alti[2012]))
dump('torri.json', dict(torri2020=alti[2020], torri2012=alti[2012]))
# 4. crescita 2012 -> 2020 per quartiere
crescita = []
for q in range(len(feat)):
    a, b = H[2012][q], H[2020][q]
    crescita.append(dict(i=feat[q]['properties']['i'], n=nomi[q], v12=round(a['vol'] / 1e6, 3), v20=round(b['vol'] / 1e6, 3),
                         dv=round((b['vol'] - a['vol']) / 1e6, 3), perc=round(100 * (b['vol'] / a['vol'] - 1), 1) if a['vol'] > 5e4 else None,
                         m12=round(a['media'], 1) if a['media'] else None, m20=round(b['media'], 1) if b['media'] else None))
dump('crescita.json', crescita)
# 5. numeri in alto
tot = {a: dict(pianta=float(U[a]['area'].sum()), vol=float((U[a]['area'] * U[a]['h']).sum())) for a in (2012, 2020)}
oltre30 = {a: float(U[a]['area'][U[a]['h'] >= 30].sum() / U[a]['area'].sum()) for a in (2012, 2020)}
LIM = [0, 6, 12, 21, 30, 60, 1e9]
classi = {str(a): [round(float(U[a]['area'][(U[a]['h'] >= LIM[k]) & (U[a]['h'] < LIM[k + 1])].sum() / U[a]['area'].sum()), 4) for k in range(6)] for a in (2012, 2020)}
riep = dict(classi=classi, limiti_classi=LIM[:-1], media20=tot[2020]['vol'] / tot[2020]['pianta'], media12=tot[2012]['vol'] / tot[2012]['pianta'],
            vol20_mm3=tot[2020]['vol'] / 1e6, vol12_mm3=tot[2012]['vol'] / 1e6, pianta20_km2=tot[2020]['pianta'] / 1e6, pianta12_km2=tot[2012]['pianta'] / 1e6,
            oltre30_20=oltre30[2020], oltre30_12=oltre30[2012], n60_20=len(alti[2020]), n60_12=len(alti[2012]), n100_20=c100[2020], n100_12=c100[2012],
            n_unita={str(a): int(len(U[a]['h'])) for a in U}, fuori_nil={str(a): int((U[a]['q'] < 0).sum()) for a in U},
            alto20=alti[2020][0], max12=alti[2012][0])
dump('riepilogo.json', riep)
print(json.dumps(riep, ensure_ascii=False, indent=1, default=float))
