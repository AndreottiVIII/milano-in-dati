# -*- coding: utf-8 -*-
"""Controllo indipendente dei numeri sui tratti (km sotto i 15 km/h alle 8 e alle 22, tratto piu' lento).
Python puro, haversine vera, ricerca a mano del punto piu' vicino. Uso: python -I -X utf8 velocita/scripts/verifica_tratti.py"""
import csv, os, math, json, statistics as st, collections
QUI = os.path.dirname(os.path.abspath(__file__)); RAD = os.path.dirname(os.path.dirname(QUI))
G = os.path.join(RAD, "bici-auto-mezzi", "raw", "gtfs", "ext_comune_new"); csv.field_size_limit(10**9)
def rd(n):
    with open(os.path.join(G, n), encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def hav(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(x))
sec = lambda t: sum(int(x) * m for x, m in zip(t.split(":"), (3600, 60, 1)))
ref = json.load(open(os.path.join(RAD, "docs", "velocita", "data", "tratti.json"), encoding="utf-8"))
sv = {r["service_id"] for r in rd("calendar_dates.txt") if r["date"] == "20261124" and r["exception_type"] == "1"}
tr = [t for t in rd("trips.txt") if t["service_id"] in sv and t["route_id"] in ref]
main = {}
for rid in ref: main[rid] = collections.Counter(t["shape_id"] for t in tr if t["route_id"] == rid).most_common(1)[0][0]
tr = [t for t in tr if t["shape_id"] == main[t["route_id"]]]; ids = {t["trip_id"] for t in tr}
stops = {s["stop_id"]: (float(s["stop_lat"]), float(s["stop_lon"])) for s in rd("stops.txt")}
tt = collections.defaultdict(list)
with open(os.path.join(G, "stop_times.txt"), encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["trip_id"] in ids: tt[r["trip_id"]].append((int(r["stop_sequence"]), r["arrival_time"], r["departure_time"], r["stop_id"]))
sh = collections.defaultdict(list)
for r in rd("shapes.txt"):
    if r["shape_id"] in set(main.values()): sh[r["shape_id"]].append((int(r["shape_pt_sequence"]), float(r["shape_pt_lat"]), float(r["shape_pt_lon"])))
FA = [lambda h: True, lambda h: 7 <= h <= 9, lambda h: 10 <= h <= 15, lambda h: 17 <= h <= 19, lambda h: h >= 21]
tot = [[0, 0] for _ in FA]; best = None
for rid, sid in main.items():
    v = sorted(sh[sid]); lat = [p[1] for p in v]; lon = [p[2] for p in v]; cum = [0.0]
    for i in range(1, len(v)): cum.append(cum[-1] + hav(lat[i-1], lon[i-1], lat[i], lon[i]))
    mine = [t["trip_id"] for t in tr if t["route_id"] == rid]
    seqs = collections.Counter(tuple(x[3] for x in sorted(tt[t])) for t in mine)
    pat = seqs.most_common(1)[0][0]; idx = []; prev = 0
    for s_ in pat:
        best_i, bd = prev, 1e18
        for i in range(prev, len(lat)):
            if cum[i] > cum[prev] + 3000: break
            d = hav(stops[s_][0], stops[s_][1], lat[i], lon[i])
            if d < bd: bd, best_i = d, i
        idx.append(best_i); prev = best_i
    bound = [0]
    for j in range(1, len(pat)):
        if cum[idx[j]] - cum[idx[bound[-1]]] >= 400: bound.append(j)
    if bound[-1] != len(pat) - 1:
        if len(bound) > 1 and cum[idx[-1]] - cum[idx[bound[-1]]] < 400: bound[-1] = len(pat) - 1
        else: bound.append(len(pat) - 1)
    for a, b in zip(bound, bound[1:]):
        L = cum[idx[b]] - cum[idx[a]]; vs = [[] for _ in FA]
        for t in mine:
            arr = {x[3]: x[1] for x in tt[t]}; dep = {x[3]: x[2] for x in tt[t]}
            if pat[a] in dep and pat[b] in arr:
                dt = sec(arr[pat[b]]) - sec(dep[pat[a]])
                if dt > 0:
                    h = sec(dep[pat[a]]) // 3600
                    for k, fn in enumerate(FA):
                        if fn(h): vs[k].append(L / dt * 3.6)
        if not (len(vs[0]) >= 10 and 2 <= st.median(vs[0]) <= 60): continue
        for k in range(len(FA)):
            if len(vs[k]) >= (3 if k == 0 else 2):
                m = st.median(vs[k]); tot[k][1] += L; tot[k][0] += L if m < 15 else 0
        if best is None or st.median(vs[0]) < best[0]: best = (round(st.median(vs[0]), 1), rid, pat[a], pat[b], round(L))
for k, n in enumerate(["tutto il giorno", "8", "13", "18", "22"]):
    print("km sotto 15 km/h,", n, ":", round(100 * tot[k][0] / tot[k][1], 1), "% su", round(tot[k][1] / 1000), "km")
print("tratto piu' lento:", best)
