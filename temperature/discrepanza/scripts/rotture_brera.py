"""Cerca i "salti" (rotture) di Brera rispetto alle stazioni vicine, separatamente per massime (TX) e minime (TN).
uso: python -I rotture_brera.py GIORNALIERI_H OUTDIR [ANNO_DA ANNO_A]
  GIORNALIERI_H  out_2008/giornalieri_H.csv (da giornalieri_H.py: data, sensore, TX, TN, TG, n)
  default 1995-2026

Metodo (in breve; spiegato in RAPPORTO_2008_2016.md):
 1. Per ogni stazione vicina k: differenza giornaliera Brera - k, solo nei giorni in cui ci sono entrambe; media
    mensile se il mese ha almeno 20 giorni in comune.
 2. Tolta la stagionalita' della differenza (per ogni coppia, la media di quel mese del calendario su tutto il periodo).
 3. "Composita" = MEDIANA delle differenze delle coppie, mese per mese (almeno 3 coppie). La mediana non si lascia
    trascinare da una sola vicina che salta (per esempio Lambrate 2008-2011 o Zavattari 2019-2020).
 4. Test SNHT (Alexandersson 1986) sulla serie: per ogni mese possibile calcola quanto la serie e' meglio descritta da
    "due livelli diversi prima e dopo" che da un livello solo; il mese con il valore piu' alto (T massimo) e' il
    candidato. Il salto conta se T supera la soglia del 95% ottenuta simulando 2000 serie casuali SENZA salti con la
    stessa lunghezza e la stessa "memoria" da un mese all'altro (autocorrelazione) della serie vera. Poi si ripete su
    ciascun pezzo (segmentazione binaria), con pezzi di almeno 12 mesi.
 5. Lo stesso test su OGNI coppia Brera-vicina e su ogni vicina contro le altre vicine (Brera esclusa): un salto che
    compare in quasi tutte le coppie con Brera ma non nelle coppie tra vicine e' di Brera.
 6. Per i salti della composita: giorno piu' probabile cercato sulla mediana GIORNALIERA delle differenze, +-300 giorni.
Scrive in OUTDIR: mensili_brera_meno_vicine.csv, rotture.csv, rotture_giorno.csv, salti_coppie.csv"""
import sys, os
import numpy as np, pandas as pd

f, od = sys.argv[1:3]
A0, A1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1995, 2026)
os.makedirs(od, exist_ok=True)
T0 = 5897
rng = np.random.default_rng(20261029)
D = pd.read_csv(f, parse_dates=['data'])
D = D[(D.data.dt.year >= A0) & (D.data.dt.year <= A1)]
MIN_GG = 20
MINLEN = 12


def mensile(d):
    g = d.groupby(d.index.to_period('M')).agg(['mean', 'count'])
    return g['mean'].where(g['count'] >= MIN_GG).dropna()


def destag(s):
    return s - s.groupby(s.index.month).transform('mean')


_crit = {}


def soglia(n, phi):
    key = (int(round(n / 10) * 10), round(min(max(phi, 0), 0.9), 1))
    if key not in _crit:
        nn, ph = max(key[0], 2 * MINLEN), key[1]
        e = rng.standard_normal((2000, nn))
        x = np.empty_like(e); x[:, 0] = e[:, 0]
        for i in range(1, nn):
            x[:, i] = ph * x[:, i - 1] + e[:, i]
        _crit[key] = np.quantile([snht(r)[1] for r in x], 0.95)
    return _crit[key]


def snht(x):
    x = np.asarray(x, float); n = len(x)
    z = (x - x.mean()) / (x.std(ddof=1) or 1.0)
    c = np.cumsum(z)
    k = np.arange(MINLEN, n - MINLEN + 1)
    if len(k) == 0:
        return 0, 0.0
    z1 = c[k - 1] / k
    z2 = (c[-1] - c[k - 1]) / (n - k)
    T = k * z1 ** 2 + (n - k) * z2 ** 2
    i = int(np.argmax(T))
    return int(k[i]), float(T[i])


def ar1(x):
    x = np.asarray(x, float) - np.mean(x)
    return float(np.sum(x[1:] * x[:-1]) / np.sum(x * x)) if len(x) > 2 else 0.0


def phi_residui(v, nmax=6):
    """'memoria' (autocorrelazione a un mese) dei residui dopo aver tolto fino a nmax salti trovati senza soglia:
    se la si misurasse sulla serie con i salti dentro, i salti stessi sembrerebbero 'memoria' e la soglia salirebbe."""
    cuts = [0, len(v)]
    for _ in range(nmax):
        best = None
        for a, b in zip(cuts[:-1], cuts[1:]):
            if b - a >= 2 * MINLEN:
                k, T = snht(v[a:b])
                if best is None or T > best[1]:
                    best = (a + k, T)
        if best is None:
            break
        cuts = sorted(cuts + [best[0]])
    r = np.concatenate([v[a:b] - v[a:b].mean() for a, b in zip(cuts[:-1], cuts[1:])])
    return ar1(r)


def binseg(s):
    """s: Series mensile senza buchi di indice (i buchi sono semplicemente saltati). Ritorna lista di rotture."""
    out = []
    phi = phi_residui(s.values)
    def rec(a, b):
        x = s.iloc[a:b]
        if len(x) < 2 * MINLEN:
            return
        k, T = snht(x.values)
        cr = soglia(len(x), phi)
        if T > cr:
            out.append({'mese': str(x.index[k]), 'T': round(T, 1), 'soglia95': round(cr, 1), 'n': len(x),
                        'prima': round(x.values[:k].mean(), 2), 'dopo': round(x.values[k:].mean(), 2),
                        'salto': round(x.values[k:].mean() - x.values[:k].mean(), 2),
                        'pezzo': f'{x.index[0]}..{x.index[-1]}', 'phi': round(phi, 2)})
            rec(a, a + k); rec(a + k, b)
    rec(0, len(s))
    return sorted(out, key=lambda r: r['mese'])


righe_rot, righe_coppie, righe_giorno, mens = [], [], [], {}
for el in ['TX', 'TN']:
    W = D.pivot(index='data', columns='sensore', values=el)
    vic = [c for c in W.columns if c != T0 and (W[T0] - W[c]).notna().sum() >= 5 * 300]
    pairs, pairs_d = {}, {}
    for k in vic:
        d = (W[T0] - W[k]).dropna()
        m = mensile(d)
        mens[f'{el}_B-{k}'] = m.round(2)
        pairs[k] = destag(m)
        pairs_d[k] = d - d.groupby(d.index.month).transform('mean')
    P = pd.DataFrame(pairs)
    comp = P.median(axis=1).where(P.notna().sum(axis=1) >= 3).dropna()
    mens[f'{el}_composita'] = comp.round(2); mens[f'{el}_n_coppie'] = P.notna().sum(axis=1)
    for r in binseg(comp):
        righe_rot.append({'serie': f'{el} Brera - mediana vicine', 'elemento': el, **r})
    # coppie Brera-k
    for k in vic:
        for r in binseg(pairs[k].dropna()):
            righe_coppie.append({'elemento': el, 'coppia': f'Brera-{k}', **r})
    # vicine contro le altre vicine (Brera esclusa): chi salta da solo?
    for j in vic:
        oth = [k for k in vic if k != j and (W[j] - W[k]).notna().sum() >= 5 * 300]
        Q = pd.DataFrame({k: destag(mensile((W[j] - W[k]).dropna())) for k in oth})
        cj = Q.median(axis=1).where(Q.notna().sum(axis=1) >= 3).dropna()
        mens[f'{el}_{j}-mediana_altre'] = cj.round(2)
        for r in binseg(cj):
            righe_rot.append({'serie': f'{el} {j} - mediana altre vicine', 'elemento': el, **r})
    # giorno del salto: mediana giornaliera delle differenze destagionalizzate
    Pd = pd.DataFrame(pairs_d)
    cd = Pd.median(axis=1).where(Pd.notna().sum(axis=1) >= 3).dropna()
    for r in [x for x in righe_rot if x['serie'] == f'{el} Brera - mediana vicine']:
        t = pd.Period(r['mese']).to_timestamp()
        w = cd[(cd.index >= t - pd.Timedelta(days=300)) & (cd.index <= t + pd.Timedelta(days=300))]
        x = w.values; c = np.cumsum(x - x.mean()); n = len(x)
        kk = np.arange(30, n - 30)
        T = (c[kk - 1] ** 2) * n / (kk * (n - kk))          # equivalente a SNHT su dati non standardizzati
        i = kk[int(np.argmax(T))]
        righe_giorno.append({'elemento': el, 'mese_rottura': r['mese'], 'giorno_piu_probabile': w.index[i].date(),
                             'media_90gg_prima': round(x[max(0, i - 90):i].mean(), 2),
                             'media_90gg_dopo': round(x[i:i + 90].mean(), 2),
                             'giorni_finestra': n})
    print(el, 'vicine usate:', vic)

pd.DataFrame(mens).rename_axis('mese').to_csv(f'{od}/mensili_brera_meno_vicine.csv')
R = pd.DataFrame(righe_rot); R.to_csv(f'{od}/rotture.csv', index=False)
C = pd.DataFrame(righe_coppie); C.to_csv(f'{od}/salti_coppie.csv', index=False)
G = pd.DataFrame(righe_giorno); G.to_csv(f'{od}/rotture_giorno.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.to_string()); print(G.to_string())
print(C.to_string())
