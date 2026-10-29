"""Controllo: Brera meno vicine, anno per anno, prima e dopo la correzione proposta (solo sul sensore, ore :00).
uso: python -I verifica_2008_2016.py GIORNALIERI_H PROPOSTA_CSV DA A OUTCSV
Per ogni vicina: media annua di (Brera - vicina) meno la sua media 2003-2007 (livello "buono" di prima); poi la
MEDIANA sulle vicine (almeno 3). Con la correzione la serie dovrebbe stare vicina a 0 anche nel 2008-2016."""
import sys
import numpy as np, pandas as pd
f, pf, DA, A, out = sys.argv[1:6]
D = pd.read_csv(f, parse_dates=['data'])
P = pd.read_csv(pf)
res = {}
for el in ['TX', 'TN']:
    W = D.pivot(index='data', columns='sensore', values=el)
    off = P[P.elemento == el].set_index('mese').correzione_lisciata
    m = (W.index >= DA) & (W.index <= A)
    Bc = W[5897].copy(); Bc[m] = Bc[m] + off.reindex(W.index[m].month).values
    for nome, B in (('grezza', W[5897]), ('corretta', Bc)):
        cols = {}
        for k in [c for c in W.columns if c != 5897]:
            d = (B - W[k]).dropna()
            y = d.groupby(d.index.year).agg(['mean', 'count']); y = y[y['count'] >= 200]['mean']
            base = y.loc[2003:2007]
            if len(base) >= 3:
                cols[k] = y - base.mean()
        T = pd.DataFrame(cols)
        res[f'{el}_{nome}'] = T.median(axis=1).where(T.notna().sum(axis=1) >= 3).round(2)
        res[f'{el}_n'] = T.notna().sum(axis=1)
R = pd.DataFrame(res).loc[2000:]; R.index.name = 'anno'
R.to_csv(out)
print(R.to_string())
