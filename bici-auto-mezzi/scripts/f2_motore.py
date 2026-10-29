"""Fase 2: motore bici / auto / mezzi pubblici / piedi per Milano (Python puro, numpy + scipy + numba).
Uso come libreria: from f2_motore import Motore ; m = Motore(S) ; r = m.viaggio((lon, lat), dest, '08')
Tutte le ipotesi sono in f2_parametri.py."""
import sys, os, json, time, glob
import numpy as np
from numba import njit
import heapq
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as shp_transform
from shapely import contains_xy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f2_parametri as P

KM = 1 / 3.6
WALK_MS = P.WALK_KMH * KM
TR = Transformer.from_crs(4326, 32632, always_xy=True)
INF = np.inf

def xy_of(lon, lat):
    a, b = TR.transform(np.asarray(lon, float), np.asarray(lat, float))
    return np.atleast_1d(np.asarray(a)), np.atleast_1d(np.asarray(b))

@njit(cache=True)
def ldij(indptr, indices, w, src, limit, dist, touched):
    h = [(0.0, np.int64(src))]
    dist[src] = 0.0; touched[0] = src; cnt = 1
    while len(h) > 0:
        d, u = heapq.heappop(h)
        if d > dist[u]: continue
        for k in range(indptr[u], indptr[u + 1]):
            v = indices[k]; nd = d + w[k]
            if nd <= limit and nd < dist[v]:
                if dist[v] == np.inf:
                    touched[cnt] = v; cnt += 1
                dist[v] = nd
                heapq.heappush(h, (nd, np.int64(v)))
    return cnt

@njit(cache=True)
def tree_accum(order, pred, indptr, indices, ln, inarea, out_len, out_flag):
    for ii in range(len(order)):
        v = order[ii]; p = pred[v]
        if p < 0: continue
        l = 0.0
        for k in range(indptr[p], indptr[p + 1]):
            if indices[k] == v:
                l = ln[k]; break
        out_len[v] = out_len[p] + l
        out_flag[v] = out_flag[p] or inarea[v]

@njit(cache=True)
def csa(f, t, dep, arr, trip, start, tmax, ready, arrv, trip_on, fp_ptr, fp_to, fp_w, slack):
    for i in range(start, len(f)):
        d = dep[i]
        if d > tmax: break
        tr = trip[i]
        if trip_on[tr] or ready[f[i]] <= d:
            trip_on[tr] = True
            a = arr[i]; s = t[i]
            if a < arrv[s]:
                arrv[s] = a
                if a + slack < ready[s]: ready[s] = a + slack
                for k in range(fp_ptr[s], fp_ptr[s + 1]):
                    s2 = fp_to[k]; a2 = a + fp_w[k]
                    if a2 < arrv[s2]: arrv[s2] = a2
                    if a2 + slack < ready[s2]: ready[s2] = a2 + slack

@njit(cache=True)
def egress_best(arrv, ptr, stop, w, n_dest):
    out = np.full(n_dest, np.inf)
    for c in range(n_dest):
        b = np.inf
        for k in range(ptr[c], ptr[c + 1]):
            a = arrv[stop[k]] + w[k]
            if a < b: b = a
        out[c] = b
    return out

class Dest:
    """insieme di destinazioni: coordinate + agganci ai grafi + elenco fermate a piedi"""
    pass

class Motore:
    def __init__(self, S, carscale=None, verbose=True):
        self.S = S; O = S + '/out/'; self.O = O
        t0 = time.time()
        self.scale = tuple(carscale) if carscale else P.CAR_SCALE
        W = np.load(O + 'g_walk.npz'); B = np.load(O + 'g_bike.npz'); C = np.load(O + 'g_car.npz')
        self.w = {k: W[k] for k in W.files}; self.b = {k: B[k] for k in B.files}; self.c = {k: C[k] for k in C.files}
        n = len(self.w['x']); self.Gw = csr_matrix((self.w['t0'].astype(float), self.w['indices'], self.w['indptr']), shape=(n, n))
        self.Gw_len = self.w['len'].astype(np.float64)
        n = len(self.b['x']); self.Gb = csr_matrix((self.b['t0'].astype(float), self.b['indices'], self.b['indptr']), shape=(n, n))
        self.set_car(self.scale)
        self.tw = cKDTree(np.c_[self.w['x'], self.w['y']]); self.tb = cKDTree(np.c_[self.b['x'], self.b['y']])
        # per l'auto: non agganciare a autostrade/tangenziali
        cls = json.load(open(O + 'grafi_stats.json'))['classi_auto']
        self.cls_names = cls
        n = len(self.c['x']); deg_ok = np.zeros(n, bool)
        urban = np.array([nm not in ('motorway', 'motorway_link', 'trunk', 'trunk_link') for nm in cls] + [True])
        src = np.repeat(np.arange(n), np.diff(self.c['indptr']))
        deg_ok[src[urban[self.c['cls']]]] = True
        self.car_snap_ids = np.where(deg_ok)[0]
        self.tc = cKDTree(np.c_[self.c['x'][deg_ok], self.c['y'][deg_ok]])
        # Area C
        d = json.load(open(S + '/../area-c/raw/ds51_aree-pedonali-e-ztl/disciplina_aree.geojson', encoding='utf-8'))
        ac = [f for f in d['features'] if f['properties']['tipo'] == 'AREA_C'][0]
        self.areac = shp_transform(lambda x, y, z=None: TR.transform(x, y), shape(ac['geometry']))
        self.car_in_areac = contains_xy(self.areac, self.c['x'], self.c['y'])
        self.duomo = xy_of(P.DUOMO_LL[1], P.DUOMO_LL[0])
        # trasporto pubblico
        g = np.load(O + 'gtfs_conn.npz')
        self.g = {k: g[k] for k in g.files}
        self.ns = len(self.g['stop_lat'])
        sx, sy = xy_of(self.g['stop_lon'], self.g['stop_lat']); self.sx, self.sy = sx, sy
        d, i = self.tw.query(np.c_[sx, sy])
        self.stop_node = i.astype(np.int64); self.stop_snap = d
        self.stop_ok = d <= P.STOP_SNAP_MAX_M
        # fermate per nodo (CSR)
        ok = np.where(self.stop_ok)[0]
        o = np.argsort(self.stop_node[ok], kind='stable'); so = ok[o]
        self.nn_ptr = np.zeros(len(self.w['x']) + 1, np.int64)
        np.add.at(self.nn_ptr, self.stop_node[so] + 1, 1); self.nn_ptr = np.cumsum(self.nn_ptr)
        self.nn_stop = so.astype(np.int64)
        self._footpaths()
        self._buf = np.full(len(self.w['x']), np.inf); self._touch = np.zeros(len(self.w['x']), np.int64)
        if verbose: print('motore pronto', round(time.time() - t0, 1), 's', flush=True)

    # ---------- auto: tempi per fascia
    def set_car(self, scale):
        c = self.c; self.scale = tuple(scale)
        n = len(c['x']); self.Gc = []
        names = json.load(open(self.O + 'grafi_stats.json'))['classi_auto']
        for b in range(3):
            tab = np.array([P.CAR_SPEED[nm][b] for nm in names] + [1.0])
            base = tab[c['cls']]
            cap = np.where(c['maxs'] > 0, P.CAR_MAXSPEED_FRAC * c['maxs'], 1e9)
            v = np.minimum(base, cap) * scale[b]
            t = c['len'] / np.maximum(v * KM, 0.5) + P.CAR_SIGNAL_S[b] * c['sig']
            self.Gc.append(csr_matrix((t.astype(float), c['indices'], c['indptr']), shape=(n, n)))
        self.Gc_len = c['len'].astype(np.float64)

    # ---------- passerelle a piedi tra fermate
    def _footpaths(self):
        fn = self.O + 'footpaths.npz'
        if os.path.exists(fn):
            z = np.load(fn)
            if int(z['ns']) == self.ns:
                self.fp_ptr, self.fp_to, self.fp_w = z['ptr'], z['to'], z['w']; return
        w = self.w; ip, ix, ln = w['indptr'], w['indices'], self.Gw_len
        dist = np.full(len(w['x']), np.inf); touched = np.zeros(len(w['x']), np.int64)
        rows = [[] for _ in range(self.ns)]
        for s in np.where(self.stop_ok)[0]:
            lim = P.TRANSFER_M - self.stop_snap[s]
            if lim < 0: continue
            cnt = ldij(ip, ix, ln, self.stop_node[s], lim, dist, touched)
            for u in touched[:cnt]:
                for k in range(self.nn_ptr[u], self.nn_ptr[u + 1]):
                    s2 = self.nn_stop[k]
                    if s2 == s: continue
                    tot = dist[u] + self.stop_snap[s] + self.stop_snap[s2]
                    if tot <= P.TRANSFER_M: rows[s].append((s2, tot / WALK_MS))
            dist[touched[:cnt]] = np.inf
        ptr = np.zeros(self.ns + 1, np.int64); ptr[1:] = np.cumsum([len(r) for r in rows])
        to = np.array([a for r in rows for a, _ in r], np.int64); ww = np.array([b for r in rows for _, b in r], np.float64)
        np.savez_compressed(fn, ptr=ptr, to=to, w=ww, ns=self.ns)
        self.fp_ptr, self.fp_to, self.fp_w = ptr, to, ww

    # ---------- destinazioni
    def dest(self, lon, lat):
        D = Dest(); lon = np.atleast_1d(lon); lat = np.atleast_1d(lat)
        D.lon, D.lat = lon, lat; D.n = len(lon)
        D.x, D.y = xy_of(lon, lat)
        q = np.c_[D.x, D.y]
        d, i = self.tw.query(q); D.w_node, D.w_snap = i, d
        d, i = self.tb.query(q); D.b_node, D.b_snap = i, d
        d, i = self.tc.query(q); D.c_node, D.c_snap = self.car_snap_ids[i], d
        D.in_areac = contains_xy(self.areac, D.x, D.y)
        dd = np.hypot(D.x - self.duomo[0][0], D.y - self.duomo[1][0])
        D.dist_duomo_km = dd / 1000
        D.zona = np.where(D.in_areac, 'areac', np.where(dd <= P.SEMICENTRO_KM * 1000, 'semicentro', 'periferia'))
        D.park_s = np.array([P.PARK_MIN[z] * 60 for z in D.zona], float)
        # fermate raggiungibili a piedi (egress)
        ip, ix, ln = self.w['indptr'], self.w['indices'], self.Gw_len
        dist, touched = self._buf, self._touch
        ptr = [0]; st = []; wt = []
        for c in range(D.n):
            lim = P.ACCESS_M - D.w_snap[c]
            if lim > 0:
                cnt = ldij(ip, ix, ln, D.w_node[c], lim, dist, touched)
                best = {}
                for u in touched[:cnt]:
                    for k in range(self.nn_ptr[u], self.nn_ptr[u + 1]):
                        s = self.nn_stop[k]; tot = dist[u] + D.w_snap[c] + self.stop_snap[s]
                        if tot <= P.ACCESS_M and (s not in best or tot < best[s]): best[s] = tot
                dist[touched[:cnt]] = np.inf
                for s, tot in best.items(): st.append(s); wt.append(tot / WALK_MS)
            ptr.append(len(st))
        D.eg_ptr = np.array(ptr, np.int64); D.eg_stop = np.array(st, np.int64); D.eg_w = np.array(wt, np.float64)
        return D

    # ---------- un'origine verso tutte le destinazioni
    def _snap(self, tree, x, y, ids=None):
        d, i = tree.query([x, y]); return (int(ids[i]) if ids is not None else int(i)), float(d)

    def piedi(self, o, D, limit_s=5400):
        x, y = o; n, sn = self._snap(self.tw, x, y)
        dist = dijkstra(self.Gw, directed=False, indices=n, limit=limit_s)
        t = dist[D.w_node] + (sn + D.w_snap) / WALK_MS
        return np.where(np.isfinite(dist[D.w_node]), t, np.inf)

    def bici(self, o, D):
        x, y = o; n, sn = self._snap(self.tb, x, y)
        dist, pred = dijkstra(self.Gb, directed=True, indices=n, return_predecessors=True)
        t = dist[D.b_node] + (sn + D.b_snap) / (P.BIKE_KMH_WALKING * KM)
        return t

    def auto(self, o, D, band):
        b = P.BANDS.index(band)
        x, y = o; n, sn = self._snap(self.tc, x, y, self.car_snap_ids)
        G = self.Gc[b]
        dist, pred = dijkstra(G, directed=True, indices=n, return_predecessors=True)
        fin = np.isfinite(dist); order = np.argsort(dist)[:int(fin.sum())]
        ol = np.zeros(len(dist)); of = np.zeros(len(dist), np.bool_)
        tree_accum(order, pred.astype(np.int64), self.c['indptr'], self.c['indices'], self.Gc_len, self.car_in_areac, ol, of)
        drive = dist[D.c_node] + (sn + D.c_snap) * 1.0 / (WALK_MS)   # tratto fuori rete a piedi
        dlen = ol[D.c_node]
        charge = (of[D.c_node] | D.in_areac)
        return drive, dlen, charge

    def mezzi(self, o, D, tstart):
        """tempo medio (s) sulle partenze tstart + offset; inf se irraggiungibile"""
        x, y = o; n, sn = self._snap(self.tw, x, y)
        ip, ix, ln = self.w['indptr'], self.w['indices'], self.Gw_len
        dist, touched = self._buf, self._touch
        lim = P.ACCESS_M - sn
        acc = {}
        if lim > 0:
            cnt = ldij(ip, ix, ln, n, lim, dist, touched)
            for u in touched[:cnt]:
                for k in range(self.nn_ptr[u], self.nn_ptr[u + 1]):
                    s = self.nn_stop[k]; tot = dist[u] + sn + self.stop_snap[s]
                    if tot <= P.ACCESS_M and (s not in acc or tot < acc[s]): acc[s] = tot
            dist[touched[:cnt]] = np.inf
        if not acc: return np.full(D.n, np.inf)
        g = self.g; res = []
        for off in P.DEP_OFFSETS_MIN:
            t0 = tstart + off * 60
            ready = np.full(self.ns, 10 ** 9, np.int64); arrv = np.full(self.ns, 10 ** 9, np.int64)
            for s, tot in acc.items():
                a = t0 + int(round(tot / WALK_MS)); ready[s] = min(ready[s], a); arrv[s] = min(arrv[s], a)
            trip_on = np.zeros(int(g['trip'].max()) + 1, np.bool_)
            start = int(np.searchsorted(g['dep'], t0))
            csa(g['f'], g['t'], g['dep'], g['arr'], g['trip'], start, t0 + P.MAX_TRIP_S, ready, arrv, trip_on,
                self.fp_ptr, self.fp_to, self.fp_w, P.TRANSIT_SLACK_S)
            best = egress_best(arrv.astype(np.float64), D.eg_ptr, D.eg_stop, D.eg_w, D.n)
            res.append(best - t0)
        res = np.array(res)
        return res.mean(axis=0)   # inf se una partenza non arriva

    def viaggio(self, origin_lonlat, D, band):
        """origin (lon, lat) -> dict di array (secondi / metri) per le D.n destinazioni"""
        ox, oy = xy_of(*origin_lonlat); o = (float(ox[0]), float(oy[0]))
        tstart = P.DEPARTURES[band]
        r = {}
        r['straight_m'] = np.hypot(D.x - o[0], D.y - o[1])
        r['walk_s'] = self.piedi(o, D)
        r['bike_s'] = self.bici(o, D) + P.BIKE_FIXED_S
        drive, dlen, charge = self.auto(o, D, band)
        r['car_drive_s'] = drive; r['car_len_m'] = dlen
        r['car_s'] = drive + 2 * P.CAR_WALK_S + D.park_s
        r['areac'] = charge & (band != '21')       # Area C attiva solo lun-ven 7:30-19:30 (da verificare)
        r['transit_s'] = self.mezzi(o, D, tstart)
        return r
