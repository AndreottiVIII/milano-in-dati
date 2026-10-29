"""Confini dei NIL (ds964, NIL vigenti PGT 2030; cartella dell'altro filone, SOLO LETTURA) semplificati per il sito,
piu' tabelle piccole: nil_info.json (nome, municipio, sezioni, quota di civici in sezioni condivise) e nil_sezioni.json (NIL -> [[sezione, quota %, 1 se e' il NIL prevalente della sezione], ...]).
uso: python -I 41_nil_geo.py <cartella elezioni> <cartella docs/elezioni> <geojson NIL>
"""
import sys, os, json
import pandas as pd
from shapely.geometry import shape, mapping

base, docs, src = sys.argv[1], sys.argv[2], sys.argv[3]
pul = os.path.join(base, 'pulito')
inf = pd.read_csv(os.path.join(pul, 'nil_info.csv'), encoding='utf-8-sig').set_index('nil')
w = pd.read_csv(os.path.join(pul, 'sezione_nil.csv'), encoding='utf-8-sig')
g = json.load(open(src, encoding='utf-8'))


def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 5), round(c[1], 5)]
    return [rnd(x) for x in c]


feats, diff = [], []
for f in g['features']:
    n = int(f['properties']['ID_NIL'])
    nome = f['properties']['NIL']
    if n in inf.index and inf.loc[n, 'nome'] != nome:
        diff.append((n, nome, inf.loc[n, 'nome']))
    s = shape(f['geometry']).simplify(0.00007, preserve_topology=True)
    geo = mapping(s)
    geo = {'type': geo['type'], 'coordinates': rnd(geo['coordinates'])}
    feats.append({'type': 'Feature', 'properties': {'n': n, 'nome': nome}, 'geometry': geo})
feats.sort(key=lambda f: f['properties']['n'])
out = os.path.join(docs, 'data', 'nil.geojson')
json.dump({'type': 'FeatureCollection', 'features': feats}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('nil.geojson', len(feats), 'NIL', os.path.getsize(out), 'byte; nomi diversi tra ds964 e ds939:', diff)
print('NIL del confine senza civici in ds939:', sorted({f['properties']['n'] for f in feats} - set(inf.index)))

info = {}
for n, r in inf.iterrows():
    info[str(n)] = dict(nome=r.nome, m=int(r.municipio), s=int(r.sezioni), se=float(r.sezioni_eff), sp=int(r.sezioni_prevalenti),
                        c=int(r.civici), q=float(r.quota_civici_condivisi))
json.dump(info, open(os.path.join(docs, 'data', 'nil_info.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
ns = {}
for r in w.itertuples():
    ns.setdefault(str(r.id_nil), []).append([int(r.sezione), int(round(r.peso * 100)), 1 if r.prevalente == 'si' else 0])
for k in ns:
    ns[k].sort()
json.dump(ns, open(os.path.join(docs, 'data', 'nil_sezioni.json'), 'w'), separators=(',', ':'))
print('nil_info.json', os.path.getsize(os.path.join(docs, 'data', 'nil_info.json')), 'nil_sezioni.json', os.path.getsize(os.path.join(docs, 'data', 'nil_sezioni.json')))
