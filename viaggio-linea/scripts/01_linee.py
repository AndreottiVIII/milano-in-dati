"""Passo 1 - le linee: ordine delle fermate, coordinate e tracciato, dagli orari GTFS ATM/AMAT.

Per ogni linea scelta si prende una "corsa tipo": tra le corse del percorso (shape) indicato si sceglie quella con piu'
fermate (a parita', la prima). L'ordine delle fermate e' quello di quella corsa, le coordinate sono quelle di stops.txt.
Entrata: bici-auto-mezzi/raw/gtfs/ext_comune_new/ (GTFS ATM/AMAT, versione 425, validita' 26/10-30/11/2026, CC-BY)
Uscita:  viaggio-linea/out/linee_gtfs.json
Uso: python -I -X utf8 01_linee.py <milano-in-dati-assoluto>
"""
import sys, os, json
import pandas as pd

BASE = sys.argv[1]
G = os.path.join(BASE, 'bici-auto-mezzi', 'raw', 'gtfs', 'ext_comune_new')
OUT = os.path.join(BASE, 'viaggio-linea', 'out')
os.makedirs(OUT, exist_ok=True)

# id pagina, route_id GTFS, shape_id della corsa tipo, nome, tipo, colore, descrizione del tratto
LINEE = [
    ('M1', 'M1', 'RHO FIERAMILANO___SESTO 1 MAGGIO FS', 'M1', 'metro', '#d0021b', 'ramo Rho Fiera (non il ramo Bisceglie)'),
    ('M2', 'M2', 'ABBIATEGRASSO___GESSATE', 'M2', 'metro', '#2e9e3a', 'Abbiategrasso-Gessate (non il ramo Assago)'),
    ('M3', 'M3', 'SAN DONATO___COMASINA', 'M3', 'metro', '#d9a400', ''),
    ('M4', 'M4', 'LINATE AEROPORTO___SAN CRISTOFORO', 'M4', 'metro', '#1f5fd0', ''),
    ('M5', 'M5', 'SAN SIRO STADIO___BIGNAMI', 'M5', 'metro', '#7b3fb0', ''),
    ('T9', 'T9', '4538', 'Tram 9', 'tram', '#8a4a10', ''),
    ('T15', 'T15', '9901', 'Tram 15', 'tram', '#8a4a10', ''),
    ('F90', 'B90', ['15430', '15433'], 'Filobus 90', 'filobus', '#00695c', "circolare: nel feed il giro è spezzato in due metà (Lodi-Lotto e Lotto-Lodi), qui attaccate"),
    ('F91', 'B91', ['15438', '15439'], 'Filobus 91', 'filobus', '#00695c', "circolare in senso opposto al 90: due metà attaccate"),
]

trips = pd.read_csv(os.path.join(G, 'trips.txt'), dtype=str)
stops = pd.read_csv(os.path.join(G, 'stops.txt'), dtype=str).set_index('stop_id')
cand = {}
def lista(x):
    return x if isinstance(x, list) else [x]


for lid, rid, shp, *_ in LINEE:
    t = trips[(trips.route_id == rid) & (trips.shape_id.isin(lista(shp)))]
    assert len(t), (lid, 'nessuna corsa')
    cand[lid] = t
want = set(pd.concat(cand.values()).trip_id)
print('corse candidate', len(want))

parts = []
for ch in pd.read_csv(os.path.join(G, 'stop_times.txt'), usecols=['trip_id', 'stop_id', 'stop_sequence'], dtype=str, chunksize=1_000_000):
    parts.append(ch[ch.trip_id.isin(want)])
st = pd.concat(parts)
st['stop_sequence'] = st.stop_sequence.astype(int)
n = st.groupby('trip_id').size()

shp_ids = {x for _, _, shp, *_ in LINEE for x in lista(shp)}
sh = pd.read_csv(os.path.join(G, 'shapes.txt'), usecols=['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'], dtype={'shape_id': str})
sh = sh[sh.shape_id.isin(shp_ids)].copy()
sh['shape_pt_sequence'] = sh.shape_pt_sequence.astype(int)

out = {'gtfs': 'ATM/AMAT versione 425, validita 26/10/2026-30/11/2026', 'linee': []}
for lid, rid, shp, nome, tipo, col, nota in LINEE:
    fer = []
    shape = []
    tids = []
    for k, sid in enumerate(lista(shp)):
        t = cand[lid]
        t = t[t.shape_id == sid]
        t = t.assign(ns=t.trip_id.map(n).fillna(0)).sort_values('ns', ascending=False, kind='stable')
        tid = t.iloc[0].trip_id
        tids.append(tid)
        s = st[st.trip_id == tid].sort_values('stop_sequence')
        for j, (_, r) in enumerate(s.iterrows()):
            if k > 0 and j == 0 and fer and fer[-1]['stop_id'] == r.stop_id:
                continue  # capolinea in comune tra le due meta'
            sp = stops.loc[r.stop_id]
            fer.append({'stop_id': r.stop_id, 'nome': sp.stop_name, 'lat': float(sp.stop_lat), 'lon': float(sp.stop_lon)})
        p = sh[sh.shape_id == sid].sort_values('shape_pt_sequence')
        shape += [[round(a, 5), round(b, 5)] for a, b in zip(p.shape_pt_lat, p.shape_pt_lon)]
    tid = ' + '.join(tids)
    out['linee'].append({'id': lid, 'route_id': rid, 'nome': nome, 'tipo': tipo, 'colore': col, 'nota': nota,
                         'trip_id': tid, 'n_corse_percorso': int(len(cand[lid])),
                         'fermate': fer, 'shape': shape})
    print(lid, tid, len(fer), fer[0]['nome'], '->', fer[-1]['nome'], 'shape pts', len(shape))
json.dump(out, open(os.path.join(OUT, 'linee_gtfs.json'), 'w', encoding='utf-8'), ensure_ascii=False)
