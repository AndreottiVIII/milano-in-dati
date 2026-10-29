"""Costruisce la serie giornaliera unica di Milano Brera dalle fonti grezze, secondo temperature/splice.json.

uso: python -I costruisci_serie.py RAWDIR SPLICE_JSON OUT_CSV
  RAWDIR      cartella temperature/raw
  SPLICE_JSON temperature/splice.json (quale fonte per quale intervallo, correzioni additive)
  OUT_CSV     temperature/serie/serie_unica.csv  (date,tmin,tmax,tmean,fonte,qflag)

Regole:
- Maugeri/GHCN-D: TMIN/TMAX in decimi di C (sentinella -9999 = mancante); qflag NOAA tenuti in colonna qflag;
  nel config si possono scartare i valori con certi qflag ("scarta_qflag").
- ARPA 5897: si scartano le righe con stato diverso da 'VA' e i valori <= -100 (sentinella -999).
  Giorno = (timestamp - 1 secondo) troncato a mezzanotte: il timestamp e' la FINE dell'intervallo (ora solare),
  quindi 00:00 appartiene al giorno prima.
  Un giorno e' valido solo se ha almeno ceil(frazione_minima * attese) letture valide; attese = 24 (dati orari, fino al
  2020-12-31) o 144 (ogni 10 minuti, dal 2021-01-01). Frazione di default 0,83 -> almeno 20/24 e 120/144.
  risoluzione 'native' = tutte le letture; 'hourly' = dal 2021 solo le letture al minuto :00 (stessa risoluzione
  oraria degli anni precedenti, massime meno alte).
- tmean = (tmin + tmax) / 2 per TUTTE le fonti (definizione unica attraverso la cucitura), solo se ci sono entrambe.
"""
import sys, os, glob, gzip, json, math
import numpy as np
import pandas as pd

raw, cfg_path, out_csv = sys.argv[1:4]
cfg = json.load(open(cfg_path, encoding='utf-8-sig'))


def carica_ghcnd(spec):
    p = os.path.join(raw, spec['file'])
    d = pd.read_csv(gzip.open(p, 'rt'), header=None,
                    names=['id', 'date', 'elem', 'val', 'm', 'q', 's', 't'], dtype={'q': str, 'm': str, 'date': str})
    d = d[d.elem.isin(['TMAX', 'TMIN'])].copy()
    d = d[d.val != -9999]
    scarta = set(spec.get('scarta_qflag', []))
    if scarta:
        d = d[~d.q.isin(scarta)]
    d['date'] = pd.to_datetime(d.date, format='%Y%m%d')
    d['val'] = d.val / 10.0
    v = d.pivot(index='date', columns='elem', values='val').rename(columns={'TMAX': 'tmax', 'TMIN': 'tmin'})
    q = d.assign(q=d.q.fillna('')).pivot(index='date', columns='elem', values='q').fillna('')
    v['qflag'] = (q.get('TMIN', '').astype(str).replace('', '-') + q.get('TMAX', '').astype(str).replace('', '-'))
    v['qflag'] = v['qflag'].where(v['qflag'] != '--', '')
    return v[['tmin', 'tmax', 'qflag']]


def carica_arpa(spec):
    files = sorted(glob.glob(os.path.join(raw, spec['file'])))
    A = pd.concat([pd.read_csv(f, dtype={'stato': str}, usecols=['data', 'valore', 'stato']) for f in files])
    A = A[(A.stato == 'VA') & (A.valore > -100)].copy()
    A['t'] = pd.to_datetime(A.data)
    if spec.get('risoluzione', 'native') == 'hourly':
        A = A[A.t.dt.minute == 0]
    A['day'] = (A.t - pd.Timedelta('1s')).dt.floor('D')
    frac = spec.get('frazione_minima_letture_valide', 0.83)
    g = A.groupby('day').valore.agg(['count', 'min', 'max'])
    cut = pd.Timestamp('2021-01-01')
    hourly = spec.get('risoluzione', 'native') == 'hourly'
    attese = np.where((g.index < cut) | hourly, 24, 144)
    minimo = np.ceil(frac * attese - 1e-9)
    g = g[g['count'] >= minimo]
    out = pd.DataFrame({'tmin': g['min'], 'tmax': g['max'], 'qflag': ''}, index=g.index)
    out.index.name = 'date'
    return out


def carica_continua(spec):
    """Serie gia' cucita da discrepanza/scripts/giunzione.py (data,TX,TN,TG,fonte_usata,nota): la fonte resta quella
    del file; i qflag NOAA si riprendono dal file GHCN-D indicato in 'qflag_da_ghcnd' per i giorni MAUGERI."""
    d = pd.read_csv(os.path.join(raw, spec['file']), parse_dates=['data']).set_index('data')
    out = pd.DataFrame({'tmin': d.TN, 'tmax': d.TX, 'fonte': d.fonte_usata, 'qflag': ''}, index=d.index)
    out.index.name = 'date'
    if spec.get('qflag_da_ghcnd'):
        q = carica_ghcnd({'file': spec['qflag_da_ghcnd']}).qflag
        m = out.fonte == 'MAUGERI'
        out.loc[m, 'qflag'] = q.reindex(out.index[m]).fillna('').values
    return out


tipi = {'ghcnd': carica_ghcnd, 'arpa': carica_arpa, 'continua': carica_continua}
fonti = {k: tipi[s['tipo']](s) for k, s in cfg['fonti'].items()}

pezzi = []
for seg in cfg['segmenti']:
    f = fonti[seg['fonte']].copy()
    da = pd.Timestamp(seg['da']); a = pd.Timestamp(seg['a']) if seg.get('a') else f.index.max()
    f = f[(f.index >= da) & (f.index <= a)]
    adj = seg.get('adjust', {})
    f['tmin'] = f.tmin + adj.get('tmin', 0.0)
    f['tmax'] = f.tmax + adj.get('tmax', 0.0)
    if 'fonte' not in f:
        f['fonte'] = seg['fonte']
    pezzi.append(f)
S = pd.concat(pezzi)
S = S[~S.index.duplicated(keep='first')].sort_index()   # priorita' = ordine dei segmenti
S = S[S.tmin.notna() | S.tmax.notna()]
S['tmean'] = (S.tmin + S.tmax) / 2.0
S = S[['tmin', 'tmax', 'tmean', 'fonte', 'qflag']]
os.makedirs(os.path.dirname(out_csv), exist_ok=True)
S.round(2).to_csv(out_csv, index_label='date', float_format='%.2f', lineterminator='\n')

print('righe:', len(S), 'dal', S.index.min().date(), 'al', S.index.max().date(), '| stato cucitura:', cfg.get('stato'))
print(S.fonte.value_counts().to_string())
print('giorni con tmin e tmax:', int(S.tmean.notna().sum()), '| solo uno dei due:', int(S.tmean.isna().sum()))
print('tmax<tmin:', int((S.tmax < S.tmin).sum()))
