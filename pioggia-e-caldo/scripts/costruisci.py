"""Fase 1 - pulizia: dai file grezzi ARPA (raw/arpa/<dataset>/<T|P>_<idsensore>.csv) costruisce
  pulito/intermedi/T_orario.parquet   (idsensore, ora, t)           temperatura alle ore :00 (valori validi)
  pulito/intermedi/P_orario.parquet   (idsensore, ora, mm, n_ok)    pioggia oraria (ora solare, somma delle 6 letture da 10' o valore orario)
  pulito/intermedi/P_10min.parquet    (idsensore, ora, mm)          pioggia a 10 minuti (solo dal 2011)
  pulito/qualita_sensori.csv          per sensore: righe, validi, -999, stato diverso da VA, fuori soglia, buchi, passo
uso: python -I -X utf8 costruisci.py <cartella pioggia-e-caldo assoluta>
Orari: "ora solare" (CET fisso, niente ora legale), il valore e' riferito all'osservazione fino all'orario indicato (descrizione ARPA).
Validi: stato == 'VA' e valore > -900. Soglie: T tra -35 e 48 gradi; pioggia 0..100 mm in 10' e 0..250 mm in 1 h (fuori soglia -> scartato e contato)."""
import sys, os, glob
import numpy as np, pandas as pd
base = sys.argv[1]
sel = pd.read_csv(os.path.join(base, 'pulito', 'sensori_selezionati.csv'), dtype=str)
rawd = os.path.join(base, 'raw', 'arpa')
outd = os.path.join(base, 'pulito', 'intermedi'); os.makedirs(outd, exist_ok=True)
ORDER = ['6eu4-4tja', 'e7r2-7m84', 'd4kj-kbpj', '2kar-pnuk', 'w9wd-u6jh', 'pstb-pga6', '647i-nhxk']
Tl, Pl, P10l, Q = [], [], [], []
for _, s in sel.iterrows():
    k = 'T' if s.tipologia == 'Temperatura' else 'P'
    parts = []
    for ds in ORDER:
        fn = os.path.join(rawd, ds, f'{k}_{s.idsensore}.csv')
        if os.path.exists(fn) and os.path.getsize(fn) > 60:
            # il dataset 'mese in corso' (647i-nhxk) ha 5 campi (con idoperatore) ma la richiesta a gruppi li scriveva con intestazione a 4:
            # si leggono quindi i nomi dal numero di campi della prima riga di dati, non dall'intestazione
            with open(fn, encoding='utf-8') as fh:
                fh.readline(); nf = len(fh.readline().split(','))
            names = ['idsensore', 'data', 'valore', 'stato'] if nf == 4 else ['idsensore', 'data', 'valore', 'idoperatore', 'stato']
            d = pd.read_csv(fn, skiprows=1, header=None, names=names, dtype={'idsensore': str, 'stato': str}); d['ds'] = ds; parts.append(d)
    if not parts: continue
    d = pd.concat(parts, ignore_index=True)
    d['ora'] = pd.to_datetime(d['data'])
    n0 = len(d)
    d = d.sort_values('ora', kind='stable').drop_duplicates('ora', keep='first')
    ndup = n0 - len(d)
    m999 = int((d.valore <= -900).sum()); nstato = int(((d.stato != 'VA') & (d.valore > -900)).sum())
    ok = (d.stato == 'VA') & (d.valore > -900)
    lo, hi = (-35, 48) if k == 'T' else (0, 100)
    fuori = int((ok & ((d.valore < lo) | (d.valore > hi))).sum())
    ok &= (d.valore >= lo) & (d.valore <= hi)
    v = d[ok]
    rec = dict(idsensore=s.idsensore, tipologia=s.tipologia, nomestazione=s.nomestazione, righe=n0, duplicati=ndup,
               meno999=m999, stato_non_VA=nstato, fuori_soglia=fuori, validi=int(ok.sum()),
               primo=str(d.ora.min()), ultimo=str(d.ora.max()))
    if k == 'T':
        h = v[v.ora.dt.minute == 0][['ora', 'valore']].rename(columns={'valore': 't'}); h.insert(0, 'idsensore', s.idsensore)
        Tl.append(h); rec['ore_in_punto'] = len(h)
    else:
        # 10 minuti (dopo il 2011 il passo e' 10')
        step = d.ora.diff().dt.total_seconds().div(60)
        rec['passo_10min_righe'] = int((step == 10).sum()); rec['passo_60min_righe'] = int((step == 60).sum())
        # orario: ora t = somma dei valori con ora in (t-60', t]; per i dati orari e' il valore stesso
        vv = v[['ora', 'valore']].copy()
        vv['h'] = vv.ora.dt.ceil('h')            # 00:10..01:00 -> 01:00 ; 01:00 -> 01:00
        g = vv.groupby('h').agg(mm=('valore', 'sum'), n=('valore', 'size'))
        # il passo del periodo: dove i dati sono orari (<2011) n=1 e basta; dove sono a 10' servono 6 letture
        # se in un'ora esiste almeno una lettura con minuto != 0 allora l'ora e' a 10'
        has_sub = vv.assign(sub=(vv.ora.dt.minute != 0)).groupby('h')['sub'].max()
        need = np.where(has_sub.reindex(g.index).values, 6, 1)
        g['ok'] = g.n >= need
        g['n_ok'] = g.n
        g = g[g.ok]
        ph = g[['mm', 'n_ok']].reset_index().rename(columns={'h': 'ora'}); ph.insert(0, 'idsensore', s.idsensore)
        ph = ph[ph.mm <= 250]
        Pl.append(ph); rec['ore_valide'] = len(ph)
        sub = v[v.ora >= '2011-01-01'][['ora', 'valore']].rename(columns={'valore': 'mm'}); sub.insert(0, 'idsensore', s.idsensore)
        P10l.append(sub)
    Q.append(rec)
    print(k, s.idsensore, s.nomestazione, rec['righe'], rec['validi'], flush=True)
pd.concat(Tl).to_parquet(os.path.join(outd, 'T_orario.parquet'), index=False)
pd.concat(Pl).to_parquet(os.path.join(outd, 'P_orario.parquet'), index=False)
pd.concat(P10l).to_parquet(os.path.join(outd, 'P_10min.parquet'), index=False)
pd.DataFrame(Q).to_csv(os.path.join(base, 'pulito', 'qualita_sensori.csv'), index=False)
print('FATTO')
