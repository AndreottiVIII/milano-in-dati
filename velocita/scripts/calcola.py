# -*- coding: utf-8 -*-
"""Passo 2: dalle corse (prepara.py) alle velocita' previste dall'orario, per linea e per ora.
Velocita' di una corsa = lunghezza del percorso (shapes, tra le posizioni della prima e dell'ultima fermata)
 / tempo dalla partenza dal capolinea all'arrivo all'ultimo capolinea. Poi mediana per linea e per fascia.
Scrive in docs/velocita/data/: linee.json, tratte.json, riepilogo.json, linee.csv, nil.geojson.
Uso: python -I -X utf8 velocita/scripts/calcola.py
"""
import os, json, csv, shutil
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point, shape, box
from shapely.ops import unary_union

QUI = os.path.dirname(os.path.abspath(__file__))
RAD = os.path.dirname(os.path.dirname(QUI))
GTFS = os.path.join(RAD, "bici-auto-mezzi", "raw", "gtfs", "ext_comune_new")
OUT = os.path.join(RAD, "docs", "velocita", "data")
os.makedirs(OUT, exist_ok=True)
FILOBUS = {"B90", "B91", "B92", "B93"}
BICI = 15.0

d = pd.read_csv(os.path.join(RAD, "velocita", "lavoro", "corse.csv"), dtype={"route_id": str, "shape_id": str})
rotte = pd.read_csv(os.path.join(GTFS, "routes.txt"), dtype=str).set_index("route_id")
n_tot = len(d)
# corse parziali (rientri in deposito, tratti brevi): meno della meta' della lunghezza mediana della linea
med_l = d.groupby("route_id").lung_m.transform("median")
parz = d.lung_m < 0.5 * med_l
print("corse parziali scartate", int(parz.sum()), "su", n_tot)
d = d[~parz].copy()
d["v"] = d.lung_m / d.durata_s * 3.6
d["ora"] = (d.partenza_s // 3600).astype(int)

def tipo(rid):
    if rid in FILOBUS: return "filobus"
    return {"0": "tram", "1": "metro", "3": "bus"}[rotte.loc[rid, "route_type"]]
d["tipo"] = d.route_id.map(tipo)

# quota del percorso dentro Milano (confini dei quartieri)
nil = json.load(open(os.path.join(RAD, "docs", "negozi", "data", "nil.geojson"), encoding="utf-8"))
milano = unary_union([shape(f["geometry"]).buffer(0) for f in nil["features"]])
xmin, ymin, xmax, ymax = milano.bounds
cornice = box(xmin - 0.02, ymin - 0.015, xmax + 0.02, ymax + 0.015)
sh = pd.read_csv(os.path.join(GTFS, "shapes.txt"), dtype=str, usecols=["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"])
sh["q"] = sh.shape_pt_sequence.astype(int)
sh = sh.sort_values(["shape_id", "q"])
shp = {}
for sid, g in sh.groupby("shape_id", sort=False):
    shp[sid] = LineString(np.c_[g.shape_pt_lon.astype(float).values, g.shape_pt_lat.astype(float).values])

linee = []
tratte = {}
for rid, g in d.groupby("route_id"):
    sid = g.shape_id.value_counts().index[0]
    ls = shp[sid]
    dentro = ls.intersection(milano).length / ls.length
    p = g[(g.ora >= 7) & (g.ora <= 9) | (g.ora >= 17) & (g.ora <= 19)]
    f = g[(g.ora >= 10) & (g.ora <= 15)]
    s = g[(g.ora >= 21)]
    ore = {}
    for h in range(5, 26):
        x = g[g.ora == h]
        ore[h] = round(float(x.v.median()), 2) if len(x) >= 2 else None
    r = rotte.loc[rid]
    nome = r.route_long_name
    linee.append({
        "id": rid, "n": r.route_short_name, "tipo": tipo(rid), "nome": nome,
        "corse": int(len(g)), "km": round(float(g.lung_m.median()) / 1000, 1),
        "v": round(float(g.v.median()), 2),
        "v_punta": round(float(p.v.median()), 2) if len(p) >= 3 else None,
        "v_fuori": round(float(f.v.median()), 2) if len(f) >= 3 else None,
        "v_sera": round(float(s.v.median()), 2) if len(s) >= 3 else None,
        "fkm": round(float((g.fermate / (g.lung_m / 1000)).median()), 2),
        "dentro": round(float(dentro), 2), "ore": [ore[h] for h in range(5, 26)],
    })
    # tratta per la mappa: il percorso piu' usato, ritagliato su Milano
    if dentro >= 0.0:
        c = ls.intersection(cornice).simplify(0.00018)
        parti = [c] if c.geom_type == "LineString" else list(getattr(c, "geoms", []))
        tr = []
        for q in parti:
            if q.geom_type != "LineString" or q.is_empty: continue
            tr.append([[round(x, 4), round(y, 4)] for x, y in q.coords])
        tratte[rid] = tr
linee.sort(key=lambda z: z["v"])
json.dump(linee, open(os.path.join(OUT, "linee.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(tratte, open(os.path.join(OUT, "tratte.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
shutil.copyfile(os.path.join(RAD, "docs", "negozi", "data", "nil.geojson"), os.path.join(OUT, "nil.geojson"))

with open(os.path.join(OUT, "linee.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["linea", "tipo", "nome", "corse_del_giorno", "lunghezza_km", "velocita_kmh", "velocita_punta_kmh", "velocita_fuori_punta_kmh", "velocita_sera_kmh", "fermate_per_km", "quota_percorso_in_milano"] + ["kmh_ora_%02d" % (h % 24) for h in range(5, 26)])
    for z in sorted(linee, key=lambda z: (["metro", "tram", "filobus", "bus"].index(z["tipo"]), int("".join(c for c in z["n"] if c.isdigit()) or 0))):
        fm = lambda x: "" if x is None else str(x).replace(".", ",")
        w.writerow([z["n"], z["tipo"], z["nome"], z["corse"], fm(z["km"]), fm(z["v"]), fm(z["v_punta"]), fm(z["v_fuori"]), fm(z["v_sera"]), fm(z["fkm"]), fm(z["dentro"])] + [fm(x) for x in z["ore"]])

# riepilogo: i numeri della pagina, tutti ricalcolati qui
cit = [z for z in linee if z["tipo"] in ("tram", "bus", "filobus") and z["dentro"] >= 0.6]
def med(l, k): return float(np.median([z[k] for z in l if z[k] is not None]))
riep = {"giorno": "24/11/2026", "corse_usate": int(len(d)), "corse_parziali_scartate": int(parz.sum()), "corse_totali": int(n_tot),
        "linee_cittadine": len(cit), "linee_escluse": len([z for z in linee if z["tipo"] != "metro"]) - len(cit)}
for t in ("tram", "bus", "filobus", "metro"):
    l = [z for z in linee if z["tipo"] == t and (t == "metro" or z["dentro"] >= 0.6)]
    riep[t] = {"linee": len(l), "mediana_linee": round(med(l, "v"), 1)}
# mediana sulle corse (non sulle linee)
for t in ("tram", "bus", "filobus", "metro"):
    riep[t]["mediana_corse"] = round(float(d[d.tipo == t].v.median()), 1)
riep["sotto_bici"] = [z["n"] + " " + z["tipo"] for z in cit if z["v"] < BICI]
riep["n_sotto_bici"] = len(riep["sotto_bici"])
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(riep, ensure_ascii=False, indent=1))
print("piu' lente:", [(z["n"], z["tipo"], z["v"]) for z in cit[:8]])
print("piu' veloci:", [(z["n"], z["tipo"], z["v"]) for z in cit[-8:]])
for f in ("linee.json", "tratte.json"):
    print(f, os.path.getsize(os.path.join(OUT, f)))
