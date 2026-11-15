"""Acquisizioni di cittadinanza italiana a Milano per anno e motivo (2003-2024).
Legge ds221 (2003-2020) e ds1964 (2021-2024), CC BY, Comune di Milano; somma maschi e femmine
e raggruppa i motivi in cinque. Scrive docs/comunita/data/naturalizzazioni_motivo.json.
Uso: python -I -X utf8 comunita/scripts/naturalizzazioni_motivo.py"""
import csv, collections, json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE = [os.path.join(R, 'popolazione', 'raw', 'comune_ds221', 'ds221-popolazione-stranieri-acquisizioni-cittadinanza.csv'),
        os.path.join(R, 'popolazione', 'raw', 'comune_ds1964', 'ds1964_acquisizioni-cittadinanza_motivo.csv')]
GRUPPO = {'Residenza in Italia da almeno 10 anni': 'residenza',
          'Convivenza genitore che ha acquisito la cittadinanza italiana': 'figli',
          'Matrimonio': 'matrimonio',
          'Nascita in Italia e raggiungimento della maggiore età': 'nascita',
          'Altro': 'altro', 'n.d.': 'altro'}
tot = collections.defaultdict(collections.Counter)
for f in FILE:
    for r in csv.reader(open(f, encoding='utf-8-sig'), delimiter=';'):
        if r[0] == 'Anno':
            continue
        tot[int(r[0])][GRUPPO[r[2]]] += int(r[3])
anni = sorted(tot)
out = {'anni': anni}
for g in ['residenza', 'figli', 'matrimonio', 'nascita', 'altro']:
    out[g] = [tot[a][g] for a in anni]
out['totale'] = [sum(tot[a].values()) for a in anni]
p = os.path.join(R, 'docs', 'comunita', 'data', 'naturalizzazioni_motivo.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(p, out['totale'][:3], out['totale'][-1])
