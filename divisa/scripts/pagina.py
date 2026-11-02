"""Pagina - dati per docs/divisa/ (riscrive tutto ogni volta).
Entrate: divisa/out/*.csv|json (passi 01-04), docs/eta/data/nil.geojson (confini dei NIL, ds964 del Comune, gia' pubblicati), popolazione/pulito/nil_anagrafica.csv.
Uscite in <docs>/divisa/data/: riepilogo.json, mappa.json, nil.geojson, e i CSV scaricabili (reddito_serie, reddito_41_citta, reddito_varianti_milano,
cittadinanza_serie, cittadinanza_comunita, eta_serie, laureati_serie, reddito_cap_milano, reddito_nil_milano).
NON si pubblicano: i file dei conteggi per NIL x gruppo grezzi (stanno gia' dentro mappa.json) ne' i log.
Uso: python -I -X utf8 pagina.py <milano-in-dati> <divisa> <docs>/divisa"""
import sys, os, json, shutil, datetime
import numpy as np
import pandas as pd

BASE, DIV, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.path.join(DIV, 'out')
DATA = os.path.join(DOCS, 'data')
os.makedirs(DATA, exist_ok=True)
rd = lambda f: pd.read_csv(os.path.join(OUT, f))


def r4(x, n=4):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return round(float(x), n)


def col(df, c, n=4):
    return [r4(v, n) for v in df[c].tolist()]


RS = rd('reddito_serie.csv'); RV = rd('reddito_varianti_milano.csv'); R41 = rd('reddito_41_citta.csv')
CS = rd('cittadinanza_serie.csv'); CC = rd('cittadinanza_comunita.csv'); ES = rd('eta_serie.csv'); LS = rd('laureati_serie.csv')
CN = rd('cittadinanza_nil.csv'); EN = rd('eta_nil.csv'); RN = rd('reddito_nil_milano.csv'); RCAP = rd('reddito_cap_milano.csv')
rlog = json.load(open(os.path.join(OUT, 'reddito_log.json'), encoding='utf-8'))
ana = pd.read_csv(os.path.join(BASE, 'popolazione', 'pulito', 'nil_anagrafica.csv'))
gj = json.load(open(os.path.join(BASE, 'docs', 'eta', 'data', 'nil.geojson'), encoding='utf-8'))
shutil.copyfile(os.path.join(BASE, 'docs', 'eta', 'data', 'nil.geojson'), os.path.join(DATA, 'nil.geojson'))
ids = [f['properties']['i'] for f in gj['features']]
nomi = {f['properties']['i']: f['properties']['n'] for f in gj['features']}

NOMEC = dict(MILANO='Milano', ROMA='Roma', TORINO='Torino', NAPOLI='Napoli', BOLOGNA='Bologna')
def tit(s):
    t = s.title().replace("Nell'E", "nell'E").replace(' Di ', ' di ').replace("Forli'", 'Forlì').replace("Pesaro", 'Pesaro')
    return t

# ------------------------------------------------------------------ riepilogo
R = {'generato': datetime.date.today().isoformat()}
# reddito
rr = {'anni': sorted(RS.anno.unique().tolist()), 'citta': {}}
for c, g in RS.groupby('citta'):
    g = g.sort_values('anno')
    rr['citta'][NOMEC[c]] = dict(anni=g.anno.tolist(), n_cap=g.n_cap.tolist(), per_cap=[round(x) for x in g.per_cap], contribuenti=g.contribuenti.tolist(),
                                 hr=col(g, 'hr', 5), hr_lo=col(g, 'hr_lo', 5), hr_hi=col(g, 'hr_hi', 5), hr_base=col(g, 'hr_base', 5),
                                 d=col(g, 'd'), d_lo=col(g, 'd_lo'), d_hi=col(g, 'd_hi'), d_base=col(g, 'd_base'),
                                 iso=col(g, 'iso'), quota_alto=col(g, 'quota_alto'), quota_basso=col(g, 'quota_basso'), d_soglie=col(g, 'd_soglie'))
rr['varianti'] = {n: dict(anni=g.sort_values('anno').anno.tolist(), hr=col(g.sort_values('anno'), 'hr', 5), n_cap=int(g.n_cap.iloc[0]))
                  for n, g in RV.groupby('variante')}
a, b = R41[R41.anno == 2011].set_index('citta'), R41[R41.anno == 2024].set_index('citta')
c41 = []
for c in b.index:
    if c not in a.index:
        continue
    c41.append(dict(citta=tit(c), n_cap=int(b.loc[c, 'n_cap']), per_cap=int(round(b.loc[c, 'per_cap'])), hr11=r4(a.loc[c, 'hr'], 5), hr24=r4(b.loc[c, 'hr'], 5),
                    hr24_lo=r4(b.loc[c, 'hr_lo'], 5), hr24_hi=r4(b.loc[c, 'hr_hi'], 5), d11=r4(a.loc[c, 'd']), d24=r4(b.loc[c, 'd']), principale=c in NOMEC))
rr['citta41'] = sorted(c41, key=lambda x: -x['hr24'])
rr['laureati'] = {n: dict(anni=g.anno.tolist(), d=col(g, 'd'), d_lo=col(g, 'd_lo'), d_hi=col(g, 'd_hi'), d_base=col(g, 'd_base'), quota=col(g, 'quota_laureati'),
                          iso=col(g, 'iso_laureati'), n_nil=g.n_nil.tolist()) for n, g in LS.groupby('insieme')}
rr['log'] = {k: v for k, v in rlog.items() if k in ('imputati_per_differenza', 'imputati_per_quota_mediana', 'cap_sotto_500_scartati')}
R['reddito'] = rr
# cittadinanza
cz = {'anni': CS.anno.tolist()}
for c in ['residenti', 'stranieri']:
    cz[c] = CS[c].tolist()
for c, n in [('quota_stranieri', 4), ('d', 4), ('d_lo', 4), ('d_hi', 4), ('d_base', 4), ('iso_stranieri', 4), ('h_tutte', 5), ('h_tutte_lo', 5), ('h_tutte_hi', 5), ('h_tutte_base', 5),
             ('h_stranieri', 5), ('h_stranieri_lo', 5), ('h_stranieri_hi', 5), ('h_stranieri_base', 5)]:
    cz[c] = col(CS, c, n)
cz['n_nil'] = CS.n_nil.tolist()
cz['comunita'] = {}
for n, g in CC.groupby('comunita'):
    g = g.sort_values('anno')
    cz['comunita'][n] = dict(res=g.residenti.tolist(), quota=col(g, 'quota_citta', 5), d=col(g, 'd'), d_lo=col(g, 'd_lo'), d_hi=col(g, 'd_hi'), d_base=col(g, 'd_base'))
R['cittadinanza'] = cz
# eta
ez = {'anni': ES.anno.tolist()}
for c, n in [('quota_65p', 4), ('quota_u35', 4), ('eta_media', 2), ('d', 4), ('d_lo', 4), ('d_hi', 4), ('d_base', 4), ('d_75_2534', 4), ('iso_65p', 4),
             ('hr', 5), ('hr_lo', 5), ('hr_hi', 5), ('hr_base', 5)]:
    ez[c] = col(ES, c, n)
R['eta'] = ez

# ------------------------------------------------------------------ numeri chiave (tutti calcolati qui)
mi = RS[RS.citta == 'MILANO'].set_index('anno')
N = {}
N['reddito_hr_2011'] = r4(mi.loc[2011, 'hr'], 5); N['reddito_hr_2015'] = r4(mi.loc[2015, 'hr'], 5); N['reddito_hr_2024'] = r4(mi.loc[2024, 'hr'], 5)
N['reddito_hr_cambio_2015_2024_pct'] = r4((mi.loc[2024, 'hr'] / mi.loc[2015, 'hr'] - 1) * 100, 1)
N['reddito_hr_cambio_2011_2024_pct'] = r4((mi.loc[2024, 'hr'] / mi.loc[2011, 'hr'] - 1) * 100, 1)
V = RV.pivot(index='anno', columns='variante', values='hr')
N['reddito_hr_2011_senza'] = r4(V.loc[2011, 'senza 20121 e 20122'], 5); N['reddito_hr_2024_senza'] = r4(V.loc[2024, 'senza 20121 e 20122'], 5)
N['reddito_hr_2011_uniti'] = r4(V.loc[2011, '20121 e 20122 uniti'], 5); N['reddito_hr_2024_uniti'] = r4(V.loc[2024, '20121 e 20122 uniti'], 5)
N['reddito_d_2011'] = r4(mi.loc[2011, 'd']); N['reddito_d_2024'] = r4(mi.loc[2024, 'd'])
N['reddito_iso_2011'] = r4(mi.loc[2011, 'iso']); N['reddito_iso_2024'] = r4(mi.loc[2024, 'iso'])
N['reddito_quota_alto_2011'] = r4(mi.loc[2011, 'quota_alto']); N['reddito_quota_alto_2024'] = r4(mi.loc[2024, 'quota_alto'])
N['reddito_per_cap_2024'] = int(round(mi.loc[2024, 'per_cap']))
big = [x for x in rr['citta41'] if x['n_cap'] >= 10]
N['reddito_n_citta_10cap'] = len(big)
N['reddito_posto_milano_2024'] = [i + 1 for i, x in enumerate(big) if x['citta'] == 'Milano'][0]
N['reddito_prima'] = big[0]['citta']; N['reddito_prima_hr'] = big[0]['hr24']
N['reddito_ultima'] = big[-1]['citta']; N['reddito_ultima_hr'] = big[-1]['hr24']
lau = LS[LS.insieme == '88 NIL'].set_index('anno')
N['laureati_d_1991'] = r4(lau.loc[1991, 'd']); N['laureati_d_2023'] = r4(lau.loc[2023, 'd'])
N['laureati_q_1991'] = r4(lau.loc[1991, 'quota_laureati']); N['laureati_q_2023'] = r4(lau.loc[2023, 'quota_laureati'])
cs = CS.set_index('anno')
N['citt_d_1999'] = r4(cs.loc[1999, 'd']); N['citt_d_2025'] = r4(cs.loc[2025, 'd'])
pk = cs.d.idxmax(); N['citt_d_picco'] = r4(cs.loc[pk, 'd']); N['citt_anno_picco'] = int(pk)
N['citt_d_2003'] = r4(cs.loc[2003, 'd']); N['citt_d_2002'] = r4(cs.loc[2002, 'd']); N['citt_d_2011'] = r4(cs.loc[2011, 'd']); N['citt_d_2012'] = r4(cs.loc[2012, 'd'])
N['citt_quota_1999'] = r4(cs.loc[1999, 'quota_stranieri']); N['citt_quota_2025'] = r4(cs.loc[2025, 'quota_stranieri'])
N['citt_iso_1999'] = r4(cs.loc[1999, 'iso_stranieri']); N['citt_iso_2025'] = r4(cs.loc[2025, 'iso_stranieri'])
N['citt_d_base_max'] = r4(cs.d_base.max())
ee = ES.set_index('anno')
N['eta_d_1999'] = r4(ee.loc[1999, 'd']); N['eta_d_2025'] = r4(ee.loc[2025, 'd']); pk = ee.d.idxmax()
N['eta_d_picco'] = r4(ee.loc[pk, 'd']); N['eta_anno_picco'] = int(pk)
N['eta_hr_1999'] = r4(ee.loc[1999, 'hr'], 5); N['eta_hr_2025'] = r4(ee.loc[2025, 'hr'], 5); N['eta_hr_picco'] = r4(ee.hr.max(), 5)
N['eta_q65_1999'] = r4(ee.loc[1999, 'quota_65p']); N['eta_q65_2025'] = r4(ee.loc[2025, 'quota_65p'])
N['eta_iso_65_2025'] = r4(ee.loc[2025, 'iso_65p'])
# comunita': D 2025 e anno con D massimo (solo anni con almeno 300 residenti)
K = CC[(CC.residenti >= 300)]
cm = {}
for n, g in K.groupby('comunita'):
    g = g.sort_values('anno')
    cm[n] = dict(d_2025=r4(g[g.anno == 2025].d.iloc[0]), res_2025=int(g[g.anno == 2025].residenti.iloc[0]), d_max=r4(g.d.max()), anno_max=int(g.loc[g.d.idxmax(), 'anno']),
                 d_primo=r4(g.d.iloc[0]), anno_primo=int(g.anno.iloc[0]), d_base_2025=r4(g[g.anno == 2025].d_base.iloc[0]))
N['comunita'] = cm
R['numeri'] = N
json.dump(R, open(os.path.join(DATA, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ------------------------------------------------------------------ mappe (array per anno, ordine dei NIL = ids)
def wide(df, anni, field):
    p = df.pivot(index='anno', columns='id_nil', values=field).reindex(index=anni, columns=ids)
    return [[(None if pd.isna(v) else round(float(v), 4) if field in ('alto', 'basso', 'media') else int(v)) for v in row] for row in p.values]


M = {'nil': ids, 'nomi': [nomi[i] for i in ids]}
ar = sorted(RN.anno.unique().tolist())
M['reddito'] = dict(anni=ar, alto=wide(RN, ar, 'alto'), basso=wide(RN, ar, 'basso'), media=wide(RN, ar, 'media'))
ac = sorted(CN.anno.unique().tolist())
mc = dict(anni=ac, res=wide(CN, ac, 'residenti'), stra=wide(CN, ac, 'stranieri'), comm={})
for c in [x for x in CN.columns if x.startswith('c_')]:
    mc['comm'][c[2:]] = wide(CN, ac, c)
M['cittadinanza'] = mc
ae = sorted(EN.anno.unique().tolist())
M['eta'] = dict(anni=ae, res=wide(EN, ae, 'residenti'), a65=wide(EN, ae, 'a65'), u35=wide(EN, ae, 'u35'), a2534=wide(EN, ae, 'a2534'), a75=wide(EN, ae, 'a75'),
                eta_somma=[[(None if pd.isna(v) else round(float(v))) for v in row] for row in EN.pivot(index='anno', columns='id_nil', values='eta_somma').reindex(index=ae, columns=ids).values])
json.dump(M, open(os.path.join(DATA, 'mappa.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ------------------------------------------------------------------ CSV scaricabili
for f in ['reddito_serie.csv', 'reddito_41_citta.csv', 'reddito_varianti_milano.csv', 'cittadinanza_serie.csv', 'cittadinanza_comunita.csv', 'eta_serie.csv',
          'laureati_serie.csv', 'reddito_cap_milano.csv', 'reddito_nil_milano.csv']:
    shutil.copyfile(os.path.join(OUT, f), os.path.join(DATA, f))
for f in sorted(os.listdir(DATA)):
    print(f, os.path.getsize(os.path.join(DATA, f)))
print(json.dumps({k: v for k, v in N.items() if k != 'comunita'}, ensure_ascii=False, indent=0))
