"""Legge le tabelle zip delle statistiche catastali (Agenzia delle Entrate) già scaricate
in dati_grezzi/ e scrive pulito/catasto_categorie.csv: una riga per anno, provincia,
capoluogo/resto, categoria. Uso: python -I -X utf8 scripts/01_estrai_catasto.py"""
import os, re, csv, glob, openpyxl
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(R, 'dati_grezzi')
rows = {}   # (anno, sigla, tipo, cat) -> [uiu, rendita, c6, c7]
nomi = {}
def num(x):
    return float(x) if isinstance(x, (int, float)) else None
def cat_da_titolo(t, gruppo):
    m = re.search(r'CATEGORIA\s*(?:([A-F])\s*)?0?(\d+)', str(t or ''), re.I)
    return '%s%02d' % ((m.group(1) or gruppo).upper(), int(m.group(2))) if m else None
for anno in range(2018, 2025):
    for kind, tipo in (('Capoluogo', 'cap'), ('Provincia', 'prov')):
        for p in glob.glob(os.path.join(G, 'x%d' % anno, kind, '*.xlsx')):
            wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
            for ws in wb:
                it = ws.iter_rows(values_only=True)
                r = [next(it, None) for _ in range(2)]
                cat = cat_da_titolo(r[1][0] if r[1] else None, re.search(r'GRUPPO_([A-F])_', p).group(1) if re.search(r'GRUPPO_([A-F])_', p) else 'A')
                if not cat or ws.title.startswith(('2011', '2009')):
                    continue
                for row in it:
                    if not row or len(row) < 5: continue
                    row = tuple(row) + (None,) * (8 - len(row))
                    sig = row[2]
                    if not (isinstance(sig, str) and len(sig.strip()) == 2): continue
                    u = num(row[4])
                    if u is None: continue
                    sig = sig.strip().upper()
                    if tipo == 'cap': nomi[sig] = str(row[3]).strip().title()
                    rows[(anno, sig, tipo, cat)] = [u, num(row[5]) or 0, num(row[6]) or 0, num(row[7]) or 0]
# resto della provincia = provincia - capoluogo
for (a, s, t, c), v in list(rows.items()):
    if t == 'prov':
        cp = rows.get((a, s, 'cap', c), [0, 0, 0, 0])
        rows[(a, s, 'resto', c)] = [v[i] - cp[i] for i in range(4)]
# 2025: csv già diviso
fl = lambda s: float(s.replace(',', '.'))
for f in glob.glob(os.path.join(G, 'x2025', 'Gruppo_[A-F].csv')):
    for r in csv.DictReader(open(f, encoding='utf-8'), delimiter=';'):
        k = r['Cap']; t = 'cap' if k == 'cap' else 'resto'
        key = (2025, r['Provincia'], t, r['Categoria'])
        g = lambda *ks: next((fl(r[k]) for k in ks if k in r and r[k] != ''), 0.0)
        c6 = g('Totale_Vani', 'Totale_Consistenza_MQ', 'Totale_Consistenza_MC')
        c7 = g('Totale_Superficie_MQ')
        rows[key] = [g('Totale_UIU', 'UIU con rend'), g('Totale_Rendita'), c6, c7]
os.makedirs(os.path.join(R, 'pulito'), exist_ok=True)
with open(os.path.join(R, 'pulito', 'catasto_categorie.csv'), 'w', encoding='utf-8', newline='') as fo:
    w = csv.writer(fo, delimiter=';')
    w.writerow(['anno', 'provincia', 'capoluogo', 'tipo', 'categoria', 'unita', 'rendita_euro', 'vani_o_mq', 'superficie_mq'])
    for (a, s, t, c) in sorted(rows):
        if t == 'prov': continue
        v = rows[(a, s, t, c)]
        w.writerow([a, s, nomi.get(s, ''), t, c, int(round(v[0])), round(v[1], 2), round(v[2], 1), round(v[3], 1)])
print(len(rows), 'righe;', len(nomi), 'capoluoghi')
