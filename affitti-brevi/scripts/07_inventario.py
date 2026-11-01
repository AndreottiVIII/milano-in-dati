r"""Fase 1 - inventario dei file scaricati: righe, dimensione, date. Uso: python -I -X utf8 07_inventario.py <affitti-brevi (assoluta)>
Scrive pulito\inventario_fonti.csv. Non apre le colonne con testi personali: conta solo le righe.
"""
import sys, gzip, os, csv, datetime
from pathlib import Path

base = Path(sys.argv[1]); raw = base/'raw'
rows = []
def nlines(p):
    op = gzip.open if str(p).endswith('.gz') else open
    n = 0
    with op(p, 'rb') as f:
        for ch in iter(lambda: f.read(1 << 22), b''):
            n += ch.count(b'\n')
    return n
for p in sorted(raw.rglob('*')):
    if not p.is_file() or p.suffix in ('.html', '.js', '.part') or 'pagine' in p.parts and p.suffix != '.csv' and p.suffix != '.json':
        continue
    righe = ''
    if p.suffix in ('.gz', '.csv') and p.stat().st_size < 400_000_000:
        # i csv di listings/reviews contengono righe su piu linee (testi): il conteggio e' solo indicativo
        try: righe = nlines(p) - 1
        except Exception: righe = ''
    rows.append(dict(file=str(p.relative_to(base)), byte=p.stat().st_size, righe_indicative=righe,
                     scaricato_il=datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M')))
with open(base/'pulito/inventario_fonti.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['file', 'byte', 'righe_indicative', 'scaricato_il']); w.writeheader(); w.writerows(rows)
tot = sum(r['byte'] for r in rows)
print(len(rows), 'file', round(tot/1e6, 1), 'MB')
