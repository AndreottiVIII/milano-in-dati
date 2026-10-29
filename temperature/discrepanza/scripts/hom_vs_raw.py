"""Differenza tra serie omogeneizzata ECA&D (HOM, Squintu et al.) e serie Maugeri non-blended, per periodi.
uso: python -I hom_vs_raw.py GIORNALIERI_CSV OUTCSV
Output: periodo; HOM-MAUGERI medio per TX, TN, TG; giorni."""
import sys, pandas as pd
D = pd.read_csv(sys.argv[1], parse_dates=['data'])
W = D[D.fonte.isin(['HOM', 'MAUGERI'])].pivot_table(index='data', columns='fonte', values=['TX', 'TN', 'TG'])
per = [(1781, 1834), (1835, 1899), (1900, 1949), (1950, 1986), (1987, 1994), (1995, 2000), (2001, 2001), (2002, 2008)]
rows = []
for a, b in per:
    r = {'periodo': f'{a}-{b}'}
    for el in ['TX', 'TN', 'TG']:
        d = (W[el]['HOM'] - W[el]['MAUGERI']).dropna()
        d = d[(d.index.year >= a) & (d.index.year <= b)]
        r[f'HOM_meno_MAUGERI_{el}'] = round(d.mean(), 2); r[f'{el}_giorni'] = len(d)
    rows.append(r)
T = pd.DataFrame(rows); T.to_csv(sys.argv[2], index=False); print(T.to_string())
