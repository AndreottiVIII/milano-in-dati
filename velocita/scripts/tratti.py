# -*- coding: utf-8 -*-
"""Passo 3: velocita' prevista dall'orario tratto per tratto.
Per ogni linea di superficie "cittadina" (docs/velocita/data/linee.json) si prende il percorso piu' usato (shape) e
la sequenza di fermate piu' comune su quel percorso. Le fermate si raggruppano in tratti lunghi almeno 400 m
(i tempi del GTFS sono al secondo, ma tra due fermate vicine l'arrotondamento e le soste fanno saltare la velocita').
Velocita' del tratto = lunghezza lungo il percorso / (arrivo all'ultima fermata del tratto - partenza dalla prima),
mediana delle corse del giorno (24/11/2026) che fanno quel percorso con entrambe le fermate; poi per fasce:
tutto il giorno, 8 (partenze 7-9), 13 (10-15), 18 (17-19), 22 (dalle 21).
Scrive docs/velocita/data/tratti.json. Uso: python -I -X utf8 velocita/scripts/tratti.py
"""
import os, json, collections
import numpy as np, pandas as pd
from shapely.geometry import LineString, box
from shapely.ops import unary_union
from shapely.geometry import shape as gshape

QUI = os.path.dirname(os.path.abspath(__file__)); RAD = os.path.dirname(os.path.dirname(QUI))
GTFS = os.path.join(RAD, "bici-auto-mezzi", "raw", "gtfs", "ext_comune_new")
OUT = os.path.join(RAD, "docs", "velocita", "data")
GIORNO = "20261124"; MINLEN = 400.0
R = 6371008.8; K = np.cos(np.radians(45.46))
def dm(la1, lo1, la2, lo2):
    return np.hypot(np.radians(np.asarray(la2) - la1) * R, np.radians(np.asarray(lo2) - lo1) * R * K)
def sec(t):
    h, m, s = t.split(":"); return int(h) * 3600 + int(m) * 60 + int(s)

linee = {z["id"]: z for z in json.load(open(os.path.join(OUT, "linee.json"), encoding="utf-8"))}
citta = {i for i, z in linee.items() if z["tipo"] != "metro" and z["dentro"] >= 0.6 and not i.startswith(("BQ", "BN"))}   # niente bus di quartiere ne' notturni: poche corse e percorsi ad anello, le fermate non si assegnano al tracciato con sicurezza
cal = pd.read_csv(os.path.join(GTFS, "calendar_dates.txt"), dtype=str)
sv = set(cal[(cal.date == GIORNO) & (cal.exception_type == "1")].service_id)
trips = pd.read_csv(os.path.join(GTFS, "trips.txt"), dtype=str, usecols=["route_id", "service_id", "trip_id", "shape_id"])
trips = trips[trips.service_id.isin(sv) & trips.route_id.isin(citta)]
# percorso piu' usato per linea
main = trips.groupby("route_id").shape_id.agg(lambda s: s.value_counts().index[0])
trips = trips[trips.shape_id == trips.route_id.map(main)]
ids = set(trips.trip_id)
print("linee", len(main), "corse sul percorso principale", len(trips))
stops = pd.read_csv(os.path.join(GTFS, "stops.txt"), dtype=str, usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"]).set_index("stop_id")
pz = []
for ch in pd.read_csv(os.path.join(GTFS, "stop_times.txt"), dtype=str, chunksize=2_000_000, usecols=["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"]):
    pz.append(ch[ch.trip_id.isin(ids)])
stt = pd.concat(pz); stt["seq"] = stt.stop_sequence.astype(int); stt = stt.sort_values(["trip_id", "seq"])
sh = pd.read_csv(os.path.join(GTFS, "shapes.txt"), dtype=str, usecols=["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"])
sh = sh[sh.shape_id.isin(set(main))]; sh["q"] = sh.shape_pt_sequence.astype(int); sh = sh.sort_values(["shape_id", "q"])
SH = {}
for sid, g in sh.groupby("shape_id"):
    la = g.shape_pt_lat.astype(float).values; lo = g.shape_pt_lon.astype(float).values
    SH[sid] = (la, lo, np.concatenate([[0], np.cumsum(dm(la[:-1], lo[:-1], la[1:], lo[1:]))]))
tinfo = trips.set_index("trip_id")
nil = json.load(open(os.path.join(OUT, "nil.geojson"), encoding="utf-8"))
mil = unary_union([gshape(f["geometry"]).buffer(0) for f in nil["features"]])
cornice = box(mil.bounds[0] - 0.02, mil.bounds[1] - 0.015, mil.bounds[2] + 0.02, mil.bounds[3] + 0.015)
FASCE = [("t", lambda h: True), ("8", lambda h: 7 <= h <= 9), ("13", lambda h: 10 <= h <= 15), ("18", lambda h: 17 <= h <= 19), ("22", lambda h: h >= 21)]
def nome(sid):
    n = stops.loc[sid, "stop_name"] if sid in stops.index else sid
    return n
out = {}; tot_chunks = 0
bytr = {tid: g for tid, g in stt.groupby("trip_id", sort=False)}
for rid, sid in main.items():
    tl = trips[trips.route_id == rid].trip_id.tolist()
    la, lo, cum = SH[sid]
    # sequenza piu' comune di fermate
    seqs = collections.Counter(tuple(bytr[t].stop_id) for t in tl if t in bytr)
    pat = list(seqs.most_common(1)[0][0])
    idx = []; prev = 0
    for s_ in pat:
        a, b = float(stops.loc[s_, "stop_lat"]), float(stops.loc[s_, "stop_lon"])
        hi = np.searchsorted(cum, cum[prev] + 3000)
        d = dm(la[prev:hi + 1], lo[prev:hi + 1], a, b); i = prev + int(np.argmin(d)); idx.append(i); prev = i
    # confini dei tratti: almeno MINLEN m
    bound = [0]
    for j in range(1, len(pat)):
        if cum[idx[j]] - cum[idx[bound[-1]]] >= MINLEN: bound.append(j)
    if bound[-1] != len(pat) - 1:
        if len(bound) > 1 and cum[idx[-1]] - cum[idx[bound[-1]]] < MINLEN: bound[-1] = len(pat) - 1
        else: bound.append(len(pat) - 1)
    chunks = []
    pairs = [(bound[k], bound[k + 1]) for k in range(len(bound) - 1)]
    vel = {p: {f: [] for f, _ in FASCE} for p in pairs}
    for t in tl:
        g = bytr.get(t)
        if g is None: continue
        arr = dict(zip(g.stop_id, g.arrival_time)); dep = dict(zip(g.stop_id, g.departure_time))
        for (a, b) in pairs:
            sa, sb = pat[a], pat[b]
            if sa in dep and sb in arr:
                dt = sec(arr[sb]) - sec(dep[sa])
                if dt <= 0: continue
                v = (cum[idx[b]] - cum[idx[a]]) / dt * 3.6
                h = sec(dep[sa]) // 3600
                for f, fn in FASCE:
                    if fn(h): vel[(a, b)][f].append(v)
    rl = []
    for (a, b) in pairs:
        i0, i1 = idx[a], idx[b]
        ls = LineString(np.c_[lo[i0:i1 + 1], la[i0:i1 + 1]]).intersection(cornice)
        if ls.is_empty: continue
        ls = ls.simplify(0.00018)
        parts = [ls] if ls.geom_type == "LineString" else [x for x in getattr(ls, "geoms", []) if x.geom_type == "LineString"]
        if not parts: continue
        coords = [[round(x, 4), round(y, 4)] for x, y in max(parts, key=lambda q: q.length).coords]
        sp = []
        okv = len(vel[(a, b)]["t"]) >= 10 and 2 <= float(np.median(vel[(a, b)]["t"])) <= 60
        for f, _ in FASCE:
            v = vel[(a, b)][f]
            sp.append(round(float(np.median(v)), 1) if okv and len(v) >= (3 if f == "t" else 2) else None)
        rl.append({"d": nome(pat[a]), "a": nome(pat[b]), "m": int(round(cum[idx[b]] - cum[idx[a]])), "v": sp, "n": len(vel[(a, b)]["t"]), "c": coords, "s": int(round(cum[idx[a]]))})
    out[rid] = rl; tot_chunks += len(rl)
print("tratti", tot_chunks)
json.dump(out, open(os.path.join(OUT, "tratti.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("byte", os.path.getsize(os.path.join(OUT, "tratti.json")))
