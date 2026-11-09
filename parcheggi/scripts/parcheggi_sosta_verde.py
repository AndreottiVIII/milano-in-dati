"""Sosta su strada contro parchi, in metri quadrati a testa, per quartiere (almeno 5.000 residenti).
Legge docs/parcheggi/data/nil.csv e docs/verde/data/nil_verde.csv, scrive docs/parcheggi/data/sosta_contro_verde.json.
Gli stalli per quartiere sono una stima (stalli ripartiti in proporzione ai km di strada), non un conteggio.
Uso: python -I -X utf8 parcheggi/scripts/parcheggi_sosta_verde.py"""
import csv, json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def C(p):
    return list(csv.DictReader(open(os.path.join(R, 'docs', p), encoding='utf-8-sig'), delimiter=';'))
def f(x):
    try: return float(x)
    except: return None
pk = {r['id_nil']: r for r in C('parcheggi/data/nil.csv')}
vg = {r['id_nil']: r for r in C('verde/data/nil_verde.csv')}
ab_citta = sum(f(r['abitanti_2024']) for r in vg.values())
cit = {'ab': ab_citta,
       'A': sum(f(r['verde_A_m2']) for r in vg.values()) / ab_citta,
       'B': sum(f(r['verde_B_m2']) for r in vg.values()) / ab_citta}
q = []
for k, r in pk.items():
    ab = f(r['abitanti_2024'])
    if not ab or ab < 5000 or k not in vg: continue
    q.append({'id': int(k), 'n': r['nil'], 'ab': int(ab), 's': f(r['STIMA_m2_stalli_per_abitante']),
              'a': f(vg[k]['m2_ab_A']), 'b': f(vg[k]['m2_ab_B'])})
q.sort(key=lambda x: x['id'])
pa = [x for x in q if x['s'] > x['a']]; pb = [x for x in q if x['s'] > x['b']]
print('quartieri', len(q), 'sosta > parchi disegnati (A):', len(pa), 'residenti', sum(x['ab'] for x in pa), 'su', sum(x['ab'] for x in q))
print('sosta > stima completa (B):', len(pb), 'residenti', sum(x['ab'] for x in pb))
print('citta verde A %.2f B %.2f' % (cit['A'], cit['B']))
for x in sorted(q, key=lambda x: -(x['s'] / x['a'] if x['a'] else 1e9))[:8]:
    print(x['n'], x['s'], x['a'], x['b'], round(x['s'] / x['a'], 1) if x['a'] else None)
json.dump({'citta': cit, 'q': q}, open(os.path.join(R, 'docs', 'parcheggi', 'data', 'sosta_contro_verde.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
