"""Quanto sono complete le palestre private: sedi pubblicate da alcune catene contro OpenStreetMap e contro la pagina.
Le sedi sono copiate dai siti delle catene il 4/11/2026. Ogni sede e' (parola del nome della via, numero civico o None se il sito non lo da').
Una sede e' "trovata" se c'e' un punto con il nome della catena entro RAGGIO metri dal civico (o dalla via, se manca il numero).
Uso: python -I -X utf8 prova_catene.py <radice del progetto>"""
import csv, io, json, math, re, sys, unicodedata, zipfile

R = sys.argv[1]
CATENE = {
    'Virgin Active': (r'virgin', [('CENA', None), ('TOSCANA', 30), ('SORESINA', 4), ('DIAZ', 6), ('LODI', 39), ('VECCHIO POLITECNICO', 4),
                                  ('COMO', 15), ('CORSIA', 11), ('SARCA', 232), ('AMADEO', 55), ('GASPERI', None), ('IMBONATI', 24)]),
    'McFit': (r'mc\s*fit', [('MOLA', 48), ('BATTISTOTTI', 11), ('TESTI', None)]),
    'Urban Fitness': (r'urban\s*fit', [('ERBA CARLO', None), ('CONFALONIERI', 15), ('CONI ZUGNA', 63), ('AREZZO', 1), ('MANTEGNA', 17), ('MASSAIA', 3),
                                       ('PACINI', 24), ('PIRANESI', 34), ('PISANI', 9), ('PORTA ROMANA', 106), ('RUBENS', 14), ('SABOTINO', 20),
                                       ('GIOVANNI SUL MURO', 17), ('CINQUE GIORNATE', 6)]),
    'GetFit': (r'get\s*fit', [('CENISIO', None), ('MEDA', None), ('PIACENZA', None), ('PINEROLO', None), ('PIRANESI', None), ('RAVIZZA', None), ('STELVIO', None), ('VICO', None)]),
    'FitActive': (r'fit\s*active', [('RIPAMONTI', None), ('ROSSI PELLEGRINO', None), ('SISMONDI', None), ('STELVIO', None)]),
}
RAGGIO, VICINO = 300, 100


def norm(s):
    s = unicodedata.normalize('NFD', s.upper())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]', ' ', s)).strip()


def dist(a, b):
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(45.47)))


z = zipfile.ZipFile(R + '/citta-15-minuti/raw/comune_milano/civici/ds634_civici_coordinategeografiche_20261001_final_csv.zip')
n = next(x for x in z.namelist() if x.lower().endswith('.csv'))
t = z.read(n).decode('utf-8-sig', 'replace')
sep = ';' if t[:2000].count(';') > t[:2000].count(',') else ','
C = []
for r in csv.DictReader(io.StringIO(t), delimiter=sep):
    try:
        C.append((norm(r['DENOMINAZIONE']), re.sub(r'\D', '', r['NUMERO']), (float(r['LAT_WGS84'].replace(',', '.')), float(r['LONG_WGS84'].replace(',', '.')))))
    except ValueError:
        pass
osm = []
for e in json.load(open(R + '/sport/raw/osm/overpass_sport_milano.json', encoding='utf-8'))['elements']:
    tg = e.get('tags', {})
    la, lo = e.get('lat') or e.get('center', {}).get('lat'), e.get('lon') or e.get('center', {}).get('lon')
    if la:
        osm.append((' '.join(str(tg.get(k, '')) for k in ('name', 'brand', 'operator')), (la, lo)))
siti = [(' '.join((r['nome'], r['nomi_alt'], r['info'])), (float(r['lat']), float(r['lon']))) for r in csv.DictReader(open(R + '/sport/pulito/siti.csv', encoding='utf-8')) if r['palestra'] == 'True']
print('civici', len(C), 'punti OSM', len(osm), 'palestre nella pagina', len(siti))
T = dict(sedi=0, osm=0, pagina=0, qualsiasi=0, geo=0)
for cat, (rx, vie) in CATENE.items():
    c = dict(sedi=len(vie), osm=0, pagina=0, qualsiasi=0, geo=0)
    for via, num in vie:
        tutti = [p for nome, nu, p in C if re.search(r'\b' + via + r'\b', nome)]
        pt = [p for nome, nu, p in C if re.search(r'\b' + via + r'\b', nome) and (num is None or nu == str(num))] or tutti
        if not pt:
            print('  ', cat, via, 'VIA NON TROVATA')
            continue
        c['geo'] += 1
        d_o = min((min(dist(q, p) for p in pt) for nm, q in osm if re.search(rx, nm, re.I)), default=1e9)
        d_s = min((min(dist(q, p) for p in pt) for nm, q in siti if re.search(rx, nm, re.I)), default=1e9)
        d_a = min(min(dist(q, p) for p in pt) for _, q in siti)
        print('  ', cat, '|', via, num, '| civici', len(pt), '| mappa', round(d_o), 'm | pagina', round(d_s), 'm | palestra qualsiasi', round(d_a), 'm')
        c['osm'] += d_o <= RAGGIO
        c['pagina'] += d_s <= RAGGIO
        c['qualsiasi'] += d_a <= VICINO
    print(cat, c)
    for k in T:
        T[k] += c[k]
print('TOTALE', T)
