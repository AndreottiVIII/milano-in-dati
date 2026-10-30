"""Estrae le fermate delle linee M1-M5 dal GTFS AMAT (sola lettura) in ordine di percorso.
Uso: python -I 01_metro_da_gtfs.py <cartella_gtfs> <file_output.csv>
"""
import csv, sys, os, collections
gtfs, out = sys.argv[1], sys.argv[2]
metro = {'M1','M2','M3','M4','M5'}
trips = {}   # trip_id -> (route, direction)
with open(os.path.join(gtfs,'trips.txt'), encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        if r['route_id'] in metro:
            trips[r['trip_id']] = (r['route_id'], r.get('shape_id',''))
# una corsa per (linea, direzione) con piu' fermate
stops_by_trip = collections.defaultdict(list)
with open(os.path.join(gtfs,'stop_times.txt'), encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        t = r['trip_id']
        if t in trips:
            stops_by_trip[t].append((int(r['stop_sequence']), r['stop_id']))
best = {}
for t, lst in stops_by_trip.items():
    k = trips[t]
    if k not in best or len(lst) > len(best[k][1]):
        best[k] = (t, lst)
stops = {}
with open(os.path.join(gtfs,'stops.txt'), encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        stops[r['stop_id']] = r
with open(out, 'w', encoding='utf-8', newline='') as g:
    w = csv.writer(g); w.writerow(['linea','percorso','ordine','stop_id','nome','lat','lon','parent_station'])
    for (route, d), (t, lst) in sorted(best.items()):
        for i, (seq, sid) in enumerate(sorted(lst)):
            s = stops.get(sid, {})
            w.writerow([route, d, i+1, sid, s.get('stop_name',''), s.get('stop_lat',''), s.get('stop_lon',''), s.get('parent_station','')])
print('scritto', out)
