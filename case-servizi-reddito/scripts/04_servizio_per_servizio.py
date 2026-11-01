"""Quali servizi si associano al prezzo, a parita di distanza dal Duomo e di reddito? (esplorativo: 20 confronti, 41 zone)
Uso: python -I -X utf8 04_servizio_per_servizio.py <ABS milano-in-dati> <ABS case-servizi-reddito>
Entrate: out/civici_zone.csv, out/zone_tabella.csv (da 01, 02); citta-15-minuti/out/civici_tempi.csv e civici_tempi_extra.csv (min_*; sola lettura).
Uscita: out/servizi_singoli.csv
Per ogni servizio: quota di residenti della zona (peso = residenti stimati) con il servizio entro 15 minuti a piedi, poi correlazione di Spearman
con il prezzo OMI (stima) e Spearman parziale controllando distanza dal Duomo e reddito. Con 20 confronti e 41 zone qualche valore alto
esce anche per caso: leggere come indicazione, non come prova.
"""
import sys
import numpy as np, pandas as pd
from scipy import stats

def P(a): return a.replace(chr(92), '/').rstrip('/')
R, O = P(sys.argv[1]), P(sys.argv[2])
ESS = ['farmacie', 'medici', 'nidi', 'scuole', 'biblioteche', 'mercati', 'parchi', 'sport', 'poste', 'vicinato']
EXT = ['cinema', 'teatri_musei', 'giochi', 'piscine', 'cani', 'metro', 'bikemi', 'supermercati', 'ospedali', 'librerie']
c = pd.read_csv(O + '/out/civici_zone.csv', usecols=['IDMASTER', 'zona', 'peso'])
a = pd.read_csv(R + '/citta-15-minuti/out/civici_tempi.csv', usecols=['IDMASTER'] + ['min_' + k for k in ESS])
b = pd.read_csv(R + '/citta-15-minuti/out/civici_tempi_extra.csv', usecols=['IDMASTER'] + ['min_' + k for k in EXT])
c = c.merge(a, on='IDMASTER', validate='1:1').merge(b, on='IDMASTER', validate='1:1')
for k in ESS + EXT:
    c['in_' + k] = (c['min_' + k] <= 15).astype(float)
q = {}
for z, g in c.groupby('zona'):
    q[z] = {k: float((g['in_' + k] * g.peso).sum() / g.peso.sum()) for k in ESS + EXT}
Q = pd.DataFrame(q).T
Q.index.name = 'zona'
t = pd.read_csv(O + '/out/zone_tabella.csv')
t = t[(t.prezzo_eur_m2.notna()) & (t.zona != 'D39')].merge(Q.reset_index(), on='zona')
SEED, NB = 20261101, 3000

def prs(d, x, y, ctrl):
    r = d[[x, y] + ctrl].rank().values
    C = np.column_stack([np.ones(len(d)), r[:, 2:]])
    rx = r[:, 0] - C @ np.linalg.lstsq(C, r[:, 0], rcond=None)[0]
    ry = r[:, 1] - C @ np.linalg.lstsq(C, r[:, 1], rcond=None)[0]
    return np.corrcoef(rx, ry)[0, 1]

ctrl = ['dist_duomo_centroide_m', 'reddito_imponibile_medio_2024_pesato']
rows = []
rng = np.random.default_rng(SEED)
idx = [rng.integers(0, len(t), len(t)) for _ in range(NB)]
for k in ESS + EXT:
    if t[k].nunique() < 4:
        rows.append(dict(servizio=k, tipo='essenziale' if k in ESS else 'extra', quota_media_zone=t[k].mean(), zone_distinte=t[k].nunique()))
        continue
    sp = stats.spearmanr(t[k], t.prezzo_eur_m2).statistic
    pp = prs(t, k, 'prezzo_eur_m2', ctrl)
    bs = []
    for i in idx:
        d = t.iloc[i]
        if d[k].nunique() < 4:
            continue
        v = prs(d, k, 'prezzo_eur_m2', ctrl)
        if np.isfinite(v):
            bs.append(v)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    rows.append(dict(servizio=k, tipo='essenziale' if k in ESS else 'extra', quota_media_zone=t[k].mean(), minimo_zone=t[k].min(),
                     massimo_zone=t[k].max(), zone_distinte=t[k].nunique(), spearman_prezzo=sp, spearman_parziale=pp, ic95_basso=lo, ic95_alto=hi))
S = pd.DataFrame(rows).sort_values('spearman_parziale', ascending=False)
S.to_csv(O + '/out/servizi_singoli.csv', index=False, float_format='%.4f')
pd.set_option('display.width', 220)
print(S.round(3).to_string())
