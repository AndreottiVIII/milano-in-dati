"""I proverbi alla prova: legge le temperature di Brera (docs/il-tuo-giorno/data) e la pioggia di Milano
(docs/pioggia/data/anni), scrive docs/proverbi/data/proverbi.json. Uso: python -I -X utf8 01_calcola.py [-q]"""
import csv, json, os, sys, datetime as dt, collections
import numpy as np
from dateutil.easter import easter
from scipy import stats
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = dt.date
OUT = os.path.join(R, 'docs', 'proverbi', 'data'); os.makedirs(OUT, exist_ok=True)
VERBOSE = '-q' not in sys.argv

# ---------- dati ----------
T = {}
for f in ('temperature_brera_giornaliere_1763-1930.csv', 'temperature_brera_giornaliere_1931-2026.csv'):
    for r in csv.DictReader(open(os.path.join(R, 'docs/il-tuo-giorno/data', f), encoding='utf-8-sig'), delimiter=';'):
        try: T[D.fromisoformat(r['data'])] = (float(r['minima_gradi']) + float(r['massima_gradi'])) / 2
        except Exception: pass
P = {}
d0 = os.path.join(R, 'docs/pioggia/data/anni')
for f in sorted(os.listdir(d0)):
    y = int(f[:4]); v = json.load(open(os.path.join(d0, f), encoding='utf-8'))['v']
    for i, x in enumerate(v):
        if x is not None: P[D(y, 1, 1) + dt.timedelta(days=i)] = x
Y0, Y1 = 1763, 2025          # anni interi di temperatura
R0 = 1996                    # ultimi 30 anni: 1996-2025
P0 = 1858
RAIN = 1.0                   # mm: soglia di giorno di pioggia
def r1(x): return round(float(x), 1)
def r2(x): return round(float(x), 2)
def log(*a):
    if VERBOSE: print(*a)

# ---------- medie per giorno del calendario (senza 29 febbraio) ----------
def cal_days():
    d = D(2001, 1, 1); out = []
    while d.year == 2001: out.append((d.month, d.day)); d += dt.timedelta(days=1)
    return out
CAL = cal_days(); IDX = {k: i for i, k in enumerate(CAL)}
def clim(y0, y1):
    a = collections.defaultdict(list)
    for d, v in T.items():
        if y0 <= d.year <= y1 and (d.month, d.day) != (2, 29): a[(d.month, d.day)].append(v)
    return np.array([np.mean(a[k]) for k in CAL])
C_ALL = clim(Y0, Y1); C_REC = clim(R0, Y1)
def smooth(a, w):  # media mobile circolare, w dispari
    h = w // 2; n = len(a)
    return np.array([np.mean([a[(i + j) % n] for j in range(-h, h + 1)]) for i in range(n)])
def win3(c):  # media di 3 giorni consecutivi, indicizzata dal primo giorno
    n = len(c); return np.array([np.mean([c[(i + j) % n] for j in range(3)]) for i in range(n)])
def dlab(i): m, d = CAL[i]; return '%d/%d' % (d, m)

out = {'meta': {'anni_temperatura': [Y0, Y1], 'ultimi_anni': [R0, Y1], 'anni_pioggia': [P0, 2025], 'soglia_pioggia_mm': RAIN}}

# ====================== 1. giorni della merla ======================
w_all, w_rec = win3(C_ALL), win3(C_REC)
iM = IDX[(1, 29)]
rank_all = int((w_all < w_all[iM]).sum()) + 1; rank_rec = int((w_rec < w_rec[iM]).sum()) + 1
imin_all, imin_rec = int(np.argmin(w_all)), int(np.argmin(w_rec))
log('MERLA media 29-31/1 tutti', r2(w_all[iM]), 'rank', rank_all, '/365; piu freddo', dlab(imin_all), dlab((imin_all + 2) % 365), r2(w_all[imin_all]))
log('MERLA recenti', r2(w_rec[iM]), 'rank', rank_rec, 'piu freddo', dlab(imin_rec), r2(w_rec[imin_rec]))
def inverni(y0, y1):
    starts = collections.Counter(); n = 0; merla_best = 0; merla_near = 0; merla_colder_jan = 0
    for y in range(y0, y1 + 1):
        d = D(y - 1, 12, 1); end = D(y, 2, 26); vals = []
        try:
            while d <= end:
                vals.append((np.mean([T[d + dt.timedelta(days=j)] for j in range(3)]), d)); d += dt.timedelta(days=1)
            mer = np.mean([T[D(y, 1, k)] for k in (29, 30, 31)]); rest = np.mean([T[D(y, 1, k)] for k in range(1, 29)])
        except KeyError: continue
        b = min(vals)[1]; n += 1
        starts[(b.month, b.day)] += 1
        merla_best += b == D(y, 1, 29); merla_near += abs((b - D(y, 1, 29)).days) <= 1
        merla_colder_jan += mer < rest
    return n, starts, merla_best, merla_near, merla_colder_jan
out['merla'] = {}
for nm, (a, b) in (('tutti', (Y0 + 1, Y1)), ('ultimi30', (R0, Y1))):
    n, st_, mb, mn, mj = inverni(a, b)
    log('MERLA', nm, 'inverni', n, 'tris piu freddo parte il 29/1:', mb, 'tra 28 e 30:', mn, 'merla piu fredda del resto di gennaio:', mj, round(100 * mj / n))
    out['merla'][nm] = {'inverni': n, 'parte_29_gen': mb, 'parte_28_30_gen': mn, 'piu_fredda_resto_gen': mj}
nW, stW, _, _, _ = inverni(Y0 + 1, Y1); nR, stR, _, _, _ = inverni(R0, Y1)
iw = [IDX[(12, d)] for d in range(1, 32)] + [IDX[(1, d)] for d in range(1, 32)] + [IDX[(2, d)] for d in range(1, 29)]
s_all, s_rec = smooth(C_ALL, 5), smooth(C_REC, 5)
out['merla']['curva'] = {'giorni': [CAL[i][0] * 100 + CAL[i][1] for i in iw], 'tutti': [r1(s_all[i]) for i in iw], 'ultimi30': [r1(s_rec[i]) for i in iw]}
out['merla']['tris'] = {'merla_tutti': r1(w_all[iM]), 'merla_rec': r1(w_rec[iM]), 'rank_tutti': rank_all, 'rank_rec': rank_rec,
    'freddo_tutti': {'da': CAL[imin_all], 'a': CAL[(imin_all + 2) % 365], 'c': r1(w_all[imin_all])},
    'freddo_rec': {'da': CAL[imin_rec], 'a': CAL[(imin_rec + 2) % 365], 'c': r1(w_rec[imin_rec])}}
days_w = [(12, d) for d in range(1, 32)] + [(1, d) for d in range(1, 32)] + [(2, d) for d in range(1, 27)]
out['merla']['partenze_tutti'] = [stW.get(k, 0) for k in days_w]
out['merla']['partenze_rec'] = [stR.get(k, 0) for k in days_w]
out['merla']['partenze_giorni'] = [k[0] * 100 + k[1] for k in days_w]
log('partenze top', sorted(stW.items(), key=lambda x: -x[1])[:6])

# ====================== 2. estate di San Martino ======================
NV = [(10, d) for d in range(15, 32)] + [(11, d) for d in range(1, 31)] + [(12, d) for d in range(1, 11)]
def share_warmer(y0, y1, k=7):
    res = {}
    for m, dd in NV:
        c = n = 0
        for y in range(y0, y1 + 1):
            d = D(y, m, dd)
            try: pre = np.mean([T[d - dt.timedelta(days=j)] for j in range(1, k + 1)]); v = T[d]
            except KeyError: continue
            n += 1; c += v > pre
        res[(m, dd)] = (c, n)
    return res
sw_all, sw_rec = share_warmer(Y0, Y1), share_warmer(R0, Y1)
keys = list(sw_all)
out['martino'] = {'giorni': [m * 100 + d for m, d in keys],
    'tutti': [r1(100 * sw_all[k][0] / sw_all[k][1]) for k in keys], 'ultimi30': [r1(100 * sw_rec[k][0] / sw_rec[k][1]) for k in keys],
    'l11_tutti': {'c': sw_all[(11, 11)][0], 'n': sw_all[(11, 11)][1]}, 'l11_rec': {'c': sw_rec[(11, 11)][0], 'n': sw_rec[(11, 11)][1]}}
sh = [100 * sw_all[k][0] / sw_all[k][1] for k in keys]
v11 = 100 * sw_all[(11, 11)][0] / sw_all[(11, 11)][1]
rk = sorted(sh, reverse=True).index(v11) + 1
out['martino']['posto_11_nov'] = {'posto': rk, 'su': len(keys), 'media_giorni': r1(np.mean(sh)), 'min': r1(min(sh)), 'max': r1(max(sh))}
log('SAN MARTINO 11/11 piu caldo della settimana prima: tutti', sw_all[(11, 11)], r1(v11), 'recenti', sw_rec[(11, 11)], 'posto', rk, 'su', len(keys), 'media tutti giorni', r1(np.mean(sh)), min(sh), max(sh))
def sm3(y0, y1):
    n = c = 0; diffs = []
    for y in range(y0, y1 + 1):
        try:
            a = np.mean([T[D(y, 11, d)] for d in (10, 11, 12)]); b = np.mean([T[D(y, 11, d)] for d in (5, 6, 7)]); e = np.mean([T[D(y, 11, d)] for d in (15, 16, 17)])
        except KeyError: continue
        n += 1; c += a > b; diffs.append(a - (b + e) / 2)
    return n, c, float(np.mean(diffs)), float(np.std(diffs) / np.sqrt(len(diffs)))
for nm, (a, b) in (('tutti', (Y0, Y1)), ('ultimi30', (R0, Y1))):
    n, c, dm, se = sm3(a, b); log('SM 10-12 vs 5-7', nm, n, c, round(100 * c / n), 'scarto vs prima/dopo', r2(dm), '+-', r2(se))
    out['martino']['tris_' + nm] = {'n': n, 'piu_caldo_settimana_prima': c, 'scarto': r2(dm), 'errore': r2(se)}
out['martino']['media_giorno'] = [r1(C_ALL[IDX[k]]) for k in NV]
out['martino']['media_giorno_rec'] = [r1(C_REC[IDX[k]]) for k in NV]
base = smooth(C_ALL, 15)
def spells(y0, y1, thr=2.0):
    out_ = {}
    for st0 in NV:
        c = n = 0
        for y in range(y0, y1 + 1):
            ok = True; run = 0; best = 0
            for j in range(7):
                dd = D(y, st0[0], st0[1]) + dt.timedelta(days=j)
                if (dd.month, dd.day) == (2, 29): continue
                if dd not in T: ok = False; break
                an = T[dd] - base[IDX[(dd.month, dd.day)]]
                run = run + 1 if an >= thr else 0; best = max(best, run)
            if not ok: continue
            n += 1; c += best >= 3
        out_[st0] = (c, n)
    return out_
sp = spells(Y0, Y1)
spk = [k for k in NV if k <= (11, 24)]
spv = {k: 100 * sp[k][0] / sp[k][1] for k in spk}
log('SM periodi caldi (3 giorni a +2 C) nella settimana che parte l 8/11:', sp[(11, 8)], r1(spv[(11, 8)]), '| media altre settimane', r1(np.mean(list(spv.values()))), 'min', r1(min(spv.values())), 'max', r1(max(spv.values())))
out['martino']['spell'] = {'giorni': [k[0] * 100 + k[1] for k in spk], 'valori': [r1(spv[k]) for k in spk], 'l8': r1(spv[(11, 8)]), 'media': r1(np.mean(list(spv.values()))), 'n': sp[(11, 8)][1]}

# ====================== 3. weekend ======================
def weekday(y0, y1):
    a = collections.defaultdict(list)
    for d, x in P.items():
        if y0 <= d.year <= y1: a[d.weekday()].append(x)
    return a
out['weekend'] = {}
for nm, (a, b) in (('tutti', (P0, 2025)), ('ultimi30', (R0, 2025))):
    wd = weekday(a, b)
    quota = [100 * sum(1 for x in wd[k] if x >= RAIN) / len(wd[k]) for k in range(7)]
    mm = [float(np.mean(wd[k])) for k in range(7)]
    tab = np.array([[sum(1 for x in wd[k] if x >= RAIN), sum(1 for x in wd[k] if x < RAIN)] for k in range(7)])
    chi, p, _, _ = stats.chi2_contingency(tab)
    we = [x for k in (5, 6) for x in wd[k]]; fe = [x for k in range(5) for x in wd[k]]
    log('WEEKEND', nm, 'giorni', sum(len(v) for v in wd.values()), 'quota >=1mm lun..dom', [r1(q) for q in quota], 'mm', [r2(m) for m in mm], 'chi2 p', r2(p),
        'we', r1(100 * sum(1 for x in we if x >= RAIN) / len(we)), 'feriali', r1(100 * sum(1 for x in fe if x >= RAIN) / len(fe)))
    tab2 = np.array([[sum(1 for x in we if x >= RAIN), sum(1 for x in we if x < RAIN)], [sum(1 for x in fe if x >= RAIN), sum(1 for x in fe if x < RAIN)]])
    p2 = stats.chi2_contingency(tab2)[1]; log('  weekend contro feriali p', r2(p2))
    out['weekend'][nm] = {'p_we': r2(p2), 'quota': [r1(q) for q in quota], 'mm': [r2(m) for m in mm], 'giorni': int(sum(len(v) for v in wd.values())), 'p': r2(p),
        'we': r1(100 * sum(1 for x in we if x >= RAIN) / len(we)), 'feriali': r1(100 * sum(1 for x in fe if x >= RAIN) / len(fe))}

# ====================== 4. pioggia dopo il santo (Ascensione, Santa Bibiana) ======================
def dopo(giorno_fn, nlen, y0, y1):
    si, no = [], []
    for y in range(y0, y1 + 1):
        d = giorno_fn(y)
        try:
            r = P[d] >= RAIN; n = sum(1 for j in range(1, nlen + 1) if P[d + dt.timedelta(days=j)] >= RAIN)
        except KeyError: continue
        (si if r else no).append(n)
    return si, no
def confronto(si, no, seed=1):
    dm = float(np.mean(si) - np.mean(no)); allv = np.array(si + no); k = len(si); rng = np.random.default_rng(seed); c = 0
    for _ in range(20000):
        rng.shuffle(allv); c += abs(allv[:k].mean() - allv[k:].mean()) >= abs(dm)
    return dm, (c + 1) / 20001
for nome, fn, nl, y1 in (('ascensione', lambda y: easter(y) + dt.timedelta(days=39), 40, 2025), ('bibiana', lambda y: D(y, 12, 2), 47, 2024)):
    res = {}
    for nm, a in (('tutti', P0), ('ultimi30', R0)):
        si, no = dopo(fn, nl, a, y1); dm, p = confronto(si, no)
        res[nm] = {'anni_piove': len(si), 'anni_asciutto': len(no), 'gg_piove': r1(np.mean(si)), 'gg_asciutto': r1(np.mean(no)), 'max_piove': int(max(si)), 'p': r2(p), 'diff': r2(dm)}
        log(nome.upper(), nm, res[nm])
    res['finestra'] = nl
    si, no = dopo(fn, nl, P0, y1)
    res['meta_pioggia'] = {'piove': int(sum(1 for n in si if n >= nl / 2)), 'anni_piove': len(si), 'asciutto': int(sum(1 for n in no if n >= nl / 2)), 'anni_asciutto': len(no)}
    log(nome, 'anni con almeno meta giorni di pioggia', res['meta_pioggia'])
    out[nome] = res
log('Ascensione 2025', easter(2025) + dt.timedelta(days=39), '2024', easter(2024) + dt.timedelta(days=39))

# ====================== 5. Natale con il sole, Pasqua con il tizzone ======================
def loc_anom(d):  # scarto dalla media dei 31 giorni attorno, nello stesso anno
    try: return T[d] - np.mean([T[d + dt.timedelta(days=j)] for j in range(-15, 16)])
    except KeyError: return None
pairs = []
for y in range(Y0, 2025):
    nat = D(y, 12, 25); pas = easter(y + 1)
    a, b = loc_anom(nat), loc_anom(pas)
    if a is None or b is None: continue
    pairs.append((y, a, b, P.get(nat), P.get(pas)))
arr = np.array([(p[1], p[2]) for p in pairs]); rr, pp = stats.pearsonr(arr[:, 0], arr[:, 1])
log('NATALE-PASQUA coppie', len(pairs), 'correlazione scarti', r2(rr), 'p', r2(pp))
rec = [p for p in pairs if p[0] >= R0 - 1]
rr2, pp2 = stats.pearsonr([p[1] for p in rec], [p[2] for p in rec]); log('  ultimi 30', len(rec), r2(rr2), r2(pp2))
mite = [p for p in pairs if p[1] > 0]; freddo = [p for p in pairs if p[1] <= 0]
fre = lambda g: 100 * sum(1 for p in g if p[2] < 0) / len(g)
log('  Natale piu mite del mese:', len(mite), 'Pasqua piu fredda del mese in', r1(fre(mite)), '% ; Natale non mite', len(freddo), r1(fre(freddo)))
pr = [p for p in pairs if p[3] is not None and p[4] is not None and p[0] >= P0]
sec = [p for p in pr if p[3] < RAIN]; bag = [p for p in pr if p[3] >= RAIN]
pq = lambda g: 100 * sum(1 for p in g if p[4] >= RAIN) / len(g)
log('  Natale asciutto', len(sec), 'Pasqua piovosa', r1(pq(sec)), '; Natale con pioggia', len(bag), r1(pq(bag)))
tab = np.array([[sum(1 for p in sec if p[4] >= RAIN), sum(1 for p in sec if p[4] < RAIN)], [sum(1 for p in bag if p[4] >= RAIN), sum(1 for p in bag if p[4] < RAIN)]])
log('  chi2 p', r2(stats.chi2_contingency(tab)[1]))
out['natale_pasqua'] = {'coppie': len(pairs), 'r': r2(rr), 'p': r2(pp), 'r_ultimi30': r2(rr2), 'n_ultimi30': len(rec), 'p_ultimi30': r2(pp2),
    'natale_mite': {'n': len(mite), 'pasqua_fredda': r1(fre(mite))}, 'natale_non_mite': {'n': len(freddo), 'pasqua_fredda': r1(fre(freddo))},
    'natale_asciutto': {'n': len(sec), 'pasqua_piovosa': r1(pq(sec))}, 'natale_pioggia': {'n': len(bag), 'pasqua_piovosa': r1(pq(bag))},
    'punti': [[p[0], r2(p[1]), r2(p[2])] for p in pairs]}

# ====================== 6. Marzo pazzerello ======================
def sbalzi(y0, y1):
    a = collections.defaultdict(list)
    for d, v in T.items():
        if y0 <= d.year <= y1:
            p = d - dt.timedelta(days=1)
            if p in T: a[d.month].append(abs(v - T[p]))
    return [float(np.mean(a[m])) for m in range(1, 13)]
def piove(y0, y1):
    a = collections.defaultdict(list)
    for d, x in P.items():
        if y0 <= d.year <= y1: a[d.month].append(x >= RAIN)
    return [100 * float(np.mean(a[m])) for m in range(1, 13)]
sb_all, sb_rec = sbalzi(Y0, Y1), sbalzi(R0, Y1)
log('SBALZI per mese tutti', [r2(x) for x in sb_all], '\n rec', [r2(x) for x in sb_rec])
log('PIOVE per mese tutti', [r1(x) for x in piove(P0, 2025)], '\n rec', [r1(x) for x in piove(R0, 2025)])
out['marzo'] = {'sbalzi_tutti': [r2(x) for x in sb_all], 'sbalzi_rec': [r2(x) for x in sb_rec], 'piove_tutti': [r1(x) for x in piove(P0, 2025)], 'piove_rec': [r1(x) for x in piove(R0, 2025)]}

# ====================== 7. Prima di Natale né freddo né fame ======================
def media_periodo(y, a, b):
    v = [T[a(y) + dt.timedelta(days=j)] for j in range((b(y) - a(y)).days + 1) if (a(y) + dt.timedelta(days=j)) in T]
    return float(np.mean(v)) if len(v) > 0.9 * ((b(y) - a(y)).days + 1) else None
def prima_dopo(y0, y1):
    pr_, do_ = [], []
    for y in range(y0, y1 + 1):
        a = media_periodo(y, lambda y: D(y, 12, 1), lambda y: D(y, 12, 24)); b = media_periodo(y, lambda y: D(y, 12, 26), lambda y: D(y + 1, 1, 31))
        if a is None or b is None: continue
        pr_.append(a); do_.append(b)
    return pr_, do_
out['natale_prima'] = {}
for nm, (a, b) in (('tutti', (Y0, 2024)), ('ultimi30', (R0 - 1, 2024))):
    pr_, do_ = prima_dopo(a, b)
    freddo_dopo = sum(1 for x, z in zip(pr_, do_) if z < x)
    log('PRIMA DI NATALE', nm, len(pr_), 'prima', r1(np.mean(pr_)), 'dopo', r1(np.mean(do_)), 'dopo piu freddo in', freddo_dopo, r1(100 * freddo_dopo / len(pr_)))
    out['natale_prima'][nm] = {'n': len(pr_), 'prima': r1(np.mean(pr_)), 'dopo': r1(np.mean(do_)), 'dopo_piu_freddo': freddo_dopo}
# robustezza Natale-Pasqua: spearman e media su 3 giorni
sp_ = stats.spearmanr(arr[:, 0], arr[:, 1]); log('NATALE-PASQUA spearman', r2(sp_[0]), r2(sp_[1]))
out['natale_pasqua']['spearman'] = {'r': r2(sp_[0]), 'p': r2(sp_[1])}
def loc3(d):
    try: return np.mean([T[d + dt.timedelta(days=j)] for j in (-1, 0, 1)]) - np.mean([T[d + dt.timedelta(days=j)] for j in range(-15, 16)])
    except KeyError: return None
p3 = [(loc3(D(y, 12, 25)), loc3(easter(y + 1))) for y in range(Y0, 2025)]; p3 = [p for p in p3 if p[0] is not None and p[1] is not None]
r3 = stats.pearsonr([p[0] for p in p3], [p[1] for p in p3]); log('NATALE-PASQUA 3 giorni', len(p3), r2(r3[0]), r2(r3[1]))
out['natale_pasqua']['tre_giorni'] = {'r': r2(r3[0]), 'p': r2(r3[1]), 'n': len(p3)}
# per secolo
for a, b in ((1763, 1850), (1851, 1950), (1951, 2024)):
    q = [p for p in pairs if a <= p[0] <= b]; rr_ = stats.pearsonr([p[1] for p in q], [p[2] for p in q]); log('  periodo', a, b, len(q), r2(rr_[0]), r2(rr_[1]))

json.dump(out, open(os.path.join(OUT, 'proverbi.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), default=lambda o: o.item())
log('scritto', os.path.getsize(os.path.join(OUT, 'proverbi.json')), 'byte')
