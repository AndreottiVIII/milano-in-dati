"""Passo 1: da ogni sezione elettorale al CAP (e al NIL), e reddito per CAP e per NIL.

Fonte del legame: ds939 (stradario del referendum 2020, una riga per civico: SEZIONE, CAP a 3 cifre, ID_NIL).
Il CAP e quello ufficiale dello stradario (non stimato come nel filone 9). Una sezione puo contenere civici di piu CAP:
si tiene il peso (quota dei civici della sezione in quel CAP), come fatto per i NIL nel filone elezioni.

Uso: python -I -X utf8 10_sezione_cap.py <milano-in-dati> <voto-reddito>
Scrive in <voto-reddito>/out: sezione_cap.csv, sezione_cap_qualita.csv, cap_reddito.csv, nil_reddito.csv, controllo_cap_filone9.json
"""
import sys, os, json
import numpy as np
import pandas as pd

base, dest = sys.argv[1], sys.argv[2]
out = os.path.join(dest, 'out')
os.makedirs(out, exist_ok=True)

P939 = os.path.join(base, 'elezioni', 'raw', 'ds939-referendum-costituzionale-2020-stradario-abbinamento-numeri-civici-sezioni',
                    'ds939_Stradario_referendum_2020.csv')
d = pd.read_csv(P939, sep=';', encoding='cp1252', dtype=str, keep_default_na=False)
d['cap_num'] = d.CAP.astype(int)
d['CAP5'] = 20000 + d.cap_num
n_tot = len(d)
# CAP 100 = 20100 (CAP generico di Milano, 80 civici) e 54 (1 civico): non hanno reddito nei dati MEF -> fuori
inc_caps = sorted(pd.read_csv(os.path.join(base, 'redditi', 'pulito', 'cap_milano_media_nominale.csv')).cap.unique())
d['cap_ok'] = d.CAP5.isin(inc_caps)
n_fuori = int((~d.cap_ok).sum())
dd = d[d.cap_ok].copy()

# ---- pesi sezione -> CAP
w = dd.groupby(['SEZIONE', 'CAP5']).size().rename('n_civici').reset_index()
w['sezione'] = w.SEZIONE.astype(int)
w['cap'] = w.CAP5
w['peso'] = w.n_civici / w.groupby('sezione').n_civici.transform('sum')
mx = w.groupby('sezione').peso.transform('max')
w['prevalente'] = (w.peso == mx).astype(int)
# parita: tieni il CAP con id piu basso
w = w.sort_values(['sezione', 'peso', 'cap'], ascending=[True, False, True])
w['rk'] = w.groupby('sezione').cumcount()
w['prevalente'] = (w.rk == 0).astype(int)
w = w[['sezione', 'cap', 'n_civici', 'peso', 'prevalente']].sort_values(['sezione', 'cap'])
w.to_csv(os.path.join(out, 'sezione_cap.csv'), index=False, encoding='utf-8-sig')

q = w.groupby('sezione').agg(n_cap=('cap', 'nunique'), n_civici=('n_civici', 'sum'), peso_max=('peso', 'max')).reset_index()
q.to_csv(os.path.join(out, 'sezione_cap_qualita.csv'), index=False, encoding='utf-8-sig')

# ---- reddito per CAP (fonte: redditi/pulito/cap_milano_media_nominale.csv e _euro2025.csv, da mef_cap_2011_2024.csv)
nom = pd.read_csv(os.path.join(base, 'redditi', 'pulito', 'cap_milano_media_nominale.csv')).set_index('cap')
eur = pd.read_csv(os.path.join(base, 'redditi', 'pulito', 'cap_milano_media_euro2025.csv')).set_index('cap')
con = pd.read_csv(os.path.join(base, 'redditi', 'pulito', 'cap_milano_contribuenti.csv')).set_index('cap')
yrs = ['2019', '2020', '2021', '2022']
cr = pd.DataFrame(index=nom.index)
cr['reddito_2019_22_euro2025'] = eur[yrs].mean(axis=1)           # misura principale (euro 2025, media dei 4 anni d'imposta 2019-2022)
for y in ['2015', '2019', '2020', '2021', '2022', '2023', '2024']:
    cr['nom_' + y] = nom[y]
cr['reddito_2024_euro2025'] = eur['2024']
cr['contribuenti_2019_22'] = con[yrs].mean(axis=1)
cr['contribuenti_2024'] = con['2024']
civ = dd.groupby('CAP5').size().rename('civici_ds939')
cr = cr.join(civ)
cr['decile_cap_unweighted'] = pd.qcut(cr.reddito_2019_22_euro2025, 10, labels=False) + 1
cr.index.name = 'cap'
cr.reset_index().to_csv(os.path.join(out, 'cap_reddito.csv'), index=False, encoding='utf-8-sig')

# ---- reddito per NIL: media dei redditi dei CAP pesata per i civici (stessa idea del filone 9)
dd2 = dd[dd.ID_NIL != ''].copy()
dd2['id_nil'] = dd2.ID_NIL.astype(int)
dd2 = dd2.merge(cr[['reddito_2019_22_euro2025']].reset_index().rename(columns={'cap': 'CAP5'}), on='CAP5')
g = dd2.groupby('id_nil')
nilr = pd.DataFrame({'nil': g.NIL.first(), 'civici': g.size(),
                     'reddito_2019_22_euro2025': g.reddito_2019_22_euro2025.mean(),
                     'n_cap': g.CAP5.nunique(),
                     'quota_cap_dominante': g.CAP5.agg(lambda s: s.value_counts(normalize=True).iloc[0])}).reset_index()
nilr.to_csv(os.path.join(out, 'nil_reddito.csv'), index=False, encoding='utf-8-sig')

# ---- controllo: CAP ufficiale di ds939 contro CAP stimato dal filone 9 (civici_tempi.csv), chiave via+civico
ct = pd.read_csv(os.path.join(base, 'citta-15-minuti', 'out', 'civici_tempi.csv'),
                 usecols=['CODICE_VIA', 'NUMEROCOMPLETO', 'CAP', 'RESIDENZIALE']).dropna(subset=['CAP'])
ct = ct[ct.NUMEROCOMPLETO.astype(str).str.fullmatch(r'\d+[A-Z]?')].copy()
ct['key'] = ct.CODICE_VIA.astype(int).astype(str) + '|' + ct.NUMEROCOMPLETO.astype(str)
dk = dd[dd.BARRATO == ''].copy()
dk['key'] = dk.CODICE_VIA.astype(int).astype(str) + '|' + dk.CIVICO.astype(str)
dk = dk.drop_duplicates('key')
ct = ct.drop_duplicates('key')
m = dk.merge(ct[['key', 'CAP']].rename(columns={'CAP': 'CAP_f9'}), on='key', how='inner')
ctrl = dict(civici_ds939=int(n_tot), civici_senza_reddito_cap100_cap54=n_fuori,
            civici_confrontabili=int(len(m)), stesso_cap_pct=round(float((m.CAP5 == m.CAP_f9.astype(int)).mean() * 100), 2))
json.dump(ctrl, open(os.path.join(out, 'controllo_cap_filone9.json'), 'w'), indent=1)

print('civici ds939', n_tot, 'fuori (CAP 100/54)', n_fuori)
print('sezioni con CAP', w.sezione.nunique(), '; per numero di CAP:', q.n_cap.value_counts().sort_index().to_dict())
print('peso_max mediano', q.peso_max.median(), '; sezioni con peso_max>=0.8:', (q.peso_max >= 0.8).sum(), 'su', len(q))
print('controllo filone 9:', ctrl)
print(cr.reddito_2019_22_euro2025.describe())
print(nilr.describe())
