"""Brera (ARPA 5897, versione _H a passo orario costante) meno ciascuna stazione di confronto, medie annue.
uso: python -I brera_vs_singole.py GIORNALIERI_CSV ANNO_DA ANNO_A OUTCSV"""
import sys, pandas as pd
f, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
D = pd.read_csv(f, parse_dates=['data']); D = D[(D.data.dt.year >= a) & (D.data.dt.year <= b)]
W = D.pivot_table(index='data', columns='fonte', values=['TX', 'TN', 'TG'])
res = {}
for el in ['TX', 'TN', 'TG']:
    for s in ['ARPA_5909_H', 'ARPA_5911_H', 'ARPA_5920_H', 'LINATE']:
        d = (W[el]['BRERA_H'] - W[el][s]).dropna()
        res[f'BRERA_meno_{s}_{el}'] = d.groupby(d.index.year).mean().round(2)
T = pd.DataFrame(res); T.index.name = 'anno'; T.to_csv(out)
pd.set_option('display.width', 250)
for el in ['TX', 'TN', 'TG']: print(T[[c for c in T.columns if c.endswith(el)]].to_string())
