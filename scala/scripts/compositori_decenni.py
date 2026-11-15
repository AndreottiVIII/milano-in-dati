"""Compositori dei concerti per decennio: conta, per ogni compositore e decennio, le locandine di concerto
che lo citano (una volta per locandina). Legge scala/locandine/concerti_compositori.csv.
Scrive docs/scala/data/concerti_decenni.json (primi 14 compositori, gli stessi di riepilogo.json).
Uso: python -I -X utf8 scala/scripts/compositori_decenni.py"""
import csv, collections as C, json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dec = list(range(1940, 2030, 10))
cnt = C.defaultdict(lambda: [0] * len(dec)); tot = C.Counter()
for x in csv.DictReader(open(os.path.join(R, 'scala', 'locandine', 'concerti_compositori.csv'), encoding='utf-8-sig')):
    d = int(x['data'][:3] + '0')
    for c in set(q for q in x['musiche'].split(' ; ') if q):
        cnt[c][dec.index(d)] += 1; tot[c] += 1
rie = json.load(open(os.path.join(R, 'docs', 'scala', 'data', 'serate', 'riepilogo.json'), encoding='utf-8'))
top = [x['c'] for x in rie['concerti_compositori'][:14]]
for x in rie['concerti_compositori'][:14]:
    assert tot[x['c']] == x['n'], (x, tot[x['c']])
out = {'decenni': dec, 'compositori': [{'c': c, 'n': tot[c], 'd': cnt[c]} for c in top]}
p = os.path.join(R, 'docs', 'scala', 'data', 'concerti_decenni.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(p, [(x['c'], x['n']) for x in out['compositori']][:4])
