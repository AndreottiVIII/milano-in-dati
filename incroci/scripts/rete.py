"""Passo 2: dal ritaglio OpenStreetMap di Milano (ODbL) trova i nodi-incrocio e li raggruppa in incroci.
Nodo-incrocio = nodo dove si toccano almeno 3 tratti di strade con nome (una strada che passa conta 2) e almeno 2 nomi diversi.
Strade considerate: highway = motorway/trunk/primary/secondary/tertiary/unclassified/residential/living_street (niente service, link, pedonali).
Raggruppamento: nodi a meno di 25 m, oppure a meno di 90 m se hanno in comune almeno 2 nomi (le due carreggiate dello stesso incrocio); tetto 160 m di diametro.
Uso: python -I -X utf8 rete.py <ABS osm.gz> <ABS cartella incroci>   -> pulito/incroci_osm.csv, pulito/vie_osm.csv"""
import sys, gzip, collections, json
import numpy as np, pandas as pd
from lxml import etree
from pyproj import Transformer
from scipy.spatial import cKDTree
OSM, S = sys.argv[1], sys.argv[2]
HW = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'living_street'}
nodes = {}; ways = []
with gzip.open(OSM, 'rb') as f:
    for ev, e in etree.iterparse(f, events=('end',), tag=('node', 'way')):
        if e.tag == 'node':
            nodes[int(e.get('id'))] = (float(e.get('lat')), float(e.get('lon')))
        else:
            tg = {t.get('k'): t.get('v') for t in e.iterfind('tag')}
            if tg.get('highway') in HW and tg.get('name') and tg.get('area') != 'yes':
                ways.append((tg['highway'], tg['name'], [int(n.get('ref')) for n in e.iterfind('nd')], tg.get('oneway', '')))
        e.clear()
print('nodi', len(nodes), 'strade con nome', len(ways))
T = Transformer.from_crs(4326, 32632, always_xy=True)
ends = collections.defaultdict(list)       # nodo -> [(nome, n tratti)]
for hw, nm, refs, ow in ways:
    for i, r in enumerate(refs):
        c = 1 if i in (0, len(refs) - 1) else 2
        ends[r].append((nm.strip().lower(), c))
cand = []
for n, lst in ends.items():
    names = set(x[0] for x in lst)
    if len(names) >= 2 and sum(x[1] for x in lst) >= 3 and n in nodes:
        cand.append(n)
print('nodi-incrocio', len(cand))
lat = np.array([nodes[n][0] for n in cand]); lon = np.array([nodes[n][1] for n in cand])
x, y = T.transform(lon, lat)
names = [frozenset(a for a, _ in ends[n]) for n in cand]
# unione dei nodi vicini
par = list(range(len(cand)))
def find(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
tree = cKDTree(np.c_[x, y])
for i, j in tree.query_pairs(90):
    d = float(np.hypot(x[i] - x[j], y[i] - y[j]))
    if d <= 25 or len(names[i] & names[j]) >= 2:
        ri, rj = find(i), find(j)
        if ri != rj: par[rj] = ri
root = np.array([find(i) for i in range(len(cand))])
# tetto al diametro: se un gruppo supera 160 m si rifa con semi (nodo con piu' nomi) e raggio 60 m
final = np.full(len(cand), -1); nxt = 0
for r in np.unique(root):
    idx = np.where(root == r)[0]
    diam = 0 if len(idx) < 2 else max(np.ptp(x[idx]), np.ptp(y[idx]))
    if diam <= 160:
        final[idx] = nxt; nxt += 1
    else:
        left = set(idx.tolist())
        order = sorted(idx, key=lambda i: -len(names[i]))
        for s in order:
            if s not in left: continue
            grp = [i for i in left if np.hypot(x[i] - x[s], y[i] - y[s]) <= 60]
            for i in grp: final[i] = nxt; left.discard(i)
            nxt += 1
print('incroci (gruppi)', nxt)
rows = []
for g in range(nxt):
    idx = np.where(final == g)[0]
    cnt = collections.Counter()
    for i in idx:
        for a, c in ends[cand[i]]: cnt[a] += c
    nm = [a for a, _ in cnt.most_common(4)]
    rows.append({'id': g, 'lon': round(float(lon[idx].mean()), 6), 'lat': round(float(lat[idx].mean()), 6), 'nodi': len(idx),
                 'diam_m': int(max(np.ptp(x[idx]), np.ptp(y[idx]))), 'nomi_osm': ' / '.join(nm)})
pd.DataFrame(rows).to_csv(S + '/pulito/incroci_osm.csv', index=False)
pd.DataFrame({'nodo': cand, 'lon': lon.round(6), 'lat': lat.round(6), 'incrocio': final}).to_csv(S + '/pulito/nodi_incrocio_osm.csv.gz', index=False, compression='gzip')
d = pd.DataFrame(rows); print(d.nodi.describe().to_dict(), 'diametro max', int(d.diam_m.max()), 'sopra 100 m:', int((d.diam_m > 100).sum()))
