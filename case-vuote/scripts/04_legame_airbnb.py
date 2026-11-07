"""Legame tra case senza residenti e case intere su Airbnb, per quartiere.
Legge docs/case-vuote/data/nil.csv e nil.geojson e docs/affitti-brevi/data/nil.csv.
Scrive docs/case-vuote/data/legame_airbnb.csv (file nuovo) e stampa le correlazioni."""
import csv, json, sys
from pathlib import Path
from scipy.stats import pearsonr, spearmanr

R = Path(__file__).resolve().parents[2]
CV = R / 'docs/case-vuote/data'
AB = R / 'docs/affitti-brevi/data/nil.csv'
OUT = CV / 'legame_airbnb.csv'

def rd(p, d):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=d))

cv = rd(CV / 'nil.csv', ';')
ab = {int(r['nil']): r for r in rd(AB, ',')}
rows = []
for r in cv:
    i = int(r['id_nil']); a = ab.get(i)
    if a is None: continue
    abit = float(r['abitazioni_2023']); ci = float(a['case_intere'])
    rows.append(dict(id_nil=i, quartiere=r['quartiere'], municipio=r['municipio_prevalente'],
        distanza_duomo_km=r['distanza_duomo_km'], abitazioni_2023=int(abit),
        quota_senza_residenti_pct_2023=r['quota_non_occupate_pct_2023'],
        case_intere_airbnb=int(ci), case_intere_ogni_1000_abitazioni=round(ci / abit * 1000, 1),
        confronti=r['abbastanza_abitazioni_per_confronti']))
if OUT.exists():
    sys.exit('esiste già: ' + str(OUT))
keys = list(rows[0].keys())
with open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys, delimiter=';'); w.writeheader(); w.writerows(rows)

def cor(sel, nome):
    x = [r['case_intere_ogni_1000_abitazioni'] for r in sel]
    y = [float(r['quota_senza_residenti_pct_2023']) for r in sel]
    p = pearsonr(x, y); s = spearmanr(x, y)
    print(f'{nome}: n={len(sel)} pearson={p[0]:.3f} spearman={s[0]:.3f}')
ok = [r for r in rows if r['confronti'] == '1']
cor(ok, 'tutti (69)')
cor([r for r in ok if r['municipio'] != '1'], 'senza Municipio 1')
cor([r for r in ok if r['municipio'] == '1'], 'solo Municipio 1')
cor([r for r in ok if r['municipio'] != '1' and float(r['distanza_duomo_km']) > 4], 'oltre 4 km')
