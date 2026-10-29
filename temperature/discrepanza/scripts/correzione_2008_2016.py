"""Stima la correzione (da AGGIUNGERE a Brera) per il periodo anomalo tra due rotture, mese del calendario per mese,
contro piu' stazioni vicine, con incertezza.
uso: python -I correzione_2008_2016.py GIORNALIERI_H ROTTURE_CSV OUTDIR DA A RIF_DA RIF_A [DOPO_A [PRINCIPALE]]
  GIORNALIERI_H  out_2008/giornalieri_H.csv
  ROTTURE_CSV    out_2008/rotture.csv (da rotture_brera.py): serve a riconoscere le vicine che saltano da sole
  DA, A          periodo anomalo di Brera (primo e ultimo giorno), es. 2007-12-11 2016-09-30
  RIF_DA, RIF_A  periodo di riferimento PRIMA (Brera "buona"), es. 2002-12-11 2007-12-06
  DOPO_A         (facoltativo) fine del riferimento DOPO (dal giorno dopo A)
  PRINCIPALE     variante da cui esce la proposta: prima | dopo | prima+dopo (default prima+dopo se c'e' DOPO_A)

Per ogni vicina k e ogni mese del calendario m:
   scarto_k(m) = media(Brera - k nei mesi m del riferimento) - media(Brera - k nei mesi m del periodo anomalo)
 (media delle medie mensili, mese valido con almeno 20 giorni in comune: ogni anno pesa uguale).
Correzione(m) = MEDIANA degli scarto_k(m) sulle vicine. Annua = media dei 12 mesi.
Incertezza: 2000 ricampionamenti (bootstrap): si ripescano a caso le vicine e, per ciascuna, gli anni del riferimento
e del periodo anomalo; intervallo 5-95%.
Proposta finale: correzione mensile lisciata (media mobile circolare su 3 mesi), perche' i singoli mesi sono rumorosi.
Varianti scritte per confronto: rif = prima / dopo / prima+dopo; vicine = tutte / senza quelle che saltano da sole
(salto >= 0,4 C nella serie 'vicina meno mediana delle altre' dentro la finestra usata).
Scrive OUTDIR/correzione_proposta.csv, OUTDIR/correzione_varianti.csv, OUTDIR/correzione_per_vicina.csv"""
import sys, os
import numpy as np, pandas as pd

f, rotf, od, DA, A, RDA, RA = sys.argv[1:8]
DOPO = sys.argv[8] if len(sys.argv) > 8 else None
T0 = 5897
rng = np.random.default_rng(29102026)
D = pd.read_csv(f, parse_dates=['data'])
ROT = pd.read_csv(rotf)
DA, A, RDA, RA = map(pd.Timestamp, (DA, A, RDA, RA))
DOPO = pd.Timestamp(DOPO) if DOPO else None
PRINC = sys.argv[9] if len(sys.argv) > 9 else ('prima+dopo' if DOPO is not None else 'prima')


def mensili(d, a, b):
    d = d[(d.index >= a) & (d.index <= b)]
    g = d.groupby([d.index.year, d.index.month]).agg(['mean', 'count'])
    g = g[g['count'] >= 20]['mean']
    g.index.names = ['y', 'm']
    return g


def sbalzate(el, a, b):
    """vicine con un salto proprio (>= 0,4 C) tra a e b nella serie 'vicina - mediana delle altre vicine'"""
    r = ROT[(ROT.elemento == el) & ROT.serie.str.contains('mediana altre')].copy()
    r['t'] = pd.PeriodIndex(r.mese, freq='M').to_timestamp()
    r = r[(r.t >= a) & (r.t <= b) & (r.salto.abs() >= 0.4)]
    return sorted({int(s.split()[1]) for s in r.serie})


def stima(W, el, rif, vicine, nboot=2000):
    """rif: lista di (da, a). Ritorna (tabella per vicina, mediana per mese, bootstrap per mese)."""
    per = {}
    for k in vicine:
        d = (W[T0] - W[k]).dropna()
        s = mensili(d, DA, A).unstack('m').reindex(columns=range(1, 13))       # righe = anni, colonne = mesi
        r = pd.concat([mensili(d, a, b) for a, b in rif])
        r = r.groupby(level=['y', 'm']).mean().unstack('m').reindex(columns=range(1, 13))
        if len(s) < 3 or len(r) < 2:
            continue
        per[k] = (r.values, s.values)
    if len(per) < 3:
        return None
    with np.errstate(all='ignore'):
        import warnings; warnings.simplefilter('ignore')
        tab = pd.DataFrame({k: np.nanmean(r, 0) - np.nanmean(s, 0) for k, (r, s) in per.items()}, index=range(1, 13))
        med = tab.median(axis=1)
        ks = list(per)
        boot = np.full((nboot, 12), np.nan)
        for i in range(nboot):
            cols = []
            for k in rng.choice(ks, len(ks), replace=True):
                r, s = per[k]
                cols.append(np.nanmean(r[rng.integers(0, len(r), len(r))], 0) - np.nanmean(s[rng.integers(0, len(s), len(s))], 0))
            boot[i] = np.nanmedian(np.array(cols), axis=0)
    return tab, med, boot


def liscia(v):
    v = np.asarray(v, float)
    return (np.roll(v, 1) + v + np.roll(v, -1)) / 3


varianti, proposta, pervic = [], [], []
rif_opts = {'prima': [(RDA, RA)]}
if DOPO is not None:
    rif_opts['dopo'] = [(A + pd.Timedelta(days=1), DOPO)]
    rif_opts['prima+dopo'] = [(RDA, RA), (A + pd.Timedelta(days=1), DOPO)]
for el in ['TX', 'TN']:
    W = D.pivot(index='data', columns='sensore', values=el)
    tutte = [c for c in W.columns if c != T0]
    for rn, rif in rif_opts.items():
        lo, hi = min([DA] + [a for a, b in rif]), max([A] + [b for a, b in rif])   # finestra = riferimento + periodo anomalo
        esc = sbalzate(el, lo, hi)
        for vn, vic in [('tutte', tutte), ('senza_sbalzate', [k for k in tutte if k not in esc])]:
            res = stima(W, el, rif, vic, nboot=2000)
            if res is None:
                continue
            tab, med, boot = res
            ann_b = np.nanmean(boot, axis=1)
            varianti.append({'elemento': el, 'riferimento': rn, 'principale': rn == PRINC and vn == 'tutte', 'vicine': vn, 'n_vicine': tab.shape[1],
                             'vicine_usate': ' '.join(map(str, tab.columns)), 'escluse': ' '.join(map(str, esc)) if vn != 'tutte' else '',
                             'correzione_annua': round(float(med.mean()), 2),
                             'p05': round(float(np.nanpercentile(ann_b, 5)), 2), 'p95': round(float(np.nanpercentile(ann_b, 95)), 2),
                             **{f'm{m:02d}': round(float(med[m]), 2) for m in range(1, 13)}})
            if rn == PRINC and vn == 'tutte':
                sm = liscia(med.values)
                bsm = np.array([liscia(b) for b in boot])
                for m in range(1, 13):
                    proposta.append({'elemento': el, 'mese': m, 'correzione_grezza': round(float(med[m]), 2),
                                     'correzione_lisciata': round(float(sm[m - 1]), 2),
                                     'p05': round(float(np.nanpercentile(bsm[:, m - 1], 5)), 2),
                                     'p95': round(float(np.nanpercentile(bsm[:, m - 1], 95)), 2),
                                     'n_vicine': int(tab.loc[m].notna().sum())})
                for k in tab.columns:
                    pervic.append({'elemento': el, 'vicina': k, 'scarto_annuo': round(float(tab[k].mean()), 2),
                                   **{f'm{m:02d}': round(float(tab.loc[m, k]), 2) for m in range(1, 13)}})
os.makedirs(od, exist_ok=True)
V = pd.DataFrame(varianti); V.to_csv(f'{od}/correzione_varianti.csv', index=False)
P = pd.DataFrame(proposta); P.to_csv(f'{od}/correzione_proposta.csv', index=False)
Q = pd.DataFrame(pervic); Q.to_csv(f'{od}/correzione_per_vicina.csv', index=False)
pd.set_option('display.width', 250)
print(V.to_string()); print(P.to_string()); print(Q.to_string())
