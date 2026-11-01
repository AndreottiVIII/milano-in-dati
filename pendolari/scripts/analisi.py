"""Riepiloghi sul pendolarismo da/verso Milano (1991, 2001, 2011, 2021) e confronto con la matrice regionale OD2016.

Uso: python -I -X utf8 analisi.py <cartella pendolari, percorso assoluto>
Prima: codici.py, parse_censimenti.py, distanze.py, od2016.py.
Scrive in pulito/: serie_totali.csv, origini_gruppi.csv, top_comuni.csv, bande_distanza.csv, modi_per_banda.csv,
tempi_per_banda.csv, orari_entrata.csv, uscite_top.csv, scambi_vicini.csv, mappa_comuni.csv, od2016_bande_modi.csv,
riepilogo.json.
Bande di distanza = km stradali da ISTAT (matrice distanze 2021) dal comune di residenza a Milano; solo comuni lombardi.
"""
import sys, json, re, unicodedata
from pathlib import Path
import numpy as np
import pandas as pd

P = Path(sys.argv[1])
OUT = P / 'pulito'
MI = 15146

com = pd.read_csv(OUT / 'comuni_2021.csv').set_index('pro_com')
dist = pd.read_csv(OUT / 'distanze_milano.csv').set_index('pro_com')
fl = pd.read_csv(OUT / 'flussi_milano.csv')
dt = pd.read_csv(OUT / 'dettaglio_milano.csv', dtype={'modo_raw': str, 'orario': str, 'tempo': str})
og = pd.read_csv(OUT / 'origini_lombardia.csv')
R = {}

BINS = [-1, 0.5, 10, 20, 30, 50, 80, 10000]
LAB = ['Milano', '0-10 km', '10-20 km', '20-30 km', '30-50 km', '50-80 km', 'oltre 80 km']


def banda_da_km(km):
    return pd.cut(km, BINS, labels=LAB).astype(object)


def banda(df):
    km = df['altro'].map(dist['km_verso_milano'])
    b = banda_da_km(km)
    b = pd.Series(b, index=df.index).fillna('fuori Lombardia')
    b[df['direzione'] == 'interno'] = 'Milano'
    return b


# ---------------------------------------------------------------- 1. totali
t = fl.groupby(['anno', 'motivo', 'direzione'])['n'].sum().unstack().reset_index()
t['quota_di_fuori'] = t['entra'] / (t['entra'] + t['interno'])
t['quota_milanesi_fuori'] = t['esce'] / (t['esce'] + t['interno'])
t = t.round(4)
t.to_csv(OUT / 'serie_totali.csv', index=False)
tt = fl.groupby(['anno', 'direzione'])['n'].sum().unstack()
tt['saldo'] = tt['entra'] - tt['esce']
tt['rapporto_entra_esce'] = tt['entra'] / tt['esce']
R['totali'] = {int(a): {k: round(float(v), 1) for k, v in r.items()} for a, r in tt.iterrows()}
R['quota_di_fuori_lavoro'] = {int(r.anno): round(float(r.quota_di_fuori), 4) for r in t[t.motivo == 'lavoro'].itertuples()}
R['quota_milanesi_fuori_lavoro'] = {int(r.anno): round(float(r.quota_milanesi_fuori), 4) for r in t[t.motivo == 'lavoro'].itertuples()}
R['totali_per_motivo'] = {f'{r.anno}_{r.motivo}': {'entra': round(r.entra), 'esce': round(r.esce), 'interno': round(r.interno)} for r in t.itertuples()}

# ---------------------------------------------------------------- 2. gruppi di origine
e = fl[fl.direzione == 'entra'].copy()
e['uts'] = e['altro'].map(com['uts'])
e['reg'] = e['altro'].map(com['regione'])
LOMB_UTS = ['Varese', 'Como', 'Lecco', 'Bergamo', 'Brescia', 'Pavia', 'Lodi', 'Cremona', 'Mantova', 'Sondrio']


def gruppo(r):
    if pd.isna(r.reg):
        return 'Non agganciato'
    if r.uts == 'Milano':
        return 'Resto della città metropolitana di Milano'
    if r.uts == 'Monza e della Brianza':
        return 'Monza e Brianza'
    if r.reg == 'Lombardia':
        return r.uts
    if r.reg in ('Piemonte', 'Emilia-Romagna'):
        return r.reg
    return 'Altre regioni'


e['gruppo'] = [gruppo(r) for r in e.itertuples()]
g = e.groupby(['anno', 'motivo', 'gruppo'], as_index=False)['n'].sum()
g.to_csv(OUT / 'origini_gruppi.csv', index=False)
gg = e.groupby(['anno', 'gruppo'])['n'].sum().unstack(0).fillna(0)
R['origini_gruppi'] = {k: {int(a): round(float(v)) for a, v in row.items()} for k, row in gg.iterrows()}
R['non_agganciato_quota'] = {int(a): round(float(v), 4) for a, v in (e[e.gruppo == 'Non agganciato'].groupby('anno')['n'].sum().reindex([1991, 2001, 2011, 2021]).fillna(0) / e.groupby('anno')['n'].sum()).items()}

# ---------------------------------------------------------------- 3. top comuni di origine
eg = e.groupby(['anno', 'altro'])['n'].sum().unstack(0).fillna(0)
el = e[e.motivo == 'lavoro'].groupby(['anno', 'altro'])['n'].sum().unstack(0).fillna(0)
es = e[e.motivo == 'studio'].groupby(['anno', 'altro'])['n'].sum().unstack(0).fillna(0)
top = eg.sort_values(2021, ascending=False).head(40).copy()
top.columns = [f'n_{c}' for c in top.columns]
top['nome'] = [com['nome'].get(i) for i in top.index]
top['uts'] = [com['uts'].get(i) for i in top.index]
top['km'] = [dist['km_verso_milano'].get(i) for i in top.index]
top['min_strada'] = [dist['min_verso_milano'].get(i) for i in top.index]
top['lavoro_2021'] = el[2021].reindex(top.index)
top['studio_2021'] = es[2021].reindex(top.index)
top['pop_2021'] = [com['pop_2021'].get(i) for i in top.index]
top.index.name = 'pro_com'
top.round(0).reset_index().to_csv(OUT / 'top_comuni.csv', index=False)
R['top10_2021'] = [(com['nome'].get(i), round(float(v))) for i, v in eg[2021].sort_values(ascending=False).head(10).items()]
R['top10_2011'] = [(com['nome'].get(i), round(float(v))) for i, v in eg[2011].sort_values(ascending=False).head(10).items()]

# ---------------------------------------------------------------- 4. bande di distanza (solo entrata)
e['banda'] = banda(e)
bd = e.groupby(['anno', 'motivo', 'banda'], as_index=False)['n'].sum()
bd.to_csv(OUT / 'bande_distanza.csv', index=False)
km = e['altro'].map(dist['km_verso_milano'])
mn = e['altro'].map(dist['min_verso_milano'])
stat = {}
for y in (1991, 2001, 2011, 2021):
    s = e[(e.anno == y) & km.notna()].copy()
    s['km'] = km[s.index]
    s['mn'] = mn[s.index]
    tot_y = e[e.anno == y]['n'].sum()

    def med(col):
        x = s.sort_values(col)
        c = x['n'].cumsum() / x['n'].sum()
        return float(x[col][(c >= 0.5).values].iloc[0])
    stat[y] = {'mediana_km': round(med('km'), 1), 'media_km': round(float((s.km * s.n).sum() / s.n.sum()), 1),
               'mediana_min_strada': round(med('mn'), 1),
               'quota_oltre_30km': round(float(s[s.km > 30].n.sum() / tot_y), 4),
               'quota_oltre_50km': round(float(s[s.km > 50].n.sum() / tot_y), 4),
               'quota_fuori_lombardia': round(float(1 - s.n.sum() / tot_y), 4),
               'lavoratori_oltre_50km': round(float(s[(s.km > 50) & (s.motivo == 'lavoro')].n.sum()))}
R['distanze'] = stat

# ---------------------------------------------------------------- 5. mezzi e tempi (1991, 2001, 2011)
d = dt[dt.modo != 'nd'].copy()
d['banda'] = banda(d)
modi = d[d.direzione.isin(['entra', 'interno', 'esce'])].groupby(['anno', 'motivo', 'direzione', 'banda', 'modo'], as_index=False)['n'].sum()
modi['n'] = modi['n'].round(1)
modi.to_csv(OUT / 'modi_per_banda.csv', index=False)
ms = d[d.direzione == 'entra'].groupby(['anno', 'motivo', 'modo'])['n'].sum().unstack()
ms = ms.div(ms.sum(axis=1), axis=0).round(4)
R['modi_entrata'] = {f'{a}_{m}': {k: float(v) for k, v in r.items()} for (a, m), r in ms.iterrows()}
mi_int = d[d.direzione == 'interno'].groupby(['anno', 'motivo', 'modo'])['n'].sum().unstack()
mi_int = mi_int.div(mi_int.sum(axis=1), axis=0).round(4)
R['modi_interno'] = {f'{a}_{m}': {k: float(v) for k, v in r.items()} for (a, m), r in mi_int.iterrows()}
# quota di record con mezzo non indicato
nd = dt[dt.direzione == 'entra'].groupby('anno').apply(lambda x: float(x[x.modo == 'nd'].n.sum() / x.n.sum()), include_groups=False)
R['mezzo_non_indicato_quota'] = {int(a): round(v, 4) for a, v in nd.items()}

dtm = dt[(dt.tempo != 'nd') & dt.direzione.isin(['entra', 'interno', 'esce'])].copy()
dtm['banda'] = banda(dtm)
tm = dtm.groupby(['anno', 'motivo', 'direzione', 'banda', 'tempo'], as_index=False)['n'].sum()
tm['n'] = tm['n'].round(1)
tm.to_csv(OUT / 'tempi_per_banda.csv', index=False)
x = dtm[dtm.direzione == 'entra'].groupby(['anno', 'tempo'])['n'].sum().unstack()
x = x.div(x.sum(axis=1), axis=0).round(4)
R['tempi_entrata'] = {int(a): {k: float(v) for k, v in r.items()} for a, r in x.iterrows()}
dor = dt[(dt.orario != 'nd') & (dt.direzione == 'entra')]
oo = dor.groupby(['anno', 'motivo', 'orario'], as_index=False)['n'].sum()
oo['n'] = oo['n'].round(1)
oo.to_csv(OUT / 'orari_entrata.csv', index=False)

# ---------------------------------------------------------------- 6. uscite e scambi con i vicini
o = fl[fl.direzione == 'esce'].copy()
og2 = o.groupby(['anno', 'altro'])['n'].sum().unstack(0).fillna(0)
ut = og2.sort_values(2021, ascending=False).head(25).copy()
ut.columns = [f'n_{c}' for c in ut.columns]
ut['nome'] = [com['nome'].get(i) for i in ut.index]
ut['uts'] = [com['uts'].get(i) for i in ut.index]
ut.index.name = 'pro_com'
ut.round(0).reset_index().to_csv(OUT / 'uscite_top.csv', index=False)
R['uscite_top5_2021'] = [(com['nome'].get(i), round(float(v))) for i, v in og2[2021].sort_values(ascending=False).head(5).items()]
sc = pd.DataFrame({f'entra_{y}': eg[y] for y in eg.columns}).join(pd.DataFrame({f'esce_{y}': og2[y] for y in og2.columns}), how='outer').fillna(0)
sc['nome'] = [com['nome'].get(i) for i in sc.index]
sc['scambi_2021'] = sc['entra_2021'] + sc['esce_2021']
sc = sc[sc.scambi_2021 >= 3000].sort_values('scambi_2021', ascending=False)
sc.index.name = 'pro_com'
sc.round(0).reset_index().to_csv(OUT / 'scambi_vicini.csv', index=False)
pos = sc[(sc['esce_1991'] > sc['entra_1991']) & (sc['esce_2001'] > sc['entra_2001']) & (sc['esce_2011'] > sc['entra_2011']) & (sc['esce_2021'] > sc['entra_2021'])]
R['comuni_che_ricevono_piu_di_quanti_mandano'] = [(r.nome, {y: [round(getattr(r, f'entra_{y}')), round(getattr(r, f'esce_{y}'))] for y in (1991, 2001, 2011, 2021)}) for r in pos.itertuples()]

# ---------------------------------------------------------------- 7. mappa: comuni lombardi
tot_or = og.groupby(['anno', 'origine'])[['totale', 'interno', 'verso_milano']].sum().reset_index()
mp = com[com.cod_regione == 3][['nome', 'uts', 'sigla', 'pop_2021', 'lon', 'lat']].copy()
mp.index.name = 'pro_com'
for y in (1991, 2001, 2011, 2021):
    a = tot_or[tot_or.anno == y].set_index('origine')
    mp[f'entra_{y}'] = eg[y].reindex(mp.index).fillna(0).round(0)
    mp[f'tot_{y}'] = a['totale'].reindex(mp.index)
    mp[f'quota_{y}'] = (a['verso_milano'] / a['totale']).reindex(mp.index).round(4)
mp['km'] = dist['km_verso_milano'].reindex(mp.index)
mp['min'] = dist['min_verso_milano'].reindex(mp.index)
mp.reset_index().to_csv(OUT / 'mappa_comuni.csv', index=False)
R['comuni_lombardi'] = int(len(mp))
R['comuni_lombardi_con_flussi_2021'] = int((mp['entra_2021'] > 0).sum())
R['quota_2021_comuni_che_mandano_a_milano_oltre_20pc'] = int((mp['quota_2021'] > 0.2).sum())

# ---------------------------------------------------------------- 8. OD2016 (stime regionali, spostamenti non persone)
od = pd.read_csv(OUT / 'od2016_milano.csv')
lav = [c for c in od.columns if c.startswith('lav_')]
stu = [c for c in od.columns if c.startswith('stu_')]


def norm(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]', '', s)


lom = com[com.regione == 'Lombardia']
idx = {(r.sigla, norm(r.nome)): i for i, r in lom.iterrows()}
oe = od[od.direzione == 'entra'].copy()
oe['zona_base'] = oe['zona'].str.replace(r'\s+\d+$', '', regex=True)
oe['pc'] = [idx.get((p, norm(z))) for p, z in zip(oe['prov'], oe['zona_base'])]
oe['km'] = oe['pc'].map(dist['km_verso_milano'])
oe['banda'] = banda_da_km(oe['km'])
oe.loc[oe['pc'].isna() & oe['prov'].isin(['MI', 'MB', 'VA', 'CO', 'LC', 'BG', 'BS', 'PV', 'LO', 'CR', 'MN', 'SO']), 'banda'] = 'zona composta'
oe['banda'] = oe['banda'].fillna('fuori Lombardia')
tot_oe = oe[lav + stu].sum().sum()
R['od2016'] = {'entra_lavoro': round(float(oe[lav].sum().sum())), 'entra_studio': round(float(oe[stu].sum().sum())),
               'esce_lavoro': round(float(od[od.direzione == 'esce'][lav].sum().sum())), 'esce_studio': round(float(od[od.direzione == 'esce'][stu].sum().sum())),
               'interno_lavoro': round(float(od[od.direzione == 'interno'][lav].sum().sum())), 'interno_studio': round(float(od[od.direzione == 'interno'][stu].sum().sum())),
               'quota_zone_composte': round(float(oe[oe.banda == 'zona composta'][lav + stu].sum().sum() / tot_oe), 4)}
rows = []
for mot, cols in (('lavoro', lav), ('studio', stu)):
    gb = oe.groupby('banda')[cols].sum()
    for b, r in gb.iterrows():
        for c in cols:
            rows.append((mot, b, c.split('_', 1)[1], round(float(r[c]), 1)))
odb = pd.DataFrame(rows, columns=['motivo', 'banda', 'modo', 'spostamenti'])
odb.to_csv(OUT / 'od2016_bande_modi.csv', index=False)
M = {'cond': 'auto', 'pax': 'auto', 'moto': 'moto', 'ferro': 'ferro', 'gomma': 'bus', 'bici': 'piedi_bici_altro', 'piedi': 'piedi_bici_altro', 'altro': 'piedi_bici_altro'}
odb['modo6'] = odb['modo'].map(M)
s = odb.groupby(['motivo', 'modo6'])['spostamenti'].sum().unstack()
R['od2016_modi_entrata'] = {m: {k: round(float(v / s.loc[m].sum()), 4) for k, v in s.loc[m].items()} for m in s.index}

json.dump(R, open(OUT / 'riepilogo.json', 'w', encoding='utf8'), indent=1, ensure_ascii=False, default=str)
print(json.dumps(R, indent=1, ensure_ascii=False, default=str))
