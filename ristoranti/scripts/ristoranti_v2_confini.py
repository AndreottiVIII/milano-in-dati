"""Copia i confini dei quartieri nella cartella della pagina Ristoranti, tenendo solo numero e nome.
Uso: python -I -X utf8 scripts/ristoranti_v2_confini.py"""
import json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # progetto milano-in-dati
g = json.load(open(os.path.join(R, 'docs', 'medici-farmacie', 'data', 'nil.geojson'), encoding='utf-8'))
for f in g['features']:
    p = f['properties']
    f['properties'] = {'i': p['i'], 'n': p['n']}
out = os.path.join(R, 'docs', 'ristoranti', 'data', 'nil.geojson')
open(out, 'w', encoding='utf-8').write(json.dumps(g, ensure_ascii=False, separators=(',', ':')))
print(out, os.path.getsize(out))
