"""Estrae dalla matrice OD2016 (Regione Lombardia, passeggeri) gli spostamenti per lavoro e studio da/verso Milano.

Uso: python -I -X utf8 od2016.py <cartella pendolari, percorso assoluto>
Legge raw/lombardia_od2016/x/matrice_od_2016_passeggeri.csv (2,8 GB, 8,5 milioni di righe: coppia di zone x fascia oraria)
e raw/lombardia_od2016/zone_od2016.geojson. Milano e' divisa in 16 zone ("MILANO 1".."MILANO 16").
Scrive pulito/od2016_milano.csv: direzione (entra/esce/interno), prov, zona, fascia, e le 16 colonne lav_*/stu_*.
Sono SPOSTAMENTI di un giorno feriale medio di persone da 14 anni in su, non persone; matrice stimata con modelli.
"""
import sys
from pathlib import Path
import pandas as pd

P = Path(sys.argv[1])
F = P / 'raw/lombardia_od2016/x/matrice_od_2016_passeggeri.csv'
modi = ['COND', 'PAX', 'MOTO', 'FERRO', 'GOMMA', 'BICI', 'PIEDI', 'ALTRO']
vals = [f'{m}_{x}' for m in ('LAV', 'STU') for x in modi]
use = ['PROV_ORIG', 'ZONA_ORIG', 'PROV_DEST', 'ZONA_DEST', 'FASCIA_ORARIA'] + vals
parts = []
n = 0
for ch in pd.read_csv(F, usecols=use, chunksize=600000, dtype={c: float for c in vals}):
    n += len(ch)
    om = ch['ZONA_ORIG'].str.fullmatch(r'MILANO \d+') & (ch['PROV_ORIG'] == 'MI')
    dm = ch['ZONA_DEST'].str.fullmatch(r'MILANO \d+') & (ch['PROV_DEST'] == 'MI')
    s = ch[om | dm].copy()
    if not len(s):
        continue
    s['om'] = om[s.index]
    s['dm'] = dm[s.index]
    s['direzione'] = 'interno'
    s.loc[s['dm'] & ~s['om'], 'direzione'] = 'entra'
    s.loc[s['om'] & ~s['dm'], 'direzione'] = 'esce'
    s['prov'] = s['PROV_ORIG'].where(s['direzione'] == 'entra', s['PROV_DEST'])
    s['zona'] = s['ZONA_ORIG'].where(s['direzione'] == 'entra', s['ZONA_DEST'])
    s.loc[s['direzione'] == 'interno', ['prov', 'zona']] = ['MI', 'MILANO']
    parts.append(s.groupby(['direzione', 'prov', 'zona', 'FASCIA_ORARIA'], as_index=False)[vals].sum())
    print(n, flush=True)
out = pd.concat(parts).groupby(['direzione', 'prov', 'zona', 'FASCIA_ORARIA'], as_index=False)[vals].sum()
out.columns = [c.lower() for c in out.columns]
out = out.rename(columns={'fascia_oraria': 'fascia'})
out[[c for c in out.columns if c.startswith(('lav_', 'stu_'))]] = out[[c for c in out.columns if c.startswith(('lav_', 'stu_'))]].round(2)
out.to_csv(P / 'pulito/od2016_milano.csv', index=False)
print(len(out), out.groupby('direzione')[[c for c in out.columns if c.startswith(('lav_', 'stu_'))]].sum().round(0).T.to_string())
