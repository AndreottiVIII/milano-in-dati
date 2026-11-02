"""Correzioni: F con denominatore sulle stesse 10 lingue; I senza imporre tendenza; L con le sole notti in albergo della provincia."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 300)
L = open(os.path.join(OUT, 'FIL2.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
lc = p('luoghi-cercati', 'pulito')
den = pd.read_csv(os.path.join(lc, 'luoghi_vs_wikipedia_mensile.csv'), sep=';')
den['gr'] = np.where(den.lingua == 'it', 'it', 'estero10')
D_ = den.pivot_table(index='mese', columns='gr', values='wikipedia_totale', aggfunc='sum'); N_ = den.pivot_table(index='mese', columns='gr', values='luoghi_milano', aggfunc='sum')
Q = N_ / D_ * 1e6
for c in ['it', 'estero10']:
    base = np.mean([Q.loc[f'{y}-02', c] for y in (2023, 2024, 2025)]); bg = np.mean([N_.loc[f'{y}-02', c] for y in (2023, 2024, 2025)]); bd = np.mean([D_.loc[f'{y}-02', c] for y in (2023, 2024, 2025)])
    say(c, f'grezzo feb26/base {N_.loc["2026-02", c] / bg:.3f}; denominatore {D_.loc["2026-02", c] / bd:.3f}; per milione {Q.loc["2026-02", c] / base:.3f}')
    say(' per milione feb:', {y: round(Q.loc[f'{y}-02', c], 1) for y in range(2016, 2027)})
    say(' per milione 2026 sullo stesso mese 2023-25:', {f'{m:02d}': round(Q.loc[f'2026-{m:02d}', c] / np.mean([Q.loc[f'{y}-{m:02d}', c] for y in (2023, 2024, 2025)]), 2) for m in range(1, 11)})
    say(' denominatore 2026 sullo stesso mese 2023-25:', {f'{m:02d}': round(D_.loc[f'2026-{m:02d}', c] / np.mean([D_.loc[f'{y}-{m:02d}', c] for y in (2023, 2024, 2025)]), 2) for m in range(1, 11)})
    r = {y: np.log(Q.loc[f'{y}-02', c]) - np.log((Q.loc[f'{y}-01', c] + Q.loc[f'{y}-03', c]) / 2) for y in range(2017, 2027) if y != 2020}
    oth = [r[y] for y in r if y != 2026]; say(' feb rispetto a gen+mar: 2026', round(np.exp(r[2026]), 3), 'altri anni media', round(np.exp(np.mean(oth)), 3), 'min/max', round(np.exp(min(oth)), 3), round(np.exp(max(oth)), 3), 'z', round((r[2026] - np.mean(oth)) / np.std(oth, ddof=1), 1))
# senza voci olimpiche: stesso calcolo sulla stessa base, per milione
v = pd.read_csv(os.path.join(lc, 'views_mensili.csv'), sep=';'); lu = pd.read_csv(os.path.join(lc, 'luoghi.csv'), sep=';', low_memory=False)
v = v.merge(lu[['qid', 'tipo']], on='qid'); v = v[v.tipo == 'luogo']; lin = den.lingua.unique()
v = v[v.lingua.isin(lin)]; v['gr'] = np.where(v.lingua == 'it', 'it', 'estero10')
OL = {'Q133566': 'Meazza', 'Q64825395': 'Unipol Dome', 'Q112134535': 'Villaggio', 'Q776576': 'Arco Pace', 'Q3875281': 'Porta Sempione', 'Q3940173': 'Rogoredo', 'Q3857803': 'Santa Giulia', 'Q3967938': 'Agorà', 'Q3889169': 'PalaSharp', 'Q3889354': 'PalaLido'}
for c in ['it', 'estero10']:
    x = v[v.gr == c]
    tot = x.groupby('mese').views.sum(); no = x[~x.qid.isin(OL)].groupby('mese').views.sum()
    qq = no / D_[c] * 1e6
    say(c, 'senza 10 voci olimpiche, per milione feb26/base:', round(qq['2026-02'] / np.mean([qq[f'{y}-02'] for y in (2023, 2024, 2025)]), 3), ' grezzo:', round(no['2026-02'] / np.mean([no[f'{y}-02'] for y in (2023, 2024, 2025)]), 3))
    say('   gen26/stessa base', round(qq['2026-01'] / np.mean([qq[f'{y}-01'] for y in (2023, 2024, 2025)]), 3), 'mar26', round(qq['2026-03'] / np.mean([qq[f'{y}-03'] for y in (2023, 2024, 2025)]), 3))
    pv = x.pivot_table(index='qid', columns='mese', values='views', aggfunc='sum').fillna(0)
    pv['b'] = pv[['2023-02', '2024-02', '2025-02']].mean(axis=1); pv['d'] = pv['2026-02'] - pv.b
    t = pv.sort_values('d', ascending=False); say('   salto netto', int(t.d.sum()), 'quota prime 2/4/10', [round(t.d.head(k).sum() / t.d.sum() * 100, 1) for k in (2, 4, 10)], 'senza prime 5/20', [round(t.iloc[k:].d.sum() / t.iloc[k:].b.sum() * 100, 1) for k in (5, 20)], 'voci', len(t))
# I
say('\n=== I, forma delle serie')
r = pd.read_csv(p('docs', 'reati-citta', 'data', 'famiglia_stalking_mensile.csv'))
for tp in ['CP572', 'CP612BIS']:
    s = r[r.tipo_codice == tp].pivot_table(index=['anno', 'mese'], columns='territorio', values='denunce', aggfunc='sum')
    s.index = pd.PeriodIndex([f'{a}-{m:02d}' for a, m in s.index], freq='M').to_timestamp()
    mi, it = 'Milano (provincia)', 'Italia'
    rat = s[mi] / s[it] * 100
    say(tp, 'Milano media mensile per semestre', {f'{k.year}S{1 if k.month <= 6 else 2}': round(v_, 1) for k, v_ in s[mi].resample('6MS').mean().items()})
    say(tp, 'Italia media mensile per semestre', {f'{k.year}S{1 if k.month <= 6 else 2}': round(v_, 0) for k, v_ in s[it].resample('6MS').mean().items()})
    say(tp, 'Quota Milano per semestre', {f'{k.year}S{1 if k.month <= 6 else 2}': round(v_, 2) for k, v_ in (s[mi].resample('6MS').sum() / s[it].resample('6MS').sum() * 100).items()})
    # gradino senza tendenza sul rapporto Milano/Italia; scansione
    y = np.log(s[mi] / s[it]).values; idx = s.index; n = len(y); md = pd.get_dummies(idx.month, drop_first=True).values.astype(float); res = []
    for k in range(int(n * .15), int(n * .85)):
        X = np.column_stack([(np.arange(n) >= k).astype(float), np.ones(n), md]); b, se, u = hac_ols(y, X, lags=6); res.append((idx[k].strftime('%Y-%m'), round(b[0], 3), round(b[0] / se[0], 1)))
    res.sort(key=lambda t: -abs(t[2])); say(tp, 'rapporto Milano/Italia, gradino senza tendenza:', res[:4])
    # placebo su 107 province non disponibile. Rottura sui conteggi Poisson: test su due periodi
    a_, b_ = s[mi]['2022-09':'2023-08'].sum(), s[mi]['2023-09':'2024-08'].sum(); c_, d_ = s[it]['2022-09':'2023-08'].sum(), s[it]['2023-09':'2024-08'].sum()
    say(tp, f'12 mesi prima/dopo set 2023: Milano {a_}->{b_} ({(b_ / a_ - 1) * 100:+.1f}%), Italia {c_}->{d_} ({(d_ / c_ - 1) * 100:+.1f}%)')
    a_, b_ = s[mi]['2021-01':'2021-11'].sum(), s[mi]['2022-01':'2022-11'].sum(); c_, d_ = s[it]['2021-01':'2021-11'].sum(), s[it]['2022-01':'2022-11'].sum()
    say(tp, f'gen-nov 2021/2022: Milano {a_}->{b_} ({(b_ / a_ - 1) * 100:+.1f}%), Italia {c_}->{d_} ({(d_ / c_ - 1) * 100:+.1f}%)')
# L alberghi provincia
say('\n=== L, solo alberghi (provincia)')
pm = pd.read_csv(p('turisti', 'pulito', 'provincia_mensile.csv'), nrows=3); say(pm.to_string()[:600])
pm = pd.read_csv(p('turisti', 'pulito', 'provincia_mensile.csv'), low_memory=False)
say(list(pm.columns), {c: pm[c].nunique() for c in pm.columns if pm[c].dtype == object or str(pm[c].dtype).startswith('str')})
for c in pm.columns:
    if pm[c].nunique() < 12:
        say(c, pm[c].unique()[:12].tolist())
L.close()
