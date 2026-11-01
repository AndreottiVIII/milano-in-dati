"""Confronti semplici (terzili di servizi) e struttura dei CAP dentro le zone. Serve per le frasi 'in chiaro' e per i limiti.
Uso: python -I -X utf8 07_gruppi_e_cap.py <ABS milano-in-dati> <ABS case-servizi-reddito>
Entrate: out/zone_tabella.csv, out/civici_zone.csv. Uscite: out/gruppi_terzili.csv, out/cap_per_zona.csv, out/log_07.json
Prezzi = stime OMI. Campione: 41 zone (senza D39 e R2).
"""
import sys, json
import numpy as np, pandas as pd

def P(a): return a.replace(chr(92), '/').rstrip('/')
R, O = P(sys.argv[1]), P(sys.argv[2])
t = pd.read_csv(O + '/out/zone_tabella.csv')
t = t[(t.prezzo_eur_m2.notna()) & (t.zona != 'D39')].copy()
LOG = {}
rows = []
for col, lab in [('servizi20_pesato', 'servizi su 20'), ('servizi10_pesato', 'servizi su 10'), ('reddito_imponibile_medio_2024_pesato', 'reddito'),
                 ('dist_duomo_centroide_m', 'distanza dal Duomo (alta = lontano)')]:
    t['g'] = pd.qcut(t[col].rank(method='first'), 3, labels=['basso', 'medio', 'alto'])
    for g, d in t.groupby('g', observed=True):
        rows.append(dict(criterio=lab, terzile=g, n_zone=len(d), valore_mediano=d[col].median(), prezzo_mediano=d.prezzo_eur_m2.median(),
                         prezzo_min=d.prezzo_eur_m2.min(), prezzo_max=d.prezzo_eur_m2.max(), affitto_mediano=d.affitto_eur_m2_mese.median()))
G = pd.DataFrame(rows)
G.to_csv(O + '/out/gruppi_terzili.csv', index=False, float_format='%.3f')
print(G.round(2).to_string())
# a parita di distanza (terzili di distanza): i servizi contano?
t['gd'] = pd.qcut(t.dist_duomo_centroide_m.rank(method='first'), 3, labels=['vicino', 'medio', 'lontano'])
w = []
for g, d in t.groupby('gd', observed=True):
    d = d.copy()
    hi = d[d.servizi20_pesato >= d.servizi20_pesato.median()]
    lo = d[d.servizi20_pesato < d.servizi20_pesato.median()]
    w.append(dict(fascia_distanza=g, n=len(d), dist_km_da=d.dist_duomo_centroide_m.min() / 1000, dist_km_a=d.dist_duomo_centroide_m.max() / 1000,
                  prezzo_mediano_piu_servizi=hi.prezzo_eur_m2.median(), prezzo_mediano_meno_servizi=lo.prezzo_eur_m2.median(),
                  servizi20_mediano_piu=hi.servizi20_pesato.median(), servizi20_mediano_meno=lo.servizi20_pesato.median(),
                  reddito_mediano_piu=hi.reddito_imponibile_medio_2024_pesato.median(), reddito_mediano_meno=lo.reddito_imponibile_medio_2024_pesato.median()))
W = pd.DataFrame(w)
W.to_csv(O + '/out/stessa_distanza.csv', index=False, float_format='%.3f')
print(W.round(2).to_string())
# CAP dentro le zone
c = pd.read_csv(O + '/out/civici_zone.csv')
c = c[c.RESIDENZIALE == 1]
rr = []
for z, g in c.groupby('zona'):
    s = g.groupby('CAP').peso.sum().sort_values(ascending=False)
    inc = g.drop_duplicates('CAP').set_index('CAP').imponibile_medio_2024
    rr.append(dict(zona=z, n_cap=len(s), quota_cap_principale=s.iloc[0] / s.sum(), cap_principale=int(s.index[0]),
                   n_cap_ge10pct=int((s / s.sum() >= 0.10).sum()), reddito_min=inc.min(), reddito_max=inc.max()))
C = pd.DataFrame(rr)
C.to_csv(O + '/out/cap_per_zona.csv', index=False, float_format='%.3f')
LOG['zone_con_un_solo_CAP_ge90pct'] = int((C.quota_cap_principale >= 0.9).sum())
LOG['zone_con_2_o_piu_CAP_ge10pct'] = int((C.n_cap_ge10pct >= 2).sum())
LOG['n_zone'] = len(C)
LOG['n_cap_totali'] = int(c.CAP.nunique())
json.dump(LOG, open(O + '/out/log_07.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(LOG, indent=1))
