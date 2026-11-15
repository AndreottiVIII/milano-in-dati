# -*- coding: utf-8 -*-
"""Tempi di percorrenza del metrò dall'orario GTFS (Comune di Milano, ds929, CC BY 4.0), martedì 24/11/2026.
Costruisce la rete: nodi = stazione di una linea (134), archi tra stazioni successive con il tempo mediano
(arrivo alla successiva - arrivo alla precedente, corse con partenza tra le 7 e le 20), scambi = stazioni
in comune tra linee (distanza sotto 120 m, oppure sotto 300 m con lo stesso nome: Loreto).
Calcola anche, per ogni percorso da capolinea a capolinea, minuti, chilometri (sul tracciato) e velocità media.
Scrive docs/metro/data/tempi.json. Uso: python -I -X utf8 metro/scripts/tempi.py"""
import csv, os, json, math, statistics as st, collections
QUI = os.path.dirname(os.path.abspath(__file__)); RAD = os.path.dirname(os.path.dirname(QUI))
G = os.path.join(RAD, "bici-auto-mezzi", "raw", "gtfs", "ext_comune_new"); csv.field_size_limit(10**9)
OUT = os.path.join(RAD, "docs", "metro", "data", "tempi.json")
LINEE = ("M1", "M2", "M3", "M4", "M5")
def rd(n, f=None):
    with open(os.path.join(G, n), encoding="utf-8-sig", newline="") as fh:
        return [r for r in csv.DictReader(fh) if (f is None or f(r))]
def hav(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(x))
sec = lambda t: sum(int(x) * m for x, m in zip(t.split(":"), (3600, 60, 1)))
sv = {r["service_id"] for r in rd("calendar_dates.txt", lambda r: r["date"] == "20261124" and r["exception_type"] == "1")}
trips = {t["trip_id"]: t for t in rd("trips.txt", lambda t: t["route_id"] in LINEE and t["service_id"] in sv)}
stops = {s["stop_id"]: s for s in rd("stops.txt")}
tt = collections.defaultdict(list)
for r in rd("stop_times.txt", lambda r: r["trip_id"] in trips):
    tt[r["trip_id"]].append((int(r["stop_sequence"]), sec(r["arrival_time"]), sec(r["departure_time"]), r["stop_id"]))
for k in tt: tt[k].sort()
print("corse del metro", len(trips))
# nomi e coordinate delle stazioni dal file della pagina (stesse stazioni, stessi nomi)
ref = []
with open(os.path.join(RAD, "docs", "metro", "data", "stazioni_metro.csv"), encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh): ref.append((r["stazione"], r["linee"].split(","), float(r["lat"]), float(r["lon"])))
def nome_rif(sid, linea):
    s = stops[sid]; la, lo = float(s["stop_lat"]), float(s["stop_lon"]); best = None
    for n, ls, a, b in ref:
        if linea in ls:
            d = hav(la, lo, a, b)
            if best is None or d < best[0]: best = (d, n)
    return best
nodi = {}
for t in trips.values():
    for _, _, _, sid in tt[t["trip_id"]]: nodi[(t["route_id"], sid)] = None
chiavi = sorted(nodi, key=lambda k: (k[0], k[1]))
idn = {k: i for i, k in enumerate(chiavi)}
nome_n = {}
for k in chiavi:
    d, n = nome_rif(k[1], k[0]); nome_n[k] = (n.replace(" " + k[0], "").strip() if n.endswith(" " + k[0]) else n); assert d < 400, (k, d, n)
# stazioni = nodi uniti dagli scambi
par = list(range(len(chiavi)))
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
def xy(k): s = stops[k[1]]; return float(s["stop_lat"]), float(s["stop_lon"])
for i, a in enumerate(chiavi):
    for j in range(i + 1, len(chiavi)):
        b = chiavi[j]
        if a[0] == b[0]: continue
        d = hav(*xy(a), *xy(b))
        if d < 120 or (d < 300 and nome_n[a].split()[0].lower() == nome_n[b].split()[0].lower()): par[f(i)] = f(j)
gr = collections.defaultdict(list)
for i in range(len(chiavi)): gr[f(i)].append(i)
stazioni = []; st_di = {}
for g_, mem in sorted(gr.items(), key=lambda kv: min(nome_n[chiavi[i]] for i in kv[1])):
    nm = min((nome_n[chiavi[i]] for i in mem), key=len)
    la = st.mean(xy(chiavi[i])[0] for i in mem); lo = st.mean(xy(chiavi[i])[1] for i in mem)
    for i in mem: st_di[i] = len(stazioni)
    stazioni.append({"n": nm, "lat": round(la, 5), "lon": round(lo, 5), "l": sorted({chiavi[i][0] for i in mem})})
print("nodi", len(chiavi), "stazioni", len(stazioni), "interscambi", sum(1 for s in stazioni if len(s["l"]) > 1))
# archi
camp = collections.defaultdict(list)
for t in trips.values():
    s = tt[t["trip_id"]]
    if not (7 <= s[0][2] // 3600 <= 20): continue
    for a, b in zip(s, s[1:]):
        camp[(idn[(t["route_id"], a[3])], idn[(t["route_id"], b[3])])].append(b[1] - a[1])
arch = {}
for (a, b), v in camp.items():
    if len(v) < 20: continue
    k = (min(a, b), max(a, b)); arch.setdefault(k, []).extend(v)
archi = [[a, b, int(round(st.median(v)))] for (a, b), v in sorted(arch.items())]
print("archi", len(archi), "tempo mediano tra stazioni", st.median(x[2] for x in archi))
# percorsi capolinea-capolinea
sh = collections.defaultdict(list)
for r in rd("shapes.txt"): sh[r["shape_id"]].append((int(r["shape_pt_sequence"]), float(r["shape_pt_lat"]), float(r["shape_pt_lon"])))
shp = {}
for k, v in sh.items():
    v.sort(); cum = [0.0]
    for i in range(1, len(v)): cum.append(cum[-1] + hav(v[i-1][1], v[i-1][2], v[i][1], v[i][2]))
    shp[k] = ([p[1] for p in v], [p[2] for p in v], cum)
def near(la, lo, lat, lon, start=0):
    bd, bi = 1e18, start
    for i in range(start, len(lat)):
        d = hav(la, lo, lat[i], lon[i])
        if d < bd: bd, bi = d, i
    return bi
pat = collections.defaultdict(list)
for t in trips.values():
    s = tt[t["trip_id"]]
    if not (7 <= s[0][2] // 3600 <= 20): continue
    pat[(t["route_id"], s[0][3], s[-1][3])].append((s[-1][1] - s[0][2], len(s), t["shape_id"], s))
percorsi = []
for (l, a, b), v in sorted(pat.items()):
    if len(v) < 40: continue
    s = v[0][3]; lat, lon, cum = shp[v[0][2]]
    i0 = near(*xy((l, a)), lat, lon); i1 = near(*xy((l, b)), lat, lon, min(i0 + 1, len(lat) - 1))
    kmq = (cum[i1] - cum[i0]) / 1000; mn = st.median(x[0] for x in v) / 60
    percorsi.append({"l": l, "da": nome_n[(l, a)], "a": nome_n[(l, b)], "min": round(mn, 1), "km": round(kmq, 1), "kmh": round(kmq / mn * 60, 1), "fermate": v[0][1], "corse": len(v)})
for p in percorsi: print(p)
json.dump({"giorno": "24/11/2026", "scambio_min": 4, "stazioni": stazioni,
           "nodi": [[st_di[i], chiavi[i][0]] for i in range(len(chiavi))], "archi": archi, "percorsi": percorsi},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(os.path.getsize(OUT), "byte")
