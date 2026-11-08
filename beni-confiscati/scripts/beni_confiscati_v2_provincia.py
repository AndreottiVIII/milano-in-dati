"""Crea docs/beni-confiscati/data/provincia_milano.csv: i beni confiscati dei comuni della Città metropolitana di Milano,
agganciati ai confini dei comuni (docs/hinterland/data/comuni.geojson) per nome. Uso: python -I -X utf8 scripts/beni_confiscati_v2_provincia.py"""
import csv, json, os, unicodedata
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(R, 'docs', 'beni-confiscati', 'data')
def n(s): return unicodedata.normalize('NFKD', s.upper()).encode('ascii', 'ignore').decode().replace("'", ' ').replace('-', ' ').strip()
geo = json.load(open(os.path.join(R, 'docs', 'hinterland', 'data', 'comuni.geojson'), encoding='utf-8'))
com = {n(f['properties']['n']): f['properties'] for f in geo['features'] if f['properties']['g'] in ('MI', 'MILANO')}
rows = [r for r in csv.DictReader(open(os.path.join(D, 'confronto_comuni.csv'), encoding='utf-8')) if r['provincia'] == 'Milano']
agg = {}
for r in rows:
    k = n(r['comune'])
    if k in ('ZELO SURRIGONE', 'VERMEZZO'):   # i due comuni si sono uniti nel 2019
        k = n('Vermezzo con Zelo')
    if k not in com: raise SystemExit('comune non trovato: ' + r['comune'])
    a = agg.setdefault(k, [0, 0, 0])
    a[0] += int(r['totale']); a[1] += int(r['immobili']); a[2] += int(r['aziende'])
out = []
for k, p in com.items():
    a = agg.get(k, [0, 0, 0])
    out.append([p['i'], p['n'], a[0], a[1], a[2]])
out.sort(key=lambda x: -x[2])
with open(os.path.join(D, 'provincia_milano.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f); w.writerow(['istat', 'comune', 'totale', 'immobili', 'aziende']); w.writerows(out)
print(len(out), sum(x[2] for x in out))
