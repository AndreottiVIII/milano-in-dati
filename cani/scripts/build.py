"""Pulizia e riepiloghi 'Cani di Milano' fase 1.
import warnings; warnings.filterwarnings("ignore")
Uso: python -I -X utf8 build.py <cani assoluto> <milano-in-dati assoluto>
Legge: raw/comune_ds52, raw/osm, ../citta-15-minuti (NIL), ../censimenti (ds205, municipi), ../alberi/pulito/nil_alberi.csv (aree NIL corrette)
Scrive: pulito/*.csv e pulito/riepilogo.json"""
import sys, os, csv, json, collections, statistics
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.strtree import STRtree
C, P = sys.argv[1], sys.argv[2]
out = os.path.join(C, "pulito"); os.makedirs(out, exist_ok=True)
T = Transformer.from_crs(4326, 32632, always_xy=True).transform


def wcsv(name, rows, cols):
    with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


R = {}
# ---------- NIL ----------
nils = json.load(open(os.path.join(P, "citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson"), encoding="utf-8"))
nil_poly = []
nil_info = []
for f in nils["features"]:
    nil_poly.append(transform(T, shape(f["geometry"])))
    nil_info.append((int(f["properties"]["ID_NIL"]), f["properties"]["NIL"]))
tree = STRtree(nil_poly)


def nil_of(lon, lat):
    x, y = T(lon, lat)
    pt = Point(x, y)
    for i in tree.query(pt):
        if nil_poly[i].contains(pt):
            return nil_info[i], False, 0.0
    j = int(tree.nearest(pt))
    d = nil_poly[j].distance(pt)
    return (nil_info[j], True, d) if d <= 100 else (None, True, d)


# ---------- ds52 ----------
src = os.path.join(C, "raw/comune_ds52/ds52_aree_fruizione_cani.csv")
rows = list(csv.DictReader(open(src, encoding="utf-8-sig"), delimiter=";"))
gj = json.load(open(os.path.join(C, "raw/comune_ds52/ds52_aree_fruizione_cani.geojson"), encoding="utf-8"))
geom = {str(f["properties"]["obj_id"]): transform(T, shape(f["geometry"])) for f in gj["features"]}
bulk_dates = {d for d, n in collections.Counter(r["data_ini"] for r in rows).items() if n >= 12}
clean = []
for r in rows:
    lon, lat = float(r["LONG_X_4326"]), float(r["LAT_Y_4326"])
    nl, prox, dist = nil_of(lon, lat)
    di = r["data_ini"].replace("/", "-") if r["data_ini"] else ""
    clean.append({"obj_id": r["obj_id"], "id_area": r["id_area"], "municipio": int(r["municipio"]), "localita": r["località"],
                  "data_scheda": di, "anno_scheda": di[:4], "flag_data_convenzionale": int(r["data_ini"] in bulk_dates or r["data_ini"] == ""),
                  "area_mq": round(float(r["area_mq"]), 1), "perim_m": round(float(r["perim_m"]), 1), "lon": lon, "lat": lat,
                  "id_nil": nl[0] if nl else "", "nil": nl[1] if nl else "", "nil_per_vicinanza": int(prox and nl is not None), "dist_nil_m": round(dist, 1)})
wcsv("aree_cani.csv", clean, list(clean[0].keys()))
R["ds52"] = {"righe": len(rows), "id_area_unici": len({r['id_area'] for r in rows}), "obj_id_unici": len({r['obj_id'] for r in rows}),
             "mq_totali": round(sum(c["area_mq"] for c in clean)), "mq_mediana": statistics.median(c["area_mq"] for c in clean),
             "data_vuota": sum(1 for r in rows if not r["data_ini"]), "date_convenzionali": sorted(bulk_dates),
             "righe_con_data_convenzionale": sum(c["flag_data_convenzionale"] for c in clean),
             "fuori_nil_oltre_100m": sum(1 for c in clean if not c["id_nil"]), "nil_per_vicinanza": sum(c["nil_per_vicinanza"] for c in clean),
             "anno_scheda_max": max(c["anno_scheda"] for c in clean if c["anno_scheda"]), "aree_mq_sotto_100": sum(1 for c in clean if c["area_mq"] < 100),
             "aree_mq_sopra_10000": sum(1 for c in clean if c["area_mq"] > 10000)}
R["ds52"]["punto_csv_fuori_poligono"] = sum(1 for c in clean if not geom[c["obj_id"]].buffer(5).contains(Point(*T(c["lon"], c["lat"]))))
by_nil = collections.defaultdict(collections.Counter)
for c in clean:
    if c["id_nil"]:
        by_nil[c["id_nil"]][c["municipio"]] += 1
R["ds52"]["nil_con_aree_in_piu_municipi"] = sum(1 for k, v in by_nil.items() if len(v) > 1)
# ---------- popolazione ds205 ----------
ds205 = list(csv.DictReader(open(os.path.join(P, "censimenti/raw/comune_annuale_nil/ds205_dati_quartieri_2011_2024_.csv"), encoding="utf-8-sig"), delimiter=";"))
pop = collections.defaultdict(dict)
tot = collections.defaultdict(int)
for r in ds205:
    if not r["Totale"].strip() or not r["NIL"].strip():
        continue
    y = int(r["Anno"])
    n = int(r["NIL"])
    pop[n][y] = int(r["Totale"])
    tot[y] += int(r["Totale"])
R["ds205_totali"] = dict(tot)
area_nil = {}
for r in csv.DictReader(open(os.path.join(P, "alberi/pulito/nil_alberi.csv"), encoding="utf-8"), delimiter=";"):
    area_nil[int(r["id_nil"])] = float(r["area_km2"])
# ---------- aree cani per NIL ----------
agg = collections.defaultdict(lambda: [0, 0.0])
for c in clean:
    if c["id_nil"]:
        a = agg[int(c["id_nil"])]
        a[0] += 1
        a[1] += c["area_mq"]
nil_rows = []
for i, nm in nil_info:
    n, mq = agg.get(i, (0, 0.0))
    p24 = pop.get(i, {}).get(2024, 0)
    nil_rows.append({"id_nil": i, "nil": nm, "abitanti_2024_ds205": p24, "area_km2": area_nil.get(i, ""), "aree_cani": n, "mq_aree_cani": round(mq),
                     "aree_cani_per_100mila_ab": round(n / p24 * 1e5, 1) if p24 >= 5000 else "",
                     "mq_aree_cani_per_abitante": round(mq / p24, 3) if p24 >= 5000 else "",
                     "abitanti_per_area_cani": round(p24 / n) if n and p24 >= 5000 else "",
                     "nota": "" if p24 >= 5000 else "meno di 5000 abitanti: rapporti non calcolati"})
wcsv("aree_cani_per_nil.csv", nil_rows, list(nil_rows[0].keys()))
# ---------- per municipio (popolazione censimento permanente 2023) ----------
mp = {}
for r in csv.DictReader(open(os.path.join(P, "censimenti/pulito/indicatori_municipi.csv"), encoding="utf-8")):
    if r["anno"] == "2023":
        mp[int(r["mun"])] = int(r["pop"])
mun_rows = []
for m in range(1, 10):
    cs = [c for c in clean if c["municipio"] == m]
    mun_rows.append({"municipio": m, "aree_cani": len(cs), "mq_aree_cani": round(sum(c["area_mq"] for c in cs)), "id_area_distinti": len({c["id_area"] for c in cs}),
                     "abitanti_censimento_2023": mp[m], "aree_cani_per_100mila_ab": round(len(cs) / mp[m] * 1e5, 1),
                     "mq_per_abitante": round(sum(c["area_mq"] for c in cs) / mp[m], 3), "abitanti_per_area_cani": round(mp[m] / len(cs))})
wcsv("aree_cani_per_municipio.csv", mun_rows, list(mun_rows[0].keys()))
R["comune_aree"] = {"aree": len(clean), "abitanti_per_area_ds205_2024": round(tot[2024] / len(clean)),
                    "mq_per_abitante_2024": round(sum(c["area_mq"] for c in clean) / tot[2024], 3),
                    "aree_per_100mila_2024": round(len(clean) / tot[2024] * 1e5, 1)}
# ---------- serie per anno scheda ----------
ser = []
byy = collections.Counter(c["anno_scheda"] for c in clean if c["anno_scheda"])
for y in range(2011, 2025):
    cum = sum(n for k, n in byy.items() if int(k) <= y)
    cm = sum(c["area_mq"] for c in clean if c["anno_scheda"] and int(c["anno_scheda"]) <= y)
    ser.append({"anno": y, "aree_con_scheda_entro_anno": cum, "mq": round(cm), "abitanti_ds205": tot[y],
                "aree_per_100mila_ab": round(cum / tot[y] * 1e5, 1), "nuove_schede_nell_anno": byy.get(str(y), 0)})
wcsv("serie_aree_cani_per_anno_scheda.csv", ser, list(ser[0].keys()))
R["serie_aree"] = {s["anno"]: s["aree_con_scheda_entro_anno"] for s in ser}
# ---------- OSM ----------
osm = json.load(open(os.path.join(C, "raw/osm/dog_park.json"), encoding="utf-8"))["elements"]
orow = []
polys = list(geom.values())
ptree = STRtree(polys)
for e in osm:
    lat, lon = (e["lat"], e["lon"]) if e["type"] == "node" else (e["center"]["lat"], e["center"]["lon"])
    x, y = T(lon, lat)
    pt = Point(x, y)
    j = int(ptree.nearest(pt))
    d = polys[j].distance(pt)
    nl, prox, dist = nil_of(lon, lat)
    orow.append({"osm_tipo": e["type"], "osm_id": e["id"], "lon": lon, "lat": lat, "nome": e.get("tags", {}).get("name", ""),
                 "dist_da_area_ds52_m": round(d, 1), "presente_in_ds52_entro_50m": int(d <= 50), "id_nil": nl[0] if nl else ""})
wcsv("osm_dog_park.csv", orow, list(orow[0].keys()))
opts = [Point(*T(o["lon"], o["lat"])) for o in orow]
ot = STRtree(opts)
R["osm"] = {"elementi": len(orow), "dentro_confini_milano": sum(1 for o in orow if o["id_nil"]), "dentro_milano_entro_50m_da_ds52": sum(1 for o in orow if o["id_nil"] and o["presente_in_ds52_entro_50m"]), "entro_50m_da_ds52": sum(o["presente_in_ds52_entro_50m"] for o in orow),
            "oltre_50m": sum(1 for o in orow if not o["presente_in_ds52_entro_50m"]),
            "aree_ds52_con_osm_entro_50m": sum(1 for g in polys if len(ot.query(g.buffer(50), predicate="intersects")) > 0)}
# ---------- totali pubblicati (stampa, non primari) ----------
pub = [
    {"anno_riferimento": "2018 (non dichiarato; articolo del 27/11/2018)", "ambito": "Comune di Milano", "grandezza": "cani iscritti all'anagrafe regionale", "valore": 104067, "fonte": "7giorni.info, articolo 27/11/2018 (cita 'anagrafe regionale' senza data dei dati)", "anno_pop": 2018},
    {"anno_riferimento": "2018 (idem)", "ambito": "ATS Milano (citta' metropolitana)", "grandezza": "cani iscritti", "valore": 351311, "fonte": "stessa", "anno_pop": ""},
    {"anno_riferimento": "2020", "ambito": "Comune di Milano", "grandezza": "animali registrati all'anagrafe (letto come cani)", "valore": 118292, "fonte": "Il Giorno 17/01/2022 su Legambiente X rapporto Animali in Citta", "anno_pop": 2020},
    {"anno_riferimento": "2020", "ambito": "ATS Milano (citta' metropolitana)", "grandezza": "cani in anagrafe ATS", "valore": 375887, "fonte": "stessa", "anno_pop": ""},
    {"anno_riferimento": "2020", "ambito": "Lombardia", "grandezza": "cani", "valore": 1768444, "fonte": "stessa", "anno_pop": ""},
]
for p in pub:
    p["cani_per_100_abitanti_ds205"] = round(p["valore"] / tot[p["anno_pop"]] * 100, 2) if p["anno_pop"] and p["ambito"] == "Comune di Milano" else ""
wcsv("totali_pubblicati.csv", pub, list(pub[0].keys()))
R["totali_pubblicati"] = {f'{p["anno_riferimento"][:4]}_{p["ambito"]}': (p["valore"], p["cani_per_100_abitanti_ds205"]) for p in pub}
json.dump(R, open(os.path.join(out, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
