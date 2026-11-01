"""Suolo consumato per NIL a 2006, 2012, 2015, 2018 (carte v6) e 2024, 2025 (carte v8), e confronto del totale di Milano con le cifre ISPRA.
Uso: python -I -X utf8 raster_nil_serie.py <suolo assoluto> <nil geojson assoluto>
Scrive pulito/nil_suolo_serie.csv, pulito/controllo_raster_vs_ispra_milano.csv
"""
import sys, os, json
import numpy as np, pandas as pd, pyproj, shapely, rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from shapely.geometry import shape
from shapely.ops import unary_union
base, nilp = sys.argv[1], sys.argv[2]
R = os.path.join(base, "raw", "raster"); P = os.path.join(base, "pulito")
d = json.load(open(nilp, encoding="utf8"))
tr = pyproj.Transformer.from_crs(4326, 7794, always_xy=True)
proj = lambda g: shapely.transform(g, lambda a: np.column_stack(tr.transform(a[:, 0], a[:, 1])))
nils = [(f["properties"]["ID_NIL"], f["properties"]["NIL"], proj(shape(f["geometry"]))) for f in d["features"]]
b = unary_union([g for _, _, g in nils]).bounds
MAPS = {2006: "SC_2006_RDN_v6.tif", 2012: "SC_2012_RDN_v6.tif", 2015: "SC_2015_RDN_v6.tif", 2018: "SC_2018_RDN_v6.tif", 2024: "SC_2024_RDN_v8.tif", 2025: "SC_2025_RDN_v8.tif"}
cons = lambda a: (a == 1) | (a == 11) | (a == 12) | ((a >= 111) & (a <= 126))
C, org = {}, {}
for y, fn in MAPS.items():
    with rasterio.open(os.path.join(R, fn)) as r:
        w = from_bounds(*b, transform=r.transform).round_offsets().round_lengths()
        a = r.read(1, window=w); t = r.window_transform(w)
    org[y] = (t.c, t.f); C[y] = cons(a); trf = t; shp = a.shape
assert len(set(org.values())) == 1, org
nid = rasterize([(g, int(i)) for i, _, g in nils], out_shape=shp, transform=trf, fill=0, dtype="int32")
rows = []
for i, n, _ in nils:
    m = nid == i
    row = {"id_nil": i, "nil": n, "area_ha": m.sum() / 100}
    for y in MAPS: row[f"consumato_{y}_ha"] = (C[y] & m).sum() / 100
    rows.append(row)
df = pd.DataFrame(rows)
for y0, y1 in [(2006, 2012), (2012, 2015), (2015, 2018), (2018, 2024), (2024, 2025), (2012, 2025)]:
    df[f"delta_{y0}_{y1}_ha"] = df[f"consumato_{y1}_ha"] - df[f"consumato_{y0}_ha"]
df.round(2).to_csv(os.path.join(P, "nil_suolo_serie.csv"), sep=";", index=False)
ispra = {2006: 10364.99, 2012: 10478.46, 2015: 10540.36, 2018: 10588.15, 2024: 10650.91, 2025: 10678.98}
ck = pd.DataFrame([{"anno": y, "carta": MAPS[y], "raster_ha": df[f"consumato_{y}_ha"].sum(), "ispra_ha": ispra[y]} for y in MAPS])
ck["diff_ha"] = ck.raster_ha - ck.ispra_ha; ck["diff_%"] = 100 * ck.diff_ha / ck.ispra_ha
ck.round(2).to_csv(os.path.join(P, "controllo_raster_vs_ispra_milano.csv"), sep=";", index=False)
print(ck.round(2).to_string())
pd.set_option("display.width", 250)
print(df.sort_values("delta_2012_2025_ha", ascending=False).head(12)[["nil", "delta_2006_2012_ha", "delta_2012_2015_ha", "delta_2015_2018_ha", "delta_2018_2024_ha", "delta_2024_2025_ha", "delta_2012_2025_ha"]].round(1).to_string())
