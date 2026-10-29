"""Verifica: serie continua meno media delle vicine ARPA (5909/5911/5920 _H), media annua. Deve restare piatta attorno al 1995.
uso: python -I verifica_giunzione.py SERIE_CONTINUA_CSV GIORNALIERI_CSV OUTCSV"""
import sys, pandas as pd
S = pd.read_csv(sys.argv[1], parse_dates=['data'], index_col='data', low_memory=False)
D = pd.read_csv(sys.argv[2], parse_dates=['data']); D = D[D.fonte.isin(['ARPA_5909_H', 'ARPA_5911_H', 'ARPA_5920_H'])]
W = D.pivot_table(index='data', columns='fonte', values=['TX', 'TN', 'TG'])
res = {}
for el in ['TX', 'TN', 'TG']:
    ref = W[el].mean(axis=1).where(W[el].notna().sum(axis=1) >= 2)
    d = (pd.to_numeric(S[el]) - ref).dropna(); d = d[d.index.year <= 2007]
    res[f'continua_meno_vicine_{el}'] = d.groupby(d.index.year).mean().round(2)
T = pd.DataFrame(res); T.index.name = 'anno'; T.to_csv(sys.argv[3]); print(T.to_string())
