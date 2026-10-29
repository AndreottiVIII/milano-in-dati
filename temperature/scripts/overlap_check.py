"""Sovrapposizione 1990-2008 tra serie Maugeri (ECA&D non-blended) e ARPA Brera (sensore 5897). Solo medie annuali delle differenze (controllo, non omogeneizzazione).
uso: python -I overlap_check.py RAWDIR OUTCSV"""
import sys, os, glob, io, pandas as pd
raw, out = sys.argv[1:3]
def ecad(p):
    L=open(p,encoding='latin-1').read().splitlines(); i=[k for k,l in enumerate(L) if l.strip().startswith('STAID')][0]
    d=pd.read_csv(io.StringIO('\n'.join(L[i:])),skipinitialspace=True); d.columns=[c.strip() for c in d.columns]
    el=[c for c in d.columns if c in('TX','TN','TG')][0]
    d['d']=pd.to_datetime(d.DATE.astype(str),format='%Y%m%d'); d=d[(d['Q_'+el]!=9)&(d[el]!=-9999)]
    return d.set_index('d')[el]/10
tx=ecad(f'{raw}/ecad/nonblend_tx/TX_SOUID105248.txt'); tn=ecad(f'{raw}/ecad/nonblend_tn/TN_SOUID105247.txt'); tg=ecad(f'{raw}/ecad/nonblend_tg/TG_SOUID105249.txt')
A=pd.concat([pd.read_csv(p,dtype={'stato':str}) for p in sorted(glob.glob(f'{raw}/arpa/brera_5897_*.csv'))])
A=A[(A.stato=='VA')&(A.valore>-100)].copy(); A['t']=pd.to_datetime(A.data); A['day']=(A.t-pd.Timedelta('1s')).dt.floor('D')
g=A.groupby('day').valore.agg(['count','max','min','mean']); g=g[g['count']>=20]
r=pd.DataFrame({'dTX':g['max']-tx,'dTN':g['min']-tn,'dTG':g['mean']-tg}).dropna(how='all')
r=r[(r.index>='1990-01-01')&(r.index<='2008-11-30')]
t=r.groupby(r.index.year).agg(['mean','count']).round(2)
t.columns=['_'.join(c) for c in t.columns]; t.to_csv(out); print(t.to_string())
print(r.mean().round(2).to_dict())
