"""Sport v2: minuti a piedi al luogo piu' vicino per quartiere e per citta' (stesso metodo di sport/scripts/analisi.py).
Uso: python -I -X utf8 calcola.py <ABS sport> <ABS citta-15-minuti>  -> data/sport_tempi.json"""
import sys, json
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse import load_npz, csr_matrix
from scipy.sparse.csgraph import dijkstra
S, C = sys.argv[1].rstrip('/' + chr(92)), sys.argv[2].rstrip('/' + chr(92)); O = C + '/out/'
OUTF = sys.argv[3] if len(sys.argv) > 3 else 'sport_tempi.json'
SPEED = 4.5/3.6; LIM = 3200.0; MAXSNAP = 150.0
P = pd.read_csv(S + '/pulito/siti.csv', dtype={'ID_NIL': 'Int64'})
nil = pd.read_csv(O + 'nil_punteggi.csv')[['ID_NIL', 'NIL_nome', 'residenti_2025']]; nil['ID_NIL'] = nil.ID_NIL.astype(int)
imp = P.livello == 'impianto'
com = P.gestione.isin(['milanosport', 'comune_concessione', 'comune_da_verificare'])
GRP = {'piscine': imp & P.piscina, 'palestre': imp & P.palestra, 'campi': P.campo, 'tutti': imp,
       'comunali': imp & com, 'milanosport': P.gestione == 'milanosport', 'piscine_comunali': imp & P.piscina & com,
       'piscine_altro': imp & P.piscina & ~com}
G = load_npz(O + 'grafo_pedonale_csr.npz'); nd = np.load(O + 'grafo_pedonale_nodi.npz'); N = G.shape[0]
tree = cKDTree(np.c_[nd['x'], nd['y']])
c = pd.read_csv(O + 'civici_tempi.csv', usecols=['IDMASTER', 'ID_NIL', 'RESIDENZIALE', 'x', 'y', 'snap_m'])
c['node'] = tree.query(np.c_[c.x.values, c.y.values])[1]
dist, nodes = tree.query(np.c_[P.x.values, P.y.values]); P['node'] = nodes; P['snap_m'] = dist
indptr = G.indptr; ind = G.indices; dat = G.data
base_r = np.repeat(np.arange(N), np.diff(indptr))
def minutes(sub):
    sub = sub[sub.snap_m <= MAXSNAP]
    best = pd.DataFrame({'n': sub.node.values, 's': sub.snap_m.values}).groupby('n', as_index=False).s.min()
    A = csr_matrix((np.r_[dat, best.s.values + 0.01], (np.r_[base_r, np.full(len(best), N)], np.r_[ind, best.n.values])), shape=(N + 1, N + 1))
    dn = dijkstra(A, directed=True, indices=N, limit=LIM)[:N]
    dm = dn[c.node.values] + c.snap_m.values
    return np.round(np.where(dm > LIM + MAXSNAP, np.nan, dm / SPEED / 60.0), 2)
res = c[(c.RESIDENZIALE == 1) & c.ID_NIL.notna()].copy(); res['ID_NIL'] = res.ID_NIL.astype(int)
pop = nil.set_index('ID_NIL').residenti_2025
res['peso'] = res.ID_NIL.map(pop) / res.ID_NIL.map(res.groupby('ID_NIL').size()); res = res[res.peso.notna()]
def wmed(v, w):
    o = np.argsort(v); cw = np.cumsum(w[o]); return float(v[o][np.searchsorted(cw, cw[-1]/2)])
# ---------------------------------------------------------------- piscine "solo per iscritti"
# Regola: piscine OSM con access=customers/members/permit, oppure senza access (o private SOLO se non sono di condominio: qui non si accettano) entro 80 m da un centro
# sportivo/palestra con nome e circolo/catena (virgin, aspria, tennis, sporting, club) non privato; piu' le 8 sedi Virgin Active che il sito della catena dichiara con piscina.
# Si scartano le piscine con access=private/no (condomini, case, alberghi chiusi) e quelle a meno di 80 m da una piscina gia' contata come aperta.
import math, re, zipfile, io, csv
from pyproj import Transformer
from shapely.geometry import shape, Point
tr = Transformer.from_crs(4326, 32632, always_xy=True)
def dm(a, b): return math.hypot((a[0]-b[0])*111320*math.cos(math.radians(45.47)), (a[1]-b[1])*111320)
nilp = [(f['properties']['i'], f['properties']['n'], shape(f['geometry'])) for f in json.load(open(S + '/../docs/sport/data/nil.geojson', encoding='utf-8'))['features']]
def nil_di(lon, lat):
    for i_, n_, pg in nilp:
        if pg.contains(Point(lon, lat)): return i_, n_
    return None, None
osm = json.load(open(S + '/raw/osm/overpass_sport_milano.json', encoding='utf-8'))['elements']
def pos(e): return (e['center']['lon'], e['center']['lat']) if 'center' in e else (e['lon'], e['lat'])
poolo = [(r.lon, r.lat) for r in P[imp & P.piscina].itertuples()]
centri = [e for e in osm if e['tags'].get('leisure') in ('fitness_centre', 'sports_centre', 'sports_hall') or e['tags'].get('amenity') == 'gym']
CLUB = re.compile(r'virgin|aspria|club|tennis|sporting|fitness|wellness|palestra|gym', re.I)
ISC = []
for e in osm:
    t = e['tags']
    if t.get('leisure') != 'swimming_pool': continue
    lon, lat = pos(e); acc = t.get('access')
    if min([dm((lon, lat), q) for q in poolo] + [1e9]) <= 80: continue
    vicino = [c for c in centri if dm((lon, lat), pos(c)) <= 80 and c['tags'].get('access') not in ('private', 'no') and CLUB.search(c['tags'].get('name', ''))]
    if acc in ('customers', 'members', 'permit'): regola = 'OSM: accesso solo ai clienti o agli iscritti'
    elif acc is None and vicino: regola = 'OSM: piscina dentro un circolo o una palestra (' + vicino[0]['tags']['name'] + ')'
    else: continue
    ISC.append(dict(nome=t.get('name') or (vicino[0]['tags']['name'] if vicino else 'Piscina per clienti'), lon=lon, lat=lat, fonte=regola))
# sedi Virgin Active con piscina secondo il sito della catena (letto il 6/11/2026); solo il si'/no, coordinate dai civici del Comune
VIRGIN = [('Virgin Active Cavour', 'VECCHIO POLITECNICO', '4'), ('Virgin Active Corso Como', 'COMO', '15'), ('Virgin Active Vittorio Emanuele', 'CORSIA DEI SERVI', '11'),
          ('Virgin Active Bocconi', 'TOSCANA', '30'), ('Virgin Active Bicocca', 'SARCA', '232'), ('Virgin Active Kennedy', 'GASPERI', '2'),
          ('Virgin Active Maciachini', 'IMBONATI', '24'), ('Virgin Active Piazzale Lodi', 'LODI', '39')]
z = zipfile.ZipFile(C + '/raw/comune_milano/civici/ds634_civici_coordinategeografiche_20261001_final_csv.zip')
t_ = z.read(next(x for x in z.namelist() if x.lower().endswith('.csv'))).decode('utf-8-sig', 'replace')
rows = list(csv.DictReader(io.StringIO(t_), delimiter=';' if t_[:2000].count(';') > t_[:2000].count(',') else ','))
for nome, via, num in VIRGIN:
    m = [(float(r['LONG_WGS84']), float(r['LAT_WGS84'])) for r in rows if re.search(r'(^|[^A-Z])' + via + r'($|[^A-Z])', r['DENOMINAZIONE'].upper()) and r['NUMERO'] == num]
    p = (sum(a for a, b in m)/len(m), sum(b for a, b in m)/len(m))
    # se OSM ha gia' una piscina iscritti a meno di 80 m (stessa sede) la si sostituisce col nome della catena
    gia = [i for i, q in enumerate(ISC) if dm(p, (q['lon'], q['lat'])) <= 80]
    if min([dm(p, q) for q in poolo] + [1e9]) <= 80: continue
    if gia: ISC[gia[0]].update(nome=nome, fonte='sito della catena (piscina si/no) e OpenStreetMap'); continue
    ISC.append(dict(nome=nome, lon=p[0], lat=p[1], fonte='sito della catena (solo se ha una piscina)'))
ISC.sort(key=lambda q: q['nome'] == 'Piscina per clienti')   # prima le sedi con nome
tenute = []
for q in ISC:
    if all(dm((q['lon'], q['lat']), (k['lon'], k['lat'])) > 80 for k in tenute): tenute.append(q)
ISC = tenute
for q in ISC:
    if q['nome'] == 'Piscina per clienti': q['nome'] = 'Piscina senza nome (solo clienti)'
ISC = [dict(q, **dict(zip(('id_nil', 'nil'), nil_di(q['lon'], q['lat'])))) for q in ISC]
ISC = [q for q in ISC if q['id_nil'] is not None]
fi = pd.DataFrame([dict(zip('xy', tr.transform(q['lon'], q['lat']))) for q in ISC])
dd, nn = tree.query(np.c_[fi.x, fi.y]); fi['node'] = nn; fi['snap_m'] = dd
op = P[imp & P.piscina][['node', 'snap_m']]
GRP_EXTRA = {'piscine_iscritti': fi, 'piscine_tutte': pd.concat([op, fi[['node', 'snap_m']]])}
OUT = {'residenti': int(res.peso.sum()), 'citta': {}, 'nil': {}}
ALL = [(g, P[m], int(m.sum())) for g, m in GRP.items()] + [(g, f, len(f)) for g, f in GRP_EXTRA.items()]
for g, sub, nsub in ALL:
    t = pd.Series(minutes(sub), index=c.index).loc[res.index].fillna(99).values
    w = res.peso.values; tot = w.sum()
    OUT['citta'][g] = {'b5': float(w[t <= 5].sum()/tot), 'b10': float(w[t <= 10].sum()/tot), 'b15': float(w[t <= 15].sum()/tot), 'med': round(wmed(t, w), 1), 'n': nsub}
    if g in ('piscine', 'palestre', 'campi', 'piscine_tutte'):
        for nid, d in res.assign(t=t).groupby('ID_NIL'):
            OUT['nil'].setdefault(int(nid), {})[g] = round(wmed(d.t.values, d.peso.values), 1)
OUT['iscritti'] = [dict(nome=q['nome'], lon=round(q['lon'], 5), lat=round(q['lat'], 5), id_nil=int(q['id_nil']), nil=q['nil'], fonte=q['fonte']) for q in ISC]
json.dump(OUT, open(OUTF, 'w', encoding='utf-8'), separators=(',', ':'))
print(json.dumps(OUT['citta']['piscine_tutte'])); print(json.dumps(OUT['iscritti'], ensure_ascii=False, indent=0)); print(len(OUT['nil']))
