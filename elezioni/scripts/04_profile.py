"""Profila ogni CSV scaricato: codifica, separatore, colonne, righe, sezioni distinte, date. Nessuna pulizia."""
import sys, os, csv, io, json, re
import pandas as pd
rawdir, out = sys.argv[1:3]
rows = []
def detect(path):
    b = open(path,'rb').read()
    bom = b.startswith(b'\xef\xbb\xbf')
    try:
        t = b.decode('utf-8-sig'); enc = 'utf-8' + ('-bom' if bom else '')
    except UnicodeDecodeError:
        t = b.decode('cp1252', errors='replace'); enc = 'cp1252(non utf-8)'
    first = t.split('\n',1)[0]
    delim = max([';', ',', '\t', '|'], key=lambda d: first.count(d))
    crlf = '\r\n' in t[:2000]
    return t, enc, delim, first.strip('\r'), crlf, ('�' in t)
for root, dirs, files in os.walk(rawdir):
    for fn in files:
        if not fn.lower().endswith('.csv'): continue
        path = os.path.join(root, fn)
        rel = os.path.relpath(path, rawdir)
        ds = rel.split(os.sep)[0]
        t, enc, delim, first, crlf, repl = detect(path)
        rec = dict(dataset=ds, file=rel, size=os.path.getsize(path), encoding=enc, delimiter=delim, crlf=crlf, has_replacement_char=repl, header=first)
        try:
            df = pd.read_csv(io.StringIO(t), sep=delim, dtype=str, keep_default_na=False, on_bad_lines='skip')
            rec['rows'] = len(df); rec['ncols'] = df.shape[1]
            cols = {c.lower().strip(): c for c in df.columns}
            sc = next((cols[k] for k in ('sezione','sezione elettorale','sez','n_sez') if k in cols), None)
            rec['sez_col'] = sc or ''
            if sc is not None:
                s = pd.to_numeric(df[sc], errors='coerce')
                rec['sez_distinct'] = int(s.nunique()); rec['sez_min'] = s.min(); rec['sez_max'] = s.max()
                rec['sez_nonnumeric'] = int(s.isna().sum())
            dc = next((cols[k] for k in ('sessione','data','data_elezione') if k in cols), None)
            if dc: rec['dates'] = ';'.join(sorted(df[dc].unique())[:6])
            for k in ('elettori','elettori_tot','tot_elettori','votanti'):
                pass
        except Exception as e:
            rec['error'] = repr(e)[:200]
        rows.append(rec)
pd.DataFrame(rows).sort_values('file').to_csv(out, index=False, encoding='utf-8-sig')
print(len(rows), 'csv profilati')
