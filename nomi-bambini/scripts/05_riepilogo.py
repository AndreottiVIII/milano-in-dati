"""Riepilogo: Bergamo (nati per anno di nascita, residenti oggi), Rozzano (nati 2007-2017), nascite Milano ds289.
Uso: python -I -X utf8 05_riepilogo.py <cartella nomi-bambini>   Scrive pulito/riepilogo_*.csv e out/riepilogo.txt"""
import sys, os, csv, collections
base = sys.argv[1]
P = os.path.join(base, 'pulito'); os.makedirs(os.path.join(base, 'out'), exist_ok=True)
L = []
def say(*a):
    s = ' '.join(str(x) for x in a); L.append(s); print(s)
FILES = []
def wcsv(name, head):
    f = open(os.path.join(P, name), 'w', encoding='utf8', newline=''); FILES.append(f)
    w = csv.writer(f); w.writerow(head); return w
rows = [(int(x['anno']), x['sesso'], x['nome'], x['cittadinanza'], int(x['nati']))
        for x in csv.DictReader(open(os.path.join(P, 'nomi_nati_bergamo.csv'), encoding='utf8'))]
years = sorted({r[0] for r in rows})
say('BERGAMO anni', years[0], years[-1], 'righe', len(rows), 'bambini (somma)', sum(r[4] for r in rows))
tot = collections.defaultdict(int)
for a, s, n, c, k in rows: tot[(a, c)] += k
w = wcsv('riepilogo_bergamo_totali.csv', ['anno', 'italiana', 'straniera', 'totale', 'quota_straniera_pct'])
for a in years:
    i, s = tot[(a, 'italiana')], tot[(a, 'straniera')]
    w.writerow([a, i, s, i + s, round(100 * s / (i + s), 1)])
def dec(a):
    return '1987-1989' if a < 1990 else '1990-1999' if a < 2000 else '2000-2009' if a < 2010 else '2010-2019' if a < 2020 else '2020-2025'
D = collections.defaultdict(lambda: collections.defaultdict(int)); DT = collections.defaultdict(int)
for a, s, n, c, k in rows:
    D[(dec(a), s)][n] += k; DT[(dec(a), s)] += k
w = wcsv('riepilogo_bergamo_top_decenni.csv', ['periodo', 'sesso', 'posizione', 'nome', 'nati', 'quota_pct'])
for key in sorted(D):
    top = sorted(D[key].items(), key=lambda x: (-x[1], x[0]))[:10]
    for i, (n, k) in enumerate(top, 1): w.writerow([key[0], key[1], i, n, k, round(100 * k / DT[key], 1)])
    say(key, 'tot', DT[key], [f'{n} {k}' for n, k in top[:5]])
Y = collections.defaultdict(lambda: collections.defaultdict(int))
for a, s, n, c, k in rows: Y[(a, s)][n] += k
w = wcsv('riepilogo_bergamo_concentrazione.csv', ['anno', 'sesso', 'nati', 'nomi_distinti', 'nomi_distinti_ogni_100', 'quota_primi10_pct', 'quota_primo_pct', 'nomi_con_1_solo_bambino'])
for a in years:
    for s in 'MF':
        d = Y[(a, s)]; t = sum(d.values()); top = sorted(d.values(), reverse=True)
        w.writerow([a, s, t, len(d), round(100 * len(d) / t, 1), round(100 * sum(top[:10]) / t, 1), round(100 * top[0] / t, 1), sum(1 for v in d.values() if v == 1)])
for f in FILES: f.flush()
say('--- concentrazione: (nati, quota primi 10 %, nomi distinti ogni 100 bambini)')
conc = list(csv.DictReader(open(os.path.join(P, 'riepilogo_bergamo_concentrazione.csv'), encoding='utf8')))
for a in (1987, 1992, 1997, 2002, 2007, 2012, 2017, 2022, 2025):
    say(a, {c['sesso']: (c['nati'], c['quota_primi10_pct'], c['nomi_distinti_ogni_100']) for c in conc if int(c['anno']) == a})
def per(lo, hi):
    d = collections.defaultdict(int)
    for a, s, n, c, k in rows:
        if lo <= a <= hi: d[(s, n)] += k
    return d
old, new = per(1987, 1999), per(2015, 2025)
told = collections.defaultdict(int); tnew = collections.defaultdict(int)
for (s, n), k in old.items(): told[s] += k
for (s, n), k in new.items(): tnew[s] += k
say('--- scomparsi: >=20 bambini nel 1987-1999 e <=2 nel 2015-2025')
sc = sorted([(k, s, n, new.get((s, n), 0)) for (s, n), k in old.items() if k >= 20 and new.get((s, n), 0) <= 2], reverse=True)
w = wcsv('riepilogo_bergamo_scomparsi.csv', ['sesso', 'nome', 'nati_1987_1999', 'nati_2015_2025'])
for k, s, n, kn in sc: w.writerow([s, n, k, kn])
say(len(sc), [f'{n}({s}) {k}->{kn}' for k, s, n, kn in sc[:20]])
say('--- nuovi: <=1 bambino nel 1987-2004 e >=25 nel 2015-2025')
a04 = per(1987, 2004)
nu = sorted([(k, s, n) for (s, n), k in new.items() if k >= 25 and a04.get((s, n), 0) <= 1], reverse=True)
w = wcsv('riepilogo_bergamo_nuovi.csv', ['sesso', 'nome', 'nati_1987_2004', 'nati_2015_2025'])
for k, s, n in nu: w.writerow([s, n, a04.get((s, n), 0), k])
say(len(nu), [f'{n}({s}) {k}' for k, s, n in nu[:20]])
say('--- crescita della quota 2015-2025 vs 1987-1999 (nomi con >=30 bambini nel 2015-2025, almeno 3 nel periodo vecchio)')
gr = []
for (s, n), k in new.items():
    o = old.get((s, n), 0)
    if k >= 30 and o >= 3:
        gr.append(((k / tnew[s]) / (o / told[s]), s, n, o, k))
gr.sort(reverse=True)
say([f'{n}({s}) {o}->{k} x{r:.1f}' for r, s, n, o, k in gr[:12]])
say('--- quota di nati con cittadinanza straniera tra i residenti nati in quell anno')
for a in (1987, 1995, 2000, 2005, 2010, 2015, 2020, 2025):
    i, s = tot[(a, 'italiana')], tot[(a, 'straniera')]; say(a, i + s, f'{100*s/(i+s):.1f}% straniera')
for lo, hi in ((1987, 2004), (2005, 2014), (2015, 2025)):
    for c in ('italiana', 'straniera'):
        d = collections.defaultdict(int)
        for a, s, n, cc, k in rows:
            if lo <= a <= hi and cc == c: d[(s, n)] += k
        tp = sorted(d.items(), key=lambda x: -x[1])[:8]
        say(lo, hi, c, [f'{n}({s}) {k}' for (s, n), k in tp])
say('--- nomi dati a entrambi i sessi nello stesso anno')
g = collections.defaultdict(set)
for a, s, n, c, k in rows: g[(a, n)].add(s)
say(sorted({n for (a, n), v in g.items() if len(v) > 1}))
rz = [(int(x['anno']), x['sesso'], x['nome'], int(x['nati'])) for x in csv.DictReader(open(os.path.join(P, 'nomi_nati_rozzano.csv'), encoding='utf8'))]
say('ROZZANO anni', min(r[0] for r in rz), max(r[0] for r in rz))
RT = collections.defaultdict(int); RD = collections.defaultdict(lambda: collections.defaultdict(int))
for a, s, n, k in rz: RT[(a, s)] += k; RD[(a, s)][n] += k
w = wcsv('riepilogo_rozzano_concentrazione.csv', ['anno', 'sesso', 'nati_elencati', 'nomi_distinti', 'quota_primi10_pct', 'primo_nome', 'primo_nome_nati', 'frequenza_minima'])
for a in range(2007, 2018):
    for s in 'MF':
        d = RD[(a, s)]; t = RT[(a, s)]; top = sorted(d.items(), key=lambda x: (-x[1], x[0]))
        w.writerow([a, s, t, len(d), round(100 * sum(v for _, v in top[:10]) / t, 1), top[0][0], top[0][1], min(d.values())])
        if a in (2007, 2012, 2017): say('Rozzano', a, s, 'nati elencati', t, 'nomi', len(d), 'primi', [f'{n} {v}' for n, v in top[:4]], 'min freq', min(d.values()))
M = collections.defaultdict(int); MF = collections.defaultdict(int)
fn = os.path.join(base, 'raw', 'milano_nascite', 'ds289_nascite.csv')
for x in csv.DictReader(open(fn, encoding='utf8'), delimiter=';'):
    a = int(x['Anno_evento']); k = int(x['Numerosita'])
    M[a] += k
    if x['Cittadinanza_madre2'] == 'Straniera' and x['Cittadinanza_padre2'] == 'Straniera': MF[a] += k
M2 = collections.defaultdict(int)
for x in csv.DictReader(open(os.path.join(base, 'raw', 'milano_nascite', 'ds1945_nascite_milano_2021_2024.csv'), encoding='utf8'), delimiter=';'):
    M2[int(x['Anno_evento'])] += int(x['Numerosità'])
say('MILANO nascite ds1945 (2021-2024)', dict(sorted(M2.items())))
w = wcsv('nascite_milano_ds289.csv', ['anno', 'nati_avvenuti_a_milano', 'di_cui_entrambi_genitori_stranieri', 'quota_pct', 'fonte'])
for a in sorted(M): w.writerow([a, M[a], MF[a], round(100 * MF[a] / M[a], 1), 'dati.comune.milano.it ds289 (CC BY), scaricato 2026-11-01'])
say('MILANO nascite ds289', {a: M[a] for a in sorted(M)})
for f in FILES: f.close()
open(os.path.join(base, 'out', 'riepilogo.txt'), 'w', encoding='utf8').write('\n'.join(L))
