"""Chi non vota contro il primo candidato (o la prima lista), per quartiere.
Legge docs/elezioni/data/nil/*.json e index.json, scrive docs/elezioni/data/non_votanti_nil.json.
Solo quartieri con almeno 3.000 elettori."""
import json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(R, 'docs', 'elezioni', 'data')
J = lambda p: json.load(open(os.path.join(D, p), encoding='utf-8'))
ix = {e['id']: e for e in J('index.json')['elezioni']}
info = J('nil_info.json')
out = {}
for key, eid in (('c21', 'comunali_sindaco_2021-10-03'), ('c22', 'camera_2022-09-25')):
    e = ix[eid]; n = J('nil/%s.json' % eid)
    # candidati o liste con lo stesso nome vanno sommati solo se ripetuti: qui ogni voce e' una persona o una lista
    def best(v):
        i = max(range(len(v)), key=lambda k: v[k]); return i, v[i]
    ci, cv = best(e['city']['v'])
    q = {}
    for k, d in n['p'].items():
        if d['e'] < 3000: continue
        i, b = best(d['v'])
        q[k] = {'n': info[k]['nome'], 'e': d['e'], 'vt': d['vt'], 'f': b, 'fn': e['par'][i][0]}
    out[key] = {'id': eid, 'label': e['label'], 'data': e['data'],
                'citta': {'e': e['city']['e'], 'vt': e['city']['vt'], 'f': cv, 'fn': e['par'][ci][0]}, 'q': q}
    nv = sum(1 for d in q.values() if d['e'] - d['vt'] > d['f'])
    print(key, 'quartieri', len(q), 'con piu non votanti del primo:', nv,
          'citta non votanti', e['city']['e'] - e['city']['vt'], round(100 * (e['city']['e'] - e['city']['vt']) / e['city']['e'], 1),
          'primo', e['par'][ci][0], cv, round(100 * cv / e['city']['e'], 1))
json.dump(out, open(os.path.join(D, 'non_votanti_nil.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
rows = sorted(((100 * (d['e'] - d['vt']) / d['e'], 100 * d['f'] / d['e'], d['n']) for d in out['c21']['q'].values()), reverse=True)
print('max', rows[0], 'min', rows[-1])
