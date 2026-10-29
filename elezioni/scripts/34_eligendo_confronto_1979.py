"""Confronta Camera 1979: Eligendo (comune) vs somma delle sezioni del Comune di Milano.
Uso: python -I 34_eligendo_confronto_1979.py <pulito_dir> <uscita.csv>"""
import sys, os, csv, collections
p, out = sys.argv[1], sys.argv[2]
# nomi diversi delle stesse liste tra Eligendo e Comune
MAP = {'P.RAD': 'Part. Radicale', 'MSI-DN': 'MSI', 'NUOVA SIN.UNITA': 'Nuova Sin. Unita', 'DN-CD': 'Dem. Nazionale',
       'POE': 'Part. Op. Eur.', 'PARTITO POPOLARE ITALIANO': 'PPI'}
el = collections.OrderedDict()
for r in csv.DictReader(open(os.path.join(p, 'milano_pre1979.csv'), encoding='utf-8-sig')):
    if r['elezione_id'] == 'camera_1979-06-03': el[MAP.get(r['lista'], r['lista'])] = int(r['voti'])
com = collections.Counter()
for r in csv.DictReader(open(os.path.join(p, 'voti_sezione.csv'), encoding='utf-8-sig')):
    if r['elezione_id'] == 'camera_1979-06-03': com[r['lista']] += int(r['voti'] or 0)
liste = sorted(set(el) | set(com), key=lambda x: -max(el.get(x, 0), com.get(x, 0)))
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f); w.writerow(['lista', 'eligendo', 'comune_sezioni', 'differenza', 'differenza_pct'])
    for l in liste:
        a, b = el.get(l), com.get(l)
        w.writerow([l, a if a is not None else '', b if b is not None else '', (a or 0) - (b or 0), round(100 * ((a or 0) - (b or 0)) / max(a or b, 1), 3)])
    ta, tb = sum(el.values()), sum(com.values())
    w.writerow(['TOTALE', ta, tb, ta - tb, round(100 * (ta - tb) / ta, 3)])
print(open(out, encoding='utf-8-sig').read())
