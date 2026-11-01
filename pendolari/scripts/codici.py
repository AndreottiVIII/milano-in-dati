"""Anagrafica dei comuni 2021 e raccordo dei codici storici (1991, 2001, 2011) verso i codici 2021.

Uso: python -I -X utf8 codici.py <cartella pendolari, percorso assoluto>

Legge (in raw/):
  istat_codici/x/Limiti2021_g/ElencoUnitaAmministrative2021.xlsx   (codici, nomi, abitanti 2021, punto di riferimento)
  istat_codici/Elenco-comuni-italiani.xlsx                         (codici attuali con le colonne dei codici storici)
  istat_2011/x/.../Codici Comuni italiani_1 gennaio 2011.xls       (nomi 2011 e codici a 103 province = 2001)
  istat_1991/x/elencom91.xls                                       (nomi 1991)
Scrive (in pulito/):
  comuni_2021.csv      un comune per riga, con lon/lat del punto di riferimento ISTAT (WGS84)
  raccordo_codici.csv  anno, codice storico, nome storico, codice 2021, metodo (codice / nome / nessuno)
  raccordo_sintesi.json
Regola: prima il codice (colonne storiche dell'elenco ISTAT attuale), poi il nome normalizzato dentro la
stessa regione se univoco. I comuni soppressi dopo il censimento (fusioni) senza un nome uguale restano
non agganciati: nessun numero viene inventato.
"""
import sys, json, re, unicodedata
from pathlib import Path
import pandas as pd
from pyproj import Transformer

P = Path(sys.argv[1])
RAW = P / 'raw'
OUT = P / 'pulito'
OUT.mkdir(exist_ok=True)


def norm(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    return re.sub(r'[^a-z0-9]', '', s)


# ---------- 2021
e21 = pd.read_excel(RAW / 'istat_codici/x/Limiti2021_g/ElencoUnitaAmministrative2021.xlsx', sheet_name='Comuni2021', dtype={'PRO_COM_T': str})
e21['pro_com'] = e21['PRO_COM_T'].astype(int)
e21['nome'] = e21['COMUNE_IT'].fillna(e21['COMUNE'])
tr = Transformer.from_crs('EPSG:32632', 'EPSG:4326', always_xy=True)
lon, lat = tr.transform(e21['POINT_X'].values, e21['POINT_Y'].values)
com = pd.DataFrame({
    'pro_com': e21['pro_com'], 'nome': e21['nome'], 'cod_regione': e21['COD_REG'], 'regione': e21['DEN_REG'],
    'cod_uts': e21['COD_UTS'], 'uts': e21['DEN_UTS'], 'sigla': e21['SIGLA_AUTOMOBILISTICA'],
    'pop_2021': e21['POP21'], 'superficie_kmq': e21['SUPERFICIE'].round(2),
    'lon': lon.round(5), 'lat': lat.round(5)})
com.to_csv(OUT / 'comuni_2021.csv', index=False)
set21 = set(com.pro_com)
by_reg_name = {}
for r in com.itertuples():
    by_reg_name.setdefault((r.cod_regione, norm(r.nome)), []).append(r.pro_com)

# ---------- elenco attuale con codici storici
cur = pd.read_excel(RAW / 'istat_codici/Elenco-comuni-italiani.xlsx', sheet_name=0)
c107 = 'Codice Comune numerico con 107 Province (dal 2017 al 2025)'
c110 = 'Codice Comune numerico con 110 Province (dal 2010 al 2016)'
c103 = 'Codice Comune numerico con 103 Province (dal 1995 al 2005)'
map110 = {int(a): int(b) for a, b in zip(cur[c110], cur[c107]) if pd.notna(a) and pd.notna(b)}
map103 = {int(a): int(b) for a, b in zip(cur[c103], cur[c107]) if pd.notna(a) and pd.notna(b)}

# ---------- elenco 2011 (nomi) e 1991
l11 = pd.read_excel(RAW / 'istat_2011/x/MATRICE PENDOLARISMO 2011/Pendolo 2011 documenti_utili/CLASSIFICAZIONI/Codici Comuni italiani_1 gennaio 2011.xls', sheet_name='COMUNI 01_01_2011')
l11 = l11.iloc[:, [0, 4, 5, 7]]
l11.columns = ['reg', 'cod2011', 'cod2001', 'nome']
l11 = l11.dropna(subset=['cod2011'])
l11['reg'] = l11['reg'].astype(int)
l11['cod2011'] = l11['cod2011'].astype(int)
l11['cod2001'] = pd.to_numeric(l11['cod2001'], errors='coerce')

l91 = pd.read_excel(RAW / 'istat_1991/x/elencom91.xls', sheet_name=0, header=0, dtype=str)
l91.columns = ['reg', 'prov', 'com', 'cod', 'nome']
l91 = l91.dropna(subset=['prov', 'com'])
l91['cod1991'] = l91['prov'].astype(int) * 1000 + l91['com'].astype(int)
l91['reg'] = l91['reg'].astype(int)

rows = []


def risolvi(anno, cod, nome, reg, diretto):
    """cod: codice storico; diretto: codice 2021 dal codice (o None)."""
    if diretto is not None and diretto in set21:
        return diretto, 'codice'
    cand = by_reg_name.get((reg, norm(nome)), [])
    if len(cand) == 1:
        return cand[0], 'nome'
    # fusione: il nuovo nome contiene quello vecchio (es. Vermezzo -> Vermezzo con Zelo); solo se univoco
    n = norm(nome)
    if len(n) >= 5:
        cand = [pc for (rg, nn), lst in by_reg_name.items() if rg == reg and n in nn for pc in lst]
        if len(cand) == 1:
            return cand[0], 'nome_contenuto'
    return None, 'nessuno'


for r in l11.itertuples():
    nome = r.nome
    d, m = risolvi(2011, r.cod2011, nome, r.reg, map110.get(r.cod2011))
    rows.append((2011, r.cod2011, nome, d, m))
    if pd.notna(r.cod2001):
        d, m = risolvi(2001, int(r.cod2001), nome, r.reg, map103.get(int(r.cod2001)))
        rows.append((2001, int(r.cod2001), nome, d, m))

# 1991: se il codice esiste anche nel 2001 con lo stesso nome si usa quello, poi il nome
n2001 = {(c): norm(n) for (a, c, n, d, m) in rows if a == 2001}
d2001 = {(c): d for (a, c, n, d, m) in rows if a == 2001}
for r in l91.itertuples():
    d = None
    m = 'nessuno'
    if r.cod1991 in n2001 and n2001[r.cod1991] == norm(r.nome) and d2001.get(r.cod1991):
        d, m = d2001[r.cod1991], 'codice'
    else:
        d, m = risolvi(1991, r.cod1991, r.nome, r.reg, None)
    rows.append((1991, r.cod1991, r.nome, d, m))

rac = pd.DataFrame(rows, columns=['anno', 'cod_storico', 'nome_storico', 'pro_com_2021', 'metodo'])
rac['pro_com_2021'] = rac['pro_com_2021'].astype('Int64')
rac.to_csv(OUT / 'raccordo_codici.csv', index=False)
syn = {}
for a, g in rac.groupby('anno'):
    syn[int(a)] = {'comuni_storici': int(len(g)), **{k: int(v) for k, v in g['metodo'].value_counts().items()}}
syn['comuni_2021'] = int(len(com))
json.dump(syn, open(OUT / 'raccordo_sintesi.json', 'w', encoding='utf8'), indent=1)
print(json.dumps(syn, indent=1))
