"""Massime, minime e medie giornaliere a passo ORARIO costante (solo letture al minuto :00) per Brera e per tutte le
stazioni ARPA di confronto trovate nelle cartelle indicate. Stesse regole di build_daily.py (versione _H):
stato = 'VA', valore > -100, timestamp duplicati tolti, giorno = (timestamp - 1 s) a mezzanotte (il timestamp e' la fine
dell'intervallo, ora solare), giorno valido solo con almeno 20 letture orarie.
uso: python -I giornalieri_H.py OUTCSV CARTELLA [CARTELLA ...]
  i file devono chiamarsi brera_5897_*.csv oppure sens_<idsensore>_*.csv
Scrive OUTCSV lungo: data, sensore, TX, TN, TG, n"""
import sys, os, glob, re
import pandas as pd
out, dirs = sys.argv[1], sys.argv[2:]
files = {}
for d in dirs:
    for p in sorted(glob.glob(os.path.join(d, '*.csv'))):
        b = os.path.basename(p)
        m = re.match(r'(?:brera_(5897)|sens_(\d+))_.*\.csv$', b)
        if not m or os.path.getsize(p) < 1000:
            continue
        files.setdefault(m.group(1) or m.group(2), []).append(p)
rows = []
for s, fs in sorted(files.items()):
    A = pd.concat([pd.read_csv(p, dtype={'stato': str}, usecols=['data', 'valore', 'stato']) for p in fs])
    A = A[(A.stato == 'VA') & (A.valore > -100)].copy()
    A['t'] = pd.to_datetime(A.data)
    A = A[A.t.dt.minute == 0].drop_duplicates('t')
    A['day'] = (A.t - pd.Timedelta('1s')).dt.floor('D')
    g = A.groupby('day').valore.agg(TX='max', TN='min', TG='mean', n='count')
    g = g[g.n >= 20].reset_index().rename(columns={'day': 'data'})
    g.insert(1, 'sensore', int(s))
    rows.append(g)
    print(s, len(fs), 'file', g.data.min().date(), '->', g.data.max().date(), len(g), 'giorni', flush=True)
R = pd.concat(rows, ignore_index=True)
R['TG'] = R.TG.round(3)
os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
R.to_csv(out, index=False)
