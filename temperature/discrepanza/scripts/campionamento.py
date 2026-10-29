"""Effetto del passo di campionamento ARPA (orario vs 10 minuti) su TX e TN giornalieri, sensore Brera 5897.
Nel periodo a 10 minuti si calcolano TX/TN usando tutti i valori e usando solo i valori allo scoccare dell'ora (:00),
cioe' come se il dato fosse orario. Differenza = errore dovuto al passo orario.
Trova anche la data in cui il dato passa da orario a 10 minuti.
uso: python -I campionamento.py RAW_ARPA_DIR OUTCSV"""
import sys, glob, pandas as pd
raw, out = sys.argv[1:3]
A = pd.concat([pd.read_csv(p, dtype={'stato': str}) for p in sorted(glob.glob(f'{raw}/brera_5897_*.csv'))])
A = A[(A.stato == 'VA') & (A.valore > -100)].copy(); A['t'] = pd.to_datetime(A.data); A = A.drop_duplicates('t')
first10 = A[A.t.dt.minute != 0].t.min(); print('primo dato a 10 minuti:', first10)
B = A[A.t >= first10.floor('D') + pd.Timedelta('1D')].copy()
B['day'] = (B.t - pd.Timedelta('1s')).dt.floor('D')
full = B.groupby('day').valore.agg(TX10='max', TN10='min', n='count')
h = B[B.t.dt.minute == 0].groupby('day').valore.agg(TXh='max', TNh='min', nh='count')
J = full.join(h); J = J[(J.n >= 140) & (J.nh >= 24)]
J['dTX'] = J.TXh - J.TX10; J['dTN'] = J.TNh - J.TN10
Y = J.groupby(J.index.year)[['dTX', 'dTN']].agg(['mean', 'count']).round(3)
Y.columns = ['_'.join(c) for c in Y.columns]; Y.index.name = 'anno'; Y.to_csv(out)
print(Y.to_string()); print('media', J[['dTX', 'dTN']].mean().round(3).to_dict())
