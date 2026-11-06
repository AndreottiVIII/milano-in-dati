"""Fermate delle linee di metro con la speranza di vita stimata del quartiere che attraversano.

Uso (percorsi assoluti):
  python -I -X utf8 linee_metro.py <fermate_indicatori.csv> <nil.geojson> <uscita.csv>
dove
  fermate_indicatori.csv = docs/viaggio-linea/data/fermate_indicatori.csv (fermata -> quartiere)
  nil.geojson            = docs/speranza-vita/data/nil.geojson (stime per quartiere)
  uscita.csv             = docs/speranza-vita/data/linee_metro_e0.csv  (file NUOVO, non sovrascrive gli altri)

Tiene solo M1-M5. Una fermata ha la stima del suo quartiere (2012-2019, tutti i sessi) solo se il quartiere
ha almeno 3.000 residenti e la stima non e' in 'cautela' (Morivione); altrimenti 'affidabile' = 0.
CSV: separatore punto e virgola, virgola per i decimali (come gli altri file della pagina).
"""
import csv, json, sys

fer, geo, out = sys.argv[1:4]
g = json.load(open(geo, encoding='utf-8'))
P = {f['properties']['i']: f['properties'] for f in g['features']}

def n(x, d=2):
    return ('%.*f' % (d, x)).replace('.', ',')

righe = []
for r in csv.DictReader(open(fer, encoding='utf-8-sig'), delimiter=';'):
    if r['linea'] not in ('M1', 'M2', 'M3', 'M4', 'M5'):
        continue
    i = int(float(r['id_nil'])) if r['id_nil'] else None
    p = P.get(i)
    ok = bool(p and p['cl'] == 1 and not (p.get('fm') or 0) > 1.25 and p.get('w') and p['w'].get('2012-2019'))
    w = p['w']['2012-2019']['T'] if ok else None
    righe.append([r['linea'], r['posizione'], r['fermata'], i or '', p['n'] if p else '', p['ab24'] if p else '',
                  n(w[3]) if ok else '', n(w[4]) if ok else '', n(w[5]) if ok else '', 1 if ok else 0])

with open(out, 'w', encoding='utf-8', newline='') as f:
    wr = csv.writer(f, delimiter=';', lineterminator='\n')
    wr.writerow(['linea', 'posizione', 'fermata', 'id_quartiere', 'quartiere', 'residenti_2024',
                 'speranza_vita_stimata_2012_2019', 'estremo_basso', 'estremo_alto', 'stima_affidabile'])
    wr.writerows(righe)
print(len(righe), 'fermate;', sum(r[-1] for r in righe), 'con stima')
