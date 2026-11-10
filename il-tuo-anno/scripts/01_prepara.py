"""Il tuo anno: unisce quattro serie del Comune di Milano e scrive docs/il-tuo-anno/data/anno.json.
Legge i CSV scaricati in _esplorazione/dati/ckan/csv (ds1494, ds1495, ds2918, ds223) e docs/eta/data/eta_singola_citta.json.
Uso: python -I -X utf8 01_prepara.py"""
import csv, glob, json, os, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(R, '_esplorazione', 'dati', 'ckan', 'csv')
OUT = os.path.join(R, 'docs', 'il-tuo-anno', 'data'); os.makedirs(OUT, exist_ok=True)
def rd(pat):
    f = glob.glob(os.path.join(B, pat))[0]
    return list(csv.DictReader(open(f, encoding='utf-8-sig'), delimiter=';'))
fl = lambda s: float(str(s).replace(',', '.'))

pop = {int(r['Anno']): int(r['Popolazione']) for r in rd('ds1494*/*.csv')}
nati = {int(r['Anno']): int(r['Numero Nati']) for r in rd('ds1495*/*.csv')}
tas = {int(r['Anno']): (fl(r['Tasso natalità']), fl(r['Tasso mortalità'])) for r in rd('ds2918*/*.csv') if r['Tasso natalità']}
Y0, Y1 = 1880, 2024
assert all(y in nati for y in range(Y0, Y1 + 1)) and all(y in pop for y in range(Y0, Y1 + 1)) and all(y in tas for y in range(Y0, Y1 + 1))

# residenti a fine 2025 per eta (0..100, 100 = 100 e piu), donne e uomini
j = json.load(open(os.path.join(R, 'docs', 'eta', 'data', 'eta_singola_citta.json'), encoding='utf-8'))
i = j['anni'].index(2025)
F, M = j['F'][i], j['M'][i]
assert len(F) == 101
# nati del 2024 e piu indietro: la persona nata nell'anno b ha 2025-b anni compiuti al 31/12/2025
res_b = {}      # anno di nascita -> (donne, uomini)
for b in range(1926, 2026):
    a = 2025 - b
    res_b[b] = (F[a], M[a])

# stato civile: 2012 e 2025, per sesso e per eta (18..94 e "95 e piu" = 95)
S = list(csv.DictReader(open(glob.glob(os.path.join(B, 'ds223*/*.csv'))[0], encoding='utf-8-sig'), delimiter=';'))
cols = ['nonsposati_stima', 'sposati_stima', 'divorziati_stima', 'vedovi_stima']
altre = ['già_unione_civile_scioglimento_stima', 'uniti_civilmente_stima', 'già_unione_civile_decesso_partner_stima']
agg = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
for r in S:
    if r['Anno'] not in ('2012', '2025'): continue
    e = 95 if 'più' in r['Eta'] else int(r['Eta'])
    k = (int(r['Anno']), r['Genere'][0], e)
    for n, c in enumerate(cols): agg[k][n] += int(float(r[c] or 0))
    agg[k][4] += sum(int(float(r[c] or 0)) for c in altre)
stato = {}
for anno in (2012, 2025):
    for g in ('F', 'M'):
        # per ogni eta: [mai sposati, sposati, divorziati, vedovi, altro] in unita; poi quote in % con un decimale
        righe = []
        for e in range(18, 96):
            v = agg[(anno, g, e)]; t = sum(v)
            righe.append([round(100 * x / t, 1) for x in v] + [t])
        stato['%s%d' % (g, anno)] = righe
# totali adulti sposati (18+)
tot = {}
for anno in (2012, 2025):
    t = [0] * 5
    for g in ('F', 'M'):
        for e in range(18, 96):
            for n in range(5): t[n] += agg[(anno, g, e)][n]
    tot[anno] = t

out = {
    'anni': list(range(Y0, Y1 + 1)),
    'nati': [nati[y] for y in range(Y0, Y1 + 1)],
    'pop': [pop[y] for y in range(Y0, Y1 + 1)] + [pop[2025]],     # 1880..2025
    'natalita': [tas[y][0] for y in range(Y0, Y1 + 1)],
    'mortalita': [tas[y][1] for y in range(Y0, Y1 + 1)],
    'res_nascita': {'primo': 1926, 'ultimo': 2025, 'donne': [res_b[b][0] for b in range(1926, 2026)], 'uomini': [res_b[b][1] for b in range(1926, 2026)]},
    'centenari': [F[100], M[100]],
    'stato': {'eta_da': 18, 'eta_a': 95, 'colonne': ['mai sposati', 'sposati', 'divorziati', 'vedovi', 'altro', 'persone'], **stato},
    'adulti': {str(a): {'persone': sum(t), 'sposati': t[1], 'mai_sposati': t[0]} for a, t in tot.items()},
}
json.dump(out, open(os.path.join(OUT, 'anno.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('scritto', os.path.getsize(os.path.join(OUT, 'anno.json')), 'byte')
# controlli
mx = max(nati, key=nati.get); print('record nati', mx, nati[mx]); pm = max(pop, key=pop.get); print('max pop', pm, pop[pm])
print('adulti sposati 2012', round(100 * tot[2012][1] / sum(tot[2012]), 1), '2025', round(100 * tot[2025][1] / sum(tot[2025]), 1))
ult = max(y for y in tas if tas[y][0] > tas[y][1]); print('ultimo anno con piu nati che morti', ult)
rap = {b: (res_b[b][0] + res_b[b][1]) / nati[b] for b in range(1926, 2025) if b in nati}
bm = max(rap, key=rap.get); print('rapporto max', bm, round(rap[bm], 2), nati[bm], sum(res_b[bm]))
print('1990:', nati[1990], sum(res_b[1990]), round(rap[1990], 2), 'eta', 2025 - 1990)
print('nati 2024 vs 1880', nati[2024], nati[1880], 'tassi', tas[1880], tas[2024])
print('anni con meno nati del 2024:', sorted(y for y in nati if nati[y] < nati[2024]))
print('rapporto >1 da nati', min(b for b in rap if rap[b] > 1 and b > 1990 - 1) if False else '')
print('sotto 1:', [b for b in sorted(rap) if rap[b] < 1][:8], '...', [b for b in sorted(rap) if rap[b] < 1][-8:])
