"""Passo 4b: semplifica i confini e li salva in docs/elezioni/data/ ; verifica zone 1999-2011 = municipi.
uso: python -I 21_confini_build.py <cartella elezioni> <cartella docs/elezioni>
"""
import sys, os, json, math

base, docs = sys.argv[1], sys.argv[2]
raw = os.path.join(base, 'raw', '_confini')
outd = os.path.join(docs, 'data')
os.makedirs(outd, exist_ok=True)
TOL = 0.00008  # gradi (~7 m)


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        den = dx * dx + dy * dy
        mx, mi = -1, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            if den == 0:
                d = math.hypot(px - ax, py - ay)
            else:
                t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / den))
                d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
            if d > mx:
                mx, mi = d, i
        if mx > tol:
            keep[mi] = True
            stack.append((a, mi)); stack.append((mi, b))
    return [p for p, k in zip(pts, keep) if k]


def simp_ring(r):
    s = dp([(x, y) for x, y in r], TOL)
    if len(s) < 4:
        s = [(x, y) for x, y in r]
    return [[round(x, 5), round(y, 5)] for x, y in s]


def simp_geom(g):
    if g['type'] == 'Polygon':
        return {'type': 'Polygon', 'coordinates': [simp_ring(r) for r in g['coordinates']]}
    return {'type': 'MultiPolygon', 'coordinates': [[simp_ring(r) for r in poly] for poly in g['coordinates']]}


def area(g):
    """area (gradi^2 -> km2 approx) con formula del lacciolo, solo anelli esterni"""
    polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    tot = 0
    for poly in polys:
        for k, ring in enumerate(poly):
            a = 0
            for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                a += (x1 * math.cos(math.radians(45.46)) * 111.32) * (y2 * 110.57) - (x2 * math.cos(math.radians(45.46)) * 111.32) * (y1 * 110.57)
            a = abs(a) / 2
            tot += a if k == 0 else -a
    return tot


def pip(pt, g):
    polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    x, y = pt
    for poly in polys:
        inside = False
        for k, ring in enumerate(poly[:1]):
            for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    inside = not inside
        if inside:
            return True
    return False


def load(p):
    return json.load(open(os.path.join(raw, p), encoding='utf-8'))


mun = load('ds379/ds379_municipi_label.geojson')
zone9 = load('ds153/zonedecentramento.geojson')
z20 = load('ds378/ds378_zone_decentramento_ex_20.geojson')

rep = {}
# --- municipi
feats = []
for f in mun['features']:
    n = f['properties']['MUNICIPIO']
    feats.append({'type': 'Feature', 'properties': {'n': n}, 'geometry': simp_geom(f['geometry'])})
feats.sort(key=lambda f: f['properties']['n'])
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(outd, 'municipi.geojson'), 'w'), separators=(',', ':'))
# --- confronto zone (ds153, 2013) vs municipi (ds379): area e centroide
cmp = []
mA = {f['properties']['MUNICIPIO']: area(f['geometry']) for f in mun['features']}
zA = {f['properties']['ZONADEC']: area(f['geometry']) for f in zone9['features']}
for n in sorted(mA):
    cmp.append((n, round(mA[n], 3), round(zA[n], 3), round(100 * (zA[n] - mA[n]) / mA[n], 3)))
rep['zone9_vs_municipi_km2'] = cmp
# --- 20 circoscrizioni
feats = []
for f in z20['features']:
    n = f['properties']['ZONADEC20']
    feats.append({'type': 'Feature', 'properties': {'n': n}, 'geometry': simp_geom(f['geometry'])})
feats.sort(key=lambda f: f['properties']['n'])
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(outd, 'circoscrizioni.geojson'), 'w'), separators=(',', ':'))
rep['ex20_km2'] = {f['properties']['ZONADEC20']: round(area(f['geometry']), 2) for f in z20['features']}
rep['tot_km2_mun'] = round(sum(mA.values()), 2)
rep['tot_km2_ex20'] = round(sum(rep['ex20_km2'].values()), 2)
# --- quale ex-zona contiene il Duomo / quale municipio
duomo = (9.1919, 45.4641)
rep['duomo_ex20'] = [f['properties']['ZONADEC20'] for f in z20['features'] if pip(duomo, f['geometry'])]
rep['duomo_mun'] = [f['properties']['MUNICIPIO'] for f in mun['features'] if pip(duomo, f['geometry'])]
# --- ex-zona -> municipio (punto interno approssimato = media dei vertici dell'anello esterno)
inc = {}
for f in z20['features']:
    g = f['geometry']
    ring = g['coordinates'][0] if g['type'] == 'Polygon' else max((p[0] for p in g['coordinates']), key=len)
    cx = sum(p[0] for p in ring) / len(ring); cy = sum(p[1] for p in ring) / len(ring)
    inc[f['properties']['ZONADEC20']] = [m['properties']['MUNICIPIO'] for m in mun['features'] if pip((cx, cy), m['geometry'])]
rep['ex20_centroide_in_municipio'] = inc
for fn in ('municipi.geojson', 'circoscrizioni.geojson'):
    rep['size_' + fn] = os.path.getsize(os.path.join(outd, fn))
json.dump(rep, open(os.path.join(base, 'pulito', 'confini_verifiche.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(rep, ensure_ascii=False, indent=1))
