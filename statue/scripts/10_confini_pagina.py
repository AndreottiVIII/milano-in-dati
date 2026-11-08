"""Crea docs/statue/data/quartieri_confini_statue.geojson: i confini dei 88 quartieri (NIL) con i conteggi di per_nil.csv.
Confini: copia di docs/luoghi-cercati/data/nil.geojson (Comune di Milano, ds964, CC BY), tenuto solo il disegno.
Uso: python -I -X utf8 10_confini_pagina.py <percorso assoluto di statue> <percorso assoluto di milano-in-dati>"""
import sys, os, json, csv
st, root = sys.argv[1], sys.argv[2]
g = json.load(open(os.path.join(root, 'docs', 'luoghi-cercati', 'data', 'nil.geojson'), encoding='utf-8'))
rows = {int(r['id_nil']): r for r in csv.DictReader(open(os.path.join(root, 'docs', 'statue', 'data', 'per_nil.csv'), encoding='utf-8-sig'))}
out = {'type': 'FeatureCollection', 'features': []}
for f in g['features']:
    i = f['properties']['i']; r = rows[i]
    out['features'].append({'type': 'Feature', 'properties': {
        'i': i, 'n': f['properties']['n'], 'area': float(r['area_kmq']), 'opere': int(r['opere']), 'smc': int(r['statue_monumenti_sculture']),
        'mur': int(r['murali']), 'pers': int(r['persone_reali']), 'donne': int(r['donne']), 'kmq': float(r['opere_per_kmq'])}, 'geometry': f['geometry']})
p = os.path.join(root, 'docs', 'statue', 'data', 'quartieri_confini_statue.geojson')
open(p, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
print('scritto', p, len(out['features']))
