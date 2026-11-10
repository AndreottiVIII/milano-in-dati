"""Prepara i dati della pagina "Le Olimpiadi, a cose fatte".
Legge: olimpiadi/grezzi/simico/interventi.csv (Simico, 28/8/2026), olimpiadi/grezzi/province_italia.geojson (scarica.py),
       docs/aeroporti/data/mensile_tre_aeroporti.csv, docs/hinterland/data/comuni.geojson (per sapere se un'opera e' dentro Milano).
Scrive in docs/olimpiadi/data/: opere.csv, riepilogo.json, mappa.json, aeroporti_giochi.csv.
Uso: python -I -X utf8 olimpiadi/scripts/prepara.py
"""
import csv, json, os, re, datetime as dt, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
G = os.path.join(R, 'olimpiadi', 'grezzi')
OUT = os.path.join(R, 'docs', 'olimpiadi', 'data')
os.makedirs(OUT, exist_ok=True)

rows = list(csv.DictReader(open(os.path.join(G, 'simico', 'interventi.csv'), encoding='utf-8-sig')))
assert len(rows) == 98


def dd(s):
    try:
        return dt.datetime.strptime(s[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def reg(t):
    return 'Lombardia' if t == 'Lombardia' else 'Veneto' if t.endswith('Veneto') else 'Trentino-Alto Adige'


def inside(pt, ring):
    x, y = pt
    c = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


com = json.load(open(os.path.join(R, 'docs', 'hinterland', 'data', 'comuni.geojson'), encoding='utf-8'))
mil = [f for f in com['features'] if f['properties'].get('g') == 'MILANO'][0]['geometry']
polys = [mil['coordinates']] if mil['type'] == 'Polygon' else mil['coordinates']


def in_milano(lon, lat):
    return any(inside((lon, lat), p[0]) for p in polys)


LAB = ('per olimpiadi', 'prima fase', 'lavori principali', 'ante-olimpiadi')
O = []
for x in rows:
    m = re.search(r'(\d\d)/(\d\d)/(\d{4})', x['fine ante olimpiadi'])
    fa = dt.date(int(m[3]), int(m[2]), int(m[1])) if m else None
    et = x['fine ante olimpiadi'].split('\n')[0].lower()
    lon, lat = float(x['Long']), float(x['Lat'])
    O.append(dict(cod=x['Cod.'], nome=' '.join(x['descrizione breve'].split()), territorio=x['Territorio'], regione=reg(x['Territorio']),
                  comune=x['Localizzazione'], finalita='Giochi' if x['Finalità'] == 'Evento olimpico' else 'Eredità',
                  tipo=('' if x['Tipo Legacy'] == '---' else x['Tipo Legacy']), fase=x["Fase dell'intervento"],
                  mln=round(float(x['Totale quadro economico']) / 1e6, 3), lon=lon, lat=lat,
                  inizio=dd(x['Data inizio Lavori']), fine=dd(x['Data fine Lavori']), scad=fa, scad_tipo=et,
                  attuatore=x['Soggeto attuatore'], milano=in_milano(lon, lat)))

with open(os.path.join(OUT, 'opere.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['codice', 'opera', 'territorio', 'comune', 'per_i_giochi_o_eredita', 'tipo_eredita', 'fase', 'costo_milioni_euro', 'lon', 'lat', 'inizio_lavori', 'fine_lavori', 'scadenza_intermedia', 'chi_realizza'])
    for o in O:
        w.writerow([o['cod'], o['nome'], o['territorio'], o['comune'], o['finalita'], o['tipo'], o['fase'], o['mln'], o['lon'], o['lat'], o['inizio'] or '', o['fine'] or '', o['scad'] or '', o['attuatore']])

FASI = ['concluso', 'in esecuzione', 'in gara', 'in progettazione']
tot = sum(o['mln'] for o in O)


def agg(sel):
    s = [o for o in O if sel(o)]
    return dict(n=len(s), mln=round(sum(o['mln'] for o in s), 1))


fase = {f: agg(lambda o, f=f: o['fase'] == f) for f in FASI}
fin = {k: agg(lambda o, k=k: o['finalita'] == k) for k in ('Giochi', 'Eredità')}
tipo = {k: agg(lambda o, k=k: o['finalita'] == 'Eredità' and o['tipo'] == k) for k in ('Stradali/Ferroviari', 'Altro')}
terr = {}
for r in ('Lombardia', 'Veneto', 'Trentino-Alto Adige'):
    terr[r] = agg(lambda o, r=r: o['regione'] == r)
    terr[r]['fasi'] = {f: agg(lambda o, r=r, f=f: o['regione'] == r and o['fase'] == f) for f in FASI}
prov = {t: agg(lambda o, t=t: o['territorio'] == t) for t in sorted(set(o['territorio'] for o in O))}


def chi(a):
    if a == 'SIMICO S.p.A.':
        return 'Simico'
    if a.startswith('Provincia Autonoma di Trento'):
        return 'Provincia di Trento'
    if a.startswith('RFI'):
        return 'RFI (ferrovie)'
    if a.startswith('Comune'):
        return 'Comuni'
    if a.startswith('Commissario'):
        return 'Commissario straordinario'
    return 'Ferrovienord'


for o in O:
    o['chi'] = chi(o['attuatore'])
chis = {k: agg(lambda o, k=k: o['chi'] == k) for k in sorted(set(o['chi'] for o in O))}

top = sorted(O, key=lambda o: -o['mln'])[:10]
GIOCHI = dt.date(2026, 2, 6)
conc = [o for o in O if o['fase'] == 'concluso']
anni = collections.OrderedDict()
for y in list(range(2023, 2034)) + ['nd']:
    anni[str(y)] = {f: [] for f in FASI}
for o in O:
    k = str(o['fine'].year) if o['fine'] else 'nd'
    anni[k][o['fase']].append([o['cod'], o['nome'], o['mln'], o['finalita']])
pend = [o for o in O if o['fase'] != 'concluso' and o['scad'] and o['fine'] and any(l in o['scad_tipo'] for l in LAB)]
pend = [dict(cod=o['cod'], nome=o['nome'], scad=str(o['scad']), fine=str(o['fine']), mln=o['mln'], tipo=o['scad_tipo'], regione=o['regione'], fase=o['fase'])
        for o in sorted(pend, key=lambda o: o['fine'])]

A = list(csv.DictReader(open(os.path.join(R, 'docs', 'aeroporti', 'data', 'mensile_tre_aeroporti.csv'), encoding='utf-8'), delimiter=';'))
air = [a for a in A if a['anno'] in ('2025', '2026') and 1 <= int(a['mese']) <= 5 and a['passeggeri']]
with open(os.path.join(OUT, 'aeroporti_giochi.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['aeroporto', 'anno', 'mese', 'passeggeri', 'di_cui_internazionali'])
    for a in air:
        w.writerow([a['aeroporto'], a['anno'], a['mese'], a['passeggeri'], a['internazionali']])
pas = collections.defaultdict(dict)
for a in air:
    pas[a['aeroporto']][(int(a['anno']), int(a['mese']))] = (int(a['passeggeri']), int(a['internazionali']))
aer = {}
for ap in list(pas) + ['Tre aeroporti']:
    aer[ap] = []
    for m in range(1, 6):
        if ap == 'Tre aeroporti':
            v25 = sum(pas[k][(2025, m)][0] for k in pas)
            v26 = sum(pas[k][(2026, m)][0] for k in pas)
        else:
            v25, v26 = pas[ap][(2025, m)][0], pas[ap][(2026, m)][0]
        aer[ap].append(dict(mese=m, v25=v25, v26=v26, var=round(100 * (v26 / v25 - 1), 1)))


def rdp(pts, e):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = (dx * dx + dy * dy) ** .5 or 1e-12
    dm, im = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / L
        if d > dm:
            dm, im = d, i
    if dm > e:
        return rdp(pts[:im + 1], e)[:-1] + rdp(pts[im:], e)
    return [pts[0], pts[-1]]


BB = (8.0, 44.4, 13.6, 47.4)
pj = json.load(open(os.path.join(G, 'province_italia.geojson'), encoding='utf-8'))
mp = []
for f in pj['features']:
    g = f['geometry']
    ps = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    rings = []
    for p in ps:
        r = p[0]
        xs = [q[0] for q in r]
        ys = [q[1] for q in r]
        if max(xs) < BB[0] or min(xs) > BB[2] or max(ys) < BB[1] or min(ys) > BB[3]:
            continue
        pts = [(q[0], q[1]) for q in r]
        h = len(pts) // 2
        s = rdp(pts[:h + 1], 0.004)[:-1] + rdp(pts[h:], 0.004)  # anello chiuso: si divide a meta'
        if len(s) > 3:
            rings.append([[round(a, 3), round(b, 3)] for a, b in s])
    if rings:
        mp.append(dict(n=f['properties']['n'], r=f['properties']['r'], p=rings))
json.dump(dict(province=mp, bbox=BB), open(os.path.join(OUT, 'mappa.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

dopo = [o for o in O if o['fine'] and o['fine'] >= dt.date(2027, 1, 1)]
riep = dict(
    meta=dict(data_dati='2026-08-28', n=len(O), tot_mln=round(tot, 3)),
    pf={t: {f: agg(lambda o, t=t, f=f: o['territorio'] == t and o['fase'] == f) for f in FASI} for t in prov},
    fase=fase, finalita=fin, tipo_eredita=tipo, territori=terr, province=prov, chi=chis,
    concluse_prima_giochi=sum(1 for o in conc if o['fine'] <= GIOCHI), concluse_dopo_giochi=sum(1 for o in conc if o['fine'] > GIOCHI),
    fine_dal_2027=dict(n=len(dopo), mln=round(sum(o['mln'] for o in dopo), 1)),
    fine_senza_data=sum(1 for o in O if not o['fine']),
    anni=anni, pendenza=pend,
    top=[dict(cod=o['cod'], nome=o['nome'], mln=o['mln'], fase=o['fase'], finalita=o['finalita'], regione=o['regione'], comune=o['comune'], fine=str(o['fine'] or '')) for o in top],
    in_milano=sum(1 for o in O if o['milano']),
    milano_tirano=[o['cod'] for o in O if 'Milano' in o['comune']],
    aeroporti=aer,
    opere=[[o['cod'], o['nome'], o['regione'], o['finalita'], o['fase'], o['mln'], o['lon'], o['lat'], str(o['fine'] or '')] for o in O],
)
json.dump(riep, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('tot', round(tot, 1), fase, fin, tipo)
print({r: (terr[r]['n'], terr[r]['mln']) for r in terr}, prov)
print('chi', chis)
print('pend', len(pend), [p['cod'] for p in pend])
print('milano', riep['in_milano'], riep['milano_tirano'])
print('prima/dopo giochi', riep['concluse_prima_giochi'], riep['concluse_dopo_giochi'], 'dal2027', riep['fine_dal_2027'], 'senza data', riep['fine_senza_data'])
print('aer', {k: [x['var'] for x in v] for k, v in aer.items()})
for fn in os.listdir(OUT):
    print(fn, os.path.getsize(os.path.join(OUT, fn)))
