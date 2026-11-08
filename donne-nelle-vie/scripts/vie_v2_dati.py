"""Dati aggiuntivi per la pagina 'Donne nelle vie' (versione nuova).
Uso: python -I -X utf8 scripts/vie_v2_dati.py
Legge docs/vie/data (strade_classificate_arricchite_v2.csv, vie_donne.geojson, vie_anno.json) e docs/medici-farmacie/data/nil.geojson.
Scrive docs/vie/data/vie_v2_grafici.json e docs/vie/data/quartieri_nil.geojson (solo nomi nuovi)."""
import csv, json, os, re, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # progetto milano-in-dati
D = os.path.join(R, 'docs', 'vie', 'data')
rows = list(csv.DictReader(open(os.path.join(D, 'strade_classificate_arricchite_v2.csv'), encoding='utf-8-sig')))
geo = json.load(open(os.path.join(D, 'vie_donne.geojson'), encoding='utf-8'))
nil = json.load(open(os.path.join(R, 'docs', 'medici-farmacie', 'data', 'nil.geojson'), encoding='utf-8'))
anno = json.load(open(os.path.join(D, 'vie_anno.json'), encoding='utf-8'))
mun = {str(v['c']): v['m'] for v in anno}


def pip(pt, ring):
    x, y = pt
    c = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def in_nil(pt):
    for f in nil['features']:
        g = f['geometry']
        polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        for p in polys:
            if pip(pt, p[0]) and not any(pip(pt, h) for h in p[1:]):
                return f['properties']['i']
    return None


def centro(g):
    pts = [p for l in (g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]) for p in l]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return min(pts, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)


gcod = {}
for f in geo['features']:
    gcod[f['properties']['codice_via']] = centro(f['geometry'])
gnome = {f['properties']['nome'].lower(): centro(f['geometry']) for f in geo['features']}


def anno_n(s):
    return int(s) if re.match(r'^-?\d+$', (s or '').strip()) else None


CATS = {
    'Scrittura e giornali': ['scrittor', 'poeta', 'giornalist', 'romanzier', 'saggist', 'traduttor', 'curatore editoriale', 'critico', 'drammaturg', 'diarist', 'redattor', 'librettist', 'filolog', 'sceneggiator', 'storico'],
    'Teatro, canto e musica': ['attor', 'cantant', 'music', 'compositor', 'regist', 'ballerin', 'direttore d', 'soprano'],
    'Pittura, architettura, design': ['pittor', 'scultor', 'architett', 'designer', 'disegnator', 'artist', 'fotograf', 'illustrator', 'incisor', 'intagliator'],
    'Politica, lotta e armi': ['politic', 'rivoluzion', 'patriot', 'partigian', 'sindacalist', 'attivist', 'suffraget', 'militar', 'diplomatic', 'giurist', 'avvocat', 'magistrat'],
    'Fede e religione': ['monac', 'religios', 'sacerdot', 'suora', 'teolog', 'fondatore di un ordine', 'missionar', 'vescov', 'papa', 'cardinal', 'capo religioso'],
    'Scuola, scienza e cure': ['medic', 'matematic', 'ingegner', 'fisic', 'chimic', 'biolog', 'professore', 'insegnant', 'pedagog', 'docent', 'economist', 'neurolog', 'scienziat', 'ricercator', 'filosof', 'astronom'],
    'Corti e nobiltà': ['monarc', 'aristocrat', 'consort', 'sovran', 'duc', 'princip', 'salottier', 'nobil', 'imperator'],
}


def cat_prof(r):
    t = (r['professioni'] or '').lower()
    s = set()
    for c, ws in CATS.items():
        if any(w in t for w in ws):
            s.add(c)
    if r['santa'] == '1' or r['santo'] == '1':
        s.add('Fede e religione')
    return s


donne = []
for r in rows:
    if r['categoria'] != 'donna':
        continue
    pt = gcod.get(r['codice_via']) or gnome.get(r['nome'].lower())
    nid = in_nil(pt) if pt else None
    d = r['data_intitolazione']
    donne.append({'n': r['nome'], 'p': r['persona'], 'na': anno_n(r['nascita']), 'mo': anno_n(r['morte']), 'pr': r['professioni'],
                  'd': int(d[:4]) if len(d) == 8 and d not in ('17000101', '19000101') else None,
                  's': 1 if r['santa'] == '1' else 0, 'nil': nid, 'x': round(pt[0], 5) if pt else None, 'y': round(pt[1], 5) if pt else None,
                  'm': mun.get(r['codice_via'], '')})
print('donne', len(donne), 'senza posizione', sum(1 for d in donne if d['nil'] is None))

ordine = ['prima del 1500', '1500s', '1600s', '1700s', '1800s', '1900s', '2000s']
sec = {k: {'u': 0, 'd': 0} for k in ordine}
for r in rows:
    if r['confidenza'] != 'sicuro' or r['categoria'] not in ('uomo', 'donna'):
        continue
    y = anno_n(r['nascita'])
    if y is None:
        continue
    k = 'prima del 1500' if y < 1500 else str(y // 100 * 100) + 's'
    sec[k]['u' if r['categoria'] == 'uomo' else 'd'] += 1
print(sec)

cats = list(CATS.keys())
cnt = {c: {'u': 0, 'd': 0} for c in cats}
tot = {'u': 0, 'd': 0}
for r in rows:
    if r['confidenza'] != 'sicuro' or r['categoria'] not in ('uomo', 'donna'):
        continue
    s = cat_prof(r)
    if not s:
        continue
    k = 'u' if r['categoria'] == 'uomo' else 'd'
    tot[k] += 1
    for c in s:
        cnt[c][k] += 1
print(tot)
print(cnt)

rec = []
for r in rows:
    if r['confidenza'] != 'sicuro' or r['categoria'] not in ('uomo', 'donna', 'misto'):
        continue
    d = r['data_intitolazione']
    if len(d) != 8 or d in ('17000101', '19000101'):
        continue
    if int(d[:4]) >= 2000:
        rec.append({'y': int(d[:4]), 'md': d[4:], 'k': {'uomo': 'u', 'donna': 'd', 'misto': 'm'}[r['categoria']], 'n': r['nome'], 'p': r['persona']})
print('recenti', len(rec), collections.Counter(x['k'] for x in rec))
print(sorted(collections.Counter(x['y'] for x in rec).items()))

cn = collections.Counter(d['nil'] for d in donne if d['nil'] is not None)
feats = []
for f in nil['features']:
    p = f['properties']
    feats.append({'type': 'Feature', 'properties': {'i': p['i'], 'n': p['n'], 'mu': p['mu'], 'c': cn.get(p['i'], 0)}, 'geometry': f['geometry']})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(D, 'quartieri_nil.geojson'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump({'donne': donne, 'secoli': {'ordine': ordine, 'v': sec}, 'mestieri': {'cat': cats, 'v': cnt, 'tot': tot}, 'recenti': rec},
          open(os.path.join(D, 'vie_v2_grafici.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
nm = {f['properties']['i']: f['properties']['n'] for f in nil['features']}
print([(nm[i], c) for i, c in sorted(cn.items(), key=lambda x: -x[1])[:10]], len(cn))
