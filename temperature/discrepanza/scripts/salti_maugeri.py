"""Documenta i salti della serie Maugeri.
uso: python -I salti_maugeri.py GIORNALIERI_CSV OUTDIR
Scrive:
  OUTDIR/salto_2001_finestre.csv       media MAUGERI - BRERA_H (TX, TN) nei 30 giorni prima e dopo il 2001-06-20
  OUTDIR/maugeri_meno_linate_mensile.csv  MAUGERI - LINATE per mese 1980-1992 (TX, TN, TG)
  OUTDIR/maugeri_escursione_mensile.csv   media mensile TX-TN della serie MAUGERI 1980-2008"""
import sys, pandas as pd
f, od = sys.argv[1:3]
D = pd.read_csv(f, parse_dates=['data'])
W = D[D.fonte.isin(['MAUGERI', 'BRERA_H', 'LINATE'])].pivot_table(index='data', columns='fonte', values=['TX', 'TN', 'TG'])
rows = []
for nome, a, b in [('prima', '2001-05-21', '2001-06-19'), ('dopo', '2001-06-21', '2001-07-20')]:
    r = {'finestra': nome, 'da': a, 'a': b}
    for el in ['TX', 'TN']:
        d = (W[el]['MAUGERI'] - W[el]['BRERA_H']).loc[a:b].dropna()
        r[f'MAUGERI_meno_BRERA_{el}'] = round(d.mean(), 2); r[f'{el}_giorni'] = len(d)
    rows.append(r)
T = pd.DataFrame(rows); T.to_csv(f'{od}/salto_2001_finestre.csv', index=False); print(T.to_string())
res = {}
for el in ['TX', 'TN', 'TG']:
    d = (W[el]['MAUGERI'] - W[el]['LINATE']).loc['1980':'1992'].dropna()
    res[el] = d.groupby(d.index.to_period('M')).mean().round(2)
M = pd.DataFrame(res); M.index.name = 'mese'; M.columns = [f'MAUGERI_meno_LINATE_{c}' for c in M.columns]
M.to_csv(f'{od}/maugeri_meno_linate_mensile.csv')
e = (W['TX']['MAUGERI'] - W['TN']['MAUGERI']).loc['1980':'2008'].dropna()
E = e.groupby(e.index.to_period('M')).mean().round(2).to_frame('escursione_TX_meno_TN'); E.index.name = 'mese'
E.to_csv(f'{od}/maugeri_escursione_mensile.csv')
print(M.loc['1986-06':'1987-10'].to_string())
