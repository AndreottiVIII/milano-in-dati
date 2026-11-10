"""Ascensori nelle scuole, anno scolastico 2020/21 (ds1868, Comune di Milano, CC BY).
Uso: python -I -X utf8 scuole/scripts/ascensori.py <percorso di milano-in-dati>
Scrive docs/scuole/data/ascensori_2020_21.csv: schede (righe del file) ed edifici (codice edificio unico)."""
import csv, sys, collections as C
from pathlib import Path
R = Path(sys.argv[1])
rows = list(csv.DictReader(open(R/'scuole'/'raw'/'ds1868_barriere_2020_21.csv', encoding='utf-8-sig'), delimiter=';'))
K = {'SI': 'si', 'NO': 'no', 'NON DEFINITO': 'nd'}
sch = C.Counter(K[x['ASCENSORETRASPORTODISABILI']] for x in rows)
ed = {}
for x in rows:
    ed.setdefault(x['CODICEEDIFICIO'], set()).add(K[x['ASCENSORETRASPORTODISABILI']])
# un edificio ha lo stesso valore in tutte le sue schede (verificato); altrimenti vale "si" se almeno una scheda dice si
def val(s): return 'si' if 'si' in s else 'no' if 'no' in s else 'nd'
edc = C.Counter(val(s) for s in ed.values())
out = R/'docs'/'scuole'/'data'/'ascensori_2020_21.csv'
with open(out, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['unita', 'si', 'no', 'non_definito', 'totale'])
    w.writerow(['schede', sch['si'], sch['no'], sch['nd'], len(rows)])
    w.writerow(['edifici', edc['si'], edc['no'], edc['nd'], len(ed)])
print(open(out, encoding='utf-8').read())
