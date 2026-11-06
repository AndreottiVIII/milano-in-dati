"""Coordinate delle 24 stazioni ferroviarie di Milano per la mappa: docs/metro/data/treni_stazioni_coordinate.csv
Fonte: orario Trenord (GTFS, stops.txt) nel filone bici-auto-mezzi; Porta Genova non e' nell'orario Trenord: si usa la fermata M2 omonima (a pochi metri).
Uso: python -I -X utf8 treni_coordinate.py <cartella milano-in-dati>"""
import csv, sys
R = sys.argv[1]
gt = {r["stop_name"]: r for r in csv.DictReader(open(R + "/bici-auto-mezzi/raw/gtfs/ext_trenord/stops.txt", encoding="utf8"))}
met = {r["stazione"]: r for r in csv.DictReader(open(R + "/docs/metro/data/stazioni_metro.csv", encoding="utf8"))}
ALIAS = {"Milano Porta Garibaldi (superficie)": "Milano Porta Garibaldi", "Milano Porta Garibaldi (Passante)": "Milano Porta Garibaldi Passante",
         "Milano Bovisa": "Milano Bovisa Politecnico", "Milano Bruzzano": "Milano Bruzzano Parco Nord", "Milano San Cristoforo": "Milano S.Cristoforo",
         "Milano Porta Romana": "Milano Scalo Romana"}
out = []
for r in csv.DictReader(open(R + "/docs/metro/data/treni_stazioni_milano_2019_2020_2025.csv", encoding="utf8")):
    n = r["stazione_ferroviaria"]; k = ALIAS.get(n, n)
    if k in gt:
        out.append((n, round(float(gt[k]["stop_lat"]), 5), round(float(gt[k]["stop_lon"]), 5), "orario Trenord (GTFS)"))
    elif n == "Milano Porta Genova":
        out.append((n, round(float(met["Porta Genova"]["lat"]), 5), round(float(met["Porta Genova"]["lon"]), 5), "fermata M2 omonima (ATM/AMAT GTFS)"))
    else:
        print("MANCA", n)
w = csv.writer(open(R + "/docs/metro/data/treni_stazioni_coordinate.csv", "w", encoding="utf8", newline=""))
w.writerow(["stazione_ferroviaria", "lat", "lon", "fonte_coordinate"]); w.writerows(out)
print(len(out), "stazioni")
