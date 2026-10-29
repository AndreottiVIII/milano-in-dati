"""Passo 1a: legge tutti i CSV di risultati e voti, li porta a una forma unica e salva un pickle
temporaneo (cartella di lavoro passata come argomento) + diagnostica.
uso: python -I 11_carica.py <cartella elezioni> <cartella lavoro>
"""
import sys, os, re, io, pickle
import pandas as pd

base, work = sys.argv[1], sys.argv[2]
inv = pd.read_csv(os.path.join(base, 'inventario_dataset.csv'), encoding='utf-8-sig')
inv = inv[inv.kind.isin(['risultati_sezione', 'riepilogo_sezione', 'voti_lista_sezione'])].copy()
inv['ds'] = inv.ds.astype(int)

TERR_COLS = ['Circoscrizione', 'Zona', 'Municipio']
log = []  # (ds, nota)


def read_csv(path):
    raw = open(path, 'rb').read()
    enc = 'utf-8'
    try:
        txt = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        txt = raw.decode('cp1252')
        enc = 'cp1252'
    df = pd.read_csv(io.StringIO(txt), sep=';', dtype=str, keep_default_na=False)
    df.columns = [c.strip().strip('"') for c in df.columns]
    return df, enc


def to_int(s):
    """testo -> intero; accetta '113,00', vuoto -> NaN"""
    s = s.astype(str).str.strip().str.replace(',00', '', regex=False).str.replace('.00', '', regex=False)
    return pd.to_numeric(s.replace('', pd.NA), errors='coerce')


out = {}
for _, r in inv.iterrows():
    ds = r.ds
    path = os.path.join(base, 'raw', r.csv_file)
    df, enc = read_csv(path)
    tcol = next((c for c in TERR_COLS if c in df.columns), None)
    d = pd.DataFrame()
    d['sezione_txt'] = df['Sezione'].str.strip()
    d['sezione'] = to_int(df['Sezione'])
    if tcol:
        d['territorio'] = to_int(df[tcol])
    else:
        d['territorio'] = pd.NA
    d['sessione'] = df['Sessione'].str.strip() if 'Sessione' in df else ''
    d['nome_elezione'] = df['Nome_Elezione'].str.strip() if 'Nome_Elezione' in df else ''
    for c in ['Elettori', 'Votanti', 'Validi', 'Non validi', 'Si', 'No', 'Voti']:
        if c in df.columns:
            d[c] = to_int(df[c])
    if 'Lista' in df.columns:
        d['lista'] = df['Lista'].str.strip().str.replace(r'\s+', ' ', regex=True)
    out[ds] = dict(df=d, tcol=tcol, enc=enc, title=r.title, kind=r.kind, etype=r.election_type,
                   date_start=r.date_start, nrow=len(df))
    print(ds, r.kind[:5], tcol, enc, len(df), flush=True)

with open(os.path.join(work, 'carica.pkl'), 'wb') as f:
    pickle.dump(out, f)
