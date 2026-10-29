"""Differenze annue (media giornaliera, solo giorni in comune) di ogni fonte rispetto a un riferimento.
uso: python -I diff_annual.py GIORNALIERI_CSV RIFERIMENTO ANNO_DA ANNO_A OUTCSV
Esempio: python -I diff_annual.py out/giornalieri_tutte_fonti.csv LINATE 1985 2012 out/diff_annue_vs_LINATE.csv
Output: una riga per anno; colonne <FONTE>_<EL> = media(fonte - riferimento) in gradi C; <FONTE>_<EL>_n = giorni usati.
Anni con meno di 200 giorni in comune: valore lasciato ma da leggere con cautela (colonna _n)."""
import sys, pandas as pd
f, ref, a, b, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
D = pd.read_csv(f, parse_dates=['data'])
D = D[(D.data.dt.year >= a) & (D.data.dt.year <= b)]
W = D.pivot_table(index='data', columns='fonte', values=['TX', 'TN', 'TG'])
res = {}
for el in ['TX', 'TN', 'TG']:
    if (el, ref) not in W: continue
    r = W[(el, ref)]
    for src in sorted(set(D.fonte)):
        if src == ref or (el, src) not in W: continue
        d = (W[(el, src)] - r).dropna()
        if len(d) == 0: continue
        g = d.groupby(d.index.year)
        res[f'{src}_{el}'] = g.mean().round(2)
        res[f'{src}_{el}_n'] = g.count()
T = pd.DataFrame(res); T.index.name = 'anno'
T.to_csv(out)
show = [c for c in T.columns if not c.endswith('_n') and c.endswith('_TX')]
print(T[show].to_string())
show = [c for c in T.columns if not c.endswith('_n') and c.endswith('_TN')]
print(T[show].to_string())
