"""Dati nuovi per la pagina 'Reati denunciati' (versione 2).
Legge i file puliti gia' in docs/reati/data e scrive due file NUOVI:
  cento_denunce.json      -> "100 denunce": quota per gruppo, Milano comune e Italia, anno per anno 2006-2024
  rango_province_tutte.json -> posto di tutte le province per tasso totale, anno per anno
Uso: python -I -X utf8 pagina_v2_dati.py
"""
import csv, json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(R, 'docs', 'reati', 'data')

GRUPPI = [  # id, nome, codici ISTAT che lo compongono (nessun codice e' contato due volte)
    ('furti', 'Furti', ['THEFT']),
    ('danni', 'Danneggiamenti', ['DAMAGE']),
    ('truffe', 'Truffe e delitti informatici', ['SWINCYB', 'CYBERCRIM']),
    ('persona', 'Rapine e violenze alle persone', ['ROBBER', 'INTENHOM', 'ATTEMPHOM', 'CULPINJU', 'BLOWS', 'MENACE', 'RAPE', 'RAPEUN18']),
    ('droga', 'Stupefacenti', ['DRUG']),
]
rows = list(csv.DictReader(open(os.path.join(D, 'delitti_tipo_territorio_anno.csv'), encoding='utf-8')))
terr = {'milano': 'Milano (comune)', 'italia': 'Italia'}
anni = list(range(2006, 2025))
out = {'anni': anni, 'gruppi': [{'id': g[0], 'nome': g[1]} for g in GRUPPI] + [{'id': 'altri', 'nome': 'Tutto il resto'}]}
for k, t in terr.items():
    d = {}
    for r in rows:
        if r['territorio'] == t:
            d[(int(r['anno']), r['tipo_codice'])] = int(r['denunce'])
    ser = {'totale': [d[(a, 'TOT')] for a in anni]}
    usati = [0] * len(anni)
    for gid, _, cod in GRUPPI:
        v = [sum(d[(a, c)] for c in cod) for a in anni]
        ser[gid] = v
        usati = [x + y for x, y in zip(usati, v)]
    ser['altri'] = [d[(a, 'TOT')] - u for a, u in zip(anni, usati)]
    assert all(x > 0 for x in ser['altri'])
    out[k] = ser
json.dump(out, open(os.path.join(D, 'cento_denunce.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

pr = list(csv.DictReader(open(os.path.join(D, 'province_totale_anno.csv'), encoding='utf-8')))
prov = {}
for r in pr:
    p = prov.setdefault(r['provincia'], {'n': r['provincia'], 'r': {}, 't': {}})
    p['r'][int(r['anno'])] = int(r['rango']); p['t'][int(r['anno'])] = float(r['per_100mila'])
rp = json.load(open(os.path.join(D, 'rango_province.json'), encoding='utf-8'))
mm = {int(a): v for a, v in rp['milano_con_monza'].items()}
for a in range(2006, 2011):
    mm[a] = prov['Milano']['r'][a]
res = {'anni': anni, 'n_province': {a: int(rp['n_province'][str(a)]) for a in anni},
       'milano_con_monza': {a: mm[a] for a in anni},
       'province': [{'n': p['n'], 'r': [p['r'].get(a) for a in anni], 't': [p['t'].get(a) for a in anni]} for p in sorted(prov.values(), key=lambda x: x['n'])]}
json.dump(res, open(os.path.join(D, 'rango_province_tutte.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', len(res['province']), 'province')
