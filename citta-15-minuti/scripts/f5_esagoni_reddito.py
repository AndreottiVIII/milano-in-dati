"""Fase 5: esagoni da 100 m e reddito del CAP (richiesta di Davide, 30/10/2026).
Uso: python -I f5_esagoni_reddito.py <ABS strand citta-15-minuti> <ABS docs/citta-15-minuti>
Per ogni esagono: CAP della maggioranza dei civici (e quota di civici con quel CAP), reddito imponibile medio 2024 del CAP,
quota di civici con tutti e 20 i servizi entro 15 minuti ("premium").
Il reddito esiste solo per CAP: tutti gli esagoni dello stesso CAP hanno lo stesso reddito.
Gli esagoni sono gli stessi di f3_dati.py (stessa griglia, stesso ordine)."""
import sys, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr
S = sys.argv[1]; D = sys.argv[2]; O = S + '/out/'; DD = D + '/data/'
CM = 73
c = pd.read_csv(O + 'civici_tempi.csv', dtype={'CAP': str}, usecols=['IDMASTER', 'ID_NIL', 'CAP', 'x', 'y', 'punteggio'])
e = pd.read_csv(O + 'civici_tempi_extra.csv', usecols=['IDMASTER', 'punteggio_20'])
c = c.merge(e, on='IDMASTER', how='left')
cap = pd.read_csv(O + 'cap_redditi_servizi.csv', dtype={'CAP': str}).set_index('CAP')

# stessa griglia esagonale di f3_dati.py
SZ = 100 / np.sqrt(3); x = c.x.values; y = c.y.values
q = (np.sqrt(3) / 3 * x - 1 / 3 * y) / SZ; r_ = (2 / 3 * y) / SZ
cx_ = q; cz = r_; cy = -cx_ - cz
rx = np.round(cx_); ry = np.round(cy); rz = np.round(cz)
dx = abs(rx - cx_); dy = abs(ry - cy); dz = abs(rz - cz)
m1 = (dx > dy) & (dx > dz); m2 = (~m1) & (dy > dz)
rx = np.where(m1, -ry - rz, rx); rz = np.where((~m1) & (~m2), -rx - ry, rz)
c['hq'] = rx.astype(int); c['hr'] = rz.astype(int)
c['top'] = (c.punteggio_20 >= 20).astype(float)

H = c.groupby(['hq', 'hr']).agg(n=('IDMASTER', 'size'), p=('punteggio', 'mean'), p20=('punteggio_20', 'mean'), top=('top', 'mean')).reset_index()
hx = json.load(open(DD + 'esagoni.json', encoding='utf-8'))
assert len(H) == len(hx['x']) and list(H.n) == hx['n'], 'esagoni diversi da f3_dati.py'

def moda(s):
    v = s.dropna()
    if not len(v): return ('', 0.0)
    m = v.mode().iloc[0]; return (m, float((v == m).mean()))
mc = c.groupby(['hq', 'hr']).CAP.agg(moda)
H['cap'] = [m[0] for m in mc]; H['cap_quota'] = [m[1] for m in mc]
nil = c.dropna(subset=['ID_NIL']).groupby(['hq', 'hr']).ID_NIL.agg(lambda s: s.mode().iloc[0])
H = H.merge(nil.rename('nil'), left_on=['hq', 'hr'], right_index=True, how='left')
H['red'] = H.cap.map(cap['imponibile_medio_2024'])

caps = sorted(cap.index)
ci = {k: i for i, k in enumerate(caps)}
ok = H[(H.nil != CM) & H.red.notna()].copy()

# legame esagono-reddito
rho10 = spearmanr(ok.p, ok.red).correlation
rho20 = spearmanr(ok.p20, ok.red).correlation
# quanta parte delle differenze tra esagoni sta tra un CAP e l'altro (il resto e' dentro lo stesso CAP)
def tra_cap(col):
    m = ok[col].mean(); g = ok.groupby('cap')[col]
    tra = (g.size() * (g.mean() - m) ** 2).sum(); tot = ((ok[col] - m) ** 2).sum()
    return float(tra / tot)
ok['terzo'] = pd.qcut(ok.red.rank(method='first'), 3, labels=['basso', 'medio', 'alto'])
terzi = {t: {'esagoni': int(len(g)), 'premium': int((g.p20 >= 20).sum()), 'quota_premium': round(float((g.p20 >= 20).mean()), 4),
             'p20_mediana': round(float(g.p20.median()), 2)} for t, g in ok.groupby('terzo', observed=True)}
per_cap = []
for k, g in ok.groupby('cap'):
    per_cap.append({'cap': k, 'zona': str(cap.loc[k, 'NIL_piu_frequente']).title(), 'red': round(float(cap.loc[k, 'imponibile_medio_2024'])),
                    'esagoni': int(len(g)), 'premium': int((g.p20 >= 20).sum()),
                    'p20': [round(float(v), 1) for v in np.percentile(g.p20, [10, 25, 50, 75, 90])]})
out = {
    'caps': caps,
    'zona': [str(cap.loc[k, 'NIL_piu_frequente']).title() for k in caps],
    'red': [round(float(cap.loc[k, 'imponibile_medio_2024'])) for k in caps],
    'cap': [ci.get(k, -1) for k in H.cap],
    'cq': [int(round(v * 100)) for v in H.cap_quota],
    'top': [int(round(v * 100)) for v in H.top.fillna(0)],
    'stat': {'esagoni': int(len(ok)), 'premium': int((ok.p20 >= 20).sum()), 'civici_premium': int(c[(c.ID_NIL != CM)].top.sum()),
             'civici': int((c.ID_NIL != CM).sum()),
             'rho10': round(float(rho10), 3), 'rho20': round(float(rho20), 3),
             'tra_cap10': round(tra_cap('p'), 3), 'tra_cap20': round(tra_cap('p20'), 3), 'terzi': terzi,
             'per_cap': sorted(per_cap, key=lambda z: z['red'])},
}
json.dump(out, open(DD + 'esagoni_cap.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
H.drop(columns=['hq', 'hr']).assign(id=range(len(H))).to_csv(O + 'esagoni_cap_reddito.csv', index=False)
print(json.dumps(out['stat'], ensure_ascii=False)[:1500])
