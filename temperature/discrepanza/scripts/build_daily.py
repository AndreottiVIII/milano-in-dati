"""Costruisce le serie giornaliere TX/TN/TG di tutte le fonti in un unico CSV lungo (data, fonte, TX, TN, TG, n).
uso: python -I build_daily.py RAWDIR OUTCSV
Fonti:
  MAUGERI   ECA&D non-blended SOUID 105248/105247/105249 (identica a GHCN-D ITE00100554)
  HOM       ECA&D homblend STAID 173 (Squintu et al. 2019)
  ECAD_BRERA ECA&D non-blended ARPA Brera SOUID 180713/180712 (TX14/TN13, 0-0 ora locale da orari)
  ECAD_MARCHE ECA&D non-blended ARPA Via Marche SOUID 180667 (solo TX)
  BRERA     ARPA sensore 5897 ricalcolato: solo stato VA, valore > -100; giorno = (timestamp - 1 s) in ora solare
            (il timestamp e' la fine dell'intervallo). Giorno valido solo se ha >= 20 ore orarie (o >= 120 valori a 10 min).
  BRERA24   come BRERA ma solo giorni con tutte le 24 ore (o 144 valori a 10 min)
  ARPA_<id> altri sensori ARPA Milano (tutti i file sens_<id>_*.csv), stesse regole di BRERA
  <nome>_H  per ogni serie ARPA: TX/TN/TG dai soli valori a minuto :00 (passo orario anche dopo il passaggio a 10 minuti)
  LINATE    NOAA GSOD 16080099999 (Milano Linate), MAX/MIN/TEMP in F convertiti in C, 9999.9 = mancante; giorno UTC
"""
import sys, os, io, glob
import pandas as pd, numpy as np
raw, out = sys.argv[1:3]
rows = []

def ecad(p):
    L = open(p, encoding='latin-1').read().splitlines()
    i = [k for k, l in enumerate(L) if l.strip().startswith(('STAID', 'SOUID'))][0]
    d = pd.read_csv(io.StringIO('\n'.join(L[i:])), skipinitialspace=True)
    d.columns = [c.strip() for c in d.columns]
    el = [c for c in d.columns if c in ('TX', 'TN', 'TG')][0]
    d['d'] = pd.to_datetime(d.DATE.astype(str), format='%Y%m%d')
    d = d[(d['Q_' + el] != 9) & (d[el] != -9999)]
    return d.set_index('d')[el] / 10

def add(name, tx=None, tn=None, tg=None, n=None):
    df = pd.DataFrame({'TX': tx, 'TN': tn, 'TG': tg})
    if n is not None: df['n'] = n
    df.index.name = 'data'; df['fonte'] = name
    rows.append(df.reset_index())

e = f'{raw}/ecad'
add('MAUGERI', ecad(f'{e}/nonblend_tx/TX_SOUID105248.txt'), ecad(f'{e}/nonblend_tn/TN_SOUID105247.txt'), ecad(f'{e}/nonblend_tg/TG_SOUID105249.txt'))
add('HOM', ecad(f'{e}/homblend_tx/TX_STAID000173.txt'), ecad(f'{e}/homblend_tn/TN_STAID000173.txt'), ecad(f'{e}/homblend_tg/TG_STAID000173.txt'))
add('ECAD_BRERA', ecad(f'{e}/nonblend_tx/TX_SOUID180713.txt'), ecad(f'{e}/nonblend_tn/TN_SOUID180712.txt'))
add('ECAD_MARCHE', ecad(f'{e}/nonblend_tx/TX_SOUID180667.txt'))

def arpa(files, name):
    A = pd.concat([pd.read_csv(p, dtype={'stato': str}) for p in files])
    A = A[(A.stato == 'VA') & (A.valore > -100)].copy()
    A['t'] = pd.to_datetime(A.data)
    A = A.drop_duplicates('t')
    A['day'] = (A.t - pd.Timedelta('1s')).dt.floor('D')
    A['tenmin'] = A.t.dt.minute != 0
    g = A.groupby('day').agg(TX=('valore', 'max'), TN=('valore', 'min'), TG=('valore', 'mean'), n=('valore', 'count'), m10=('tenmin', 'any'))
    full = np.where(g.m10, 144, 24); minok = np.where(g.m10, 120, 20)
    ok = g[g.n >= minok]; ok24 = g[g.n >= full]
    add(name, ok.TX, ok.TN, ok.TG, ok.n)
    if name == 'BRERA': add('BRERA24', ok24.TX, ok24.TN, ok24.TG, ok24.n)
    # versione _H: solo i valori allo scoccare dell'ora (passo orario costante per tutto il periodo)
    H = A[A.t.dt.minute == 0]
    h = H.groupby('day').agg(TX=('valore', 'max'), TN=('valore', 'min'), TG=('valore', 'mean'), n=('valore', 'count'))
    h = h[h.n >= 20]
    add(name + '_H', h.TX, h.TN, h.TG, h.n)

arpa(sorted(glob.glob(f'{raw}/arpa/brera_5897_*.csv')), 'BRERA')
sids = sorted({os.path.basename(p).split('_')[1] for p in glob.glob(f'{raw}/arpa_altre/sens_*.csv')})
for sid in sids:
    fs = [p for p in sorted(glob.glob(f'{raw}/arpa_altre/sens_{sid}_*.csv')) if os.path.getsize(p) > 1000]
    if fs: arpa(fs, f'ARPA_{sid}')

G = pd.concat([pd.read_csv(p, dtype=str) for p in sorted(glob.glob(f'{raw}/gsod_linate/*.csv'))])
G['d'] = pd.to_datetime(G.DATE)
f2c = lambda s: (pd.to_numeric(s, errors='coerce').where(lambda x: x < 9000) - 32) * 5 / 9
G = G.set_index('d')
add('LINATE', f2c(G.MAX).round(2), f2c(G.MIN).round(2), f2c(G.TEMP).round(2))

R = pd.concat(rows, ignore_index=True)
R = R[['data', 'fonte', 'TX', 'TN', 'TG', 'n']]
R.to_csv(out, index=False)
print(R.groupby('fonte').agg(da=('data', 'min'), a=('data', 'max'), giorni=('TX', 'count')).to_string())
