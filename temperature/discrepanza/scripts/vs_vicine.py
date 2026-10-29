"""Confronto con un riferimento composto dalle stazioni ARPA vicine (Juvara 5909, Marche 5911, Zavattari 5920):
riferimento del giorno = media delle stazioni disponibili quel giorno, solo se ce ne sono almeno 2.
uso: python -I vs_vicine.py GIORNALIERI_CSV OUTDIR [SUFFISSO ANNO_DA ANNO_A]
  SUFFISSO: '' (default, serie ARPA con tutti i valori) oppure '_H' (serie ARPA dai soli valori orari :00,
  campionamento costante anche dopo il 2014). Con SUFFISSO i file escono come *_vs_VICINE_H_<da>-<a>.csv.
Scrive:
  OUTDIR/diff_annue_vs_VICINE.csv   (anno; <FONTE>_<EL> media fonte-riferimento; _n giorni)
  OUTDIR/diff_mensili_vs_VICINE.csv (anno-mese; idem, 1988-2010)
  OUTDIR/diff_giornaliere_vs_VICINE.csv (data; MAUGERI, BRERA, LINATE meno riferimento, TX e TN)"""
import sys, os, pandas as pd
f, od = sys.argv[1:3]
suf = sys.argv[3] if len(sys.argv) > 3 else ''
a, b = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1988, 2010)
tag = 'VICINE' if len(sys.argv) <= 3 else f'VICINE{suf}_{a}-{b}'
D = pd.read_csv(f, parse_dates=['data'])
D = D[(D.data.dt.year >= a) & (D.data.dt.year <= b)]
if suf:  # usa le versioni _H delle serie ARPA con il nome base
    D = D[~D.fonte.str.startswith(('ARPA_', 'BRERA')) | D.fonte.str.endswith(suf)]
    D.loc[D.fonte.str.endswith(suf), 'fonte'] = D.fonte.str[:-len(suf)]
W = D.pivot_table(index='data', columns='fonte', values=['TX', 'TN', 'TG'])
nb = ['ARPA_5909', 'ARPA_5911', 'ARPA_5920']
srcs = ['MAUGERI', 'HOM', 'BRERA', 'LINATE', 'ARPA_5909', 'ARPA_5911', 'ARPA_5920', 'ARPA_2001', 'ARPA_2063']
ann, mon, day = {}, {}, {}
for el in ['TX', 'TN', 'TG']:
    R = W[el][nb]
    ref = R.mean(axis=1).where(R.notna().sum(axis=1) >= 2)
    for s in srcs:
        if s not in W[el]: continue
        if s in nb:  # per le vicine: confronto con la media delle ALTRE due (per non confrontare con se stessa)
            o = W[el][[x for x in nb if x != s]]
            r = o.mean(axis=1).where(o.notna().sum(axis=1) == 2)
        else:
            r = ref
        d = (W[el][s] - r).dropna()
        ann[f'{s}_{el}'] = d.groupby(d.index.year).mean().round(2)
        ann[f'{s}_{el}_n'] = d.groupby(d.index.year).count()
        mon[f'{s}_{el}'] = d.groupby(d.index.to_period('M')).mean().round(2)
        if s in ('MAUGERI', 'BRERA', 'LINATE') and el != 'TG': day[f'{s}_{el}'] = d.round(2)
A = pd.DataFrame(ann); A.index.name = 'anno'; A.to_csv(f'{od}/diff_annue_vs_{tag}.csv')
M = pd.DataFrame(mon); M.index.name = 'mese'; M.to_csv(f'{od}/diff_mensili_vs_{tag}.csv')
G = pd.DataFrame(day); G.index.name = 'data'; G.to_csv(f'{od}/diff_giornaliere_vs_{tag}.csv')
for el in ['TX', 'TN']:
    print(A[[c for c in A.columns if c.endswith('_' + el)]].to_string())
