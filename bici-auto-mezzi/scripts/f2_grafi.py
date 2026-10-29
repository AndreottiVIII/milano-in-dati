"""Fase 2, passo 2b: costruisce i grafi piedi, bici, auto da out/osm_parsed.pkl.
Uso: python -I f2_grafi.py <ABS strand>  -> out/g_walk.npz, g_bike.npz, g_car.npz, grafi_stats.json
(i parametri stanno in f2_parametri.py)"""
import sys, os, pickle, json, time, re
import numpy as np
from pyproj import Transformer
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f2_parametri as P
S = sys.argv[1]; O = S + '/out/'
t0 = time.time()
D = pickle.load(open(O + 'osm_parsed.pkl', 'rb'))
ids, lat, lon, ntags, ways = D['ids'], D['lat'], D['lon'], D['ntags'], D['ways']
tr = Transformer.from_crs(4326, 32632, always_xy=True)
X, Y = tr.transform(lon, lat); X = np.asarray(X); Y = np.asarray(Y)
order = np.argsort(ids); sid = ids[order]
def idx_of(refs):
    r = np.asarray(refs, dtype=np.int64); p = np.searchsorted(sid, r); p[p >= len(sid)] = 0
    ok = sid[p] == r
    return np.where(ok, order[p], -1)
KM = 1 / 3.6
MAJOR = {'primary', 'primary_link', 'secondary', 'secondary_link', 'trunk', 'trunk_link'}
ROADS_CAR = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary', 'secondary_link',
             'tertiary', 'tertiary_link', 'unclassified', 'residential', 'living_street', 'service', 'road'}
BIKE_NO_HW = {'motorway', 'motorway_link', 'construction', 'proposed', 'raceway', 'platform', 'corridor', 'elevator', 'bus_guideway',
              'services', 'emergency_bay', 'busway', 'bridleway', 'steps', 'rest_area', 'escape', 'via_ferrata'}
BAD_SERVICE = {'parking_aisle', 'driveway', 'drive-through', 'emergency_access', 'taxi_aisle', 'taxi_rank', 'taxi_parking', 'slipway'}
FOOT_OK = {'yes', 'designated', 'permissive'}
ALWAYS = {'footway', 'pedestrian', 'path', 'steps', 'living_street', 'residential', 'service', 'unclassified', 'tertiary', 'tertiary_link',
          'secondary', 'secondary_link', 'primary', 'primary_link', 'track', 'road', 'corridor'}
def walkable(t):
    h = t['highway']; foot = t.get('foot'); acc = t.get('access')
    if foot in ('no', 'private'): return False
    if t.get('indoor') == 'yes': return False
    if acc in ('private', 'no') and foot not in FOOT_OK: return False
    if h in ALWAYS: return True
    if h in ('cycleway', 'trunk', 'trunk_link'): return foot in FOOT_OK
    return False
def parse_ms(s):
    if s is None: return 0
    s = s.strip().lower()
    if s == 'it:urban': return 50
    m = re.match(r'^(\d+)\s*(mph)?', s)
    if not m: return 0
    v = int(m.group(1))
    if m.group(2): v = round(v * 1.609)
    return v
def oneway_dir(t, h, mode):
    """1 = solo da u a v, -1 = solo da v a u, 0 = doppio senso"""
    ow = t.get('oneway')
    if mode == 'bike':
        owb = t.get('oneway:bicycle')
        if owb == 'no': return 0
        if owb in ('yes', '1', 'true'): return 1
        if owb == '-1': return -1
        for k, v in t.items():
            if k.startswith('cycleway') and k.endswith('oneway') and v in ('no', '-1'): return 0
            if k.startswith('cycleway') and not k.endswith('oneway') and v in ('opposite', 'opposite_lane', 'opposite_track'): return 0
    if ow in ('yes', '1', 'true'): return 1
    if ow == '-1': return -1
    if ow in ('no', '0', 'false'): return 0
    if ow == 'reversible': return 0
    if t.get('junction') in ('roundabout', 'circular'): return 1
    if mode == 'car' and h in ('motorway', 'motorway_link'): return 1
    return 0
def bike_attr(t):
    """-> (km/h avanti, km/h indietro, e' strada, e' strada maggiore) oppure None se vietato"""
    h = t['highway']; bic = t.get('bicycle'); acc = t.get('access')
    if h in BIKE_NO_HW: return None
    if h in ('trunk', 'trunk_link') and bic not in FOOT_OK: return None
    if t.get('motorroad') == 'yes' and bic not in FOOT_OK: return None
    if bic in ('no', 'private'): return None
    if acc in ('no', 'private') and bic not in FOOT_OK: return None
    if t.get('indoor') == 'yes': return None
    surf = t.get('surface', ''); sf = 1.0
    if surf in ('unpaved', 'gravel', 'dirt', 'ground', 'grass', 'sand', 'earth', 'mud', 'fine_gravel', 'compacted', 'pebblestone'): sf = 0.8
    elif surf in ('cobblestone', 'sett', 'unhewn_cobblestone', 'cobblestone:flattened'): sf = 0.85
    # classi di velocita (Fase 3: le velocita si applicano in Motore.set_bike, qui si salva solo la classe)
    # 0 ciclabile, 1 strada, 2 servizio, 3 pedonale pedalabile, 4 a mano, 5 sterrato
    if h == 'cycleway': c = 0
    elif h == 'footway':
        if bic in ('yes', 'permissive', 'designated'): c = 3
        elif bic == 'dismount': c = 4
        else: return None
    elif h == 'pedestrian':
        c = 3 if bic in ('yes', 'designated', 'permissive') else 4
    elif h == 'path':
        c = 0 if bic == 'designated' else 3
    elif h == 'track': c = 5
    elif h == 'service':
        if t.get('service') in BAD_SERVICE: return None
        c = 2
    elif h == 'living_street': c = 2
    else:
        c = 1
        for k, val in t.items():
            if k.startswith('cycleway') and not k.endswith('oneway') and not k.endswith('surface') and val in ('lane', 'track', 'opposite_lane', 'opposite_track', 'share_busway'):
                c = 0; break
    d = oneway_dir(t, h, 'bike')
    return (d >= 0), (d <= 0), (h in ROADS_CAR), (h in MAJOR), c, sf
def car_attr(t):
    h = t['highway']
    if h not in ROADS_CAR: return None
    if h == 'service' and t.get('service') in BAD_SERVICE: return None
    mv = t.get('motor_vehicle'); acc = t.get('access'); veh = t.get('vehicle'); mc = t.get('motorcar')
    if mc == 'no' or mv in ('no', 'private', 'agricultural', 'forestry', 'delivery', 'customers'): return None
    if veh in ('no', 'private') and mv not in ('yes', 'designated'): return None
    if acc in ('no', 'private', 'customers') and mv not in ('yes', 'designated') and mc != 'yes': return None
    if t.get('area') == 'yes' or t.get('indoor') == 'yes': return None
    cls = 'alley' if (h == 'service' and t.get('service') == 'alley') else h
    return cls, oneway_dir(t, h, 'car'), parse_ms(t.get('maxspeed'))
# ---------- attributi per strada
nW = len(ways)
walk_ok = np.zeros(nW, bool)
bok_f = np.zeros(nW, bool); bok_b = np.zeros(nW, bool); b_cls = np.zeros(nW, np.int8); b_sf = np.ones(nW, np.float32); b_road = np.zeros(nW, bool); b_major = np.zeros(nW, bool)
car_cls = ['none'] * nW; car_dir = np.zeros(nW, np.int8); car_ms = np.zeros(nW); car_ok = np.zeros(nW, bool)
road_like = np.zeros(nW, bool); major_way = np.zeros(nW, bool)
for i, (t, refs) in enumerate(ways):
    h = t['highway']
    walk_ok[i] = walkable(t)
    r = bike_attr(t)
    if r is not None: bok_f[i], bok_b[i], b_road[i], b_major[i], b_cls[i], b_sf[i] = r
    r = car_attr(t)
    if r is not None: car_cls[i], car_dir[i], car_ms[i] = r; car_ok[i] = True
    road_like[i] = h in ROADS_CAR
    major_way[i] = h in MAJOR
# ---------- nodi speciali
nn = len(ids)
sig_hw = np.zeros(nn, bool); sig_cross = np.zeros(nn, bool); car_block = np.zeros(nn, bool)
CAR_BLOCK = {'bollard', 'block', 'chain', 'jersey_barrier', 'cycle_barrier', 'turnstile', 'entrance'}
for oid, tg in ntags.items():
    i = order[np.searchsorted(sid, oid)]
    if tg.get('highway') == 'traffic_signals': sig_hw[i] = True
    if tg.get('crossing') == 'traffic_signals': sig_cross[i] = True
    if tg.get('barrier') in CAR_BLOCK and tg.get('motor_vehicle') not in ('yes',): car_block[i] = True
sig_any = sig_hw | sig_cross
tree_hw = cKDTree(np.c_[X[sig_hw], Y[sig_hw]])
ci = np.where(sig_cross & ~sig_hw)[0]
dd, _ = tree_hw.query(np.c_[X[ci], Y[ci]])
iso = ci[dd > 40]
sig_road = sig_hw.copy(); sig_road[iso] = True
t2 = cKDTree(np.c_[X[iso], Y[iso]]); pairs = t2.query_pairs(40, output_type='ndarray')
drop = set()
for a, b in pairs:
    if a not in drop: drop.add(b)
for k in drop: sig_road[iso[k]] = False
# peso dei semafori "da sentiero" (ciclabili/marciapiedi): i gruppi di semafori entro 30 m (incrocio + attraversamenti) contano meno
si = np.where(sig_any)[0]; ts = cKDTree(np.c_[X[si], Y[si]])
nb = np.array([len(x) for x in ts.query_ball_point(np.c_[X[si], Y[si]], 30)])
sig_w = np.zeros(nn); sig_w[si] = 1 / np.sqrt(nb)
major_node = np.zeros(nn, bool)
# ---------- segmenti
seg_w = []; seg_u = []; seg_v = []
for i, (t, refs) in enumerate(ways):
    r = idx_of(refs)
    if major_way[i]: major_node[r[r >= 0]] = True
    a = r[:-1]; b = r[1:]
    m = (a >= 0) & (b >= 0) & (a != b)
    k = int(m.sum())
    if k:
        seg_w.append(np.full(k, i, np.int32)); seg_u.append(a[m]); seg_v.append(b[m])
seg_w = np.concatenate(seg_w); seg_u = np.concatenate(seg_u); seg_v = np.concatenate(seg_v)
seg_len = np.hypot(X[seg_u] - X[seg_v], Y[seg_u] - Y[seg_v])
print('segmenti', len(seg_w), 'semafori incrocio', int(sig_hw.sum()), 'semafori isolati', int(sig_road.sum() - sig_hw.sum()), round(time.time() - t0), 's', flush=True)
uu = np.r_[seg_u, seg_v]; vv = np.r_[seg_v, seg_u]; ll = np.r_[seg_len, seg_len]; ww = np.r_[seg_w, seg_w]
isfwd = np.r_[np.ones(len(seg_u), bool), np.zeros(len(seg_u), bool)]
stats = {}
def save_graph(name, m, times, strong=True, extra=None):
    u = uu[m]; v = vv[m]; ln = ll[m]; tms = [t[m] for t in times]
    key = u.astype(np.int64) * nn + v
    o = np.lexsort((tms[0], key)); ks = key[o]
    first = np.r_[True, ks[1:] != ks[:-1]]; sel = o[first]
    u2 = u[sel]; v2 = v[sel]
    G = csr_matrix((np.ones(len(sel)), (u2, v2)), shape=(nn, nn))
    nc, lab = connected_components(G, directed=True, connection='strong' if strong else 'weak')
    present = np.zeros(nn, bool); present[u2] = True; present[v2] = True
    cnt = np.bincount(lab[present], minlength=lab.max() + 1); big = cnt.argmax()
    keep = (lab == big) & present
    newid = -np.ones(nn, np.int64); newid[keep] = np.arange(keep.sum())
    mk = keep[u2] & keep[v2]; sel = sel[mk]; u2 = newid[u2[mk]]; v2 = newid[v2[mk]]
    oo = np.lexsort((v2, u2)); sel = sel[oo]; u2 = u2[oo]; v2 = v2[oo]
    N = int(keep.sum())
    indptr = np.zeros(N + 1, np.int64); np.add.at(indptr, u2 + 1, 1); indptr = np.cumsum(indptr)
    d = {'indptr': indptr, 'indices': v2.astype(np.int32), 'len': ln[sel].astype(np.float32),
         'node_old': np.where(keep)[0].astype(np.int32), 'x': X[keep], 'y': Y[keep]}
    for k, t in enumerate(tms): d['t%d' % k] = t[sel].astype(np.float32)
    if extra:
        for k, a in extra.items(): d[k] = a[m][sel]
    np.savez_compressed(O + 'g_%s.npz' % name, **d)
    stats[name] = {'nodi_con_archi': int(present.sum()), 'nodi': N, 'archi': int(len(sel)), 'km_archi': round(float(ln[sel].sum() / 1000), 1), 'componenti': int(nc)}
    print(name, stats[name], round(time.time() - t0), 's', flush=True)
# ---- piedi
mw = walk_ok[ww]
sigp = np.where(road_like[ww], sig_road[vv], sig_w[vv])
tw = ll / (P.WALK_KMH * KM) + P.WALK_SIGNAL_S * sigp
save_graph('walk', mw, [tw], strong=False)
# ---- bici
mb = np.where(isfwd, bok_f[ww], bok_b[ww])
VTAB = np.array([P.BIKE_KMH_CYCLEWAY, P.BIKE_KMH_ROAD, P.BIKE_KMH_SERVICE, P.BIKE_KMH_PEDESTRIAN_RIDE, P.BIKE_KMH_WALKING, P.BIKE_KMH_TRACK])
spd = np.where(mb, VTAB[b_cls[ww]] * b_sf[ww], 0) * KM
sigb = np.where(b_road[ww], sig_road[vv], sig_w[vv])
major_cross = (~b_major[ww]) & major_node[vv] & (sigb == 0)
tb = ll / np.where(spd > 0, spd, 1) + P.BIKE_SIGNAL_S * sigb + P.BIKE_MAJOR_CROSS_S * major_cross
infra = (b_cls[ww] == 0) & mb   # classe 'ciclabile' (Fase 3: prima era una soglia di velocita)
pen_b = P.BIKE_SIGNAL_S * sigb + P.BIKE_MAJOR_CROSS_S * major_cross
save_graph('bike', mb, [tb], extra={'infra': infra, 'pen': pen_b.astype(np.float32), 'sigp': sigb.astype(np.float32), 'mcross': major_cross, 'vcls': b_cls[ww], 'sf': b_sf[ww]})
# ---- auto
cok = car_ok[ww]; dr = car_dir[ww]
allowed = cok & ((dr == 0) | ((dr == 1) & isfwd) | ((dr == -1) & ~isfwd))
allowed &= ~car_block[uu] & ~car_block[vv]
cl_e = np.array(car_cls, dtype=object)[ww]
cls_names = sorted(P.CAR_SPEED)
cls_codes = {c: i for i, c in enumerate(cls_names)}; cls_codes['none'] = len(cls_names)
cls_e = np.array([cls_codes[c] for c in cl_e], np.int8)
mx = car_ms[ww]
tabs = []
for b in range(3):
    tab = np.array([P.CAR_SPEED[c][b] for c in cls_names] + [1.0])
    base = tab[cls_e]
    cap = np.where(mx > 0, P.CAR_MAXSPEED_FRAC * mx, 1e9)
    v_kmh = np.minimum(base, cap) * P.CAR_SCALE[b]
    tabs.append(ll / np.maximum(v_kmh * KM, 0.5) + P.CAR_SIGNAL_S[b] * sig_road[vv])
save_graph('car', allowed, tabs, extra={'cls': cls_e, 'sig': sig_road[vv], 'maxs': mx.astype(np.float32)})
json.dump({'stats': stats, 'classi_auto': cls_names}, open(O + 'grafi_stats.json', 'w'), indent=1)
np.savez_compressed(O + 'nodi_flag.npz', sig_road=sig_road, sig_any=sig_any, major_node=major_node, x=X, y=Y, lat=lat, lon=lon, ids=ids)
print('fatto', round(time.time() - t0), 's')
