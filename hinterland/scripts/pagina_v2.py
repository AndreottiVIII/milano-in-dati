"""Prepara i dati compatti per la pagina Hinterland rifatta.
Legge docs/hinterland/data/comuni.json, gruppi.json, voto.json (gia' calcolati da build.py)
e scrive docs/hinterland/data/pagina_comuni.json (nome nuovo, niente altro viene toccato).
Uso: python -I -X utf8 hinterland/scripts/pagina_v2.py"""
import json, os, statistics
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(R, 'docs', 'hinterland', 'data')
ld = lambda n: json.load(open(os.path.join(D, n), encoding='utf8'))
com, gr, vo = ld('comuni.json'), ld('gruppi.json'), ld('voto.json')
fam = vo['famiglie']
assert fam == ['Centrosinistra', 'Sinistra', 'Centro', 'Centrodestra', 'Destra', 'Lega', 'M5S', 'Altri']
SX = [0, 1]; CD = [3, 4, 5]
def sx(p): return round(sum(p[i] for i in SX), 2)
def cd(p): return round(sum(p[i] for i in CD), 2)
def p22(c):
    g = vo['gruppi']['MILANO'] if c['cod'] == '015146' else vo['unita'].get(c['unita'])
    return g['p'][-1] if g else None
def p76(c):
    g = vo['gruppi']['MILANO'] if c['cod'] == '015146' else vo['unita'].get(c['unita'])
    return g['p'][0] if g else None
out = []
for c in com:
    a, b = p22(c), p76(c)
    pe = c['pend']
    out.append({
        'cod': c['cod'], 'nome': c['nome'], 'g': c['g'], 'km': c['km'], 'ins': bool(c['insieme']),
        'pop': c['pop'][-1], 'pop0': c['pop'][0], 'cr': c['cr26'] if False else c['cr'],
        'str': round(100 * c['stran'][-1] / c['pop'][-1], 2),
        'o65': c['o65'][-1], 'u15': c['u15'][-1], 'em': c['em'][-1], 'red': c['red'][-1][0],
        'q': pe['q'][-1] if pe else None, 'e': pe['e'][-1] if pe else None, 't': pe['t'][-1] if pe else None,
        'cd22': cd(a) if a else None, 'sx22': sx(a) if a else None, 'sx76': sx(b) if b else None,
        'met': ', '.join(c['fermata']) if c['fermata'] else ''})
hint = [c for c in out if c['g'] != 'MILANO']
assert len(hint) == 187 and len(out) == 188
H = gr['g']['HINT']
agg = {
    'str': round(100 * H['stran'][-1] / H['pop'][-1], 2), 'o65': H['eta']['o65'][-1], 'u15': H['eta']['u15'][-1],
    'red': H['red']['medio'][-1], 'cr': round(100 * (H['pop'][-1] / H['pop'][0] - 1), 2),
    'q': round(100 * sum(c['e'] for c in hint if c['e'] is not None) / sum(c['t'] for c in hint if c['t'] is not None), 1),
    'cd22': cd(vo['gruppi']['HINT']['p'][-1]),
    'pop': statistics.median(c['pop'] for c in hint), 'km': statistics.median(c['km'] for c in hint if c['km'] is not None)}
M = gr['g']['MILANO']
def flu(G):
    s = lambda k: sum(G[k][1:25])  # 2002..2025
    f = {'pop0': G['pop'][1], 'pop1': G['pop'][25], 'nat': s('nat'), 'int': s('int'), 'est': s('est'), 'altro': s('altro')}
    f['altro_calc'] = f['pop1'] - f['pop0'] - f['nat'] - f['int'] - f['est']
    return f
fl = {'MILANO': flu(M), 'HINT': flu(H)}
print(fl)
for k, f in fl.items(): print(k, 'altro', f['altro'], 'quadratura', f['altro_calc'])
serie = {'anni': H['eta_l']['anni'], 'MILANO': M['eta_l']['o65'], 'HINT': H['eta_l']['o65']}
vt = {'anni': vo['anni']}
for k in ['MILANO', 'CINTURA', 'RESTO', 'HINT']:
    vt[k] = {'sx': [sx(p) for p in vo['gruppi'][k]['p']], 'cd': [cd(p) for p in vo['gruppi'][k]['p']]}
vt['n_cintura'] = len(vo['cintura'])
res = {'c': out, 'agg': agg, 'flussi': fl, 'o65': serie, 'voto': vt, 'generato': '2026-11-07'}
json.dump(res, open(os.path.join(D, 'pagina_comuni.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('ok', os.path.getsize(os.path.join(D, 'pagina_comuni.json')), agg)
print('km range', min(c['km'] for c in hint if c['km'] is not None), max(c['km'] for c in hint if c['km'] is not None),
      'q', min(c['q'] for c in hint if c['q'] is not None), max(c['q'] for c in hint if c['q'] is not None),
      'nulls', [c['nome'] for c in hint if c['q'] is None or c['cd22'] is None or c['km'] is None])
