"""Divide l'elenco breve delle schede (oggetti.json, 3 MB) in parti sotto 1 MB, per la regola dei 2 MB per file.
Le parti sono docs/beni-culturali/data/oggetti_1.json ... oggetti_N.json; mettendole in fila le voci tornano
nell'ordine di prima. La pagina le carica solo quando la persona arriva alla ricerca.

Uso:  python -I -X utf8 beni-culturali/scripts/10_dividi_oggetti.py [oggetti.json di partenza] [cartella di arrivo]
Di solito il file di partenza e' quello che scrive 07_pagina.py (oggetti.json nella cartella data della pagina).
"""
import json, os, sys, glob

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(R, 'docs', 'beni-culturali', 'data')
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, 'oggetti.json')
OUT = sys.argv[2] if len(sys.argv) > 2 else DATA
BUDGET = 800 * 1024  # byte per parte (lascia molto spazio sotto i 2 MB)

o = json.load(open(SRC, encoding='utf-8'))
parti, cur, peso = [], [], 0
for v in o['voci']:
    b = len(json.dumps(v, ensure_ascii=False, separators=(',', ':')).encode('utf-8')) + 1
    if cur and peso + b > BUDGET:
        parti.append(cur)
        cur, peso = [], 0
    cur.append(v)
    peso += b
if cur:
    parti.append(cur)
for f in glob.glob(os.path.join(OUT, 'oggetti_*.json')):
    os.remove(f)
for i, voci in enumerate(parti, 1):
    p = os.path.join(OUT, 'oggetti_%d.json' % i)
    json.dump({'classi': o['classi'], 'voci': voci}, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(p, len(voci), 'voci', round(os.path.getsize(p) / 1024), 'KB')
print('parti:', len(parti), '(nella pagina: PARTI_OGGETTI)')
