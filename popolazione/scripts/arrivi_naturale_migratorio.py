"""Saldo naturale (nati meno morti) e saldo migratorio (arrivi meno partenze) per quartiere.
Legge docs/nascite/data/nil_2022_2024.csv, docs/speranza-vita/data/decessi_nil_anno_sesso.csv e
docs/arrivi-partenze/data/nil_saldi.csv; scrive docs/arrivi-partenze/data/nil_naturale_migratorio.csv.
Nati e morti: media annua 2022-2024 (nati per residenza della madre, morti per residenza). Saldo migratorio: 2020-2024.
Solo quartieri con almeno 3.000 residenti.
Uso: python -I -X utf8 popolazione/scripts/arrivi_naturale_migratorio.py"""
import csv, os, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def C(p):
    return list(csv.DictReader(open(os.path.join(R, 'docs', p), encoding='utf-8-sig'), delimiter=';'))
na = {r['id_nil']: r for r in C('nascite/data/nil_2022_2024.csv')}
de = collections.defaultdict(int)
for r in C('speranza-vita/data/decessi_nil_anno_sesso.csv'):
    if r['anno'] in ('2022', '2023', '2024'): de[r['id_nil']] += int(r['decessi'])
sa = {r['id_nil']: r for r in C('arrivi-partenze/data/nil_saldi.csv')}
rows = []
for k, r in na.items():
    res = float(r['residenti_2024'])
    if res < 3000 or k not in sa: continue
    nati = float(r['nati_2022_2024']) / 3; morti = de[k] / 3
    nat = (nati - morti) / res * 1000
    mig = float(sa[k]['saldo_totale_x1000_anno_2020_2024'])
    it = float(sa[k]['saldo_italia_x1000_anno_2020_2024']); es = float(sa[k]['saldo_estero_x1000_anno_2020_2024'])
    rows.append([int(k), r['nil'], int(res), round(nati, 1), round(morti, 1), round(nat, 2), round(mig, 2), round(it, 2), round(es, 2)])
rows.sort()
out = os.path.join(R, 'docs', 'arrivi-partenze', 'data', 'nil_naturale_migratorio.csv')
with open(out, 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh, delimiter=';')
    w.writerow(['id_nil', 'nil', 'residenti_2024', 'nati_anno_2022_2024', 'morti_anno_2022_2024', 'saldo_naturale_x1000', 'saldo_migratorio_x1000_2020_2024', 'saldo_italia_x1000_2020_2024', 'saldo_estero_x1000_2020_2024'])
    w.writerows(rows)
n = len(rows)
print('quartieri', n)
print('nati/anno', round(sum(r[3] for r in rows)), 'morti/anno', round(sum(r[4] for r in rows)), 'naturale', round(sum(r[3] - r[4] for r in rows)))
print('piu nati che morti:', sum(1 for r in rows if r[5] > 0), [r[1] for r in rows if r[5] > 0])
print('naturale+migratorio < 0:', sum(1 for r in rows if r[5] + r[6] < 0))
print('perde Italia e guadagna estero:', sum(1 for r in rows if r[7] < 0 and r[8] > 0), ' perde Italia:', sum(1 for r in rows if r[7] < 0))
q = collections.Counter(('N+' if r[5] > 0 else 'N-') + ('M+' if r[6] > 0 else 'M-') for r in rows); print(q)
print('range nat', min(r[5] for r in rows), max(r[5] for r in rows), 'mig', min(r[6] for r in rows), max(r[6] for r in rows))
