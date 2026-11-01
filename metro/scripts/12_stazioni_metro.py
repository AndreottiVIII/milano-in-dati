"""Tabella unica delle stazioni metro: nome, linee, data di apertura per linea (it.wikipedia), coordinate e corse/giorno (GTFS ATM).
Riusa la lista del filone nomi-fermate (125 stazioni, fermate_metro_nomi_finale.csv + metro_stops_gtfs.csv).
Uso: python -I -X utf8 12_stazioni_metro.py <milano-in-dati> -> scrive metro/pulito/stazioni_metro.csv"""
import sys, csv, os, collections, unicodedata, re
base = sys.argv[1]
P = os.path.join(base, "metro", "pulito")
def key(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(fs|fn|m\d)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()
nf = list(csv.DictReader(open(os.path.join(base, "nomi-fermate", "pulito", "fermate_metro_nomi_finale.csv"), encoding="utf-8-sig")))
stops = list(csv.DictReader(open(os.path.join(base, "nomi-fermate", "raw", "metro_stops_gtfs.csv"), encoding="utf-8-sig")))
gt = {r["stop_id"]: r for r in csv.DictReader(open(os.path.join(P, "gtfs_metro_stazioni.csv"), encoding="utf-8"))}
wk = collections.defaultdict(dict)
wname = {}
for r in csv.DictReader(open(os.path.join(P, "stazioni_wikipedia.csv"), encoding="utf-8")):
    wk[key(r["stazione"])][r["linea"]] = r["apertura_iso"]
    wname[key(r["stazione"])] = r["stazione"]
# fermate GTFS per nome-stazione (la colonna gtfs di nomi-fermate = stop_name maiuscolo)
by_gtfs = collections.defaultdict(list)
for s in stops: by_gtfs[s["stop_name"]].append(s)
ALIAS = {"Abbiategrasso": "Piazza Abbiategrasso", "Lodi": "Lodi TIBB", "Sesto 1° Maggio": "Sesto 1º Maggio"}
rows, miss = [], []
for r in nf:
    k = key(r["stazione"])
    ap = wk.get(key(ALIAS.get(r["stazione"], r["stazione"])))
    if ap is None:
        # prova con il nome GTFS
        k2 = key(r["gtfs"]); ap = wk.get(k2)
    if ap is None: miss.append(r["stazione"])
    fs = [x for nm in r["gtfs"].split(" / ") for x in by_gtfs.get(nm.strip(), [])]
    corse = sum(int(gt[s["stop_id"]]["corse_giorno_feriale_rif"]) for s in fs if s["stop_id"] in gt)
    lat = sum(float(s["lat"]) for s in fs)/len(fs) if fs else ""
    lon = sum(float(s["lon"]) for s in fs)/len(fs) if fs else ""
    rows.append([r["stazione"], r["linee"], ";".join(f"{l}:{d}" for l, d in sorted((ap or {}).items())), round(lat, 6) if lat != "" else "", round(lon, 6) if lon != "" else "", len(fs), corse])
w = csv.writer(open(os.path.join(P, "stazioni_metro.csv"), "w", newline="", encoding="utf-8"))
w.writerow(["stazione", "linee", "apertura_per_linea_wikipedia", "lat_gtfs", "lon_gtfs", "fermate_fisiche_gtfs", "corse_giorno_feriale_gtfs_rif_2026-11-11"])
w.writerows(rows)
print(len(rows), "stazioni; senza data di apertura:", miss)
print("stazioni Wikipedia non agganciate:", sorted(set(wname) - {key(r['stazione']) for r in nf} - {key(r['gtfs']) for r in nf}))
