"""Fase 2, passo 1: grafo pedonale da OSM (sola lettura del file della filiera 7).
Uso: python -I f2_grafo.py <ABS strand>   -> out/grafo_pedonale.npz (+ out/grafo_stats.json)
Regole in NOTE.md "Fase 2". Nessuna scrittura fuori da <strand>."""
import sys, gzip, json, time
import numpy as np, pandas as pd
import xml.etree.ElementTree as ET
from pyproj import Transformer
from scipy.sparse import coo_matrix, csr_matrix, save_npz
from scipy.sparse.csgraph import connected_components
S = sys.argv[1]
OSM = S + '/../bici-auto-mezzi/raw/osm_milano/milano_buffer.osm.gz'
t0 = time.time()
FOOT_OK = {'yes', 'designated', 'permissive'}
ALWAYS = {'footway', 'pedestrian', 'path', 'steps', 'living_street', 'residential', 'service', 'unclassified',
          'tertiary', 'tertiary_link', 'secondary', 'secondary_link', 'primary', 'primary_link', 'track', 'road', 'corridor'}
ONLY_IF_FOOT = {'cycleway', 'trunk', 'trunk_link'}
def walkable(t):
    h = t.get('highway')
    if h is None: return False
    foot = t.get('foot'); acc = t.get('access')
    if foot in ('no', 'private'): return False
    if t.get('indoor') == 'yes': return False
    if acc in ('private', 'no') and foot not in FOOT_OK: return False
    if h in ALWAYS: return True
    if h in ONLY_IF_FOOT: return foot in FOOT_OK
    return False   # motorway, motorway_link, construction, proposed, raceway, bus_guideway, platform, elevator...
node_ll = {}; ways = []; n_hw = 0; excl = {}
with gzip.open(OSM, 'rb') as f:
    for ev, el in ET.iterparse(f, events=('end',)):
        tag = el.tag
        if tag == 'node':
            node_ll[int(el.get('id'))] = (float(el.get('lat')), float(el.get('lon')))
            el.clear()
        elif tag == 'way':
            t = {c.get('k'): c.get('v') for c in el if c.tag == 'tag'}
            if 'highway' in t:
                n_hw += 1
                if walkable(t):
                    ways.append([int(c.get('ref')) for c in el if c.tag == 'nd'])
                else:
                    excl[t['highway']] = excl.get(t['highway'], 0) + 1
            el.clear()
        elif tag == 'relation':
            el.clear()
print('nodi', len(node_ll), 'way highway', n_hw, 'way percorribili', len(ways), round(time.time() - t0), 's')
a = []; b = []
for refs in ways:
    for i in range(len(refs) - 1):
        u, v = refs[i], refs[i + 1]
        if u in node_ll and v in node_ll and u != v:
            a.append(u); b.append(v)
a = np.array(a, dtype=np.int64); b = np.array(b, dtype=np.int64)
ids = np.unique(np.concatenate([a, b]))
idx = {int(x): i for i, x in enumerate(ids)}
ia = np.fromiter((idx[int(x)] for x in a), dtype=np.int64, count=len(a))
ib = np.fromiter((idx[int(x)] for x in b), dtype=np.int64, count=len(b))
ll = np.array([node_ll[int(x)] for x in ids])
tr = Transformer.from_crs(4326, 32632, always_xy=True)
x, y = tr.transform(ll[:, 1], ll[:, 0]); x = np.asarray(x); y = np.asarray(y)
d = np.hypot(x[ia] - x[ib], y[ia] - y[ib])
df = pd.DataFrame({'u': np.minimum(ia, ib), 'v': np.maximum(ia, ib), 'd': d}).groupby(['u', 'v'], as_index=False)['d'].min()
n = len(ids)
G = coo_matrix((np.r_[df.d, df.d], (np.r_[df.u, df.v], np.r_[df.v, df.u])), shape=(n, n)).tocsr()
nc, lab = connected_components(G, directed=False)
sizes = np.bincount(lab); big = sizes.argmax()
keep = lab == big
print('componenti', nc, 'la piu grande', sizes[big], 'su', n)
newidx = -np.ones(n, dtype=np.int64); newidx[keep] = np.arange(keep.sum())
m = keep[df.u.values] & keep[df.v.values]
G2 = coo_matrix((np.r_[df.d[m], df.d[m]], (np.r_[newidx[df.u[m]], newidx[df.v[m]]], np.r_[newidx[df.v[m]], newidx[df.u[m]]])), shape=(keep.sum(),) * 2).tocsr()
save_npz(S + '/out/grafo_pedonale_csr.npz', G2)
np.savez_compressed(S + '/out/grafo_pedonale_nodi.npz', x=x[keep], y=y[keep], osm_id=ids[keep], lat=ll[keep, 0], lon=ll[keep, 1])
st = {'nodi_osm_totali': len(node_ll), 'way_highway': n_hw, 'way_percorribili': len(ways), 'nodi_grafo_prima_componente': int(n),
      'componenti': int(nc), 'nodi_componente_maggiore': int(keep.sum()), 'archi_unici_componente_maggiore': int(m.sum()),
      'lunghezza_totale_km': float(df.d[m].sum() / 1000), 'tag_highway_esclusi': dict(sorted(excl.items(), key=lambda kv: -kv[1])),
      'secondi': round(time.time() - t0)}
json.dump(st, open(S + '/out/grafo_stats.json', 'w'), indent=1, ensure_ascii=False)
print(st)
