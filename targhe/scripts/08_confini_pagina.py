"""Crea docs/targhe/data/quartieri_confini_targhe.geojson: i confini dei 88 quartieri (NIL) con i conteggi di per_nil.csv.
Confini: copia di docs/luoghi-cercati/data/nil.geojson (Comune di Milano, ds964, CC BY), tenuto solo il disegno.
Uso: python -I -X utf8 08_confini_pagina.py <percorso assoluto di targhe> <percorso assoluto di milano-in-dati>"""
import sys, os, json, csv
root = sys.argv[2]
g = json.load(open(os.path.join(root, 'docs', 'luoghi-cercati', 'data', 'nil.geojson'), encoding='utf-8'))
rows = {int(r['id_nil']): r for r in csv.DictReader(open(os.path.join(root, 'docs', 'targhe', 'data', 'per_nil.csv'), encoding='utf-8-sig'))}
out = {'type': 'FeatureCollection', 'features': []}
for f in g['features']:
    i = f['properties']['i']; r = rows[i]
    out['features'].append({'type': 'Feature', 'properties': {'i': i, 'n': f['properties']['n'], 'targhe': int(r['targhe']),
        'pers': int(r['targhe_con_persona']), 'res': int(r['targhe_resistenza'])}, 'geometry': f['geometry']})
p = os.path.join(root, 'docs', 'targhe', 'data', 'quartieri_confini_targhe.geojson')
open(p, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
print('scritto', p, len(out['features']))
