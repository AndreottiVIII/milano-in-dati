"""Fase 2, passo 2a: legge il ritaglio OSM una volta sola e salva in out/osm_parsed.pkl
nodi (id, lat, lon), tag dei nodi che servono, strade (highway) con i tag che servono.
Uso: python -I f2_osm.py <ABS strand>"""
import sys, gzip, pickle, time
import numpy as np
import xml.etree.ElementTree as ET
S = sys.argv[1]
OSM = S + '/raw/osm_milano/milano_buffer.osm.gz'
WAYKEYS = {'highway', 'oneway', 'oneway:bicycle', 'junction', 'maxspeed', 'bicycle', 'foot', 'access', 'motor_vehicle',
           'vehicle', 'surface', 'service', 'name', 'area', 'footway', 'cycleway', 'cycleway:left', 'cycleway:right',
           'cycleway:both', 'cycleway:left:oneway', 'cycleway:right:oneway', 'sidewalk', 'bicycle:conditional', 'tunnel',
           'ref', 'motorroad', 'maxspeed:type', 'lit', 'indoor', 'level', 'bridge', 'bus', 'psv', 'motorcar', 'highway:note'}
t0 = time.time()
ids = []; lat = []; lon = []; ntags = {}
ways = []
with gzip.open(OSM, 'rb') as f:
    for ev, el in ET.iterparse(f, events=('end',)):
        tg = el.tag
        if tg == 'node':
            i = int(el.get('id')); ids.append(i); lat.append(float(el.get('lat'))); lon.append(float(el.get('lon')))
            tt = {c.get('k'): c.get('v') for c in el if c.tag == 'tag'}
            if tt:
                keep = {k: v for k, v in tt.items() if k in ('highway', 'crossing', 'barrier', 'traffic_calming', 'traffic_signals', 'access', 'bicycle', 'motor_vehicle', 'name')}
                if keep: ntags[i] = keep
            el.clear()
        elif tg == 'way':
            tt = {c.get('k'): c.get('v') for c in el if c.tag == 'tag'}
            if 'highway' in tt:
                ways.append(({k: v for k, v in tt.items() if k in WAYKEYS or k.startswith('cycleway')}, [int(c.get('ref')) for c in el if c.tag == 'nd']))
            el.clear()
        elif tg == 'relation':
            el.clear()
ids = np.array(ids, dtype=np.int64); lat = np.array(lat); lon = np.array(lon)
pickle.dump({'ids': ids, 'lat': lat, 'lon': lon, 'ntags': ntags, 'ways': ways}, open(S + '/out/osm_parsed.pkl', 'wb'), protocol=4)
print('nodi', len(ids), 'nodi con tag', len(ntags), 'strade', len(ways), round(time.time() - t0), 's')
