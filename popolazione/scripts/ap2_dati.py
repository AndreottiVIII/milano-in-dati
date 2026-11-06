"""Dati nuovi per la pagina «Chi arriva e chi lascia» (versione 2).
1) nil_flussi_2020_2024.csv: per ogni quartiere, arrivi e partenze ogni 1.000 residenti all'anno (media 2020-2024), da Italia e da estero.
2) mappa_aree_italia.json: confini semplificati di regioni (ISTAT, limiti amministrativi, via openpolis), riuniti nelle aree della pagina,
   più la provincia di Milano (comuni con g='MI' di hinterland/comuni.geojson) e il comune di Milano.
Uso: python -I -X utf8 ap2_dati.py <popolazione assoluto> <milano-in-dati assoluto> <regioni geojson scaricato>
"""
import sys, os, json
import pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
P, R, REG = sys.argv[1:4]
OUT = os.path.join(R, "docs", "arrivi-partenze", "data")
# ---- 1. quartieri
f = pd.read_csv(os.path.join(P, "pulito", "flussi_nil_anno.csv"))
f = f[(f.anno >= 2020) & (f.anno <= 2024)]
g = f.groupby(["id_nil", "nil"]).agg(isc_i=("isc_italia", "sum"), canc_i=("canc_italia", "sum"), isc_e=("isc_estero", "sum"),
                                     canc_e=("canc_estero", "sum"), res_anni=("residenti", "sum"), res_medi=("residenti", "mean")).reset_index()
for c in ["isc_i", "canc_i", "isc_e", "canc_e"]:
    g[c + "_x1000"] = (g[c] / g.res_anni * 1000).round(1)
g["arrivi_x1000"] = ((g.isc_i + g.isc_e) / g.res_anni * 1000).round(1)
g["partenze_x1000"] = ((g.canc_i + g.canc_e) / g.res_anni * 1000).round(1)
g["saldo_italia_x1000"] = ((g.isc_i - g.canc_i) / g.res_anni * 1000).round(1)
g["saldo_estero_x1000"] = ((g.isc_e - g.canc_e) / g.res_anni * 1000).round(1)
g["saldo_totale_x1000"] = (((g.isc_i + g.isc_e) - (g.canc_i + g.canc_e)) / g.res_anni * 1000).round(1)
g["res_medi"] = g.res_medi.round(0).astype(int)
g["abbastanza_grande"] = (g.res_medi >= 3000).astype(int)
g = g.drop(columns=["res_anni"])
g.rename(columns={"id_nil": "id", "nil": "quartiere", "isc_i": "arrivi_da_italia", "canc_i": "partenze_per_italia", "isc_e": "arrivi_da_estero", "canc_e": "partenze_per_estero"}).to_csv(
    os.path.join(OUT, "nil_flussi_2020_2024.csv"), index=False, sep=";")
print(g.head(3).to_string())
# ---- 2. mappa
GR = {"Piemonte": "nord", "Valle d'Aosta/Vallée d'Aoste": "nord", "Liguria": "nord", "Trentino-Alto Adige/Südtirol": "nord", "Veneto": "nord",
      "Friuli-Venezia Giulia": "nord", "Emilia-Romagna": "nord", "Lazio": "centro", "Toscana": "centro", "Umbria": "centro", "Marche": "centro",
      "Abruzzo": "sud", "Molise": "sud", "Campania": "sud", "Puglia": "sud", "Basilicata": "sud", "Calabria": "sud", "Sicilia": "sud", "Sardegna": "sud", "Lombardia": "lombardia"}
reg = json.load(open(REG, encoding="utf-8"))
com = json.load(open(os.path.join(R, "docs", "hinterland", "data", "comuni.geojson"), encoding="utf-8"))
mi = unary_union([shape(x["geometry"]) for x in com["features"] if x["properties"]["g"] == "MI"]).buffer(0.0005).buffer(-0.0005)
milano = unary_union([shape(x["geometry"]) for x in com["features"] if x["properties"]["g"] == "MILANO"])
lomb = unary_union([shape(x["geometry"]) for x in reg["features"] if GR[x["properties"]["reg_name"]] == "lombardia"])
areas = {}
for x in reg["features"]:
    a = GR[x["properties"]["reg_name"]]
    if a == "lombardia": continue
    areas.setdefault(a, []).append(shape(x["geometry"]))
feats = []
def add(k, geom, tol):
    geom = geom.simplify(tol, preserve_topology=True)
    def rnd(c): return [round(v, 3) for v in c]
    m = mapping(geom)
    def walk(o): return [walk(i) for i in o] if isinstance(o[0], (list, tuple)) and isinstance(o[0][0], (list, tuple)) else [rnd(p) for p in o]
    feats.append({"type": "Feature", "properties": {"a": k}, "geometry": {"type": m["type"], "coordinates": walk(m["coordinates"]) if m["type"] != "Point" else m["coordinates"]}})
for k, v in areas.items(): add(k, unary_union(v), 0.015)
resto = lomb.difference(mi)
add("resto_lombardia", resto, 0.015)
add("hinterland", mi, 0.004)
add("milano", milano, 0.002)
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "mappa_aree_italia.json"), "w"), separators=(",", ":"))
print(os.path.getsize(os.path.join(OUT, "mappa_aree_italia.json")))
# ---- 3. comuni della provincia di Milano (per la mappa di dettaglio); Milano ha g='MILANO'
cf = []
for x in com["features"]:
    p = x["properties"]
    if p["g"] not in ("MI", "MILANO"): continue
    geom = shape(x["geometry"]).simplify(0.0012, preserve_topology=True)
    m = mapping(geom)
    def rnd(o): return [rnd(i) for i in o] if isinstance(o[0], (list, tuple)) else [round(o[0], 4), round(o[1], 4)]
    cf.append({"type": "Feature", "properties": {"n": p["n"], "g": p["g"]}, "geometry": {"type": m["type"], "coordinates": rnd(m["coordinates"])}})
json.dump({"type": "FeatureCollection", "features": cf}, open(os.path.join(OUT, "comuni_provincia_milano.json"), "w"), separators=(",", ":"))
print(len(cf), os.path.getsize(os.path.join(OUT, "comuni_provincia_milano.json")))
