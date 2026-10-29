"""Fase 2, passo 1/2c: GTFS (ATM nuovo + Trenord) -> connessioni del giorno DATE per l'algoritmo Connection Scan.
Uso: python -I f2_gtfs.py <ABS strand>  -> out/gtfs_conn.npz"""
import sys, os, time, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f2_parametri as P
S = sys.argv[1]; O = S + '/out/'
FEEDS = [('atm', S + '/raw/gtfs/ext_comune_new/'), ('tn', S + '/raw/gtfs/ext_trenord/')]
t0 = time.time()
def tsec(s):
    p = s.str.split(':', expand=True).astype(np.int64)
    return (p[0] * 3600 + p[1] * 60 + p[2]).values
stops_all = []; conn = []; info = {}
trip_off = 0
for name, d in FEEDS:
    cd = pd.read_csv(d + 'calendar_dates.txt', dtype=str)
    active = set(cd[(cd.date == P.DATE) & (cd.exception_type == '1')].service_id)
    removed = set(cd[(cd.date == P.DATE) & (cd.exception_type == '2')].service_id)
    active -= removed
    tr = pd.read_csv(d + 'trips.txt', dtype=str, usecols=['route_id', 'service_id', 'trip_id'])
    tr = tr[tr.service_id.isin(active)]
    rt = pd.read_csv(d + 'routes.txt', dtype=str, usecols=['route_id', 'route_type', 'route_short_name'])
    tr = tr.merge(rt, on='route_id', how='left')
    st = pd.read_csv(d + 'stop_times.txt', dtype=str, usecols=['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'])
    st = st[st.trip_id.isin(set(tr.trip_id))].copy()
    st['seq'] = st.stop_sequence.astype(int)
    st = st.sort_values(['trip_id', 'seq'], kind='stable').reset_index(drop=True)
    st['arr'] = tsec(st.arrival_time); st['dep'] = tsec(st.departure_time)
    sp = pd.read_csv(d + 'stops.txt', dtype=str, usecols=['stop_id', 'stop_name', 'stop_lat', 'stop_lon'])
    sp['feed'] = name; sp['gid'] = name + ':' + sp.stop_id
    stops_all.append(sp)
    # connessioni: coppie consecutive nella stessa corsa
    same = st.trip_id.values[:-1] == st.trip_id.values[1:]
    a = st.iloc[:-1][same].reset_index(drop=True); b = st.iloc[1:][same].reset_index(drop=True)
    tid = pd.factorize(a.trip_id)[0] + trip_off
    rtype = tr.drop_duplicates('trip_id').set_index('trip_id').route_type
    c = pd.DataFrame({'from': name + ':' + a.stop_id, 'to': name + ':' + b.stop_id, 'dep': a.dep.values, 'arr': b.arr.values, 'trip': tid,
                      'rtype': a.trip_id.map(rtype).astype(int).values})
    trip_off = int(tid.max()) + 1
    conn.append(c)
    info[name] = {'servizi_attivi': len(active), 'corse_attive': int(tr.trip_id.nunique()), 'connessioni': len(c),
                  'data': P.DATE, 'tipi_linea': {k: int(v) for k, v in tr.drop_duplicates('trip_id').route_type.value_counts().items()}}
    print(name, info[name], round(time.time() - t0), 's', flush=True)
sp = pd.concat(stops_all, ignore_index=True).drop_duplicates('gid')
sid = {g: i for i, g in enumerate(sp.gid)}
c = pd.concat(conn, ignore_index=True)
c['f'] = c['from'].map(sid); c['t'] = c['to'].map(sid)
c = c.dropna(subset=['f', 't'])
c = c[(c.arr >= c.dep)].sort_values(['dep', 'arr'], kind='stable').reset_index(drop=True)
np.savez_compressed(O + 'gtfs_conn.npz', f=c.f.values.astype(np.int32), t=c.t.values.astype(np.int32), dep=c.dep.values.astype(np.int32),
                    arr=c.arr.values.astype(np.int32), trip=c.trip.values.astype(np.int32), rtype=c.rtype.values.astype(np.int8),
                    stop_lat=sp.stop_lat.astype(float).values, stop_lon=sp.stop_lon.astype(float).values,
                    stop_name=np.array(sp.stop_name.tolist(), dtype='U'), stop_feed=np.array(sp.feed.tolist(), dtype='U'))
info['connessioni_totali'] = len(c); info['fermate_totali'] = len(sp)
json.dump(info, open(O + 'gtfs_info.json', 'w'), indent=1, ensure_ascii=False)
print(info, round(time.time() - t0), 's')
