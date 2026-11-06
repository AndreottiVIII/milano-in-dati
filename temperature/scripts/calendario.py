"""Prepara docs/temperature/data/calendario/MM-DD.json: per ogni giorno del calendario, minima e massima di Brera in ogni anno.
Serve al grafico "Un giorno a scelta" della pagina, che così scarica pochi KB invece dei 27 file per decennio (3,2 MB).
Uso: python -I -X utf8 calendario.py <milano-in-dati>   (rilanciabile: riscrive tutto)
Legge docs/temperature/data/giorni/<decennio>.json: r[i] = giorno da+i: [tmin, tmax, tmean, fonte]."""
import sys, os, json, glob, datetime
P = sys.argv[1]
G = os.path.join(P, 'docs', 'temperature', 'data', 'giorni')
OUT = os.path.join(P, 'docs', 'temperature', 'data', 'calendario')
os.makedirs(OUT, exist_ok=True)
cal = {}
for f in sorted(glob.glob(os.path.join(G, '[0-9]*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    g0 = datetime.date.fromisoformat(d['da'])
    for i, r in enumerate(d['r']):
        if not r or r[0] is None or r[1] is None:
            continue
        g = g0 + datetime.timedelta(days=i)
        k = '%02d-%02d' % (g.month, g.day)
        c = cal.setdefault(k, {'y': [], 'n': [], 'x': []})
        c['y'].append(g.year); c['n'].append(r[0]); c['x'].append(r[1])
for k, c in cal.items():
    json.dump(c, open(os.path.join(OUT, k + '.json'), 'w', encoding='utf-8'), separators=(',', ':'))
dim = [os.path.getsize(os.path.join(OUT, k + '.json')) for k in cal]
print(len(cal), 'giorni, file da', min(dim), 'a', max(dim), 'byte')
