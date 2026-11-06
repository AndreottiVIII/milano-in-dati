"""Nuovi dati aggregati per la pagina Incroci (solo nuovi file in docs/incroci/data/). Nessuna riga per singolo incidente.
Uso: python -I -X utf8 genera_dati.py"""
import json, collections, os
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from scipy.spatial import cKDTree
from pyproj import Transformer
R = r'C:\Users\davide\Desktop\ClaudeTower\milano-in-dati'
S = R + r'\incroci'; OUT = R + r'\docs\incroci\data'
ANNI = list(range(2010, 2025))
df = pd.read_csv(S + r'\pulito\incidenti_geo.csv.gz', keep_default_na=False)
df['via1_k'] = df.via1_k.astype(str); df['via2_k'] = df.via2_k.astype(str)
BUONI = ['civico', 'civico_approx', 'incrocio', 'incrocio_approx']
df['buono'] = df.livello.isin(BUONI)
# --- mesi x anni
M = [[int(((df.anno == a) & (df.mese == m)).sum()) for m in range(1, 13)] for a in ANNI]
json.dump({'anni': ANNI, 'mesi': M}, open(OUT + r'\mesi_anni.json', 'w'), separators=(',', ':'))
# --- incroci (>= 10 incidenti) con anni e posto
IC = pd.read_pickle(S + r'\pulito\_IC.pkl').sort_values(['inc', 'p3'], ascending=False).reset_index(drop=True)
IC['rank'] = np.arange(1, len(IC) + 1)
IC['rank_p1'] = IC.p1.rank(ascending=False, method='min').astype(int)
IC['rank_p3'] = IC.p3.rank(ascending=False, method='min').astype(int)
Z = IC[IC.inc >= 10]
rows = []
for r in Z.itertuples():
    rows.append([int(r.id), r.nome or r.nomi_osm, round(float(r.lon), 5), round(float(r.lat), 5), int(r.inc), int(r.feriti), int(r.morti), int(r.ped), int(r.bici), int(r.moto),
                 int(r.rank), int(r.rank_p1), int(r.rank_p3), [int(v) for v in r.y]])
json.dump({'anni': ANNI, 'n_tutti': int(len(IC)), 'campi': 'id,nome,lon,lat,inc,feriti,morti,ped,bici,moto,posto,posto_2010_14,posto_2020_24,anni', 'c': rows},
          open(OUT + r'\incroci_anni.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# slope: i 20 di 2010-14 -> posto 2020-24
t1 = IC.sort_values(['p1', 'inc'], ascending=False).head(20)
sl = [[int(r.id), r.nome or r.nomi_osm, int(r.p1), int(r.p3), int(r.rank_p1), int(r.rank_p3)] for r in t1.itertuples()]
json.dump({'campi': 'id,nome,inc_2010_14,inc_2020_24,posto_2010_14,posto_2020_24', 'c': sl}, open(OUT + r'\incroci_persistenza.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# --- vie per anno
K = df[df.livello != 'nessuna']
cnt = collections.defaultdict(lambda: np.zeros(15, int))
for r in zip(K.via1_k, K.via2_k, K.livello, K.anno):
    ks = {r[0]}
    if r[2] in ('incrocio', 'incrocio_approx', 'strada') and r[1] not in ('', 'None'): ks.add(r[1])
    for k in ks:
        if k not in ('', 'None'): cnt[k][r[3] - 2010] += 1
V = pd.read_pickle(S + r'\pulito\_V.pkl')
V = V[V.km >= 0.5].copy(); V['y'] = V.key.map(lambda k: cnt[k].tolist())
V = V[V.inc >= 60].sort_values('inc', ascending=False).reset_index(drop=True)
V['posto'] = np.arange(1, len(V) + 1)
V['posto_km'] = V.inc_km_anno.rank(ascending=False, method='min').astype(int)
vr = [[r.nome, round(float(r.km), 1), int(r.inc), int(r.feriti), int(r.morti), int(r.ped), int(r.bici), int(r.moto), round(float(r.inc_km_anno), 1), int(r.posto), int(r.posto_km), r.y] for r in V.itertuples()]
json.dump({'anni': ANNI, 'n_vie': int(len(V)), 'campi': 'nome,km,inc,feriti,morti,ped,bici,moto,inc_km_anno,posto,posto_per_km,anni', 'v': vr}, open(OUT + r'\vie_anni.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# --- quartieri (NIL) per anno
G = json.load(open(R + r'\docs\medici-farmacie\data\nil.geojson', encoding='utf-8'))
polys = [shape(f['geometry']).buffer(0) for f in G['features']]
T = Transformer.from_crs(4326, 32632, always_xy=True)
P = df[df.buono].copy(); P['lon'] = pd.to_numeric(P.lon); P['lat'] = pd.to_numeric(P.lat)
pts = shapely.points(P.lon.values, P.lat.values)
nid = np.full(len(P), -1)
tree = shapely.STRtree(polys)
ii, jj = tree.query(pts, predicate='within')
nid[ii] = jj
P['nil'] = nid
out = []
for k, f in enumerate(G['features']):
    gp = P[P.nil == k]
    a_km2 = shapely.area(shapely.transform(polys[k], lambda c: np.c_[T.transform(c[:, 0], c[:, 1])[0], T.transform(c[:, 0], c[:, 1])[1]])) / 1e6
    out.append([int(f['properties']['i']), f['properties']['n'], int(f['properties']['ab']), round(float(a_km2), 2), len(gp), int(gp.feriti.sum()), int(gp.morti.sum()), int(gp.ped.sum()), int(gp.bici.sum()), int(gp.moto.sum()),
                [int((gp.anno == a).sum()) for a in ANNI]])
json.dump({'anni': ANNI, 'campi': 'id,nome,residenti,km2,inc,feriti,morti,ped,bici,moto,anni', 'q': out, 'fuori': int((nid < 0).sum()), 'totale_con_luogo': int(len(P))},
          open(OUT + r'\quartieri_incidenti.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for f in ('mesi_anni', 'incroci_anni', 'incroci_persistenza', 'vie_anni', 'quartieri_incidenti'):
    print(f, os.path.getsize(os.path.join(OUT, f + '.json')) // 1024, 'KB')
print('fuori NIL', int((nid < 0).sum()), 'su', len(P)); print(sorted(out, key=lambda r: -r[4])[:5])
