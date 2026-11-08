"""Pagina "Acqua del sindaco" (versione 2): prepara il file con i confini dei quartieri per la mappa.
Copia docs/quartiere/data/nil.geojson (Comune di Milano, CC BY) in docs/acqua-del-sindaco/data/nil_milano.geojson
tenendo solo nome e numero del quartiere. Uso: python -I -X utf8 acqua_v2_dati.py"""
import json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
g = json.load(open(os.path.join(R, 'docs', 'quartiere', 'data', 'nil.geojson'), encoding='utf-8'))
out = {'type': 'FeatureCollection', 'features': [
    {'type': 'Feature', 'properties': {'i': f['properties']['i'], 'n': f['properties']['n']}, 'geometry': f['geometry']}
    for f in g['features']]}
p = os.path.join(R, 'docs', 'acqua-del-sindaco', 'data', 'nil_milano.geojson')
open(p, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
print(p, os.path.getsize(p), len(out['features']))
