"""Fase 1 - Morti giorno per giorno: attesi, eccessi, Covid, caldo, freddo, eta/sesso. Solo confronti, nessuna causa.
Uso: python -I -X utf8 analisi.py <cartella morti assoluta> <cartella milano-in-dati assoluta>
Legge: pulito/decessi_giorno_eta_sesso.csv; temperature/discrepanza/out/serie_continua_1763_oggi.csv;
       censimenti/raw/istat_demo/POSAS_<anno>_it_015_Milano.zip (popolazione per eta' e sesso al 1 gennaio 2019-2026).
Scrive: pulito/*.csv, pulito/riepilogo.json"""
import sys, os, json, zipfile
import numpy as np, pandas as pd

MORTI, ROOT = sys.argv[1], sys.argv[2]
PUL = os.path.join(MORTI, 'pulito')
L = pd.read_csv(os.path.join(PUL, 'decessi_giorno_eta_sesso.csv'), parse_dates=['data'])
LAST = L.data.max()
IDX = pd.date_range('2011-01-01', LAST)
COVID_YEARS = (2020, 2021)
BANDS = {'0-64': range(0, 14), '65-74': (14, 15), '75-84': (16, 17), '85+': (18, 19, 20, 21)}
R = {}  # riepilogo json


# ---------- serie giornaliere ----------
def series(scope, col='T', cls=None):
    x = L[L.scope == scope]
    if cls is not None:
        x = x[x.cl_eta.isin(list(cls))]
    return x.groupby('data')[col].sum().reindex(IDX, fill_value=0).astype(float)


# ---------- attesi ----------
def years_A(Y):   # ultimi 5 anni precedenti (da 2011 in poi)
    return [y for y in range(Y - 5, Y) if y >= 2011]


def years_B(Y):   # ultimi 5 anni precedenti senza 2020 e 2021
    out, y = [], Y - 1
    while len(out) < 5 and y >= 2011:
        if y not in COVID_YEARS:
            out.append(y)
        y -= 1
    return out


def baseline(s, yfn, minyears=3):
    piv = pd.DataFrame({'y': s.index.year, 'k': s.index.strftime('%m%d'), 'v': s.values}).pivot(index='y', columns='k', values='v')
    out_idx = pd.date_range('2014-01-01', '2026-12-31')
    res = {}
    for Y in range(2014, 2027):
        ys = yfn(Y)
        assert len(ys) >= minyears
        m = piv.loc[ys].mean(axis=0, skipna=True)
        if np.isnan(m['0229']):
            m['0229'] = (m['0228'] + m['0301']) / 2
        res[Y] = m
    raw = pd.Series([res[d.year][d.strftime('%m%d')] for d in out_idx], index=out_idx)
    return raw.rolling(15, center=True, min_periods=8).mean()   # liscio a 15 giorni


def compare(s):
    A, B = baseline(s, years_A), baseline(s, years_B)
    df = pd.DataFrame({'morti': s}).loc['2014-01-01':]
    df['attesi_A'] = A.reindex(df.index)
    df['attesi_B'] = B.reindex(df.index)
    return df, A, B


SER, CMP, FULLB = {}, {}, {}


def add(k, s):
    SER[k] = s
    CMP[k], _, FULLB[k] = compare(s)


add('Milano', series('Milano')); add('Lombardia', series('Lombardia')); add('Italia', series('Italia'))
add('Italia_senza_Lombardia', SER['Italia'] - SER['Lombardia'])
add('Lombardia_senza_Milano', SER['Lombardia'] - SER['Milano'])
for sex in 'MF':
    add(f'Milano_{sex}', series('Milano', sex))
for b, cls in BANDS.items():
    for sex in 'TMF':
        add(f'Milano_{b}_{sex}', series('Milano', sex, cls))
for k in ('Lombardia', 'Italia'):
    for b, cls in BANDS.items():
        add(f'{k}_{b}_T', series(k, 'T', cls))

# ---------- popolazione di Milano per eta' e sesso (POSAS) ----------
def cls_of(age):
    return 0 if age == 0 else (1 if age < 5 else min(age // 5 + 1, 21))


pop = {}
for y in range(2019, 2027):
    z = zipfile.ZipFile(os.path.join(ROOT, 'censimenti', 'raw', 'istat_demo', f'POSAS_{y}_it_015_Milano.zip'))
    t = pd.read_csv(z.open(z.namelist()[0]), sep=';', skiprows=1, encoding='utf-8-sig', dtype={'Codice comune': str})
    t = t[(t['Codice comune'] == '015146') & (t['Età'] < 200)]
    t = t.assign(cl=t['Età'].astype(int).map(cls_of))
    g = t.groupby('cl')[['Totale maschi', 'Totale femmine']].sum()
    pop[y] = g.rename(columns={'Totale maschi': 'M', 'Totale femmine': 'F'})
    R[f'pop_milano_1gen{y}'] = int(g.values.sum())


def pop_mean(y):   # media tra 1 gennaio y e y+1 (per il 2026: solo 1 gennaio 2026)
    return (pop[y] + pop[y + 1]) / 2 if y + 1 in pop else pop[y]


Lm = L[L.scope == 'Milano'].assign(anno=lambda d: d.data.dt.year)
dm = Lm[Lm.anno == 2019].groupby('cl_eta')[['M', 'F']].sum().reindex(range(22), fill_value=0)
rate = dm / pop_mean(2019).reindex(range(22))   # tassi per eta'/sesso del 2019
E_adj = {y: float((rate * pop_mean(y)).values.sum()) for y in range(2019, 2027)}
R['fattore_invecchiamento_milano_vs2019'] = {y: round(E_adj[y] / dm.values.sum(), 4) for y in E_adj}
R['attesi_eta_2019_milano'] = {y: round(v, 1) for y, v in E_adj.items()}


def add_age_expected(k, eadj):
    c, fb = CMP[k], FULLB[k]
    sB = fb.groupby(fb.index.year).sum()
    c['attesi_eta'] = [eadj.get(d.year, np.nan) * fb[d] / sB[d.year] for d in c.index]


add_age_expected('Milano', E_adj)
for sex in 'MF':
    add_age_expected(f'Milano_{sex}', {y: float((rate[sex] * pop_mean(y)[sex]).sum()) for y in range(2019, 2027)})

# ---------- temperature ----------
T = pd.read_csv(os.path.join(ROOT, 'temperature', 'discrepanza', 'out', 'serie_continua_1763_oggi.csv'), parse_dates=['data'])
T = T.set_index('data')[['TX', 'TN', 'TG', 'fonte_usata']]
CMP['Milano'] = CMP['Milano'].join(T[['TX', 'TN', 'TG']])


# ---------- scritture giorno/settimana ----------
def add_excess(df):
    df = df.copy()
    for a in ('A', 'B'):
        df[f'eccesso_{a}'] = df['morti'] - df[f'attesi_{a}']
        df[f'rapporto_{a}'] = df['morti'] / df[f'attesi_{a}']
    if 'attesi_eta' in df:
        df['eccesso_eta'] = df['morti'] - df['attesi_eta']
    return df


def weekly(df):
    iso = df.index.isocalendar()
    d2 = df.assign(anno_iso=iso.year.values, sett=iso.week.values, data=df.index)
    g = d2.groupby(['anno_iso', 'sett'])
    cols = [c for c in ('morti', 'attesi_A', 'attesi_B', 'attesi_eta') if c in df]
    w = g[cols].sum(min_count=1)
    w['lunedi'] = g['data'].min() - pd.to_timedelta(g['data'].min().dt.day_of_week, unit='D')
    w['giorni'] = g.size()
    w['completa'] = w['giorni'] == 7
    return add_excess(w.reset_index())


for k in ('Milano', 'Lombardia', 'Italia'):
    d = add_excess(CMP[k]).round(3)
    d.index.name = 'data'
    d.to_csv(os.path.join(PUL, f'{k.lower()}_giorno.csv'))
    weekly(CMP[k]).round({'morti': 1, 'attesi_A': 2, 'attesi_B': 2, 'eccesso_A': 2, 'eccesso_B': 2, 'rapporto_A': 3, 'rapporto_B': 3, 'attesi_eta': 2, 'eccesso_eta': 2}).to_csv(os.path.join(PUL, f'{k.lower()}_settimana.csv'), index=False)

# ---------- annuale e mensile ----------
rows = []
for k in ('Milano', 'Lombardia', 'Italia', 'Italia_senza_Lombardia', 'Lombardia_senza_Milano'):
    c = CMP[k]
    for y in range(2014, 2027):
        x = c.loc[f'{y}-01-01':f'{y}-12-31']
        r = dict(scope=k, anno=y, giorni=len(x), morti=x.morti.sum(), attesi_A=x.attesi_A.sum(), attesi_B=x.attesi_B.sum())
        if k == 'Milano' and y >= 2019:
            r['attesi_eta'] = x.attesi_eta.sum()
        rows.append(r)
A = pd.DataFrame(rows)
A['eccesso_A'] = A.morti - A.attesi_A; A['pct_A'] = 100 * A.eccesso_A / A.attesi_A
A['eccesso_B'] = A.morti - A.attesi_B; A['pct_B'] = 100 * A.eccesso_B / A.attesi_B
A['eccesso_eta'] = A.morti - A.attesi_eta; A['pct_eta'] = 100 * A.eccesso_eta / A.attesi_eta
A.round(2).to_csv(os.path.join(PUL, 'annuale_confronto.csv'), index=False)
rows = []
for k in ('Milano', 'Lombardia', 'Italia'):
    c = CMP[k]
    g = c.groupby([c.index.year.rename('anno'), c.index.month.rename('mese')])
    m = g[['morti', 'attesi_A', 'attesi_B']].sum()
    m['giorni'] = g.size()
    m['eccesso_B'] = m.morti - m.attesi_B; m['pct_B'] = 100 * m.eccesso_B / m.attesi_B
    m['eccesso_A'] = m.morti - m.attesi_A; m['pct_A'] = 100 * m.eccesso_A / m.attesi_A
    m.insert(0, 'scope', k)
    rows.append(m.reset_index())
M = pd.concat(rows)
M.round(2).to_csv(os.path.join(PUL, 'mensile_confronto.csv'), index=False)


# ---------- finestre (Covid e altre) ----------
def window(k, a, b):
    x = CMP[k].loc[a:b]
    d = dict(scope=k, da=a, a=b, giorni=len(x), morti=x.morti.sum(), attesi_B=x.attesi_B.sum(), attesi_A=x.attesi_A.sum())
    d['eccesso_B'] = d['morti'] - d['attesi_B']; d['pct_B'] = 100 * d['eccesso_B'] / d['attesi_B']
    d['eccesso_A'] = d['morti'] - d['attesi_A']; d['pct_A'] = 100 * d['eccesso_A'] / d['attesi_A']
    if 'attesi_eta' in x and x.attesi_eta.notna().all():
        d['attesi_eta'] = x.attesi_eta.sum(); d['eccesso_eta'] = d['morti'] - d['attesi_eta']; d['pct_eta'] = 100 * d['eccesso_eta'] / d['attesi_eta']
    return d


WINS = [('primavera 2020', '2020-03-01', '2020-05-31'), ('autunno 2020', '2020-10-01', '2020-12-31'),
        ('primavera 2021', '2021-03-01', '2021-04-30'), ('inverno 2021-22', '2021-12-01', '2022-03-31'),
        ('anno 2020', '2020-01-01', '2020-12-31'), ('anno 2021', '2021-01-01', '2021-12-31')]
rows = []
for k in ('Milano', 'Lombardia', 'Italia', 'Italia_senza_Lombardia', 'Lombardia_senza_Milano'):
    for n, a, b in WINS:
        rows.append(dict(finestra=n, **window(k, a, b)))
W = pd.DataFrame(rows)
W.round(2).to_csv(os.path.join(PUL, 'finestre_covid.csv'), index=False)

# picco del 2020
pk = []
for k in ('Milano', 'Lombardia', 'Italia'):
    c = add_excess(CMP[k]).loc['2020-02-01':'2020-06-30']
    c7 = c[['morti', 'attesi_B']].rolling(7, center=True).sum()
    d1 = c.morti.idxmax(); d7 = c7.morti.idxmax()
    pk.append(dict(scope=k, giorno_max=d1.date(), morti_max=int(c.loc[d1, 'morti']), attesi_B_quel_giorno=round(c.loc[d1, 'attesi_B'], 1),
                   volte_normale_giorno=round(c.loc[d1, 'rapporto_B'], 2), giorno_max_rapporto=c.rapporto_B.idxmax().date(), max_rapporto=round(c.rapporto_B.max(), 2),
                   centro_sett_max=d7.date(), morti_7g=int(c7.loc[d7, 'morti']), volte_normale_7g=round(c7.loc[d7, 'morti'] / c7.loc[d7, 'attesi_B'], 2)))
PK = pd.DataFrame(pk); PK.to_csv(os.path.join(PUL, 'picco_2020.csv'), index=False)

# ---------- eta' e sesso, Milano ----------
rows = []
EXTRA = WINS + [('estate 2022 (giu-ago)', '2022-06-01', '2022-08-31')]
for b in BANDS:
    for sex in 'TMF':
        c = CMP[f'Milano_{b}_{sex}']
        for n, a, e in EXTRA:
            x = c.loc[a:e]
            rows.append(dict(fascia=b, sesso=sex, finestra=n, morti=x.morti.sum(), attesi_B=round(x.attesi_B.sum(), 1),
                             eccesso_B=round(x.morti.sum() - x.attesi_B.sum(), 1), pct_B=round(100 * (x.morti.sum() / x.attesi_B.sum() - 1), 1)))
for sex in 'MF':
    c = CMP[f'Milano_{sex}']
    for n, a, e in EXTRA:
        x = c.loc[a:e]
        rows.append(dict(fascia='tutte', sesso=sex, finestra=n, morti=x.morti.sum(), attesi_B=round(x.attesi_B.sum(), 1),
                         eccesso_B=round(x.morti.sum() - x.attesi_B.sum(), 1), pct_B=round(100 * (x.morti.sum() / x.attesi_B.sum() - 1), 1)))
ES = pd.DataFrame(rows); ES.to_csv(os.path.join(PUL, 'milano_eta_sesso_finestre.csv'), index=False)
rows = []
for y in range(2019, 2026):
    pm_ = pop_mean(y)
    for b, cls in BANDS.items():
        for sex in 'MF':
            d_ = Lm[(Lm.anno == y) & Lm.cl_eta.isin(list(cls))][sex].sum()
            p_ = pm_.loc[list(cls), sex].sum()
            rows.append(dict(anno=y, fascia=b, sesso=sex, morti=int(d_), popolazione_media=int(p_), per100mila=round(1e5 * d_ / p_, 1)))
TASSI = pd.DataFrame(rows); TASSI.to_csv(os.path.join(PUL, 'milano_tassi_eta_sesso.csv'), index=False)
rows = []
mid = np.array([0, 2.5] + [5 * i + 2.5 for i in range(2, 21)] + [102.0])
for y in range(2011, 2026):
    x = Lm[Lm.anno == y].groupby('cl_eta')['T'].sum().reindex(range(22), fill_value=0)
    xm = Lm[Lm.anno == y].groupby('cl_eta')['M'].sum().reindex(range(22), fill_value=0)
    xf = Lm[Lm.anno == y].groupby('cl_eta')['F'].sum().reindex(range(22), fill_value=0)
    rows.append(dict(anno=y, morti=int(x.sum()), maschi=int(xm.sum()), femmine=int(xf.sum()), quota_85p=round(100 * x.loc[18:].sum() / x.sum(), 1),
                     quota_under65=round(100 * x.loc[:13].sum() / x.sum(), 1), eta_centro_classe_media=round(float((x * mid).sum() / x.sum()), 1),
                     eta_centro_classe_M=round(float((xm * mid).sum() / xm.sum()), 1), eta_centro_classe_F=round(float((xf * mid).sum() / xf.sum()), 1)))
COMP = pd.DataFrame(rows); COMP.to_csv(os.path.join(PUL, 'milano_composizione_per_anno.csv'), index=False)

# ---------- caldo ----------
cm = add_excess(CMP['Milano'])


def runs(mask, minlen):
    out, start, prev = [], None, None
    for d, v in mask.items():
        if v and start is None:
            start = d
        if not v and start is not None:
            if (prev - start).days + 1 >= minlen:
                out.append((start, prev))
            start = None
        prev = d
    if start is not None and (prev - start).days + 1 >= minlen:
        out.append((start, prev))
    return out


def episode_stats(c, a, b, tail):
    x = c.loc[a:b + pd.Timedelta(days=tail)]
    r = dict(inizio=a.date(), fine=b.date(), giorni=(b - a).days + 1, finestra_giorni=len(x),
             tx_max=round(c.loc[a:b, 'TX'].max(), 1), tx_media=round(c.loc[a:b, 'TX'].mean(), 1), tg_media=round(c.loc[a:b, 'TG'].mean(), 1),
             morti=int(x.morti.sum()), attesi_B=round(x.attesi_B.sum(), 1), attesi_A=round(x.attesi_A.sum(), 1))
    r['eccesso_B'] = round(r['morti'] - r['attesi_B'], 1); r['pct_B'] = round(100 * r['eccesso_B'] / r['attesi_B'], 1)
    r['eccesso_A'] = round(r['morti'] - r['attesi_A'], 1)
    r['z_poisson'] = round(r['eccesso_B'] / np.sqrt(r['attesi_B']), 1)
    for bn in BANDS:
        cb = CMP[f'Milano_{bn}_T'].loc[x.index[0]:x.index[-1]]
        r[f'eccesso_{bn}'] = round(cb.morti.sum() - cb.attesi_B.sum(), 1)
    return r


HOT_TH, HOT_MIN, HOT_TAIL = 33.0, 3, 3
hot = [episode_stats(cm, a, b, HOT_TAIL) for a, b in runs(cm.TX >= HOT_TH, HOT_MIN)
       if a.year >= 2014 and a.month in (5, 6, 7, 8, 9) and b <= LAST - pd.Timedelta(days=HOT_TAIL)]
HOT = pd.DataFrame(hot); HOT.to_csv(os.path.join(PUL, 'ondate_caldo.csv'), index=False)
rows = []
for y in range(2014, 2026):
    x = cm.loc[f'{y}-06-01':f'{y}-08-31']
    ex75 = sum((CMP[f'Milano_{b}_T'].loc[x.index[0]:x.index[-1]].morti - CMP[f'Milano_{b}_T'].loc[x.index[0]:x.index[-1]].attesi_B).sum() for b in ('75-84', '85+'))
    rows.append(dict(anno=y, tx_media=round(x.TX.mean(), 2), tg_media=round(x.TG.mean(), 2), giorni_tx_ge33=int((x.TX >= 33).sum()), giorni_tx_ge35=int((x.TX >= 35).sum()),
                     morti=int(x.morti.sum()), attesi_B=round(x.attesi_B.sum(), 1), eccesso_B=round(x.morti.sum() - x.attesi_B.sum(), 1),
                     pct_B=round(100 * (x.morti.sum() / x.attesi_B.sum() - 1), 1),
                     eccesso_eta=(round(x.morti.sum() - x.attesi_eta.sum(), 1) if y >= 2019 else None),
                     eccesso_75p=round(ex75, 1)))
rows2 = []
for k in ('Milano', 'Lombardia_senza_Milano', 'Lombardia', 'Italia'):
    for y in range(2014, 2026):
        x = CMP[k].loc[f'{y}-06-01':f'{y}-08-31']
        rows2.append(dict(scope=k, anno=y, morti=int(x.morti.sum()), attesi_B=round(x.attesi_B.sum(), 1), pct_B=round(100 * (x.morti.sum() / x.attesi_B.sum() - 1), 1)))
pd.DataFrame(rows2).pivot(index='anno', columns='scope', values='pct_B').to_csv(os.path.join(PUL, 'estati_pct_per_area.csv'))
EST = pd.DataFrame(rows); EST.to_csv(os.path.join(PUL, 'estati_confronto.csv'), index=False)
x = cm.loc['2014-01-01':].copy()
x['tx3'] = x.TX.rolling(3).mean()
s = x[x.index.month.isin([6, 7, 8])].dropna(subset=['tx3']).copy()
s['bin'] = pd.cut(s.tx3, [-99, 27, 30, 32, 34, 36, 99])
BIN = s.groupby('bin', observed=True).agg(giorni=('morti', 'size'), morti=('morti', 'sum'), attesi_B=('attesi_B', 'sum'))
BIN['rapporto_B'] = (BIN.morti / BIN.attesi_B).round(3)
BIN = BIN.reset_index().assign(bin=lambda d: d['bin'].astype(str))
BIN.to_csv(os.path.join(PUL, 'estate_rapporto_per_tmax3.csv'), index=False)
R['estate_bin_tmax3'] = BIN.round(3).to_dict('records')

# ---------- freddo / inverni ----------
COLD_MIN, COLD_TAIL = 3, 7
cold = []
for th in (0.0, 3.0):
    for a, b in runs(cm.TG <= th, COLD_MIN):
        if a.year >= 2014 and (a.month in (11, 12, 1, 2, 3)) and b <= LAST - pd.Timedelta(days=COLD_TAIL):
            cold.append(dict(soglia_tg=th, **episode_stats(cm, a, b, COLD_TAIL)))
COLD = pd.DataFrame(cold); COLD.to_csv(os.path.join(PUL, 'ondate_freddo.csv'), index=False)
rows = []
for y in range(2014, 2026):
    a, b = pd.Timestamp(f'{y}-12-01'), min(pd.Timestamp(f'{y+1}-03-31'), LAST)
    x = cm.loc[a:b]
    ex75 = sum((CMP[f'Milano_{bn}_T'].loc[a:b].morti - CMP[f'Milano_{bn}_T'].loc[a:b].attesi_B).sum() for bn in ('75-84', '85+'))
    rows.append(dict(inverno=f'{y}/{str(y+1)[2:]}', tg_media=round(x.TG.mean(), 2), giorni_tg_le0=int((x.TG <= 0).sum()), morti=int(x.morti.sum()), attesi_B=round(x.attesi_B.sum(), 1),
                     eccesso_B=round(x.morti.sum() - x.attesi_B.sum(), 1), pct_B=round(100 * (x.morti.sum() / x.attesi_B.sum() - 1), 1), eccesso_75p=round(ex75, 1)))
INV = pd.DataFrame(rows); INV.to_csv(os.path.join(PUL, 'inverni_confronto.csv'), index=False)

# ---------- settimane e giorni estremi ----------
wk = weekly(CMP['Milano']); wk = wk[wk.completa]
cols = ['anno_iso', 'sett', 'lunedi', 'morti', 'attesi_B', 'eccesso_B', 'rapporto_B']
top = wk.sort_values('eccesso_B', ascending=False).head(25)[cols]
top.to_csv(os.path.join(PUL, 'milano_settimane_top_eccesso.csv'), index=False)
low = wk.sort_values('eccesso_B').head(10)[cols]
low.to_csv(os.path.join(PUL, 'milano_settimane_piu_basse.csv'), index=False)
GT = cm.sort_values('morti', ascending=False).head(15)[['morti', 'attesi_B', 'rapporto_B', 'TX']].round(2)
GT.to_csv(os.path.join(PUL, 'milano_giorni_top.csv'))

# ---------- stampa riassunto ----------
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40); pd.set_option('display.max_rows', 300)
print('ULTIMO GIORNO', LAST.date())
for name, df in (('ANNUALE', A.round(1)), ('FINESTRE', W.round(1)), ('PICCO 2020', PK), ('CALDO', HOT), ('ESTATI', EST), ('ESTATI PER AREA', pd.read_csv(os.path.join(PUL, 'estati_pct_per_area.csv'))), ('BIN', BIN), ('FREDDO', COLD),
                 ('INVERNI', INV), ('SETT TOP', top), ('SETT BASSE', low), ('GIORNI TOP', GT), ('ETA SESSO', ES), ('COMPOSIZIONE', COMP), ('TASSI', TASSI)):
    print('\n' + name); print(df.to_string())
print('\nFATTORE INVECCHIAMENTO', R['fattore_invecchiamento_milano_vs2019'])
json.dump(R, open(os.path.join(PUL, 'riepilogo.json'), 'w'), indent=1, default=str)
