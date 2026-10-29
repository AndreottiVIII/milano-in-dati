"""Fase 2, passo 4: costruisce vie_donne.geojson (solo le strade intitolate a donne) unendo le way OSM di ogni strada.
Uso: python -I 13_geojson_donne.py overpass_geom.json strade_classificate_arricchite_v2.csv out.geojson [supplemento_nomi.json]"""
import sys, json, math, os, importlib.util
import pandas as pd

geom_json, csv, out = sys.argv[1:4]
supp = sys.argv[4] if len(sys.argv) > 4 else ''
spec = importlib.util.spec_from_file_location('m10', os.path.join(os.path.dirname(os.path.abspath(__file__)), '10_chiavi_e_ricerca_v2.py'))
m10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m10)
d = pd.read_csv(csv, dtype=str).fillna('')
W = d[(d.categoria == 'donna') & (d.confidenza.isin(['sicuro', 'incerto']))].copy()
data = json.load(open(geom_json, encoding='utf8'))
print('elementi geom:', len(data['elements']), '| osm base:', data.get('osm3s', {}).get('timestamp_osm_base'))

by_name, by_code = {}, {}
for e in data['elements']:
    t = e.get('tags', {})
    nm = t.get('name', '').strip()
    code = t.get('loc_ref', '').split('_')[0] if t.get('loc_ref') else ''
    # linee: way -> geometry; relation -> membri way con geometry
    lines = []
    if e['type'] == 'way' and e.get('geometry'):
        lines.append([(p['lon'], p['lat']) for p in e['geometry']])
    elif e['type'] == 'relation':
        for m in e.get('members', []):
            if m.get('type') == 'way' and m.get('geometry'):
                lines.append([(p['lon'], p['lat']) for p in m['geometry']])
    if not lines:
        continue
    rec = (e['type'][0] + str(e['id']), nm, code, lines, t)
    by_name.setdefault(nm, []).append(rec)
    if code:
        by_code.setdefault(code, []).append(rec)


supp_recs = []
if supp:
    for e in json.load(open(supp, encoding='utf8'))['elements']:
        if e['type'] == 'way' and e.get('geometry'):
            supp_recs.append((e['tags']['name'], [[(p['lon'], p['lat']) for p in e['geometry']]]))


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy)
    best, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        dist = math.hypot(x - x1, y - y1) if n == 0 else abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n
        if dist > best:
            best, idx = dist, i
    if best > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def clean(line):
    p = [(round(x, 5), round(y, 5)) for x, y in line]
    q = [p[0]]
    for a in p[1:]:
        if a != q[-1]:
            q.append(a)
    q = rdp(q, 0.000008)
    return q if len(q) >= 2 else None


feats, missing = [], []
for r in W.itertuples():
    recs = []
    code = r.codice_via
    names = [n.strip() for n in r.nome_osm.split(' | ') if n.strip()]
    if code and code in by_code:
        recs += by_code[code]
    for n in names:
        for rec in by_name.get(n, []):
            if rec in recs:
                continue
            c = rec[2]
            if (not c) or (not code) or c == code:   # stessa dicitura ma altro codice via = altra strada con lo stesso nome
                recs.append(rec)
    lines = []
    for rec in recs:
        for ln in rec[3]:
            c = clean(ln)
            if c:
                lines.append(c)
    if not lines and supp_recs:   # supplemento: stessa serie di parole significative nel nome della via
        tk = m10.core_tokens(r.nome)
        for nm, lns in supp_recs:
            if m10.core_tokens(nm) == tk:
                for ln in lns:
                    c = clean(ln)
                    if c:
                        lines.append(c)
    if not lines:
        missing.append((r.nome, r.confidenza))
        continue
    prop = dict(nome=r.nome, persona=r.persona, qid=r.qid, nascita=r.nascita, morte=r.morte, professione=r.professioni, intitolazione=r.data_intitolazione,
                confidenza=r.confidenza, santa=int(r.santa or 0), gruppo=int(r.gruppo or 0), fonte=r.fonte, codice_via=r.codice_via, motivo=r.motivo if r.confidenza == 'incerto' else '')
    feats.append(dict(type='Feature', properties=prop, geometry=dict(type='MultiLineString', coordinates=[[list(p) for p in ln] for ln in lines])))
gj = dict(type='FeatureCollection', features=feats,
          metadata=dict(osm_timestamp=data.get('osm3s', {}).get('timestamp_osm_base', ''), licenza='ODbL (OpenStreetMap contributors); dati derivati ODbL'))
s = json.dumps(gj, ensure_ascii=False, separators=(',', ':'))
open(out, 'w', encoding='utf8').write(s)
print(len(W), 'strade donna;', len(feats), 'con geometria;', len(missing), 'senza geometria:', missing[:20], '| MB', round(len(s) / 1e6, 3))
