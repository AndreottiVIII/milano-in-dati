"""Pietre d'inciampo, pagina v2: crea docs/pietre-inciampo/data/vite.json
(una riga per pietra: persona, date, campo, posizione). Solo fatti essenziali, nessuna biografia.
Uso: python -I -X utf8 scripts/pietre_v2_dati.py"""
import json, os
import pandas as pd
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
d = pd.read_csv(os.path.join(R, 'pietre-inciampo', 'pulito', 'pietre.csv'), sep=';', dtype=str).fillna('')
pj = json.load(open(os.path.join(R, 'docs', 'pietre-inciampo', 'data', 'pietre.json'), encoding='utf8'))
cat = {(p['nome'], p['via']): p for p in pj}
out = []
for _, r in d.iterrows():
    p = cat.get((r['nome'], r['indirizzo']))
    if p is None:
        raise SystemExit('manca: ' + r['nome'])
    out.append({
        'id': p['id'], 'n': r['nome'], 's': r['sesso'], 'c': p['cat'],
        'nb': r['data_nascita'][:10], 'ar': r['data_arresto'][:10], 'mo': r['data_morte'][:10],
        'cg': r['campo_gruppo'], 'my': int(p['morto']) if p['morto'] else None, 'ea': int(float(r['eta_arresto'])) if r['eta_arresto'] else None,
        'ap': int(p['anno']), 'st': p['stato'], 'via': p['via'], 'lon': p['lon'], 'lat': p['lat'],
        'nil': p['nil'], 'lk': p['link']})
open(os.path.join(R, 'docs', 'pietre-inciampo', 'data', 'vite.json'), 'w', encoding='utf8').write(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
print(len(out), 'righe')
import collections
print(collections.Counter(o['cg'] for o in out if o['c']=='altro'), min(o['nb'] for o in out if o['nb']), max(o['nb'] for o in out if o['nb']))
print(sum(1 for o in out if o['nb'] and o['ar'] and o['mo']), sum(1 for o in out if o['ar'] and o['mo']), sum(1 for o in out if o['s']=='' ))
