"""Legge le matrici del pendolarismo ISTAT 1991, 2001, 2011, 2021 e ne ricava le tabelle su Milano.

Uso: python -I -X utf8 parse_censimenti.py <cartella pendolari, percorso assoluto>
Prima va lanciato codici.py (anagrafica e raccordo dei codici).

Scrive in pulito/:
  flussi_milano.csv      anno, motivo, direzione (entra/esce/interno), altro (codice 2021 o -1 se non agganciato),
                         prov_storica, n   -> totali persone, tutti i comuni d'Italia che hanno Milano da un lato
  dettaglio_milano.csv   come sopra + modo, modo_raw, orario, tempo  (solo 1991, 2001, 2011: il 2021 non li ha)
  origini_lombardia.csv  anno, motivo, origine, totale, interno, verso_milano -> per ogni comune lombardo di residenza
  controlli_parse.json   somme di controllo (totali nazionali, confronto con i totali dichiarati da ISTAT)

Regole di lettura (tracciati record dei file leggimi):
  1991: prov(3) com(3) sesso mezzo condizione orario tempo provD(3) comD(3) n(12). condizione 1 = studente o altro,
        2 = occupato. mezzo in 6 gruppi.
  2001: larghezza fissa 43: prov[0:3] com[4:7] sesso[8] motivo[10] luogo[12] provD[14:17] comD[18:21]
        spostamento[26] (1 = si e' mosso mercoledi', 0 = no) mezzo[28:30] orario[31] tempo[33] n[34:43].
        Totale = tutti i record (spostamento 1 e 0), che riproduce i 26.764.361 individui dichiarati da ISTAT
        (verificato in controlli_parse.json).
  2011: record S (totali per strato) e record L (con mezzo, orario, tempo). Per i totali di flusso si usa il
        conteggio intero dei record S; per mezzo/orario/tempo la stima decimale dei record L.
  2021: file separati lavoro e studio: prov_res, procom_res, prov_lav/stu, procom, pendolari.
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

P = Path(sys.argv[1])
RAW = P / 'raw'
OUT = P / 'pulito'
MI = 15146
LOMB_PROV = {12, 13, 14, 15, 16, 17, 18, 19, 20, 97, 98, 108}

com = pd.read_csv(OUT / 'comuni_2021.csv')
reg = dict(zip(com.pro_com, com.cod_regione))
rac = pd.read_csv(OUT / 'raccordo_codici.csv')
RAC = {}
for a, g in rac.groupby('anno'):
    RAC[int(a)] = {int(c): (int(p) if pd.notna(p) else -1) for c, p in zip(g.cod_storico, g.pro_com_2021)}

MODI6 = {'piedi_bici_altro': 'A piedi, bici, altro', 'ferro': 'Treno, tram, metro', 'bus': 'Autobus (anche aziendale/scolastico)',
         'auto_cond': 'Auto, conducente', 'auto_pass': 'Auto, passeggero', 'moto': 'Moto, scooter'}
M2001 = {'01': 'ferro', '02': 'ferro', '03': 'ferro', '04': 'bus', '05': 'bus', '06': 'bus', '07': 'auto_cond', '08': 'auto_pass',
         '09': 'moto', '10': 'piedi_bici_altro', '11': 'piedi_bici_altro', '12': 'piedi_bici_altro'}
M1991 = {'1': 'piedi_bici_altro', '2': 'ferro', '3': 'bus', '4': 'auto_cond', '5': 'auto_pass', '6': 'moto'}

controlli = {}


def finalize(df, anno):
    """df: colonne o, d (codici storici), motivo, n, [modo, modo_raw, orario, tempo]. Aggiunge direzione/altro."""
    r = RAC[anno]
    df = df.copy()
    df['o21'] = df['o'].map(r).fillna(-1).astype(int)
    df['d21'] = df['d'].map(r).fillna(-1).astype(int)
    om = df['o'] == MI
    dm = df['d'] == MI
    df = df[om | dm].copy()
    om = df['o'] == MI
    dm = df['d'] == MI
    df['direzione'] = np.where(om & dm, 'interno', np.where(dm, 'entra', 'esce'))
    df['altro'] = np.where(df['direzione'] == 'entra', df['o21'], np.where(df['direzione'] == 'esce', df['d21'], MI))
    df['altro_stor'] = np.where(df['direzione'] == 'entra', df['o'], np.where(df['direzione'] == 'esce', df['d'], MI))
    df['prov_storica'] = df['altro_stor'] // 1000
    df['anno'] = anno
    return df


def origini(df, anno):
    """df con o,d,motivo,n (solo totali). Per ogni comune lombardo di residenza."""
    r = RAC[anno]
    df = df.copy()
    df['o21'] = df['o'].map(r).fillna(-1).astype(int)
    lom = df['o21'].map(lambda c: reg.get(c, 0) == 3) | ((df['o21'] == -1) & ((df['o'] // 1000).isin(LOMB_PROV)))
    df = df[lom]
    df['interno'] = np.where(df['o'] == df['d'], df['n'], 0)
    df['verso_milano'] = np.where((df['d'] == MI) & (df['o'] != MI), df['n'], 0)
    g = df.groupby(['motivo', 'o21', 'o'], as_index=False).agg(totale=('n', 'sum'), interno=('interno', 'sum'), verso_milano=('verso_milano', 'sum'))
    g['anno'] = anno
    return g


FL, DT, OR = [], [], []

# ============================================================ 1991
print('1991')
cols = [(0, 3), (3, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 14), (14, 17), (17, 29)]
df = pd.read_fwf(RAW / 'istat_1991/x/Pen_91It.txt', colspecs=cols, header=None, dtype=str, encoding='latin1',
                 names=['p', 'c', 'sesso', 'mezzo', 'cp', 'orario', 'tempo', 'pd', 'cd', 'n'], keep_default_na=False)
for c in df.columns:
    df[c] = df[c].str.strip()
df['n'] = df['n'].astype(int)
df['o'] = df['p'].astype(int) * 1000 + df['c'].astype(int)
# destinazione 060000 = stesso comune (nota ISTAT sul trattamento dei dati 1991)
same = df['pd'].str.startswith('060') | (df['pd'] + df['cd'] == '000000')
df['d'] = np.where(df['pd'].str.strip() == '', -1, df['pd'].replace('', '0').astype(int) * 1000 + df['cd'].replace('', '0').astype(int))
df.loc[df['pd'] + df['cd'] == '060000', 'd'] = df['o']
df['motivo'] = df['cp'].map({'1': 'studio', '2': 'lavoro'})
controlli['1991_totale_file'] = int(df['n'].sum())
controlli['1991_motivo_vuoto'] = int(df.loc[df['motivo'].isna(), 'n'].sum())
df = df[df['motivo'].notna()]
tot = df.groupby(['o', 'd', 'motivo'], as_index=False)['n'].sum()
FL.append(finalize(tot, 1991)[['anno', 'motivo', 'direzione', 'altro', 'altro_stor', 'prov_storica', 'n']])
OR.append(origini(tot, 1991))
det = df.copy()
det['modo_raw'] = det['mezzo'].where(det['mezzo'] != '', 'nd')
det['modo'] = det['mezzo'].map(M1991).fillna('nd')
det['orario'] = det['orario'].where(det['orario'] != '', 'nd')
det['tempo'] = det['tempo'].where(det['tempo'] != '', 'nd')
det = det.groupby(['o', 'd', 'motivo', 'modo', 'modo_raw', 'orario', 'tempo'], as_index=False)['n'].sum()
DT.append(finalize(det, 1991))
controlli['1991_nazionale_con_destinazione_valida'] = int(tot['n'].sum())
del df, tot, det

# ============================================================ 2001
print('2001')
cols = [(0, 3), (4, 7), (8, 9), (10, 11), (12, 13), (14, 17), (18, 21), (26, 27), (28, 30), (31, 32), (33, 34), (34, 43)]
df = pd.read_fwf(RAW / 'istat_2001/x/matrix_pendo2001.txt', colspecs=cols, header=None, dtype=str, encoding='latin1',
                 names=['p', 'c', 'sesso', 'mot', 'luogo', 'pd', 'cd', 'sp', 'mezzo', 'orario', 'tempo', 'n'], keep_default_na=False)
for c in df.columns:
    df[c] = df[c].str.strip()
df['n'] = df['n'].astype(int)
controlli['2001_totale_file_tutti_i_record'] = int(df['n'].sum())
controlli['2001_totale_solo_spostati_mercoledi'] = int(df.loc[df['sp'] == '1', 'n'].sum())
controlli['2001_dichiarato_ISTAT'] = 26764361
df = df[df['luogo'].isin(['1', '2'])]  # niente estero
df['o'] = df['p'].astype(int) * 1000 + df['c'].astype(int)
df['d'] = df['pd'].astype(int) * 1000 + df['cd'].astype(int)
df['motivo'] = df['mot'].map({'1': 'studio', '2': 'lavoro'})
tot = df.groupby(['o', 'd', 'motivo'], as_index=False)['n'].sum()
FL.append(finalize(tot, 2001)[['anno', 'motivo', 'direzione', 'altro', 'altro_stor', 'prov_storica', 'n']])
OR.append(origini(tot, 2001))
det = df[df['sp'] == '1'].copy()
det['modo_raw'] = det['mezzo']
det['modo'] = det['mezzo'].map(M2001).fillna('nd')
det['orario'] = det['orario'].replace('', 'nd')
det['tempo'] = det['tempo'].replace('', 'nd')
det = det.groupby(['o', 'd', 'motivo', 'modo', 'modo_raw', 'orario', 'tempo'], as_index=False)['n'].sum()
DT.append(finalize(det, 2001))
del df, tot, det

# ============================================================ 2011
print('2011')
F11 = RAW / 'istat_2011/x/MATRICE PENDOLARISMO 2011/matrix_pendo2011_10112014.txt'
names = ['tipo', 'tres', 'p', 'c', 'sesso', 'mot', 'luogo', 'pd', 'cd', 'stato', 'mezzo', 'orario', 'tempo', 'val', 'cnt']
S_parts, L_parts = [], []
ctrl = {'S_rows': 0, 'L_rows': 0, 'S_cnt_tot': 0, 'S_cnt_estero': 0}
for ch in pd.read_csv(F11, sep=r'\s+', header=None, names=names, dtype=str, chunksize=600000, encoding='latin1'):
    s = ch[ch['tipo'] == 'S']
    l = ch[ch['tipo'] == 'L']
    ctrl['S_rows'] += len(s)
    ctrl['L_rows'] += len(l)
    ctrl['S_cnt_tot'] += int(s['cnt'].astype(int).sum())
    ctrl['S_cnt_estero'] += int(s.loc[s['luogo'] == '3', 'cnt'].astype(int).sum())
    s = s[s['luogo'].isin(['1', '2'])].copy()
    s['o'] = s['p'].astype(int) * 1000 + s['c'].astype(int)
    s['d'] = s['pd'].astype(int) * 1000 + s['cd'].astype(int)
    s['n'] = s['cnt'].astype(int)
    s['motivo'] = s['mot'].map({'1': 'studio', '2': 'lavoro'})
    S_parts.append(s.groupby(['o', 'd', 'motivo'], as_index=False)['n'].sum())
    l = l[l['luogo'].isin(['1', '2'])].copy()
    l['o'] = l['p'].astype(int) * 1000 + l['c'].astype(int)
    l['d'] = l['pd'].astype(int) * 1000 + l['cd'].astype(int)
    l = l[(l['o'] == MI) | (l['d'] == MI)]
    l['n'] = l['val'].astype(float)
    l['motivo'] = l['mot'].map({'1': 'studio', '2': 'lavoro'})
    l['modo_raw'] = l['mezzo']
    l['modo'] = l['mezzo'].map(M2001).fillna('nd')
    L_parts.append(l.groupby(['o', 'd', 'motivo', 'modo', 'modo_raw', 'orario', 'tempo'], as_index=False)['n'].sum())
controlli['2011'] = ctrl
controlli['2011_dichiarato_ISTAT'] = 28871447
tot = pd.concat(S_parts).groupby(['o', 'd', 'motivo'], as_index=False)['n'].sum()
FL.append(finalize(tot, 2011)[['anno', 'motivo', 'direzione', 'altro', 'altro_stor', 'prov_storica', 'n']])
OR.append(origini(tot, 2011))
det = pd.concat(L_parts).groupby(['o', 'd', 'motivo', 'modo', 'modo_raw', 'orario', 'tempo'], as_index=False)['n'].sum()
DT.append(finalize(det, 2011))
controlli['2011_nazionale_senza_estero_S'] = int(tot['n'].sum())
del tot, det

# ============================================================ 2021
print('2021')
parts = []
for mot, nome, a, b in (('lavoro', 'LAVORO', 'Procom_res', 'Procom_lav'), ('studio', 'STUDIO', 'Procom_res', 'Procom_stu')):
    d = pd.read_csv(RAW / f'istat_2021/x_{nome}/matrix_pendo{nome}_2021.txt', sep='\t', dtype={a: str, b: str})
    d = d.rename(columns={a: 'o', b: 'd', 'Pendolari': 'n'})
    d['o'] = d['o'].astype(int)
    d['d'] = d['d'].astype(int)
    d['motivo'] = mot
    controlli[f'2021_{mot}_totale_file'] = int(d['n'].sum())
    parts.append(d[['o', 'd', 'motivo', 'n']])
tot = pd.concat(parts)
RAC[2021] = {int(c): int(c) for c in com.pro_com}
FL.append(finalize(tot, 2021)[['anno', 'motivo', 'direzione', 'altro', 'altro_stor', 'prov_storica', 'n']])
OR.append(origini(tot, 2021))
controlli['2021_dichiarato_ISTAT'] = {'lavoro': 19565808, 'studio': 9279329}

fl = pd.concat(FL)
fl = fl.groupby(['anno', 'motivo', 'direzione', 'altro', 'altro_stor', 'prov_storica'], as_index=False)['n'].sum()
fl['n'] = fl['n'].round(2)
fl.to_csv(OUT / 'flussi_milano.csv', index=False)
dt = pd.concat(DT)[['anno', 'motivo', 'direzione', 'altro', 'altro_stor', 'prov_storica', 'modo', 'modo_raw', 'orario', 'tempo', 'n']]
dt['n'] = dt['n'].round(2)
dt.to_csv(OUT / 'dettaglio_milano.csv', index=False)
og = pd.concat(OR).rename(columns={'o21': 'origine', 'o': 'origine_stor'})
og['totale'] = og['totale'].round(1)
og[['anno', 'motivo', 'origine', 'origine_stor', 'totale', 'interno', 'verso_milano']].to_csv(OUT / 'origini_lombardia.csv', index=False)
json.dump(controlli, open(OUT / 'controlli_parse.json', 'w', encoding='utf8'), indent=1)
print(json.dumps(controlli, indent=1))
print(fl.groupby(['anno', 'motivo', 'direzione'])['n'].sum().round(0).to_string())
