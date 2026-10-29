"""Calcola gli scarti per la giunzione e costruisce la serie continua 1763-oggi seguendo le regole raccomandate.
uso: python -I giunzione.py GIORNALIERI_CSV OUTDIR
Legge out/giornalieri_tutte_fonti.csv (da build_daily.py). Scrive:
  OUTDIR/giunzione_scarti.csv        scarti medi (per elemento e per mese) con due metodi di calcolo
  OUTDIR/regole_giunzione.csv        la tabella delle regole (da_data, a_data, fonte, correzione per elemento)
  OUTDIR/serie_continua_1763_oggi.csv  data, TX, TN, TG, fonte_usata, nota
Regole (vedi RAPPORTO.md):
  1) 1763-01-01 .. 1986-11-14  MAUGERI cosi' com'e'
  2) 1986-11-15 .. 1987-09-15  LINATE (GSOD) + scarto mensile MAUGERI-LINATE (calcolato 1982-01..1986-06 e 1988-01..1991-12)
                               (periodo del trasloco 1987: Maugeri anomala). Se Linate manca: MAUGERI con nota 'dubbio'.
  3) 1987-09-16 .. 1994-12-31  MAUGERI cosi' com'e'
  4) 1995-01-01 .. oggi        ARPA Brera 5897, versione a passo orario costante (BRERA_H) + scarto mensile
                               MAUGERI-BRERA_H calcolato sui giorni comuni 1992-01-01..1994-12-31.
                               Giorni mancanti di Brera: media delle vicine ARPA (5909, 5911, 5920, versioni _H)
                               + differenza media Brera-vicine dello stesso anno, poi + scarto; nota 'riempito'.
"""
import sys, pandas as pd, numpy as np
f, od = sys.argv[1:3]
D = pd.read_csv(f, parse_dates=['data'])
W = D.pivot_table(index='data', columns='fonte', values=['TX', 'TN', 'TG'])
EL = ['TX', 'TN', 'TG']

def monthly_offset(a, b, mask):
    d = (a - b)[mask].dropna()
    return d.groupby(d.index.month).mean(), d.mean(), len(d)

idx = W.index
rows = []
off_brera, off_linate = {}, {}
nb = ['ARPA_5909_H', 'ARPA_5911_H', 'ARPA_5920_H']
for el in EL:
    m = (idx >= '1992-01-01') & (idx <= '1994-12-31')
    mo, tot, n = monthly_offset(W[el]['MAUGERI'], W[el]['BRERA_H'], m)
    rows.append({'elemento': el, 'metodo': 'A diretto MAUGERI-BRERA_H 1992-1994', 'scarto_medio': round(tot, 2), 'giorni': n,
                 **{f'm{k:02d}': round(v, 2) for k, v in mo.items()}})
    # metodo B: passando dalle vicine (Maugeri-vicine 1989-1994) - (Brera_H-vicine 1995-2007)
    R = W[el][nb]; ref = R.mean(axis=1).where(R.notna().sum(axis=1) >= 2)
    dm = (W[el]['MAUGERI'] - ref)[(idx >= '1992-01-01') & (idx <= '1994-12-31')].dropna()
    db = (W[el]['BRERA_H'] - ref)[(idx >= '1995-01-01') & (idx <= '2007-12-31')].dropna()
    off_brera[el] = pd.Series({k: dm.groupby(dm.index.month).mean()[k] - db.groupby(db.index.month).mean()[k] for k in range(1, 13)})
    rows.append({'elemento': el, 'metodo': 'B via vicine (MAU-vic 1992-94) - (BRERA_H-vic 1995-2007)',
                 'scarto_medio': round(dm.mean() - db.mean(), 2), 'giorni': len(dm),
                 **{f'm{k:02d}': round(dm.groupby(dm.index.month).mean()[k] - db.groupby(db.index.month).mean()[k], 2) for k in range(1, 13)}})
    m2 = ((idx >= '1982-01-01') & (idx <= '1986-06-30')) | ((idx >= '1988-01-01') & (idx <= '1991-12-31'))
    mo2, tot2, n2 = monthly_offset(W[el]['MAUGERI'], W[el]['LINATE'], m2)
    off_linate[el] = mo2
    rows.append({'elemento': el, 'metodo': 'C MAUGERI-LINATE 1982-86/1988-91 (per il buco 1986-87)', 'scarto_medio': round(tot2, 2), 'giorni': n2,
                 **{f'm{k:02d}': round(v, 2) for k, v in mo2.items()}})
S = pd.DataFrame(rows); S.to_csv(f'{od}/giunzione_scarti.csv', index=False)
print(S[['elemento', 'metodo', 'scarto_medio', 'giorni']].to_string())

regole = pd.DataFrame([
    ['1763-01-01', '1986-11-14', 'MAUGERI', 'nessuna', 'ECA&D SOUID 105248/105247/105249'],
    ['1986-11-15', '1987-09-15', 'LINATE', 'scarto mensile metodo C', 'periodo del trasloco: Maugeri anomala (+3 °C TX)'],
    ['1987-09-16', '1994-12-31', 'MAUGERI', 'nessuna', ''],
    ['1995-01-01', 'oggi', 'BRERA_H', 'scarto mensile metodo B', 'ARPA 5897 solo valori :00; buchi riempiti da vicine ARPA'],
], columns=['da_data', 'a_data', 'fonte', 'correzione', 'nota'])
regole.to_csv(f'{od}/regole_giunzione.csv', index=False)

end = W.index.max()
out = pd.DataFrame(index=pd.date_range('1763-01-01', end), columns=EL + ['fonte_usata', 'nota'], dtype=object)
def put(a, b, src, offs, nota=''):
    r = pd.date_range(a, b)
    for el in EL:
        v = W[el][src].reindex(r) if src in W[el] else pd.Series(np.nan, index=r)
        if offs is not None: v = v + np.array([offs[el].get(d.month, np.nan) for d in r])
        out.loc[r, el] = v.round(2).values
    out.loc[r, 'fonte_usata'] = src; out.loc[r, 'nota'] = nota
put('1763-01-01', '1986-11-14', 'MAUGERI', None)
put('1986-11-15', '1987-09-15', 'LINATE', off_linate, 'Linate + scarto (trasloco 1987)')
miss = out.loc['1986-11-15':'1987-09-15', 'TX'].isna()
if miss.any():
    r = miss[miss].index
    for el in EL: out.loc[r, el] = W[el]['MAUGERI'].reindex(r).values
    out.loc[r, 'fonte_usata'] = 'MAUGERI'; out.loc[r, 'nota'] = 'dubbio (trasloco 1987, Linate mancante)'
put('1987-09-16', '1994-12-31', 'MAUGERI', None)
put('1995-01-01', end, 'BRERA_H', off_brera)
# riempimento buchi di Brera dal 1995
r = pd.date_range('1995-01-01', end)
gap = out.loc[r, 'TX'].isna()
filled = 0
for el in EL:
    R = W[el][nb].reindex(r); ref = R.mean(axis=1).where(R.notna().sum(axis=1) >= 2)
    dif = (W[el]['BRERA_H'].reindex(r) - ref)
    ann = dif.groupby(dif.index.year).transform('mean')
    est = ref + ann + np.array([off_brera[el].get(d.month, np.nan) for d in r])
    g = gap & out.loc[r, el].isna() & est.notna()
    out.loc[g[g].index, el] = est[g].round(2).values
gi = gap & out.loc[r, 'TX'].notna()
out.loc[gi[gi].index, 'fonte_usata'] = 'VICINE_ARPA'; out.loc[gi[gi].index, 'nota'] = 'riempito (media vicine + scarto)'
out.index.name = 'data'
out.to_csv(f'{od}/serie_continua_1763_oggi.csv')
print('giorni riempiti dalle vicine:', int(gi.sum()), '| giorni ancora vuoti dal 1995:', int(out.loc[r, 'TX'].isna().sum()))
print(out.fonte_usata.value_counts().to_string())
a = out.copy(); a['TX'] = pd.to_numeric(a.TX); a['TN'] = pd.to_numeric(a.TN)
y = a.groupby(a.index.year)[['TX', 'TN']].mean().round(2)
print(y.loc[1985:2025].to_string())
