"""Pagina La Scala (v2): conta le recite per direttore e per decennio, usando solo i file già pubblicati in docs/scala/data/serate/.
Scrive docs/scala/data/direttori_decenni.json (nome nuovo, non sovrascrive nulla).
Uso: python -I -X utf8 scala/scripts/scala_v2_dati.py   (dalla cartella del progetto)"""
import json, os, collections, datetime
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(R, 'docs', 'scala', 'data')
decs = list(range(1940, 2030, 10))
tot = collections.Counter(); per = collections.defaultdict(lambda: [0] * len(decs))
for i, d in enumerate(decs):
    for r in json.load(open(os.path.join(D, 'serate', f'{d}.json'), encoding='utf8')):
        for n in (r[7] or '').split(';'):
            n = n.strip()
            if n:
                tot[n] += 1; per[n][i] += 1
top = [n for n, _ in tot.most_common(12)]
def primo(n): return next(i for i, v in enumerate(per[n]) if v)
top.sort(key=lambda n: (primo(n), -tot[n]))
out = {'decenni': [str(d) for d in decs],
       'direttori': [{'n': n, 't': tot[n], 'd': per[n]} for n in top],
       'generato': datetime.date.today().isoformat()}
json.dump(out, open(os.path.join(D, 'direttori_decenni.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print([(n, tot[n]) for n in top])
