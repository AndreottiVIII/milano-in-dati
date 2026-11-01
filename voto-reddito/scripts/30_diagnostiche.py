"""Passo 3: diagnostiche. (1) chi c'e nell'ultimo decile di reddito; (2) elettori su adulti residenti per decile
(il registro elettorale puo gonfiare l'affluenza al denominatore); (3) tabelle di sintesi per la nota.
Uso: python -I -X utf8 30_diagnostiche.py <milano-in-dati> <voto-reddito>"""
import sys, os
import numpy as np, pandas as pd
base, dest = sys.argv[1], sys.argv[2]
OUT = os.path.join(dest, 'out')
sz = pd.read_csv(os.path.join(OUT, 'sezioni_reddito_decile.csv'))
cr = pd.read_csv(os.path.join(OUT, 'cap_reddito.csv')).set_index('cap')
ris = pd.read_csv(os.path.join(base, 'elezioni', 'pulito', 'risultati_sezione.csv'), encoding='utf-8-sig', low_memory=False)
r21 = ris[ris.elezione_id == 'comunali_consiglio_2021-10-03'][['sezione', 'elettori', 'votanti']]
x = sz.merge(r21, on='sezione', how='left')
x['reddito_cap_prev'] = x.cap_prev.map(cr.reddito_2019_22_euro2025)
# composizione dei decili per CAP prevalente (elettori 2021)
comp = x.groupby(['decile', 'cap_prev']).elettori.sum().reset_index()
comp['quota_decile'] = comp.elettori / comp.groupby('decile').elettori.transform('sum')
comp['reddito_cap'] = comp.cap_prev.map(cr.reddito_2019_22_euro2025)
comp = comp.sort_values(['decile', 'elettori'], ascending=[True, False])
comp.to_csv(os.path.join(OUT, 'composizione_decili_per_cap.csv'), index=False, encoding='utf-8-sig')
print(comp[comp.decile.isin([9, 10])].to_string())
# elettori / adulti residenti per NIL (da elezioni/pulito/nil_controllo_popolazione.csv: elettori Comunali 2021 / adulti 2021, ds205)
cp = pd.read_csv(os.path.join(base, 'elezioni', 'pulito', 'nil_controllo_popolazione.csv'), encoding='utf-8-sig')
nr = pd.read_csv(os.path.join(OUT, 'nil_reddito.csv'))
m = cp.merge(nr, left_on='id_nil', right_on='id_nil')
m = m[m.fragile == 0]
from scipy.stats import spearmanr
print('rapporto elettori/adulti vs reddito NIL: rho', spearmanr(m.rapporto, m.reddito_2019_22_euro2025).statistic)
m['q'] = pd.qcut(m.reddito_2019_22_euro2025, 5, labels=False) + 1
print(m.groupby('q').rapporto.agg(['median', 'min', 'max', 'count']))
m.to_csv(os.path.join(OUT, 'nil_rapporto_elettori_adulti_reddito.csv'), index=False, encoding='utf-8-sig')
# sezioni: elettori 2021 per decile e sezioni anomale
x['anom'] = (x.elettori <= 0) | (x.votanti > x.elettori)
print('sezioni anomale per decile', x.groupby('decile').anom.sum().to_dict(), '; totale', int(x.anom.sum()))
