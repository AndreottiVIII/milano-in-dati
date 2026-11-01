"""Servizio metro dal GTFS AMAT/ATM (feed_version 425, 26/10-30/11/2026), cartella gia' scaricata dal filone bici-auto-mezzi.
Produce:
 pulito/gtfs_metro_servizio_giorno.csv : per data e linea, numero corse, prima partenza, ultima partenza (dai calendar_dates)
 pulito/gtfs_metro_stazioni.csv        : per fermata fisica: id, nome, linee che la servono, lat, lon, corse al giorno feriale tipo
Uso: python -I -X utf8 07_gtfs_metro.py <cartella_gtfs_estratta> <out_dir>"""
import sys, csv, os, datetime, collections
g, out = sys.argv[1], sys.argv[2]
rd = lambda f: csv.DictReader(open(os.path.join(g, f), encoding="utf-8-sig"))
routes = {r["route_id"]: r["route_short_name"] for r in rd("routes.txt") if r["route_type"] == "1"}
trips = {}
for t in rd("trips.txt"):
    if t["route_id"] in routes: trips[t["trip_id"]] = (f"M{routes[t['route_id']]}", t["service_id"], t["direction_id"])
print(len(trips), "corse metro")
svc_dates = collections.defaultdict(set)
for c in rd("calendar_dates.txt"):
    if c["exception_type"] == "1": svc_dates[c["service_id"]].add(c["date"])
def secs(s): h, m, x = s.split(":"); return int(h)*3600+int(m)*60+int(x)
trip_first, trip_last = {}, {}
stop_trips = collections.defaultdict(set)
with open(os.path.join(g, "stop_times.txt"), encoding="utf-8-sig") as f:
    rdr = csv.DictReader(f)
    for r in rdr:
        tid = r["trip_id"]
        if tid not in trips: continue
        d = secs(r["departure_time"] or r["arrival_time"])
        if tid not in trip_first or d < trip_first[tid]: trip_first[tid] = d
        if tid not in trip_last or d > trip_last[tid]: trip_last[tid] = d
        stop_trips[r["stop_id"]].add(tid)
fmt = lambda s: f"{s//3600:02d}:{(s%3600)//60:02d}"
agg = collections.defaultdict(lambda: [0, 10**9, -1])
for tid, (line, sid, dr) in trips.items():
    for d in svc_dates.get(sid, ()):
        a = agg[(d, line)]; a[0] += 1; a[1] = min(a[1], trip_first[tid]); a[2] = max(a[2], trip_first[tid])
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "gtfs_metro_servizio_giorno.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["data", "giorno_settimana", "linea", "corse", "prima_partenza_prima_fermata", "ultima_partenza_prima_fermata"])
    for (d, line), (n, a, b) in sorted(agg.items()):
        dt = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:]))
        w.writerow([dt.isoformat(), dt.strftime("%a"), line, n, fmt(a), fmt(b)])
# fermate
feed = list(rd("feed_info.txt"))[0]
wd = [d for d in {d for v in svc_dates.values() for d in v} if datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])).weekday() == 2]  # mercoledi
ref = sorted(wd)[len(wd)//2] if wd else None
print("giorno feriale di riferimento", ref, "feed", feed)
stops = {s["stop_id"]: s for s in rd("stops.txt")}
with open(os.path.join(out, "gtfs_metro_stazioni.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["stop_id", "nome_gtfs", "linee", "lat", "lon", "corse_giorno_feriale_rif", "giorno_rif", "feed_version"])
    for sid, tset in sorted(stop_trips.items()):
        lines = sorted({trips[t][0] for t in tset})
        n = sum(1 for t in tset if ref in svc_dates.get(trips[t][1], ()))
        s = stops[sid]
        w.writerow([sid, s["stop_name"], "+".join(lines), s["stop_lat"], s["stop_lon"], n, ref, feed["feed_version"]])
print("fermate", len(stop_trips))
