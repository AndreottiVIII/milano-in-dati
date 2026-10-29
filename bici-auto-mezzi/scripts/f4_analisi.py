"""Fase 4 (incidenti), passo 3: analisi bici e dati per la pagina.
Legge out/f4_incidenti_geo.pkl (dopo f4_geo_tutti.py) + OSM + BikeMi; scrive docs/bici-auto-mezzi/data/incidenti.json e out/f4_*.csv
Uso: python -I f4_analisi.py <ABS strand> <ABS cartella docs/bici-auto-mezzi/data>"""
import sys, os, pickle, json, re, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import shapely
from scipy.spatial import cKDTree
from pyproj import Transformer
from f4_geocode import Geocoder4, tokens, split_tipo
S = sys.argv[1]; DATA = sys.argv[2]
df = pickle.load(open(S + '/out/f4_incidenti_geo.pkl', 'rb'))
ANNI = list(range(2010, 2025))
BUONI = ['civico', 'civico_approx', 'incrocio', 'incrocio_approx']
has = lambda codes: df.va.isin(codes) | df.vb.isin(codes) | df.vc.isin(codes)
df['bici'] = has([14, 23]); df['ebike'] = has([23]); df['monop'] = has([22]); df['fuga'] = has([20])
df['morti'] = df.morti24 + df.morti30            # morti24 = entro 24 ore, morti30 = dopo 24 ore ed entro 30 giorni: si sommano
df['rec'] = df.anno >= 2020
df['buono'] = df.livello.isin(BUONI)

# ---------------- serie annuali
g = df.groupby('anno'); gb = df[df.bici].groupby('anno'); gm = df[df.monop].groupby('anno')
ser = {'anno': ANNI, 'tutti': [int(g.size().get(a, 0)) for a in ANNI], 'bici': [int(gb.size().get(a, 0)) for a in ANNI],
       'ebike': [int(df[df.ebike].groupby('anno').size().get(a, 0)) for a in ANNI],
       'bici_morti': [int(gb.morti.sum().get(a, 0)) for a in ANNI], 'bici_feriti': [int(gb.feriti.sum().get(a, 0)) for a in ANNI],
       'monop': [int(gm.size().get(a, 0)) for a in ANNI], 'monop_morti': [int(gm.morti.sum().get(a, 0)) for a in ANNI],
       'monop_feriti': [int(gm.feriti.sum().get(a, 0)) for a in ANNI], 'tutti_morti': [int(g.morti.sum().get(a, 0)) for a in ANNI]}
ser['quota_bici_pct'] = [round(100 * b / t, 1) for b, t in zip(ser['bici'], ser['tutti'])]
ser['bici_solo'] = [int(((df.bici) & (df.vb < 0) & (df.vc < 0) & (df.anno == a)).sum()) for a in ANNI]

# ---------------- con chi si scontra la bici
KC = ["con un'auto", 'con una moto o un motorino', 'con bus, tram, camion o altro mezzo pesante', "con un'altra bici o un monopattino",
      'con un veicolo datosi alla fuga', 'nessun altro veicolo (da sola, contro un pedone o un ostacolo)']
def con_chi(r):
    altri = [x for x in (r.va, r.vb, r.vc) if x >= 0]
    for x in altri:
        if x in (14, 23): altri.remove(x); break
    if any(x in (1, 2, 3, 4) for x in altri): return KC[0]
    if any(x in (15, 16, 17) for x in altri): return KC[1]
    if any(x in (5, 6, 7, 8, 9, 10, 11, 12, 13, 18) for x in altri): return KC[2]
    if any(x in (14, 23, 22) for x in altri): return KC[3]
    if any(x == 20 for x in altri): return KC[4]
    return KC[5]
bb = df[df.bici].copy(); bb['chi'] = bb.apply(con_chi, axis=1)
cc = [[k, int((bb.chi == k).sum()), int(((bb.chi == k) & bb.rec).sum()), int(bb[bb.chi == k].morti.sum())] for k in KC]

# ---------------- qualita della geocodifica
def quote(d):
    n = len(d); lv = d.livello.value_counts()
    return {'righe': n, 'civico': round(100 * lv.get('civico', 0) / n, 1), 'civico_approx': round(100 * lv.get('civico_approx', 0) / n, 1),
            'incrocio': round(100 * lv.get('incrocio', 0) / n, 1), 'incrocio_approx': round(100 * lv.get('incrocio_approx', 0) / n, 1),
            'solo_via': round(100 * lv.get('strada', 0) / n, 1), 'nessuna': round(100 * lv.get('nessuna', 0) / n, 1),
            'posizionati_pct': round(100 * d.buono.mean(), 1)}
qual = {'tutti': quote(df), 'bici': quote(df[df.bici]), 'bici_2020_24': quote(df[df.bici & df.rec]),
        'motivi_solo_via_bici': df[df.bici & (df.livello == 'strada')].motivo.value_counts().head(6).to_dict(),
        'motivi_nessuna_bici': df[df.bici & (df.livello == 'nessuna')].motivo.value_counts().head(6).to_dict(),
        'ricerca_approssimata_pct': round(100 * float(df.fuzzy.mean()), 1)}

# ---------------- griglia 100 m
T = Transformer.from_crs(4326, 32632, always_xy=True); Ti = Transformer.from_crs(32632, 4326, always_xy=True)
P = df[df.buono].copy(); P['x'], P['y'] = T.transform(P.lon.values, P.lat.values)
CELL = 100
P['cx'] = np.floor(P.x / CELL).astype(int); P['cy'] = np.floor(P.y / CELL).astype(int)
def cnt(mask, nome):
    return P[mask].groupby(['cx', 'cy']).size().rename(nome)
G = pd.concat([cnt(P.bici, 'b15'), cnt(P.bici & P.rec, 'b5'), cnt(P.anno > 0, 'a15'), cnt(P.rec, 'a5')], axis=1).fillna(0).astype(int).reset_index()
lon_c, lat_c = Ti.transform((G.cx.values + .5) * CELL, (G.cy.values + .5) * CELL)
G['lon'] = np.round(lon_c, 5); G['lat'] = np.round(lat_c, 5)
def brk(v):
    v = v[v > 0]
    return [int(x) for x in np.unique(np.percentile(v, [50, 75, 90, 97.5]).round().astype(int))]
grid = {'cella_m': CELL, 'lon': G.lon.tolist(), 'lat': G.lat.tolist(), 'b15': G.b15.tolist(), 'b5': G.b5.tolist(), 'a15': G.a15.tolist(), 'a5': G.a5.tolist(),
        'soglie': {k: brk(G[k].values) for k in ('b15', 'b5', 'a15', 'a5')}, 'max': {k: int(G[k].max()) for k in ('b15', 'b5', 'a15', 'a5')},
        'celle_con_bici': int((G.b15 > 0).sum()), 'celle_con_bici_20_24': int((G.b5 > 0).sum())}
G.to_csv(S + '/out/f4_griglia100m.csv', index=False, sep=';')

# ---------------- primi 20 incroci
X = df[df.livello.isin(['incrocio', 'incrocio_approx']) & df.via1_k.notna() & df.via2_k.notna()].copy()
X = X[X.via1_k != X.via2_k]
X['coppia'] = [frozenset([a, b]) for a, b in zip(X.via1_k, X.via2_k)]
rows = []
for cp, grp in X.groupby('coppia'):
    gbk = grp[grp.bici]
    if len(gbk) == 0: continue
    (a, b), _ = collections.Counter(zip(gbk.via1, gbk.via2)).most_common(1)[0]
    lo, la = gbk.lon.median(), gbk.lat.median()
    xy = np.array(T.transform(gbk.lon.values, gbk.lat.values)).T; xm = np.array(T.transform(lo, la))
    rows.append({'a': a, 'b': b, 'lon': round(float(lo), 5), 'lat': round(float(la), 5), 'b15': len(gbk), 'b5': int(gbk.rec.sum()),
                 'morti': int(gbk.morti.sum()), 'feriti': int(gbk.feriti.sum()), 'a15': len(grp), 'a5': int(grp.rec.sum()),
                 'sparsi_m': int(np.hypot(*(xy - xm).T).max())})
I = pd.DataFrame(rows).sort_values(['b15', 'b5'], ascending=False).reset_index(drop=True)
I['quota'] = (100 * I.b15 / I.a15).round(0).astype(int)
I.head(60).to_csv(S + '/out/f4_top_incroci.csv', index=False, sep=';', encoding='utf-8-sig')
top_inc = I.head(20).to_dict('records')

# ---------------- OSM: lunghezza e ciclabili per via
t0 = time.time()
gc = Geocoder4(S)
D = pickle.load(open(S + '/out/osm_parsed.pkl', 'rb'))
ids = D['ids']; order = np.argsort(ids); sid = ids[order]
nx, ny = gc.nx, gc.ny
HW_OK = {'primary': 'P', 'secondary': 'P', 'trunk': 'P', 'primary_link': 'P', 'secondary_link': 'P', 'trunk_link': 'P',
         'tertiary': 'Q', 'tertiary_link': 'Q', 'residential': 'Q', 'unclassified': 'Q', 'living_street': 'Q', 'pedestrian': 'Q'}
LANE = {'lane', 'track', 'opposite_lane', 'opposite_track'}
way_idx = []; way_tag = []; cyc_pts = []
def campiona(x, y, passo):
    d = np.hypot(np.diff(x), np.diff(y)); c = np.r_[0, np.cumsum(d)]; L = c[-1]
    if L <= 0: return L, np.empty((0, 2))
    pos = np.arange(passo / 2, L, passo) if L > passo else np.array([L / 2])
    return L, np.c_[np.interp(pos, c, x), np.interp(pos, c, y)]
for t, refs in D['ways']:
    h = t['highway']
    r = np.asarray(refs, np.int64); p = np.searchsorted(sid, r); p[p >= len(sid)] = 0; ok = sid[p] == r
    idx = order[p[ok]]
    if len(idx) < 2: continue
    if h == 'cycleway' or (h in ('path', 'footway') and t.get('bicycle') == 'designated'):
        L, pts = campiona(nx[idx], ny[idx], 8)
        if len(pts): cyc_pts.append(pts)
    if h in HW_OK and t.get('name'):
        way_idx.append(idx); way_tag.append(t)
cyc = np.vstack(cyc_pts); cyc_tree = cKDTree(cyc)
print('ciclabili OSM (campioni)', len(cyc), 'strade con nome', len(way_idx), round(time.time() - t0), 's')
osm_way_by_key = collections.defaultdict(list)
for wi, t in enumerate(way_tag):
    tipo, rest = split_tipo(tokens(t['name']))
    if rest: osm_way_by_key[(tipo, frozenset(rest))].append(wi)
def via_info(key):
    tipo, fs = key; tk = sorted(fs)
    nodes = gc.street_nodes(tipo, tk)
    if nodes is None: return None
    ns = set(nodes.tolist())
    ks = set(gc.osm_keys(tipo, tk))
    wl = [wi for k in ks for wi in osm_way_by_key.get(k, [])]
    wl = [wi for wi in dict.fromkeys(wl) if np.mean([n in ns for n in way_idx[wi]]) >= .5]
    if not wl: return None
    lines = []; nsamp = 0; ninf = 0; lens = collections.Counter(); ntag = 0
    for wi in wl:
        idx = way_idx[wi]; t = way_tag[wi]; x, y = nx[idx], ny[idx]
        L, pts = campiona(x, y, 25)
        if L <= 0: continue
        lines.append(shapely.linestrings(np.c_[x, y]))
        lens[HW_OK[t['highway']]] += L
        tag = any(k.startswith('cycleway') and not k.endswith('oneway') and v in LANE for k, v in t.items())
        if len(pts):
            d, _ = cyc_tree.query(pts)
            fl = (d <= 10) | tag
            nsamp += len(pts); ninf += int(fl.sum()); ntag += len(pts) * tag
    if not lines or nsamp == 0: return None
    u = shapely.union_all(shapely.buffer(lines, 12, cap_style='flat'))
    return {'km': u.area / 24 / 1000, 'infra': ninf / nsamp, 'infra_tag': ntag / nsamp, 'cl': 'P' if lens['P'] >= lens['Q'] else 'Q'}
info = {}
t0 = time.time()
for k in list(gc.street.keys()):
    try:
        r = via_info(k)
    except Exception as e:
        r = None
    if r and r['km'] > 0: info[k] = r
print('vie con lunghezza', len(info), 'su', len(gc.street), round(time.time() - t0), 's')

# attribuzione incidenti alle vie: riga con due vie = 0,5 a ciascuna; altrimenti 1 alla prima
acc = collections.defaultdict(lambda: np.zeros(6))   # b15, b5, a15, a5, morti_b, feriti_b
def aggiungi(k, w, r):
    a = acc[k]
    if r.bici: a[0] += w; a[1] += w * r.rec; a[4] += w * r.morti; a[5] += w * r.feriti
    a[2] += w; a[3] += w * r.rec
for r in df[df.via1_k.notna() | df.via2_k.notna()].itertuples():
    if r.livello == 'nessuna': continue
    ks = [r.via1_k]
    if r.livello in ('incrocio', 'incrocio_approx', 'strada') and r.via2_k is not None and r.via2_k == r.via2_k and r.via2_k != r.via1_k:
        ks.append(r.via2_k)
    ks = [k for k in ks if k is not None and k == k]
    for k in ks: aggiungi(k, 1.0 / len(ks), r)
tot_b = float(df.bici.sum()); in_info_b = sum(a[0] for k, a in acc.items() if k in info)
print('incidenti bici attribuiti a una via con lunghezza:', round(in_info_b), 'su', int(tot_b))
V = []
for k, inf in info.items():
    a = acc.get(k, np.zeros(6))
    V.append({'key': str(k), 'nome': gc.regname.get(k, ' '.join(k[1])), 'km': inf['km'], 'infra': inf['infra'], 'infra_tag': inf['infra_tag'], 'cl': inf['cl'],
              'b15': a[0], 'b5': a[1], 'a15': a[2], 'a5': a[3], 'morti_b': a[4], 'feriti_b': a[5]})
V = pd.DataFrame(V)
V.sort_values('b5', ascending=False).to_csv(S + '/out/f4_vie.csv', index=False, sep=';', encoding='utf-8-sig')
W = V[V.km >= 0.3].copy()
W['grp'] = np.where(W.infra < .10, 'senza', np.where(W.infra < .60, 'parziale', 'quasi tutta'))
tab = []
for cl, nm in (('P', 'Strade principali e secondarie'), ('Q', 'Strade di quartiere (terziarie, residenziali, a traffico limitato)')):
    for gr, gn in (('senza', 'senza corsia o pista ciclabile (meno del 10% della lunghezza)'), ('parziale', 'con corsia o pista su parte della via (10-60%)'), ('quasi tutta', 'con corsia o pista su quasi tutta la via (60% o più)')):
        s = W[(W.cl == cl) & (W.grp == gr)]
        if len(s) == 0: continue
        km = float(s.km.sum())
        tab.append({'classe': nm, 'gruppo': gn, 'vie': int(len(s)), 'km': round(km, 1), 'b5': int(round(float(s.b5.sum()))), 'b5_km_anno': round(float(s.b5.sum()) / km / 5, 2),
                    'a5_km_anno': round(float(s.a5.sum()) / km / 5, 1), 'quota_bici_pct': round(100 * float(s.b5.sum()) / max(1e-9, float(s.a5.sum())), 1)})
T1 = V[V.km >= 1.0].copy()
T1['b5_km_anno'] = T1.b5 / T1.km / 5
top_vie = T1.sort_values('b5', ascending=False).head(15)
vie_out = [{'nome': r.nome, 'km': round(r.km, 1), 'b15': int(round(r.b15)), 'b5': int(round(r.b5)), 'b5_km_anno': round(r.b5_km_anno, 1), 'infra': int(round(100 * r.infra)),
            'quota': int(round(100 * r.b15 / max(1, r.a15)))} for r in top_vie.itertuples()]
top_km = T1[T1.b5 >= 15].sort_values('b5_km_anno', ascending=False).head(10)
vie_km = [{'nome': r.nome, 'km': round(r.km, 1), 'b5': int(round(r.b5)), 'b5_km_anno': round(r.b5_km_anno, 1), 'infra': int(round(100 * r.infra))} for r in top_km.itertuples()]

# ---------------- controllo degli incroci: posizione OSM contro posizione dal registro dei civici
ds = []
smp = X[X.livello == 'incrocio'].drop_duplicates('nome_strada')
smp = smp.sample(min(3000, len(smp)), random_state=3)
for r0 in smp.itertuples():
    m = re.split(r'\s+(?:incrocio|inc\.?|ang\.?)\s+', r0.nome_strada, flags=re.I)
    if len(m) != 2: continue
    p = gc._incrocio_civici(split_tipo(tokens(m[0])), split_tipo(tokens(m[1])))
    if p is None: continue
    x1, y1 = T.transform(r0.lon, r0.lat); x2, y2 = T.transform(*p); ds.append(float(np.hypot(x1 - x2, y1 - y2)))
ds = np.array(ds)
qual['controllo_incroci'] = {'confronti': int(len(ds)), 'mediana_m': int(round(float(np.median(ds)))), 'entro_100m_pct': round(100 * float((ds < 100).mean()), 1), 'entro_250m_pct': round(100 * float((ds < 250).mean()), 1)}

# ---------------- BikeMi
bk = pd.read_csv(S + '/raw/bikemi/bikemi_stazioni.csv', sep=';')
bikemi = [[round(float(r.LONG_X_4326), 5), round(float(r.LAT_Y_4326), 5), str(r.nome), int(r.stalli)] for r in bk.itertuples()]

out = {'anni': ANNI, 'serie': ser, 'con_chi': cc, 'qualita': qual, 'griglia': grid, 'incroci': top_inc, 'vie_top': vie_out, 'vie_km': vie_km, 'ciclabili': tab,
       'ciclabili_nota': {'vie': int(len(W)), 'km': int(round(float(W.km.sum()))), 'attribuiti_bici_pct': int(round(100 * in_info_b / tot_b)),
                          'ciclabili_osm_km_circa': int(round(len(cyc) * 8 / 1000))},
       'bikemi': bikemi, 'bici_totale_15': int(df.bici.sum()), 'bici_totale_5': int((df.bici & df.rec).sum()),
       'morti_bici_15': int(df[df.bici].morti.sum()), 'monop_totale': int(df.monop.sum())}
json.dump(out, open(DATA + '/incidenti.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('incidenti.json', os.path.getsize(DATA + '/incidenti.json') // 1024, 'KB')
print(json.dumps({k: out[k] for k in ('qualita', 'ciclabili', 'ciclabili_nota', 'con_chi', 'vie_top', 'vie_km')}, ensure_ascii=False, indent=1)[:9000])
print(I.head(25).to_string())
print(pd.DataFrame(ser).to_string())
