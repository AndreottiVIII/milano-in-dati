"""Scarica i confini delle province (Natural Earth, pubblico dominio) e li riduce a quelle del Nord Italia.
Uso: python -I -X utf8 olimpiadi/scripts/scarica.py
Il file dei dati Simico (interventi.csv) e' gia' in olimpiadi/grezzi/simico/: viene da
https://simico-ivll-public.s3.eu-south-1.amazonaws.com/data/data-export.zip (link 'Scarica i dati' di
https://www.simico.it/piano-delle-opere/), versione del 28/8/2026, scaricata il 10/11/2026.
"""
import json, os, urllib.request
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson'
req = urllib.request.Request(URL, headers={'User-Agent': 'milano-in-dati/1.0'})
d = json.loads(urllib.request.urlopen(req, timeout=180).read().decode('utf-8'))
out = []
for f in d['features']:
    p = f['properties']
    if p.get('admin') != 'Italy':
        continue
    out.append({'type': 'Feature', 'properties': {'n': p['name'], 'r': p['region']}, 'geometry': f['geometry']})
os.makedirs(os.path.join(R, 'grezzi'), exist_ok=True)
json.dump({'type': 'FeatureCollection', 'features': out}, open(os.path.join(R, 'grezzi', 'province_italia.geojson'), 'w', encoding='utf-8'), ensure_ascii=False)
print(len(out), 'province')
