"""Esplorazione veloce del CSV ISTAT: comuni per TIPO_COMUNE, valori n.d. per anno, 29 febbraio, giorni presenti.
Uso: python -I -X utf8 esplora.py <csv assoluto>"""
import sys, pandas as pd
p = sys.argv[1]
df = pd.read_csv(p, encoding='latin-1', dtype=str, na_values=[], keep_default_na=False)
print(df.shape)
print(df.groupby('TIPO_COMUNE')['COD_PROVCOM'].nunique())
print('comuni totali', df.COD_PROVCOM.nunique(), 'regioni', sorted(df.REG.unique()))
tc = [c for c in df.columns if c[:2] in ('M_','F_','T_')]
nd = (df[tc] == 'n.d.').sum()
print(nd[nd > 0])
# n.d. nei T_ per tipo comune
for y in ['11','15','20','25','26']:
    c = 'T_'+y
    print(c, df.groupby('TIPO_COMUNE')[c].apply(lambda s: (s=='n.d.').mean()))
f = df[df.GE=='0229']
print('0229 righe', len(f))
for y in ['11','12','13','14','15','16']:
    print(y, (f['T_'+y]=='n.d.').sum(), pd.to_numeric(f['T_'+y], errors='coerce').sum())
# Milano
m = df[df.COD_PROVCOM=='015146']
print(m.TIPO_COMUNE.unique(), m.CL_ETA.nunique())
print(df.GE.nunique(), sorted(df.GE.unique())[:3], sorted(df.GE.unique())[-3:])
# 2026: giorni dopo il 30 giugno
for y in ['25','26']:
    t = pd.to_numeric(df['T_'+y], errors='coerce')
    d = df.assign(t=t).groupby('GE').t.sum()
    print(y, 'ultimo giorno con dati', d[d>0].index.max(), 'primo', d[d>0].index.min())
