"""E: i varchi con zero moto toccano la stima?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
import pyarrow.parquet as pq
L = open(os.path.join(OUT, 'E2.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
a = pd.read_csv(p('docs', 'area-c', 'data', 'ingressi_giornalieri.csv'), sep=';'); a['data'] = pd.to_datetime(a.data)
cal = pd.read_csv(p('area-c', 'pulito', 'calendario.csv'), sep=';'); cal['data'] = pd.to_datetime(cal.data)
a = a.merge(cal[['data', 'agosto', 'natale_24dic_6gen', 'lavorativo', 'covid_fase']], on='data', how='left').set_index('data')
pp = pq.ParquetFile(p('pioggia-e-caldo', 'pulito', 'intermedi', 'P_orario.parquet')).read().to_pandas(); pp['idsensore'] = pd.to_numeric(pp.idsensore); pp['ora'] = pd.to_datetime(pp.ora)
pp = pp[(pp.idsensore == 19373) & (pp.ora.dt.hour >= 7) & (pp.ora.dt.hour < 20) & (pp.ora >= '2016-08-01')]
g = pp.groupby(pp.ora.dt.normalize()).mm.agg(['sum', 'count']); g.loc[g['count'] < 10, 'sum'] = np.nan
a['p'] = g['sum']; a['w'] = (a.p >= 1).where(a.p.notna()).astype(float)
a['normale'] = (a.lavorativo == 1) & (a.agosto == 0) & (a.natale_24dic_6gen == 0) & a.covid_fase.isna() & (a.flag == 'ok') & (a.tipo_moto > 0)
N = a[a.normale]
v = pd.read_csv(p('area-c', 'pulito', 'ingressi_varco_giorno.csv'), sep=';'); v['data'] = pd.to_datetime(v.data)
v = v[v.data.isin(N.index)]
v['zero'] = (v.di_cui_moto == 0) & (v.transiti >= 500)
tot = v[v.transiti >= 500]
say('varco-giorni feriali normali', len(tot), 'con zero moto', int(tot.zero.sum()), f'{tot.zero.mean() * 100:.1f}%'); say('per anno %', (tot.groupby(tot.data.dt.year).zero.mean() * 100).round(1).to_dict())
zd = tot.groupby('data').zero.sum(); N = N.assign(zeri=zd.reindex(N.index))
say('zeri medi per giorno: asciutto', round(N[N.w == 0].zeri.mean(), 2), 'bagnato', round(N[N.w == 1].zeri.mean(), 2))
def reg(df, y, x='w', log=True):
    d = df.dropna(subset=[y, x]); yy = np.log(d[y].values) if log else d[y].values.astype(float)
    X = np.column_stack([np.ones(len(d)), d[x].values, pd.get_dummies(d.index.dayofweek, drop_first=True).values.astype(float), pd.get_dummies(d.index.to_period('M').astype(str), drop_first=True).values.astype(float)])
    b, se, u = hac_ols(yy, X); return b[1], se[1], len(d)
b, se, nn = reg(N, 'zeri', log=False); say(f'varchi a zero moto, effetto pioggia: {b:+.2f} se {se:.2f} n={nn}')
# somma dei soli varchi che in quel mese non hanno zeri
v['ym'] = v.data.dt.to_period('M')
zm = v.groupby(['id_varco', 'ym']).zero.transform('sum')
pul = v[zm == 0].groupby('data')[['transiti', 'di_cui_moto']].sum()
n_v = v[zm == 0].groupby('data').id_varco.nunique()
say('varchi puliti per giorno: mediana', n_v.median(), 'min', n_v.min())
N2 = N.assign(m=pul.di_cui_moto.reindex(N.index), au=(pul.transiti - pul.di_cui_moto).reindex(N.index), nv=n_v.reindex(N.index)).dropna(subset=['m'])
N2 = N2[N2.m > 0]
for k in ['m', 'au']:
    b, se, nn = reg(N2.assign(y=N2[k] / N2.nv), 'y'); say(f'solo varchi-mese senza zeri ({k}), per varco: {(np.exp(b) - 1) * 100:+.1f}% se {se * 100:.1f} n={nn}')
# pannello: varco x giorno con moto > 0, media dei logaritmi
pan = v[(v.di_cui_moto > 0)].copy(); pan['l'] = np.log(pan.di_cui_moto); pan['la'] = np.log((pan.transiti - pan.di_cui_moto).clip(lower=1))
pan['dm'] = pan.l - pan.groupby(['id_varco', 'ym']).l.transform('mean'); pan['da'] = pan.la - pan.groupby(['id_varco', 'ym']).la.transform('mean')
dd = pan.groupby('data')[['dm', 'da']].mean(); N3 = N.join(dd).dropna(subset=['dm', 'w'])
for k in ['dm', 'da']:
    b, se, nn = reg(N3, k, log=False); say(f'pannello varco-mese ({k}): {(np.exp(b) - 1) * 100:+.1f}% se {se * 100:.1f} n={nn}')
L.close()
