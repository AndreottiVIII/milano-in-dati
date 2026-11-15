"""Dalle unità volumetriche (tabella creata da 01_estrai.py) calcola i riassunti pubblicati in docs/altezze/data/.
Edificio = tutte le unità volumetriche con lo stesso codice edificio; altezza dell'edificio = quella della sua unità più alta.
Quartieri (NIL): gli stessi confini usati nelle altre pagine (docs/negozi/data/nil.geojson)."""
import os, json, pickle, numpy as np, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, '..', 'docs', 'altezze', 'data'); os.makedirs(OUT, exist_ok=True)
d = pickle.load(open(os.path.join(R, 'x_uv.pkl'), 'rb'))
nil = json.load(open(os.path.join(R, '..', 'docs', 'negozi', 'data', 'nil.geojson'), encoding='utf-8'))
polys = [shape(f['geometry']) for f in nil['features']]
tree = STRtree(polys)
def quartiere(lon, lat):
    p = Point(lon, lat)
    for j in tree.query(p):
        if polys[j].contains(p): return int(j)
    # fuori dai confini NIL (bordi): nessun quartiere
    return -1
def edifici(v):
    ids = v['id']; ordine = np.argsort(ids, kind='stable'); ids_o = ids[ordine]
    uniq, inizio = np.unique(ids_o, return_index=True)
    ris = []
    for k, i0 in enumerate(inizio):
        i1 = inizio[k+1] if k+1 < len(inizio) else len(ids_o)
        ix = ordine[i0:i1]
        a = v['area'][ix]; h = v['h'][ix]
        ris.append(dict(id=uniq[k], h=float(h.max()), area=float(a.sum()), vol=float((a*h).sum()),
                        lon=float(np.average(v['lon'][ix], weights=a)), lat=float(np.average(v['lat'][ix], weights=a)), n=len(ix)))
    for e in ris: e['q'] = quartiere(e['lon'], e['lat'])
    return ris
E = {a: edifici(d[a]) for a in (2012, 2020)}
pickle.dump(E, open(os.path.join(R, 'x_edifici.pkl'), 'wb'))
for a in E: print(a, len(E[a]), 'fuori NIL', sum(e['q'] < 0 for e in E[a]))
