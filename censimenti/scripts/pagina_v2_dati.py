"""Pagina Censimenti, versione 2: scrive docs/censimenti/data/censimenti_v2.json (nome nuovo: i file vecchi non si toccano).
Uso: python -I -X utf8 scripts/pagina_v2_dati.py
Legge solo pulito/ (indicatori_NIL, indicatori_comune, variazioni_NIL, serie storica) e docs/censimenti/data/dati.json (serie storica gia' pronta).
Contiene, per quartiere: residenti, famiglie, quota famiglie di una persona, eta' media, quota stranieri nei 5 censimenti."""
import json, os
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, 'pulito'); OUT = os.path.join(os.path.dirname(ROOT), 'docs', 'censimenti', 'data')
Y = [1991, 2001, 2011, 2021, 2023]
nil = pd.read_csv(os.path.join(P, 'indicatori_NIL.csv'))
com = pd.read_csv(os.path.join(P, 'indicatori_comune.csv')).set_index('anno')
var = pd.read_csv(os.path.join(P, 'variazioni_NIL_1991_2023.csv')).set_index('nil')
old = json.load(open(os.path.join(OUT, 'dati.json'), encoding='utf-8'))
def col(df, c, d=2):
    return [None if pd.isna(v) else round(float(v), d) for v in df.set_index('anno').loc[Y, c]]
rows = []
for i, g in nil.groupby('nil'):
    g = g.sort_values('anno')
    rows.append({'i': int(i), 'n': g.nil_nome.iloc[0], 'm': int(var.loc[i, 'municipio']), 'ok': bool(var.loc[i, 'robusto']),
                 'pop': col(g, 'pop', 0), 'fam': col(g, 'fam', 0), 'f1': col(g, 'quota_famiglie_1_comp', 2),
                 'eta': col(g, 'eta_media_classi', 2), 'str': col(g, 'quota_stranieri', 2)})
rows.sort(key=lambda r: r['i'])
assert len(rows) == 88 and sum(r['ok'] for r in rows) == 66
c = {k: [round(float(v), 2) for v in com.loc[Y, k]] for k in ['pop', 'fam', 'fam1', 'quota_stranieri', 'eta_media_classi', 'quota_famiglie_1_comp', 'famiglie_comp_medio_approx']}
out = {'anni': Y, 'comune': {'pop': c['pop'], 'fam': c['fam'], 'fam1': c['fam1'], 'str': c['quota_stranieri'], 'eta': c['eta_media_classi'],
        'f1': c['quota_famiglie_1_comp'], 'fm': c['famiglie_comp_medio_approx']},
       'storia': old['storia'], 'nil': rows}
json.dump(out, open(os.path.join(OUT, 'censimenti_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', os.path.getsize(os.path.join(OUT, 'censimenti_v2.json')))
