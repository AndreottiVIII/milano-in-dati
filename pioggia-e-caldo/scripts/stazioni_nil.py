"""Assegna ogni sensore selezionato al NIL di Milano (punto in poligono, ds964 NIL vigenti, EPSG:4326)
e calcola gli alberi del censimento 2025 (ds2484) entro 300/500/1000 m dalla stazione.
uso: python -I -X utf8 stazioni_nil.py <pioggia-e-caldo assoluta> <milano-in-dati assoluta>
Output: pulito/stazioni_nil_alberi.csv"""
import sys, os, json, math
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
base, root = sys.argv[1], sys.argv[2]
sel = pd.read_csv(os.path.join(base, 'pulito', 'sensori_selezionati.csv'), dtype={'idsensore': str, 'idstazione': str})
gj = json.load(open(os.path.join(root, 'citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson'), encoding='utf-8'))
polys = [(shape(f['geometry']), f['properties']['ID_NIL'], f['properties']['NIL']) for f in gj['features']]
tree = STRtree([p[0] for p in polys])
st = sel.drop_duplicates('idstazione')[['idstazione', 'nomestazione', 'lat', 'lng', 'quota', 'provincia', 'dist_duomo_km']].copy()
st['lat'] = st.lat.astype(float); st['lng'] = st.lng.astype(float)
nid, nnome = [], []
for _, r in st.iterrows():
    p = Point(r.lng, r.lat)
    hit = [i for i in tree.query(p) if polys[i][0].contains(p)]
    if hit: nid.append(polys[hit[0]][1]); nnome.append(polys[hit[0]][2])
    else: nid.append(None); nnome.append(None)
st['id_nil'] = nid; st['nil'] = nnome
# alberi 2025
al = pd.read_csv(os.path.join(root, 'alberi/pulito/alberi.csv'), sep=';', usecols=['edizione', 'lon', 'lat'])
al = al[al.edizione.astype(str).str.contains('2025')]
la, lo = al.lat.values, al.lon.values
for rad in (300, 500, 1000):
    cnt = []
    for _, r in st.iterrows():
        dy = (la - r.lat) * 111200.0; dx = (lo - r.lng) * 111200.0 * math.cos(math.radians(r.lat))
        cnt.append(int((dx*dx + dy*dy <= rad*rad).sum()))
    st[f'alberi_{rad}m'] = cnt
    st[f'alberi_ha_{rad}m'] = (np.array(cnt) / (math.pi * rad * rad / 10000.0)).round(2)
nil = pd.read_csv(os.path.join(root, 'alberi/pulito/nil_alberi.csv'), sep=';', usecols=['id_nil', 'alberi_2025', 'alberi_per_km2_2025', 'alberi_per_1000ab_2025', 'indice_verde'])
st = st.merge(nil, how='left', on='id_nil')
st.to_csv(os.path.join(base, 'pulito', 'stazioni_nil_alberi.csv'), index=False)
print(st[['idstazione', 'nomestazione', 'dist_duomo_km', 'id_nil', 'nil', 'alberi_ha_500m', 'alberi_per_km2_2025']].to_string())
print(al.edizione.unique()[:5], len(al))
