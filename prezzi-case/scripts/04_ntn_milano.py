"""NTN (compravendite normalizzate) residenziali del Comune di Milano (= capoluogo della provincia MI), per trimestre.
Fonti, tutte in raw/ (scaricate da pagine pubbliche dell'Agenzia delle Entrate, nessun accesso riservato):
  raw/omi_ntn_archivio/Residenziale_<anno>.xls   serie vecchia 2004-2016 (foglio 1 = trimestrale)
  raw/omi_ntn/RESIDENZIALE_DEFINITIVO_2011_2024.zip  -> RES.csv   serie nuova 2011-2024
  raw/omi_ntn/RESIDENZIALE_2025_2026_PROVV.zip       -> RES.csv   provvisoria 2025-2026
Uscite in pulito/:
  ntn_milano_trimestrale.csv        tutte le serie, una riga per anno/trimestre/serie (le serie NON sono fuse)
  ntn_milano_confronto_2011_2016.csv  sovrapposizione delle due serie (vecchia e nuova) per vedere le revisioni
Uso: python -I 04_ntn_milano.py <cartella_raw> <cartella_pulito>
"""
import sys, os, io, zipfile, re
import pandas as pd

raw, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
righe = []

# ---- serie vecchia (xls)
arch = os.path.join(raw, 'omi_ntn_archivio')
for anno in range(2004, 2017):
    p = os.path.join(arch, f'Residenziale_{anno}.xls')
    if not os.path.exists(p):
        print('manca', p)
        continue
    x = pd.read_excel(p, sheet_name=0, header=None)
    mi = x[x.apply(lambda r: (r.astype(str).str.strip() == 'MI').any(), axis=1)]
    if len(mi) != 1:
        raise SystemExit(f'{p}: trovate {len(mi)} righe MI invece di 1')
    r = mi.iloc[0]
    # controllo l'intestazione: cerco la riga con "intera provincia"/"capoluogo" (la riga cambia da un anno all'altro)
    atteso = ['intera provincia', 'capoluogo'] * 4
    ok = False
    for i in range(min(12, len(x))):
        intest = x.iloc[i, 3:11].astype(str).str.strip().str.lower().tolist()
        if intest == atteso:
            ok = True
            break
    if not ok:
        raise SystemExit(f'{p}: intestazione "intera provincia/capoluogo" non trovata nelle prime righe')
    for t in range(4):
        righe.append(dict(anno=anno, trimestre=t + 1, serie='archivio_2004_2016',
                          ntn_capoluogo=float(r.iloc[3 + 2 * t + 1]), ntn_provincia=float(r.iloc[3 + 2 * t])))


# ---- serie nuove (zip -> RES.csv, separatore ; e virgola decimale)
def leggi_res(zpath, nome):
    with zipfile.ZipFile(zpath) as z:
        with z.open('RES.csv') as f:
            return pd.read_csv(io.TextIOWrapper(f, encoding='utf-8-sig'), sep=';', decimal=',', dtype=str)


def nuova(zpath, serie, pat):
    d = leggi_res(zpath, serie)
    d.columns = [c.strip() for c in d.columns]
    pcol = [c for c in d.columns if c.lower() == 'prov'][0]
    ccol = [c for c in d.columns if c.lower() == 'cap'][0]
    m = d[d[pcol] == 'MI']
    cap = m[m[ccol].str.lower() == 'cap'].iloc[0]
    non = m[m[ccol].str.lower() == 'noncap'].iloc[0]
    for c in d.columns:
        mm = re.fullmatch(pat, c)
        if mm:
            anno, tr = int(mm.group(1)), int(mm.group(2))
            if tr > 4:
                continue
            a = float(str(cap[c]).replace(',', '.'))
            b = float(str(non[c]).replace(',', '.'))
            righe.append(dict(anno=anno, trimestre=tr, serie=serie, ntn_capoluogo=a, ntn_provincia=a + b))


nuova(os.path.join(raw, 'omi_ntn', 'RESIDENZIALE_DEFINITIVO_2011_2024.zip'), 'definitiva_2011_2024', r'(\d{4})_(\d)')
nuova(os.path.join(raw, 'omi_ntn', 'RESIDENZIALE_2025_2026_PROVV.zip'), 'provvisoria_2025_2026', r'(\d{4})_(\d)_PROVV_NTN')

df = pd.DataFrame(righe).sort_values(['anno', 'trimestre', 'serie'])
df.to_csv(os.path.join(out, 'ntn_milano_trimestrale.csv'), index=False)
print('ntn_milano_trimestrale.csv:', len(df), 'righe;', df.groupby('serie').anno.agg(['min', 'max']).to_dict('index'))

# ---- confronto nel periodo in cui le due serie si sovrappongono
a = df[df.serie == 'archivio_2004_2016'].set_index(['anno', 'trimestre'])
b = df[df.serie == 'definitiva_2011_2024'].set_index(['anno', 'trimestre'])
j = a.join(b, lsuffix='_vecchia', rsuffix='_nuova', how='inner')
j['differenza_pct_capoluogo'] = (j.ntn_capoluogo_nuova / j.ntn_capoluogo_vecchia - 1) * 100
j[['ntn_capoluogo_vecchia', 'ntn_capoluogo_nuova', 'differenza_pct_capoluogo']].round(2).to_csv(
    os.path.join(out, 'ntn_milano_confronto_2011_2016.csv'))
print('confronto 2011-2016: differenza % media', round(j.differenza_pct_capoluogo.mean(), 2),
      'min', round(j.differenza_pct_capoluogo.min(), 2), 'max', round(j.differenza_pct_capoluogo.max(), 2))
