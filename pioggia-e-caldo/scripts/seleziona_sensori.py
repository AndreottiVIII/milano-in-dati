"""Sceglie i sensori di temperatura e precipitazione entro R km dal Duomo di Milano.
uso: python -I -X utf8 seleziona_sensori.py <anagrafica.csv> <out.csv> [raggio_km]
Fonte: ARPA Lombardia, dataset nf78-nj6b (Stazioni Idro Nivo Meteorologiche), CC0."""
import csv, math, sys
src, out = sys.argv[1], sys.argv[2]
R = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
LAT0, LON0 = 45.4642, 9.1900  # Duomo
def dist(lat, lon):
    return math.hypot((lat-LAT0)*111.2, (lon-LON0)*111.2*math.cos(math.radians(LAT0)))
rows = []
for x in csv.DictReader(open(src, encoding='utf-8')):
    if x['tipologia'] not in ('Temperatura', 'Precipitazione'): continue
    d = dist(float(x['lat']), float(x['lng']))
    if d <= R:
        x['dist_duomo_km'] = round(d, 2); rows.append(x)
rows.sort(key=lambda x: (x['dist_duomo_km'], x['tipologia']))
cols = ['idsensore','tipologia','unit_dimisura','idstazione','nomestazione','quota','provincia','datastart','datastop','storico','lat','lng','dist_duomo_km']
with open(out, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
print(len(rows), 'sensori entro', R, 'km:', sum(r['tipologia']=='Temperatura' for r in rows), 'T,', sum(r['tipologia']=='Precipitazione' for r in rows), 'P')
