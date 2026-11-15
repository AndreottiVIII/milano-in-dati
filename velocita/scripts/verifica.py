# -*- coding: utf-8 -*-
"""Controllo indipendente dei 6 numeri della pagina: rifa' il calcolo da capo in Python puro (modulo csv),
con la formula di haversine vera e una ricerca della fermata piu' vicina fatta a mano.
Non usa prepara.py ne' calcola.py. Uso: python -I -X utf8 velocita/scripts/verifica.py"""
import csv, os, math, json, statistics as st, collections
QUI = os.path.dirname(os.path.abspath(__file__)); RAD = os.path.dirname(os.path.dirname(QUI))
G = os.path.join(RAD, "bici-auto-mezzi", "raw", "gtfs", "ext_comune_new")
csv.field_size_limit(10**9)
def rd(n):
    with open(os.path.join(G, n), encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def hav(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(x))
sv = {r["service_id"] for r in rd("calendar_dates.txt") if r["date"] == "20261124" and r["exception_type"] == "1"}
trips = {t["trip_id"]: t for t in rd("trips.txt") if t["service_id"] in sv}
stops = {s["stop_id"]: (float(s["stop_lat"]), float(s["stop_lon"])) for s in rd("stops.txt")}
sh = collections.defaultdict(list)
for r in rd("shapes.txt"): sh[r["shape_id"]].append((int(r["shape_pt_sequence"]), float(r["shape_pt_lat"]), float(r["shape_pt_lon"])))
shp = {}
for k, v in sh.items():
    v.sort(); cum = [0.0]
    for i in range(1, len(v)): cum.append(cum[-1] + hav(v[i-1][1], v[i-1][2], v[i][1], v[i][2]))
    shp[k] = ([p[1] for p in v], [p[2] for p in v], cum)
tt = collections.defaultdict(list)
with open(os.path.join(G, "stop_times.txt"), encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["trip_id"] in trips: tt[r["trip_id"]].append((int(r["stop_sequence"]), r["arrival_time"], r["departure_time"], r["stop_id"]))
sec = lambda t: sum(int(x) * m for x, m in zip(t.split(":"), (3600, 60, 1)))
def near(la, lo, lat, lon, start=0):
    best = None
    for i in range(start, len(lat)):
        d = hav(la, lo, lat[i], lon[i])
        if best is None or d < best[0]: best = (d, i)
    return best[1]
cache = {}; corse = []
for tid, t in trips.items():
    s = sorted(tt[tid]); 
    if len(s) < 2: continue
    la0, lo0 = stops[s[0][3]]; la1, lo1 = stops[s[-1][3]]
    lat, lon, cum = shp[t["shape_id"]]
    key = (t["shape_id"], s[0][3], s[-1][3])
    if key not in cache:
        i0 = near(la0, lo0, lat, lon); i1 = near(la1, lo1, lat, lon, min(i0 + 1, len(lat) - 1)); cache[key] = cum[i1] - cum[i0]
    dur = sec(s[-1][1]) - sec(s[0][2])
    corse.append((t["route_id"], sec(s[0][2]) // 3600, cache[key], dur, len(s)))
by = collections.defaultdict(list)
for c in corse: by[c[0]].append(c)
linee = {}
for rid, l in by.items():
    ml = st.median([c[2] for c in l]); k = [c for c in l if c[2] >= 0.5 * ml]
    v = [c[2] / c[3] * 3.6 for c in k]
    ore = collections.defaultdict(list)
    for c in k: ore[c[1]].append(c[2] / c[3] * 3.6)
    linee[rid] = dict(v=st.median(v), fkm=st.median([c[4] / (c[2] / 1000) for c in k]), o8=st.median(ore[8]) if len(ore[8]) >= 2 else None, o22=st.median(ore[22]) if len(ore[22]) >= 2 else None)
ref = {z["id"]: z for z in json.load(open(os.path.join(RAD, "docs", "velocita", "data", "linee.json"), encoding="utf-8"))}
city = [i for i, z in ref.items() if z["tipo"] != "metro" and z["dentro"] >= 0.6]   # stesso elenco di linee cittadine
tram = [i for i in city if ref[i]["tipo"] == "tram"]
print("1) mediana tram:", round(st.median(linee[i]["v"] for i in tram), 1), "(pagina", round(st.median(ref[i]["v"] for i in tram), 1), ")")
print("2) linee sotto 15 km/h:", sum(linee[i]["v"] < 15 for i in city), "su", len(city), "(pagina", sum(ref[i]["v"] < 15 for i in city), ")")
r = [linee[i]["o8"] / linee[i]["o22"] - 1 for i in city if linee[i]["o8"] and linee[i]["o22"]]
print("3) piu' piano alle 8 che alle 22: %", round(-100 * st.median(r)), "su", len(r), "linee")
a = [linee[i]["v"] for i in city if linee[i]["fkm"] < 2.5]; b = [linee[i]["v"] for i in city if linee[i]["fkm"] >= 3.5]
print("4) fermate: <2,5 ->", round(st.median(a), 1), len(a), "linee; >=3,5 ->", round(st.median(b), 1), len(b), "linee")
sl = min(city, key=lambda i: linee[i]["v"]); print("5) linea piu' lenta:", sl, round(linee[sl]["v"], 2), "(pagina", ref[sl]["v"], ")")
met = [linee[i]["v"] for i in ("M1", "M2", "M3", "M4", "M5")]
print("6) metro mediana:", round(st.median(met), 1), "rapporto col tram", round(st.median(met) / st.median(linee[i]["v"] for i in tram), 1))
print("   metro per linea:", {i: round(linee[i]["v"], 1) for i in ("M1", "M2", "M3", "M4", "M5")})
