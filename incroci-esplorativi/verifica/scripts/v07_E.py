"""E: pioggia e ingressi in Area C. Errori Newey-West fatti in casa."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
import pyarrow.parquet as pq
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 300)
L = open(os.path.join(OUT, 'E.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
a = pd.read_csv(p('docs', 'area-c', 'data', 'ingressi_giornalieri.csv'), sep=';')
a['data'] = pd.to_datetime(a.data)
cal = pd.read_csv(p('area-c', 'pulito', 'calendario.csv'), sep=';'); cal['data'] = pd.to_datetime(cal.data)
a = a.merge(cal[['data', 'festivo', 'agosto', 'natale_24dic_6gen', 'lavorativo', 'covid_fase', 'areac_flag_attivo']], on='data', how='left')
say('flag:', a.flag.value_counts(dropna=False).to_dict()); say('covid_fase:', a.covid_fase.value_counts(dropna=False).to_dict())
say('moto: tipo_moto vs classe_moto scarto', (a.tipo_moto - a.classe_moto).abs().max(), 'tipo_moto+tipo_auto vs tot_mensili max scarto', (a.tipo_moto + a.tipo_auto - a.tot_mensili).abs().max())
pf = pq.ParquetFile(p('pioggia-e-caldo', 'pulito', 'intermedi', 'P_orario.parquet'))
say('Schema pioggia:', pf.schema_arrow.names, 'righe', pf.metadata.num_rows)
pp = pf.read().to_pandas()
say(pp.head(3).to_string())
cols = pp.columns.tolist()
idc = [c for c in cols if 'sensor' in c.lower()][0]; tc = [c for c in cols if c.lower() in ('data', 'dataora', 'ora', 'time', 'ts', 'datetime', 'data_ora')][0]; vc_ = [c for c in cols if c.lower() in ('valore', 'mm', 'p', 'pioggia', 'p_mm', 'mm_h')][0]
pp[tc] = pd.to_datetime(pp[tc]); pp[idc] = pd.to_numeric(pp[idc])
s = pd.read_csv(p('pioggia-e-caldo', 'pulito', 'sensori_selezionati.csv'))
s = s[s.tipologia == 'Precipitazione']
# Dentro l'Area C?
conf = json.load(open(p('docs', 'area-c', 'data', 'confine.json'), encoding='utf8'))
geo = conf['geometry']['coordinates'] if conf.get('type') == 'Feature' else conf['features'][0]['geometry']['coordinates']
ring = np.array(geo[0][0])
def dentro(lon, lat):
    x, y = ring[:, 0], ring[:, 1]; c = False; j = len(x) - 1
    for i in range(len(x)):
        if ((y[i] > lat) != (y[j] > lat)) and (lon < (x[j] - x[i]) * (lat - y[i]) / (y[j] - y[i]) + x[i]):
            c = not c
        j = i
    return c
kx = 111.32 * np.cos(np.radians(45.46)); ky = 110.57
s['dentro_areac'] = [dentro(l, t) for l, t in zip(s.lng, s.lat)]
s['dist_bordo_km'] = [np.min(np.hypot((ring[:, 0] - l) * kx, (ring[:, 1] - t) * ky)) for l, t in zip(s.lng, s.lat)]
s = s.sort_values('dist_duomo_km')
say(s[['idsensore', 'nomestazione', 'datastart', 'datastop', 'dist_duomo_km', 'dentro_areac', 'dist_bordo_km']].head(14).round(2).to_string())
# pioggia in ore 7.30-19.30 ora locale. Le ore del file sono solari/UTC+1? Si controlla sotto; finestra in ora del file 7-19 con prova di sensibilità.
ids = {19373: 'brera', 14121: 'rosellini', 2006: 'lambrate', 9341: 'zavattari', 5908: 'juvara', 5902: 'corsico', 4065: 'parconord'}
pp = pp[pp[idc].isin(list(ids)) & (pp[tc] >= '2016-08-01') & (pp[tc] < '2024-12-02')].copy()
pp['d'] = pp[tc].dt.normalize(); pp['h'] = pp[tc].dt.hour
def finestra(h0, h1):
    x = pp[(pp.h >= h0) & (pp.h < h1)]
    g = x.groupby(['d', idc])[vc_].agg(['sum', 'count']).reset_index()
    g.loc[g['count'] < (h1 - h0) * .8, 'sum'] = np.nan
    return g.pivot(index='d', columns=idc, values='sum').rename(columns=ids)
day = finestra(7, 20)      # ore del giorno attivo
morn = finestra(5, 10)     # decisione di partenza
tot = finestra(0, 24)
say('copertura pioggia 7-19 per sensore:', day.notna().sum().to_dict())
say('Correlazione pioggia giornaliera 7-19 tra sensori:'); say(day.corr().round(2).to_string())
for u, v in [('brera', 'lambrate'), ('brera', 'rosellini'), ('brera', 'zavattari')]:
    w = day[[u, v]].dropna(); say(f'{u}>=1mm e {v}<0.2mm: {((w[u] >= 1) & (w[v] < .2)).mean() * 100:.1f}% dei giorni; viceversa {((w[v] >= 1) & (w[u] < .2)).mean() * 100:.1f}%; giorni bagnati {u} {(w[u] >= 1).mean() * 100:.1f}%')
# temperature
try:
    tf = pq.ParquetFile(p('pioggia-e-caldo', 'pulito', 'intermedi', 'T_orario.parquet')).read().to_pandas()
    tc2 = [c for c in tf.columns if c.lower() in ('data', 'dataora', 'ora', 'time', 'ts', 'datetime', 'data_ora')][0]; idt = [c for c in tf.columns if 'sensor' in c.lower()][0]; vt = [c for c in tf.columns if c.lower() in ('valore', 't', 'temp', 'temperatura', 't_c', 'gradi')][0]
    tf[tc2] = pd.to_datetime(tf[tc2]); tf[idt] = pd.to_numeric(tf[idt]); tf = tf[(tf[idt] == 5897) & (tf[tc2] >= '2016-08-01')]
    T = tf[(tf[tc2].dt.hour >= 7) & (tf[tc2].dt.hour < 20)].groupby(tf[tc2].dt.normalize())[vt].mean()
except Exception as e:
    say('temperatura non letta', e); T = None
d = a.set_index('data').join(day.add_prefix('p_')).join(morn.add_prefix('m_')).join(tot.add_prefix('t_'))
d['T'] = T
d['p_media'] = d[['p_brera', 'p_lambrate', 'p_zavattari', 'p_rosellini']].mean(axis=1)
d['p_mediana'] = d[['p_brera', 'p_lambrate', 'p_zavattari', 'p_rosellini']].median(axis=1)
d['moto'] = d.tipo_moto; d['auto'] = d.tipo_auto
# feriali normali
d['normale'] = (d.lavorativo == 1) & (d.agosto == 0) & (d.natale_24dic_6gen == 0) & d.covid_fase.isna() & (d.flag == 'ok') & d.moto.notna() & (d.moto > 0)
say('Feriali normali', int(d.normale.sum()), 'su', len(d), ' per anno', d[d.normale].groupby(d[d.normale].index.year).size().to_dict())
def regr(df, yv, rain, extra=None, lags=7, fe='ym'):
    x = df.dropna(subset=[yv, rain] + (extra or [])).copy()
    y = np.log(x[yv].values)
    X = [np.ones(len(x)), x[rain].values]
    names = ['c', rain]
    for e in (extra or []):
        X.append(x[e].values); names.append(e)
    dow = pd.get_dummies(x.index.dayofweek, drop_first=True).values.astype(float)
    ym = pd.get_dummies(x.index.to_period('M').astype(str), drop_first=True).values.astype(float)
    X = np.column_stack(X + [dow, ym])
    b, se, u = hac_ols(y, X, lags=lags)
    return b[1], se[1], len(x), 1 - (u ** 2).sum() / ((y - y.mean()) ** 2).sum()
def riga(lab, df, rain, extra=None):
    out = []
    for yv in ['moto', 'auto']:
        b, se, nn, r2 = regr(df, yv, rain, extra)
        out.append(f"{yv}: {(np.exp(b) - 1) * 100:+6.1f}% [{(np.exp(b - 1.96 * se) - 1) * 100:+.1f},{(np.exp(b + 1.96 * se) - 1) * 100:+.1f}]")
    say(f'{lab:44s} n={nn:4d} ' + ' | '.join(out))
N = d[d.normale].copy()
for k in ['p_brera', 'p_media', 'p_mediana', 'p_lambrate', 'p_zavattari', 'p_rosellini', 'm_brera', 't_brera']:
    N[k + '_01'] = (N[k] >= 1).where(N[k].notna()).astype(float)
    N[k + '_5'] = (N[k] >= 5).where(N[k].notna()).astype(float)
    N[k + '_10'] = (N[k] >= 10).where(N[k].notna()).astype(float)
    N[k + '_log'] = np.log1p(N[k])
say('\nEffetto per sensore (giorno con almeno 1 mm tra le 7 e le 19, FE anno-mese e giorno settimana, NW 7)')
for k in ['p_brera', 'p_media', 'p_mediana', 'p_lambrate', 'p_zavattari', 'p_rosellini', 'm_brera', 't_brera']:
    riga(k + ' >=1mm', N, k + '_01')
say('\nDose (sensore Brera)')
N['brera_c'] = pd.cut(N.p_brera, [-1, .19, 1, 5, 15, 500], labels=['0', '<1', '1-5', '5-15', '15+'])
for c in ['<1', '1-5', '5-15', '15+']:
    N['_'] = (N.brera_c == c).astype(float).where(N.p_brera.notna())
    N['_altre'] = 0.0
    x = N.dropna(subset=['p_brera'])
    # modello congiunto
dums = pd.get_dummies(N.brera_c).astype(float).drop(columns=['0'])
dums.columns = ['b_lt1', 'b_1_5', 'b_5_15', 'b_15p']
Nd = N.join(dums)
for yv in ['moto', 'auto']:
    x = Nd.dropna(subset=['p_brera', yv])
    y = np.log(x[yv].values)
    X = np.column_stack([np.ones(len(x)), x[dums.columns].values, pd.get_dummies(x.index.dayofweek, drop_first=True).values.astype(float), pd.get_dummies(x.index.to_period('M').astype(str), drop_first=True).values.astype(float)])
    b, se, u = hac_ols(y, X)
    say(yv, ' '.join(f"{n_}:{(np.exp(b[i + 1]) - 1) * 100:+.1f}%(se{se[i + 1] * 100:.1f}) n={int(x[n_].sum())}" for i, n_ in enumerate(dums.columns)))
riga('Brera 1mm con temperatura', N, 'p_brera_01', ['T'])
N['T2'] = N['T'] ** 2
riga('Brera 1mm con temperatura e T2', N, 'p_brera_01', ['T', 'T2'])
riga('log1p mm Brera', N, 'p_brera_log')
# periodi e stagioni
say('\nStabilità')
periodi = {'2016-09..2019-12': ('2016-09-01', '2019-12-31'), '2017': ('2017-01-01', '2017-12-31'), '2018': ('2018-01-01', '2018-12-31'), '2019': ('2019-01-01', '2019-12-31'), '2021-07..2022-12': ('2021-07-01', '2022-12-31'), '2023': ('2023-01-01', '2023-12-31'), '2024': ('2024-01-01', '2024-11-30')}
for k, (u, v) in periodi.items():
    riga(k, N[(N.index >= u) & (N.index <= v)], 'p_brera_01')
riga('Ott-Mar', N[N.index.month.isin([10, 11, 12, 1, 2, 3])], 'p_brera_01')
riga('Apr-Giu', N[N.index.month.isin([4, 5, 6])], 'p_brera_01')
riga('Lug,Set', N[N.index.month.isin([7, 9])], 'p_brera_01')
riga('Inverno Dic-Feb', N[N.index.month.isin([12, 1, 2])], 'p_brera_01')
riga('Primavera+autunno mesi miti Mag,Giu,Set', N[N.index.month.isin([5, 6, 9])], 'p_brera_01')
# placebo: pioggia di domani e di ieri
N2 = d[d.normale].copy()
for k in [-1, 1]:
    N2[f'pl{k}'] = (d.p_brera.shift(-k) >= 1).where(d.p_brera.shift(-k).notna()).astype(float).reindex(N2.index)
N2['oggi'] = (N2.p_brera >= 1).where(N2.p_brera.notna()).astype(float)
riga('Placebo: pioggia DOMANI da sola', N2, 'pl1')
riga('Oggi, con ieri e domani', N2, 'oggi', ['pl-1', 'pl1'])
for lab, xx in [('Domani nel modello congiunto', 'pl1'), ('Ieri nel modello congiunto', 'pl-1')]:
    riga(lab, N2, xx, ['oggi'] + ['pl-1' if xx == 'pl1' else 'pl1'])
# sensori discordi: quando la pioggia è solo a Brera, oppure solo fuori
N['solo_brera'] = ((N.p_brera >= 1) & (N[['p_lambrate', 'p_zavattari', 'p_rosellini']].max(axis=1) < .2)).astype(float)
N['solo_fuori'] = ((N.p_brera < .2) & (N[['p_lambrate', 'p_zavattari', 'p_rosellini']].max(axis=1) >= 1)).astype(float)
N['ovunque'] = ((N.p_brera >= 1) & (N[['p_lambrate', 'p_zavattari', 'p_rosellini']].min(axis=1) >= 1)).astype(float)
say('giorni solo Brera', int(N.solo_brera.sum()), 'solo fuori', int(N.solo_fuori.sum()), 'ovunque', int(N.ovunque.sum()))
riga('Pioggia ovunque', N, 'ovunque', ['solo_brera', 'solo_fuori'])
riga('Solo Brera', N, 'solo_brera', ['ovunque', 'solo_fuori'])
riga('Solo fuori', N, 'solo_fuori', ['ovunque', 'solo_brera'])
# mattina contro pomeriggio
N['matt'] = (N.m_brera >= 1).where(N.m_brera.notna()).astype(float)
aft = finestra(12, 20)['brera'].reindex(N.index); N['pom'] = (aft >= 1).where(aft.notna()).astype(float)
riga('Mattina 5-10 con pomeriggio', N, 'matt', ['pom']); riga('Pomeriggio 12-20 con mattina', N, 'pom', ['matt'])
for ora, (u, v) in {'ore file 6-19': (6, 19), 'ore file 8-20': (8, 20)}.items():
    w = finestra(u, v)['brera'].reindex(N.index); N['_w'] = (w >= 1).where(w.notna()).astype(float); riga(ora, N, '_w')
# Definizione moto
say('\n=== Definizione della categoria moto')
y = d[d.normale].groupby(d[d.normale].index.year).agg(moto=('moto', 'median'), auto=('auto', 'median'), tot=('tot_mensili', 'median'))
y['quota_moto'] = y.moto / y.tot * 100
say(y.round(1).to_string())
m = d[d.normale].copy(); m['ym'] = m.index.to_period('M'); ms = m.groupby('ym').apply(lambda g: (g.moto.sum() / g.tot_mensili.sum()) * 100, include_groups=False)
say('Quota moto mese per mese:', ' '.join(f"{k}:{v:.1f}" for k, v in ms.items()))
# confronto con la serie ufficiale 2024
u = d[d.uff_730_1930_moto.notna()]
say('Giorni con serie ufficiale moto 7.30-19.30:', len(u), 'periodo', u.index.min(), u.index.max(), 'mediana uff moto', u.uff_730_1930_moto.median(), 'mediana mensili moto', u.moto.median(), 'correlazione', round(u.uff_730_1930_moto.corr(u.moto), 3), 'rapporto uff/mensili feriali', round((u[u.lavorativo == 1].uff_730_1930_moto / u[u.lavorativo == 1].moto).median(), 3))
v = pd.read_csv(p('area-c', 'pulito', 'ingressi_varco_giorno.csv'), sep=';'); v['data'] = pd.to_datetime(v.data)
v = v[v.data.isin(d[d.normale].index)]
v['anno'] = v.data.dt.year
qv = v.groupby(['id_varco', 'anno'])[['transiti', 'di_cui_moto']].sum(); qv['q'] = qv.di_cui_moto / qv.transiti * 100
qp = qv.q.unstack('anno')
qp.insert(0, 'nome', v.groupby('id_varco').nome_varco.first())
say(qp.round(1).to_string())
qq = qp.drop(columns='nome')
say('Varchi: rapporto max/min quota moto per anno', (qq.max() / qq.min()).round(1).to_dict(), ' Spearman 2017-2024 tra varchi', round(stats.spearmanr(qq[2017], qq[2024], nan_policy='omit').statistic, 3))
say('Salti annui più grandi per varco (punti):'); dd = qq.diff(axis=1); xx = dd.stack().sort_values(); say(xx.head(6).round(1).to_dict()); say(xx.tail(6).round(1).to_dict())
# Varchi costanti
vv = v[~v.id_varco.isin([87, 89])].groupby('data')[['transiti', 'di_cui_moto']].sum()
N['moto40'] = vv.di_cui_moto.reindex(N.index); N['auto40'] = (vv.transiti - vv.di_cui_moto).reindex(N.index)
for yv in ['moto40', 'auto40']:
    b, se, nn, r2 = regr(N, yv, 'p_brera_01'); say(f'40 varchi fissi {yv}: {(np.exp(b) - 1) * 100:+.1f}% se {se * 100:.1f} n={nn}')
# Per varco: effetto
res = []
vd = pd.read_csv(p('area-c', 'pulito', 'ingressi_varco_giorno.csv'), sep=';'); vd['data'] = pd.to_datetime(vd.data)
for i, g in vd.groupby('id_varco'):
    g = g.set_index('data').reindex(N.index)
    g = g[g.di_cui_moto > 0]
    g['p'] = N.p_brera_01;
    bm, sm, nn, _ = regr(g.assign(m=g.di_cui_moto), 'm', 'p'); ba, sa, _, _ = regr(g.assign(a=g.transiti - g.di_cui_moto), 'a', 'p')
    res.append(dict(id=i, nome=g.nome_varco.dropna().iloc[0], n=nn, moto=bm, se_m=sm, auto=ba, se_a=sa))
R_ = pd.DataFrame(res); say('Effetto per varco: moto mediana', round((np.exp(R_.moto.median()) - 1) * 100, 1), 'min', round((np.exp(R_.moto.min()) - 1) * 100, 1), 'max', round((np.exp(R_.moto.max()) - 1) * 100, 1), ' auto mediana', round((np.exp(R_.auto.median()) - 1) * 100, 1), 'min', round((np.exp(R_.auto.min()) - 1) * 100, 1), 'max', round((np.exp(R_.auto.max()) - 1) * 100, 1))
R_.to_csv(os.path.join(OUT, 'E_varchi.csv'), index=False)
# NW: sensibilità dei ritardi
for lg in [0, 3, 7, 14, 28]:
    b, se, nn, _ = regr(N, 'moto', 'p_brera_01', lags=lg); say(f'moto NW lag {lg}: se {se * 100:.2f} (b {b * 100:.1f})')
    b, se, nn, _ = regr(N, 'auto', 'p_brera_01', lags=lg); say(f'auto NW lag {lg}: se {se * 100:.2f} (b {b * 100:.1f})')
# Sostituzione: la caduta di moto spiega il calo totale?
b, se, nn, _ = regr(N.assign(tot=N.tot_mensili), 'tot', 'p_brera_01'); say(f'totale: {(np.exp(b) - 1) * 100:+.1f}% se {se * 100:.1f}')
wet = N[N.p_brera_01 == 1]; dry = N[N.p_brera_01 == 0]
say('Medie semplici: moto asciutto', round(dry.moto.mean()), 'bagnato', round(wet.moto.mean()), 'auto asciutto', round(dry.auto.mean()), 'bagnato', round(wet.auto.mean()), 'giorni', len(dry), len(wet))
L.close()
