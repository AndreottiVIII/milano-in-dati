"""Dati per la pagina rifatta (v2) di "Bici, auto o mezzi": riassunti per quartiere (NIL) e per luogo noto.
Legge docs/bici-auto-mezzi/data (celle, citta, incidenti, o/*.bin.gz) e i confini docs/quartiere/data/nil.geojson.
Scrive SOLO file nuovi in docs/bici-auto-mezzi/data: nil.geojson, quartieri.json, viaggi.json, luoghi.json.
Uso: python -I -X utf8 f5_dati_pagina_v2.py <cartella del progetto milano-in-dati>"""
import sys, os, json, gzip
import numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
R = sys.argv[1]
D = R + '/docs/bici-auto-mezzi/data'
J = lambda p: json.load(open(p, encoding='utf-8'))
cel = J(D + '/celle.json'); nd = len(cel['lon']); cl = np.array(cel['lon']); ca = np.array(cel['lat'])
geo = J(R + '/docs/quartiere/data/nil.geojson')
F = geo['features']; nn = len(F)
polys = [shape(f['geometry']) for f in F]
tree = STRtree(polys)
def nil_of(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p, predicate='intersects'):
        if polys[i].covers(p): return int(i)
    return int(tree.nearest(p))
cnil = np.array([nil_of(a, b) for a, b in zip(cl, ca)])
cells_of = [np.where(cnil == i)[0] for i in range(nn)]
print('celle per quartiere: min', min(len(c) for c in cells_of), 'max', max(len(c) for c in cells_of))
# ---- 1. dove vince chi parte da ogni quartiere (media delle celle, da citta.json)
ct = J(D + '/citta.json'); cit = {}
for h in ('08', '12', '21'):
    a = np.array(ct['h' + h]).reshape(nd, 3)
    cit['h' + h] = [[int(round(float(a[c, k].mean()))) for k in range(3)] if len(c) else [0, 0, 0] for c in cells_of]
# ---- 2. incidenti per quartiere
inc = J(D + '/incidenti.json'); G = inc['griglia']
gn = np.array([nil_of(a, b) for a, b in zip(G['lon'], G['lat'])])
incq = {}
for k in ('b15', 'b5', 'a15', 'a5'):
    v = np.array(G[k]); incq[k] = [int(v[gn == i].sum()) for i in range(nn)]
    assert sum(incq[k]) == int(v.sum())
def area_km2(p):
    from shapely.ops import transform
    kx = 111.32 * np.cos(np.radians(45.46)); ky = 110.57
    return transform(lambda x, y, z=None: (np.array(x) * kx, np.array(y) * ky), p).area
km2 = [round(area_km2(p), 3) for p in polys]
# incroci: quartiere di ogni incrocio (per la mappa)
incroci = [{'a': c['a'], 'b': c['b'], 'lon': c['lon'], 'lat': c['lat'], 'n': c['b15'], 'nil': nil_of(c['lon'], c['lat'])} for c in inc['incroci']]
# ---- 3. matrice quartiere -> quartiere (tempi mediani, minuti) dalle 326 origini a griglia
O = J(D + '/origini.json'); grid = O['grid']
org_nil = {g: int(cnil[g]) for g in grid}
def leggi(fn):
    b = np.frombuffer(gzip.decompress(open(fn, 'rb').read()), dtype=np.uint8)
    return b.reshape(3, 4, nd)          # fascia, strato (bici, auto, mezzi, flag), cella
INF = 1e9
def med(v):
    v = np.where(v == 255, INF, v.astype(float)); m = float(np.median(v)) if len(v) else INF
    return 255 if m >= INF else int(round(m))
per_nil = {i: [] for i in range(nn)}   # per ogni quartiere di partenza: lista di (matrice 3 fasce x 3 modi x nn)
cx = {i: (np.mean(cl[cells_of[i]]), np.mean(ca[cells_of[i]])) for i in range(nn)}
def matrice(fn, own):
    B = leggi(fn); out = np.full((3, 3, nn), 255, dtype=np.int32)
    for d in range(nn):
        cs = [c for c in cells_of[d] if c != own]
        if not cs: continue
        for h in range(3):
            for k in range(3): out[h, k, d] = med(B[h, k, cs])
    return out
for g in grid: per_nil[org_nil[g]].append(matrice(D + '/o/c%d.bin.gz' % g, g))
usati_vicini = 0; M = np.full((3, 3, nn, nn), 255, dtype=np.int32)
for i in range(nn):
    ms = per_nil[i]
    if not ms:
        usati_vicini += 1
        best = min(grid, key=lambda g: (cl[g] - cx[i][0]) ** 2 + (ca[g] - cx[i][1]) ** 2)
        ms = [matrice(D + '/o/c%d.bin.gz' % best, best)]
    S = np.stack(ms)                    # n_origini, 3, 3, nn
    S = np.where(S == 255, INF, S.astype(float)); m = np.median(S, axis=0)
    M[:, :, i, :] = np.where(m >= INF, 255, np.round(m)).astype(np.int32)
print('quartieri senza origine propria (usato il campione piu vicino):', usati_vicini)
viaggi = {}
for hi, h in enumerate(('08', '12', '21')):
    viaggi['h' + h] = {m: M[hi, k].ravel().tolist() for k, m in enumerate('bam')}
# ---- 4. luoghi noti -> luoghi noti
nomi = O['nomi']; nl = len(nomi)
dest = [int(np.argmin(((cl - lo) * np.cos(np.radians(la))) ** 2 + (ca - la) ** 2)) for _, lo, la in nomi]
dist = [[round(float(np.hypot((nomi[i][1] - nomi[j][1]) * 111.32 * np.cos(np.radians(45.46)), (nomi[i][2] - nomi[j][2]) * 110.57)), 2) for j in range(nl)] for i in range(nl)]
luoghi = {'n': [n for n, _, _ in nomi], 'km': dist}
for hi, h in enumerate(('08', '12', '21')): luoghi['h' + h] = {m: [] for m in 'bam'}
for i in range(nl):
    B = leggi(D + '/o/n%d.bin.gz' % i)
    for hi, h in enumerate(('08', '12', '21')):
        for k, m in enumerate('bam'): luoghi['h' + h][m].append([int(B[hi, k, dest[j]]) for j in range(nl)])
# ---- scrittura (solo file nuovi)
nomi_nil = [f['properties']['n'] for f in F]
def scrivi(nome, obj):
    p = D + '/' + nome
    open(p, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
    print(nome, os.path.getsize(p))
def r5(c):
    if isinstance(c[0], (int, float)): return [round(c[0], 5), round(c[1], 5)]
    return [r5(x) for x in c]
scrivi('nil.geojson', {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'i': f['properties']['i'], 'n': f['properties']['n']}, 'geometry': {'type': f['geometry']['type'], 'coordinates': r5(f['geometry']['coordinates'])}} for f in F]})
scrivi('quartieri.json', {'n': nomi_nil, 'celle': [int(len(c)) for c in cells_of], 'cit': cit, 'inc': incq, 'km2': km2, 'incroci': incroci})
scrivi('viaggi.json', viaggi)
scrivi('luoghi.json', luoghi)
