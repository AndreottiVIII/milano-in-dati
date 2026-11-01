"""Fase 1 - Morti giorno per giorno. Legge il CSV ISTAT (decessi comunali giornalieri, residenza) e produce
una tabella lunga per Milano (015146), Lombardia (REG 03), Italia: scope, data, cl_eta, M, F, T.
Le righe con zero decessi non ci sono (come nel file ISTAT, NOTA 1). 'n.d.' = non disponibile (2026 dopo il 30/6) -> escluso.
Uso: python -I -X utf8 build.py <csv ISTAT assoluto> <cartella pulito assoluta> [nome file output]"""
import sys, os, json
import numpy as np, pandas as pd

src, outdir = sys.argv[1], sys.argv[2]
outname = sys.argv[3] if len(sys.argv) > 3 else 'decessi_giorno_eta_sesso.csv'
os.makedirs(outdir, exist_ok=True)
hdr = pd.read_csv(src, encoding='latin-1', nrows=0).columns
years = sorted(2000 + int(c[2:]) for c in hdr if c.startswith('T_'))
cols = [f'{s}_{str(y)[2:]}' for s in 'MFT' for y in years]

acc = {'Milano': [], 'Lombardia': [], 'Italia': []}
nrows = 0
chunks = pd.read_csv(src, encoding='latin-1', dtype=str, na_values=['n.d.'], keep_default_na=False, chunksize=500_000)
for ch in chunks:
    nrows += len(ch)
    for c in cols:
        ch[c] = pd.to_numeric(ch[c], errors='coerce')
    ch['CL_ETA'] = ch['CL_ETA'].astype(int)
    for scope, sub in (('Milano', ch[ch.COD_PROVCOM == '015146']),
                       ('Lombardia', ch[ch.REG == '03']),
                       ('Italia', ch)):
        if len(sub):
            acc[scope].append(sub.groupby(['GE', 'CL_ETA'])[cols].sum(min_count=1))
print('righe lette', nrows)

parts = []
for scope, lst in acc.items():
    g = pd.concat(lst).groupby(level=[0, 1]).sum(min_count=1)
    g = g.reset_index()
    for y in years:
        yy = str(y)[2:]
        sub = g[['GE', 'CL_ETA', f'M_{yy}', f'F_{yy}', f'T_{yy}']].copy()
        sub.columns = ['GE', 'cl_eta', 'M', 'F', 'T']
        sub = sub.dropna(subset=['T'])
        sub = sub[sub['T'] > 0]
        sub['anno'] = y
        sub['scope'] = scope
        parts.append(sub)
L = pd.concat(parts)
# data valida: scarta 29 febbraio degli anni non bisestili
L['data'] = pd.to_datetime(L.anno.astype(str) + L.GE, format='%Y%m%d', errors='coerce')
bad = L[L.data.isna()]
print('righe con data non valida (29/2 in anni non bisestili) con T>0:', len(bad), bad['T'].sum())
L = L.dropna(subset=['data'])
for c in ('M', 'F', 'T'):
    L[c] = L[c].astype(int)
L = L[['scope', 'data', 'cl_eta', 'M', 'F', 'T']].sort_values(['scope', 'data', 'cl_eta'])
L.to_csv(os.path.join(outdir, outname), index=False)
last = L[L.scope == 'Italia'].data.max()
print('ultimo giorno con dati (Italia):', last.date(), 'righe', len(L))
chk = {'righe_lette': nrows, 'ultimo_giorno_italia': str(last.date()), 'righe_output': int(len(L))}
for s in ('Milano', 'Lombardia', 'Italia'):
    chk[f'totale_{s}'] = int(L[L.scope == s]['T'].sum())
    # controllo M+F = T
    x = L[L.scope == s]
    chk[f'righe_M+F!=T_{s}'] = int((x.M + x.F != x['T']).sum())
json.dump(chk, open(os.path.join(outdir, outname.replace('.csv', '_controlli.json')), 'w'), indent=1)
print(chk)
