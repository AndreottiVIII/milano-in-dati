"""Rifà da zero i numeri in alto della pagina «La falda che risale», con un metodo diverso da calcola.py:
- punti campionati ogni 75 m sulle linee (invece di 150 m) e interpolazione 'griddata' (invece di LinearNDInterpolator);
- celle da 80 m sfalsate (invece di 100 m);
- soggiacenza: area di intersezione tra quartiere e poligoni (invece dei punti).
Poi confronta con docs/fogne/data/falda_riepilogo.json."""
import json, pathlib, collections
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.ops import transform as sh_transform, unary_union
from shapely import prepared
from scipy.interpolate import griddata

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "falda" / "dati_grezzi"
T = Transformer.from_crs(4326, 32632, always_xy=True)
pr = lambda g: sh_transform(T.transform, g)
num = lambda s: float(str(s).replace(",", "."))


def pts_val(nome, campo, passo=75):
    P, V = [], []
    for f in json.load(open(RAW / nome, encoding="utf8"))["features"]:
        v = f["properties"].get(campo)
        if v in (None, ""):
            continue
        g = pr(shape(f["geometry"]))
        for ln in getattr(g, "geoms", [g]):
            n = max(2, int(ln.length // passo) + 1)
            for i in range(n + 1):
                p = ln.interpolate(i / n, normalized=True)
                P.append((p.x, p.y)); V.append(num(v))
    return np.array(P), np.array(V)


nil = json.load(open(ROOT / "docs" / "negozi" / "data" / "nil.geojson", encoding="utf8"))
Q = [(f["properties"]["i"], f["properties"]["n"], pr(shape(f["geometry"]))) for f in nil["features"]]
cells = {}
for i, n, g in Q:
    pg = prepared.prep(g)
    x0, y0, x1, y1 = g.bounds
    pts = [(x, y) for x in np.arange(x0 + 17, x1, 80) for y in np.arange(y0 + 23, y1, 80) if pg.contains(Point(x, y))]
    if not pts:
        c = g.representative_point(); pts = [(c.x, c.y)]
    cells[i] = np.array(pts)
allp = np.vstack(list(cells.values()))

carte = {"2007-03": ("piezo_2007_03", "piezometri"), "2007-09": ("piezo_2007_09", "piezometri"), "2010-03": ("piezo_2010_03", "contour"),
         "2013-09": ("piezo_2013_09", "quota"), "2022-03": ("piezo_2022_03", "text"), "2022-09": ("piezo_2022_09", "text"),
         "2010-09": ("piezo_2010_09", "contour")}
Z = {}
for k, (f, c) in carte.items():
    P, V = pts_val(f + ".geojson", c)
    Z[k] = {i: griddata(P, V, cells[i], method="linear") for i in cells}
    Z[k]["all"] = np.concatenate([Z[k][i] for i in cells])
    print(k, "celle senza valore:", int(np.isnan(Z[k]["all"]).sum()), "su", len(allp))

m = lambda k: float(np.nanmean(Z[k]["all"]))
r = {}
r["serie"] = {k: round(m(k), 2) for k in Z}
r["salita_2007_2013_settembre"] = round(m("2013-09") - m("2007-09"), 2)
r["marzo_2010_2022"] = round(m("2022-03") - m("2010-03"), 2)
r["marzo_2007_2022"] = round(m("2022-03") - m("2007-03"), 2)
d = {i: float(np.nanmean(Z["2022-03"][i])) - float(np.nanmean(Z["2010-03"][i])) for i in cells}
r["nil_in_discesa"] = sum(1 for v in d.values() if v < 0)
r["nil_in_salita"] = sum(1 for v in d.values() if v > 0)
r["nil_scesi_oltre_1_5m"] = sum(1 for v in d.values() if v < -1.5)
r["nil_saliti_oltre_1_5m"] = sum(1 for v in d.values() if v > 1.5)
r["nil_scesi_oltre_50cm"] = sum(1 for v in d.values() if v < -0.5)
r["nil_saliti_oltre_50cm"] = sum(1 for v in d.values() if v > 0.5)
ds = {i: float(np.nanmean(Z["2022-09"][i])) - float(np.nanmean(Z["2010-09"][i])) for i in cells}
r["nil_in_discesa_settembre"] = sum(1 for v in ds.values() if v < 0)
r["max_discesa"] = min((round(v, 2), dict((i, n) for i, n, _ in Q)[k]) for k, v in d.items())
r["max_salita"] = max((round(v, 2), dict((i, n) for i, n, _ in Q)[k]) for k, v in d.items())

# soggiacenza: area
sog = [(f["properties"]["classe"], pr(shape(f["geometry"]))) for f in json.load(open(RAW / "soggiacenza_2022_03.geojson", encoding="utf8"))["features"]]
unione = {}
for c, g in sog:
    unione.setdefault(c, []).append(g)
unione = {c: unary_union(v).buffer(0) for c, v in unione.items()}
sotto5, dom = [], {}
for i, n, g in Q:
    a = {c: g.intersection(u).area for c, u in unione.items()}
    tot = sum(a.values())
    dom[n] = max(a, key=a.get)
    if (a.get("< 2,5", 0) + a.get("2,5 - 5", 0)) / tot >= 0.5:
        sotto5.append(n)
r["nil_con_falda_sotto_5m_su_meta_territorio"] = (len(sotto5), sorted(sotto5))
r["classe_duomo"] = dom.get("Duomo")

# stazioni: classe nel punto
import csv
cl = collections.Counter()
for s in csv.DictReader(open(ROOT / "docs" / "metro" / "data" / "stazioni_metro.csv", encoding="utf8")):
    x, y = T.transform(float(s["lon"]), float(s["lat"]))
    p = Point(x, y)
    c = next((c for c, u in unione.items() if u.contains(p)), None)
    cl[c] += 1
r["stazioni_classi"] = dict(cl)
r["stazioni_sotto_10m"] = sum(cl[c] for c in ("< 2,5", "2,5 - 5", "5 - 7,5", "7,5 - 10"))
r["stazioni_sotto_5m"] = cl["< 2,5"] + cl["2,5 - 5"]
print(json.dumps(r, ensure_ascii=False, indent=1))

# confronto con riepilogo.json
R = json.load(open(ROOT / "docs" / "fogne" / "data" / "falda_riepilogo.json", encoding="utf8"))
conf = [("salita 2007-2013 (set)", r["salita_2007_2013_settembre"], R["salita_2007_2013_settembre_m"]),
        ("marzo 2010-2022", r["marzo_2010_2022"], R["variazione_media_m"]),
        ("marzo 2007-2022", r["marzo_2007_2022"], R["salita_2007_2022_marzo_m"]),
        ("quartieri scesi oltre 1,5 m", r["nil_scesi_oltre_1_5m"], R["nil_scesi_oltre_1_5m"]),
        ("quartieri saliti oltre 1,5 m", r["nil_saliti_oltre_1_5m"], R["nil_saliti_oltre_1_5m"]),
        ("quartieri scesi oltre 50 cm", r["nil_scesi_oltre_50cm"], R["nil_scesi_oltre_50cm"]),
        ("quartieri saliti oltre 50 cm", r["nil_saliti_oltre_50cm"], R["nil_saliti_oltre_50cm"]),
        ("quartieri in discesa", r["nil_in_discesa"], R["nil_in_discesa"]),
        ("quartieri in discesa (set)", r["nil_in_discesa_settembre"], R["nil_in_discesa_settembre"]),
        ("quartieri falda <5 m", r["nil_con_falda_sotto_5m_su_meta_territorio"][0], R["nil_prevalenza_sotto_5m"]),
        ("stazioni <10 m", r["stazioni_sotto_10m"], R["stazioni_falda_sotto_10m"]),
        ("stazioni <5 m", r["stazioni_sotto_5m"], R["stazioni_falda_sotto_5m"])]
for n, a, b in conf:
    print(f"{n:32s} verifica={a}  pagina={b}  {'OK' if abs(a - b) <= (0.1 if isinstance(a, float) else 0) else 'DIFFERENZA'}")
