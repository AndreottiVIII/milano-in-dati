"""Logistica ISPRA (punti = centroidi delle aree di cambiamento 2006-2023, classi: 1 GDO/commerciale, 2 produttivo/industriale, 3 e-commerce)
assegnata ai comuni della Citta' metropolitana di Milano (confini: sezioni di censimento ISTAT 2021 unite per comune).
Uso: python -I -X utf8 logistica.py <suolo assoluto> <R03_21_WGS84.shp assoluto>
Scrive pulito/logistica_metro_comuni.csv (area ha per comune x classe), pulito/logistica_metro_punti.csv, pulito/logistica_metro_periodi.csv
"""
import sys, os
import numpy as np, pandas as pd, pyproj, shapely, pyogrio
from shapely.ops import unary_union
base, shp = sys.argv[1], sys.argv[2]
P = os.path.join(base, "pulito"); L = os.path.join(base, "raw", "logistica")
metro = pd.read_csv(os.path.join(P, "metro_comuni.csv"), sep=";")
codes = set(metro.pro_com.astype(int))
res = pyogrio.raw.read(shp, columns=["PRO_COM"], where="PRO_COM >= 15000 AND PRO_COM < 16000")
geoms = shapely.from_wkb(res[2]); pc = res[3][0]
byc = {}
for g, c in zip(geoms, pc): byc.setdefault(int(c), []).append(g)
com = {c: unary_union(v) for c, v in byc.items() if c in codes}   # EPSG:32632
t = pyproj.Transformer.from_crs(3035, 32632, always_xy=True)
inv = pyproj.Transformer.from_crs(32632, 4326, always_xy=True)
frames = []
for n in ["Logistica_06_22", "Logistica_22_23"]:
    r = pyogrio.raw.read(os.path.join(L, f"x_{n}", f"{n}.shp"))
    flds = list(pyogrio.read_info(os.path.join(L, f"x_{n}", f"{n}.shp"))["fields"])
    df = pd.DataFrame({f: r[3][i] for i, f in enumerate(flds)})
    pts = shapely.from_wkb(r[2])
    xy = np.array([[p.x, p.y] for p in pts])
    x, y = t.transform(xy[:, 0], xy[:, 1])
    df["x"], df["y"] = x, y
    df["file"] = n
    frames.append(df)
d = pd.concat(frames, ignore_index=True)
# assegnazione al comune con indice spaziale
tree = shapely.STRtree(list(com.values())); keys = list(com.keys())
pts = shapely.points(d.x.values, d.y.values)
idx_p, idx_c = tree.query(pts, predicate="within")
d["pro_com"] = np.nan
d.loc[idx_p, "pro_com"] = [keys[i] for i in idx_c]
m = d[d.pro_com.notna()].copy()
m["pro_com"] = m.pro_com.astype(int)
lon, lat = inv.transform(m.x.values, m.y.values)
m["lon"], m["lat"] = lon.round(5), lat.round(5)
m = m.merge(metro[["pro_com", "comune"]], on="pro_com")
PER = {1: "2006-2012", 2: "2012-2015", 3: "2015-2016", 4: "2016-2017", 5: "2017-2018", 6: "2018-2019", 7: "2019-2020", 8: "2020-2021", 9: "2021-2022", 10: "2022-2023"}
CL = {1: "grande distribuzione/commerciale", 2: "produttivo/industriale", 3: "e-commerce"}
m["periodo"] = m.Anno_Log.map(PER); m["classe"] = m.Classe_Log.map(CL)
m[["file", "Id", "comune", "pro_com", "lon", "lat", "area_ha", "classe", "periodo", "gridcode"]].to_csv(os.path.join(P, "logistica_metro_punti.csv"), sep=";", index=False)
tab = m.pivot_table(index="comune", columns="classe", values="area_ha", aggfunc="sum", fill_value=0)
tab["totale_ha"] = tab.sum(axis=1)
tab["n_aree"] = m.groupby("comune").size()
tab["ha_dal_2012"] = m[m.Anno_Log >= 2].groupby("comune").area_ha.sum()
tab["ha_dal_2018"] = m[m.Anno_Log >= 6].groupby("comune").area_ha.sum()
tab = tab.fillna(0).sort_values("totale_ha", ascending=False).round(2)
tab.to_csv(os.path.join(P, "logistica_metro_comuni.csv"), sep=";")
per = m.pivot_table(index="periodo", columns="classe", values="area_ha", aggfunc="sum", fill_value=0).round(2)
per = per.reindex([v for v in PER.values() if v in per.index])
per.to_csv(os.path.join(P, "logistica_metro_periodi.csv"), sep=";")
print("punti totali Italia:", len(d), "in Citta' metropolitana:", len(m), "area ha:", m.area_ha.sum().round(1), "Italia ha:", d.area_ha.sum().round(1))
print(per.to_string()); print(tab.head(20).to_string())
print("Milano comune:", m[m.pro_com == 15146].groupby("classe").area_ha.sum().round(1).to_dict(), "dal 2012:", m[(m.pro_com == 15146) & (m.Anno_Log >= 2)].area_ha.sum().round(1))
