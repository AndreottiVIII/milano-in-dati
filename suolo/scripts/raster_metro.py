"""Nuovo consumo di suolo 2012-2025 nella Citta' metropolitana di Milano da carte ISPRA 10 m (differenza 2012 v6 - 2025 v8)
per comune (confini = sezioni di censimento ISTAT 2021 unite per comune, filone censimenti) e macchie grandi (>= 2 ha).
Uso: python -I -X utf8 raster_metro.py <suolo assoluto> <R03_21_WGS84.shp assoluto>
Scrive pulito/metro_raster_comuni.csv, pulito/metro_patch_grandi_2012_2025.csv
"""
import sys, os
import numpy as np, pandas as pd, pyproj, shapely, rasterio, pyogrio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from shapely.ops import unary_union
from scipy import ndimage

base, shp = sys.argv[1], sys.argv[2]
P = os.path.join(base, "pulito"); R = os.path.join(base, "raw", "raster")
metro = pd.read_csv(os.path.join(P, "metro_comuni.csv"), sep=";")
codes = set(metro.pro_com.astype(int))
res = pyogrio.raw.read(shp, columns=["PRO_COM"], where="PRO_COM >= 15000 AND PRO_COM < 16000")
geoms = shapely.from_wkb(res[2]); pc = res[3][0]
print("sezioni:", len(geoms))
t32 = pyproj.Transformer.from_crs(32632, 7794, always_xy=True)
inv = pyproj.Transformer.from_crs(7794, 4326, always_xy=True)
byc = {}
for g, c in zip(geoms, pc):
    byc.setdefault(int(c), []).append(g)
com = {c: shapely.transform(unary_union(v), lambda a: np.column_stack(t32.transform(a[:, 0], a[:, 1]))) for c, v in byc.items() if c in codes}
print("comuni trovati:", len(com), "di", len(codes), "mancanti:", sorted(codes - set(com)))
uni = unary_union(list(com.values()))
b = uni.bounds
arr = {}
for y, fn in {2012: "SC_2012_RDN_v6.tif", 2025: "SC_2025_RDN_v8.tif"}.items():
    with rasterio.open(os.path.join(R, fn)) as r:
        w = from_bounds(*b, transform=r.transform).round_offsets().round_lengths()
        arr[y] = r.read(1, window=w); t = r.window_transform(w)
        if y == 2025: trf = t
        else: t12 = t
assert (t12.c, t12.f) == (trf.c, trf.f)
print("finestra", arr[2025].shape)
def cons(a): return (a == 1) | (a == 11) | (a == 12) | ((a >= 111) & (a <= 126))
cid = rasterize([(g, c) for c, g in com.items()], out_shape=arr[2025].shape, transform=trf, fill=0, dtype="int32")
c12, c25 = cons(arr[2012]), cons(arr[2025])
new = (~c12) & c25 & (cid > 0); rest = c12 & (~c25) & (cid > 0)
lab, n = ndimage.label(new, structure=np.ones((3, 3)))
sizes = np.bincount(lab.ravel(), minlength=n + 1)
big3 = np.isin(lab, np.where(sizes >= 300)[0][1:] if n else [])
rows = []
for c in sorted(com):
    m = cid == c
    rows.append({"pro_com": c, "area_raster_ha": m.sum() / 100, "consumato_2012_ha": (c12 & m).sum() / 100, "consumato_2025_ha": (c25 & m).sum() / 100,
                 "nuovo_2012_2025_ha": (new & m).sum() / 100, "ripristino_2012_2025_ha": (rest & m).sum() / 100,
                 "nuovo_in_macchie_ge3ha": (new & big3 & m).sum() / 100})
df = pd.DataFrame(rows).merge(metro[["pro_com", "comune", "superficie_ha", "consumato_2012_ha", "consumato_2025_ha", "netto_2012_2025_ha_pubblicato", "lordo_2012_2025_ha_pubblicato"]],
                              on="pro_com", suffixes=("_raster", "_ispra"))
df["netto_raster"] = df.nuovo_2012_2025_ha - df.ripristino_2012_2025_ha
df["quota_nuovo_in_macchie_ge3ha_%"] = 100 * df.nuovo_in_macchie_ge3ha / df.nuovo_2012_2025_ha.where(df.nuovo_2012_2025_ha > 0)
df.sort_values("nuovo_2012_2025_ha", ascending=False).round(2).to_csv(os.path.join(P, "metro_raster_comuni.csv"), sep=";", index=False)
print("controllo raster vs ISPRA: lordo 2012-25 metro raster", df.nuovo_2012_2025_ha.sum(), "ISPRA", df.lordo_2012_2025_ha_pubblicato.sum())
# macchie grandi >= 2 ha
keep = np.where(sizes >= 200)[0]; keep = keep[keep > 0]
cents = ndimage.center_of_mass(new, lab, keep)
rows = []
for k, (cy, cx) in zip(keep, cents):
    m = lab == k
    X0 = trf.c + (cx + .5) * trf.a; Y0 = trf.f + (cy + .5) * trf.e
    lon, lat = inv.transform(X0, Y0)
    ccode = np.bincount(cid[m]).argmax()
    nv, nc = np.unique(arr[2025][m], return_counts=True)
    ov, oc = np.unique(arr[2012][m], return_counts=True)
    rows.append({"area_ha": m.sum() / 100, "lon": round(lon, 5), "lat": round(lat, 5), "pro_com": int(ccode),
                 "classi_2025": " / ".join(f"{int(a)}:{x/100:.1f}" for a, x in sorted(zip(nv, nc), key=lambda t: -t[1])[:4])})
pat = pd.DataFrame(rows).merge(metro[["pro_com", "comune"]], on="pro_com", how="left").sort_values("area_ha", ascending=False)
pat.round({"area_ha": 2, "km_dal_duomo": 2}).to_csv(os.path.join(P, "metro_patch_grandi_2012_2025.csv"), sep=";", index=False)
print("macchie >=2 ha:", len(pat), "area", pat.area_ha.sum(), "su totale nuovo", new.sum() / 100)
pd.set_option("display.width", 250)
print(df.sort_values("nuovo_2012_2025_ha", ascending=False).head(25)[["comune", "nuovo_2012_2025_ha", "ripristino_2012_2025_ha", "lordo_2012_2025_ha_pubblicato", "netto_raster", "netto_2012_2025_ha_pubblicato", "quota_nuovo_in_macchie_ge3ha_%"]].round(1).to_string())
print(pat.head(25).to_string())

# composizione del nuovo consumo 2012-2025 per classe 2025 (Milano / resto della Citta' metropolitana)
NOMI = {1: "consumo generico (cl. 1)", 11: "permanente", 12: "reversibile", 111: "edifici", 112: "strade pavimentate", 113: "ferrovia", 114: "aeroporti", 115: "porti",
        116: "altre aree pavimentate (piazzali, parcheggi)", 117: "serre pavimentate", 118: "discariche", 121: "strade non pavimentate",
        122: "cantieri e terra battuta", 123: "aree estrattive", 124: "cave in falda", 125: "fotovoltaico a terra", 126: "altre coperture artificiali"}
mil = cid == 15146
rows = []
for lab_, m in [("Milano", new & mil), ("Resto Citta' metropolitana", new & ~mil & (cid > 0))]:
    v, c = np.unique(arr[2025][m], return_counts=True)
    tot = c.sum()
    for a, x in zip(v, c):
        rows.append({"ambito": lab_, "classe_2025": int(a), "descrizione": NOMI.get(int(a), "non consumato / altro"), "ha": x / 100, "quota_%": 100 * x / tot})
pd.DataFrame(rows).sort_values(["ambito", "ha"], ascending=[True, False]).round(2).to_csv(os.path.join(P, "metro_nuovo_per_classe.csv"), sep=";", index=False)
q = []
for c in sorted(com):
    m = new & (cid == c)
    a = arr[2025][m]
    q.append({"pro_com": c, "nuovo_ha": m.sum() / 100, "cave_ha": ((a == 123) | (a == 124)).sum() / 100, "cantieri_122_ha": (a == 122).sum() / 100,
              "edifici_111_ha": (a == 111).sum() / 100, "pavimentate_116_ha": (a == 116).sum() / 100, "strade_112_ha": (a == 112).sum() / 100})
qd = pd.DataFrame(q).merge(metro[["pro_com", "comune"]], on="pro_com")
qd.sort_values("nuovo_ha", ascending=False).round(2).to_csv(os.path.join(P, "metro_nuovo_per_comune_e_classe.csv"), sep=";", index=False)
print(pd.read_csv(os.path.join(P, "metro_nuovo_per_classe.csv"), sep=";").to_string())
print("cave in tutto il nuovo (resto metro):", qd[qd.pro_com != 15146].cave_ha.sum(), "su", qd[qd.pro_com != 15146].nuovo_ha.sum())
