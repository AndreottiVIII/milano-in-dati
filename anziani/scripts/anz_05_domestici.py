"""Dai file INPS scaricati da anz_04_inps.py fa docs/anziani/data/domestici.json:
per ogni provincia lombarda, anno 2016-2025: badanti e colf per sesso, italiani e stranieri; più il totale Italia."""
import json
R = 'C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/'
LOMB = ["Varese", "Como", "Sondrio", "Milano", "Bergamo", "Brescia", "Pavia", "Cremona", "Mantova", "Lecco", "Lodi", "Monza e della Brianza", "Monza e Brianza"]
num = lambda s: int(s.replace('.', '')) if s not in ('', '-', None) else None
def anni(node):
    return {v['value']: num(v['measures'][0]['value']) for v in node['columns'][0]['values']}
def walk(node, path, out):
    for v in node['values']:
        p = path + [v['value']]
        if 'rows' in v: walk(v['rows'][0], p, out)
        elif 'columns' in v: out[tuple(p)] = anni(v)
    return out
a = walk(json.load(open(R + 'anziani/raw/inps/q_prov_tipo_sesso.json', encoding='utf-8')), [], {})
b = walk(json.load(open(R + 'anziani/raw/inps/q_prov_naz.json', encoding='utf-8')), [], {})
provs = sorted({k[0] for k in a})
print('province nei dati:', len(provs), [p for p in provs if 'Monza' in p or 'Total' in p][:5])
out = {'anni': list(range(2016, 2026)), 'province': {}}
for pv in provs:
    if pv not in LOMB and not pv.lower().startswith('total'): continue
    d = {}
    for t, tk in (('Badante', 'bad'), ('Colf-altro', 'colf')):
        for s, sk in (('Femmine', 'f'), ('Maschi', 'm')):
            v = a.get((pv, t, s), {}); d[tk + '_' + sk] = [v.get(str(y)) for y in out['anni']]
    for n, nk in (('Italiani', 'ita'), ('Stranieri', 'str')):
        v = b.get((pv, n), {}); d[nk] = [v.get(str(y)) for y in out['anni']]
    out['province']['Monza e Brianza' if 'Monza' in pv else ('Italia' if pv.lower().startswith('total') else pv)] = d
# totale Italia dalla somma delle province
it = {}
for k in ('bad_f', 'bad_m', 'colf_f', 'colf_m'):
    t, s = {'bad': 'Badante', 'colf': 'Colf-altro'}[k[:-2]], {'f': 'Femmine', 'm': 'Maschi'}[k[-1]]
    it[k] = [sum((a.get((pv, t, s), {}).get(str(y)) or 0) for pv in provs if not pv.lower().startswith('total')) for y in out['anni']]
out['province']['Italia'] = it
json.dump(out, open(R + 'docs/anziani/data/domestici.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
m = out['province']['Milano']
for i, y in enumerate(out['anni']):
    bad = m['bad_f'][i] + m['bad_m'][i]; colf = m['colf_f'][i] + m['colf_m'][i]
    print(y, 'badanti', bad, 'colf', colf, 'tot', bad + colf, 'donne%', round(100 * (m['bad_f'][i] + m['colf_f'][i]) / (bad + colf), 1), 'stranieri%', round(100 * m['str'][i] / (m['str'][i] + m['ita'][i]), 1))
print('Italia 2025 tot', sum(it[k][-1] for k in it))
