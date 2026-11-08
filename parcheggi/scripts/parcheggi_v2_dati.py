"""Dati nuovi per la pagina Parcheggi (versione 2).
Uso: python -I -X utf8 scripts/parcheggi_v2_dati.py <cartella_progetto>
Scrive in docs/parcheggi/data/:
  nil_cerchie.csv  per ogni quartiere, quota di area (%) in ciascuna zona tariffaria degli ambiti della sosta
  auto_serie.csv   autovetture iscritte a Milano per anno (copia dalla serie della pagina Auto)
Non tocca i file esistenti."""
import csv, json, math, os, sys
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely import affinity

R = sys.argv[1]
D = os.path.join(R, 'docs', 'parcheggi', 'data')
K = math.cos(45.46 * math.pi / 180)

def proj(g):
    return affinity.scale(shape(g), xfact=K, yfact=1, origin=(0, 0))

nil = json.load(open(os.path.join(D, 'nil.geojson'), encoding='utf-8'))
amb = json.load(open(os.path.join(D, 'ambiti.geojson'), encoding='utf-8'))
CER = ['Area C / Bastioni', 'Cerchia filoviaria', 'Extra-filoviaria', 'Interscambio (via Impastato)']
per = {c: [] for c in CER}
for f in amb['features']:
    per[f['properties']['c']].append(proj(f['geometry']).buffer(0))
uni = {c: unary_union(v) for c, v in per.items()}
# le zone non si sovrappongono: se succede, la più cara vince
tot = None
chiusa = {}
acc = None
for c in CER:
    g = uni[c] if acc is None else uni[c].difference(acc)
    chiusa[c] = g
    acc = g if acc is None else acc.union(uni[c])

rows = []
for f in nil['features']:
    p = f['properties']
    g = proj(f['geometry']).buffer(0)
    a = g.area
    q = [chiusa[c].intersection(g).area / a * 100 for c in CER]
    rows.append([p['i'], p['n'], p['qa']] + [round(x, 1) for x in q] + [round(sum(q), 1)])
rows.sort(key=lambda r: r[0])
with open(os.path.join(D, 'nil_cerchie.csv'), 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh, delimiter=';')
    w.writerow(['id_nil', 'nil', 'quota_in_ambiti_pct_file', 'area_c_pct', 'filoviaria_pct', 'extra_filoviaria_pct', 'interscambio_pct', 'somma_pct'])
    w.writerows(rows)
# controllo: la somma deve restare vicina alla quota già nel file dei quartieri
mx = max(abs(r[7] - r[2]) for r in rows)
print('differenza massima tra somma e quota nel file:', mx)

src = os.path.join(R, 'docs', 'auto', 'data', 'serie_milano_comune.csv')
rr = list(csv.DictReader(open(src, encoding='utf-8'), delimiter=';'))
with open(os.path.join(D, 'auto_serie.csv'), 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh, delimiter=';')
    w.writerow(['anno', 'autovetture'])
    for r in rr:
        w.writerow([r['anno'], r['autovetture']])
print('righe auto:', len(rr))
