"""Fase 2, passo 1: raccordo sezioni -> NIL 2021 e municipi 2021 per sovrapposizione geometrica.
Uso: python -I h1_raccordo.py <cartella censimenti>
Metodo: i NIL 2021 (88) e i municipi (9) sono ottenuti sciogliendo le sezioni 2021 per COM_ASC2 / COM_ASC1
(geojson in pulito/geometrie). Ogni sezione 1991/2001/2011 va al NIL con cui ha la sovrapposizione di area maggiore.
Si salvano purezza (area nel NIL scelto / area sezione) e copertura (area in un qualsiasi NIL / area sezione),
e le quote di area in ogni NIL (per l'alternativa 'ripartizione per area').
Output: pulito/raccordo_sezioni_<anno>.csv, pulito/raccordo_quote_area_<anno>.csv, pulito/nil_2021_anagrafica.csv
"""
import sys, json, os
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

root = sys.argv[1]
G = root + "/pulito/geometrie/"
P = root + "/pulito/"

def load(y):
    return json.load(open(G + f"sezioni_{y}_Milano.geojson"))["features"]

# --- NIL e municipi 2021 -------------------------------------------------
f21 = load(2021)
nil_geoms, mun_geoms = {}, {}
for f in f21:
    p = f["properties"]
    g = shape(f["geometry"]).buffer(0)
    a2, a1 = int(p["COM_ASC2"]), int(p["COM_ASC1"])
    nil_geoms.setdefault(a2, []).append(g)
    mun_geoms.setdefault(a1, []).append(g)
nil_poly = {k: unary_union(v) for k, v in nil_geoms.items() if k != 0}
mun_poly = {k: unary_union(v) for k, v in mun_geoms.items() if k != 0}
print("NIL 2021:", len(nil_poly), "municipi:", len(mun_poly), "sezioni 2021 senza NIL:", len(nil_geoms.get(0, [])))
nilnames = pd.read_csv(P + "aree_subcomunali_2021_NIL.csv")
nilnames["nil"] = nilnames["COD_ASC2"].astype(int)
nilname = dict(zip(nilnames.nil, nilnames.DEN_ASC2))
ana = pd.DataFrame({"nil": sorted(k % 1000 for k in nil_poly)})
ana["nil_nome"] = ana.nil.map(nilname)
ana["municipio_prevalente"] = [
    max(mun_poly, key=lambda m: nil_poly[15146000 + n].intersection(mun_poly[m]).area) % 1000 for n in ana.nil]
ana["area_km2"] = [round(nil_poly[15146000 + n].area / 1e6, 3) for n in ana.nil]
ana.to_csv(P + "nil_2021_anagrafica.csv", index=False)

nil_keys = list(nil_poly.keys())
nil_list = [nil_poly[k] for k in nil_keys]
tree = STRtree(nil_list)
mun_keys = list(mun_poly.keys()); mun_list = [mun_poly[k] for k in mun_keys]
mtree = STRtree(mun_list)

def overlay(geom, keys, lst, tr):
    res = {}
    for i in tr.query(geom):
        a = geom.intersection(lst[i]).area
        if a > 0:
            res[keys[i]] = res.get(keys[i], 0) + a
    return res

for y, keyf in [(1991, "SEZ"), (2001, "SEZ"), (2011, "SEZ")]:
    feats = load(y)
    by = {}
    for f in feats:
        k = int(float(f["properties"][keyf]))
        by.setdefault(k, []).append(shape(f["geometry"]).buffer(0))
    rows, quote = [], []
    for k, gl in sorted(by.items()):
        g = unary_union(gl)
        A = g.area
        ov = overlay(g, nil_keys, nil_list, tree)
        om = overlay(g, mun_keys, mun_list, mtree)
        if ov:
            best = max(ov, key=ov.get)
            pur = ov[best] / A; cov = sum(ov.values()) / A
            bestm = max(om, key=om.get); purm = om[bestm] / A
            nil = best % 1000; mun = bestm % 1000
        else:
            nil = mun = None; pur = cov = purm = 0
        rows.append(dict(anno=y, sezione=k, n_pezzi=len(gl), area_m2=round(A), nil=nil, municipio=mun,
                         purezza_nil=round(pur, 4), copertura=round(cov, 4), purezza_mun=round(purm, 4),
                         n_nil_toccati=sum(1 for v in ov.values() if v / A > 0.02)))
        for n, a in ov.items():
            quote.append((y, k, n % 1000, round(a / A, 5)))
    pd.DataFrame(rows).to_csv(P + f"raccordo_sezioni_{y}.csv", index=False)
    pd.DataFrame(quote, columns=["anno", "sezione", "nil", "quota_area"]).to_csv(P + f"raccordo_quote_area_{y}.csv", index=False)
    print(y, "sezioni (geometria unita):", len(rows), "senza NIL:", sum(1 for r in rows if r["nil"] is None))
