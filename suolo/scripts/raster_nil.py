"""Ritaglia le carte nazionali del consumo di suolo (ISPRA, 10 m, EPSG:7794) su Milano e calcola, per NIL:
suolo consumato 2006/2012/2025, nuovo consumo 2006-12 e 2012-25 (da differenza fra carte), ripristini, da che classe
(terreno libero o cantiere/terra battuta), + patch (macchie) di nuovo consumo 2012-2025, anelli dal Duomo, cambiamento 2024-25.
Uso: python -I -X utf8 raster_nil.py <suolo assoluto> <nil geojson assoluto>
Classi (legenda ISPRA 2025): consumato = 1, 11, 12 e 111..126; non consumato = 2 e 201..206; 255 = nessun dato.
Cambiamento 2024-25: codice = classe_prima*1000 + classe_dopo.
"""
import sys, os, json, csv
import numpy as np, pyproj, shapely, rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from shapely.geometry import shape
from shapely.ops import unary_union
from scipy import ndimage

base, nilp = sys.argv[1], sys.argv[2]
R = os.path.join(base, "raw", "raster")
OUT = os.path.join(base, "pulito")

d = json.load(open(nilp, encoding="utf8"))
tr = pyproj.Transformer.from_crs(4326, 7794, always_xy=True)
inv = pyproj.Transformer.from_crs(7794, 4326, always_xy=True)
proj = lambda g: shapely.transform(g, lambda a: np.column_stack(tr.transform(a[:, 0], a[:, 1])))
nils = [(f["properties"]["ID_NIL"], f["properties"]["NIL"], proj(shape(f["geometry"]))) for f in d["features"]]
uni = unary_union([g for _, _, g in nils])
bounds = uni.bounds

MAPS = {2006: "SC_2006_RDN_v6.tif", 2012: "SC_2012_RDN_v6.tif", 2025: "SC_2025_RDN_v8.tif"}
arr, trf = {}, None
for y, fn in MAPS.items():
    with rasterio.open(os.path.join(R, fn)) as r:
        w = from_bounds(*bounds, transform=r.transform).round_offsets().round_lengths()
        arr[y] = r.read(1, window=w)
        t = r.window_transform(w)
        origins = globals().setdefault("origins", {})
        origins[y] = (t.c, t.f)
        if y == 2025:
            trf = t
        print(y, arr[y].shape, "origine", t.c, t.f, flush=True)
with rasterio.open(os.path.join(R, "consumo_suolo_2024-2025.tif")) as r:
    w = from_bounds(*bounds, transform=r.transform).round_offsets().round_lengths()
    chg = r.read(1, window=w)
    t_chg = r.window_transform(w)
    print("cambiamenti", chg.shape, t_chg.c, t_chg.f)

# allineamento: le carte 2006/2012 partono da (6577720, 5209650), la 2025 da (6577700, 5209670): scarto di 2 pixel (20 m)
# lo correggiamo leggendo con le coordinate: ricalcoliamo la finestra per ciascuna carta sullo stesso rettangolo
shape0 = arr[2025].shape
for y in (2006, 2012):
    if arr[y].shape != shape0:
        raise SystemExit("forme diverse: serve riallineare " + str(y))
    # la finestra e' calcolata su coordinate: le origini devono coincidere
assert origins[2006] == origins[2012] == origins[2025], origins  # stessa finestra geografica
assert (t_chg.c, t_chg.f) == origins[2025]
print("origini finestre ok (stesse coordinate)")


def cons(a):
    return (a == 1) | (a == 11) | (a == 12) | ((a >= 111) & (a <= 126))


nilid = rasterize([(g, int(i)) for i, _, g in nils], out_shape=shape0, transform=trf, fill=0, dtype="int32")
inside = nilid > 0
print("pixel dentro NIL:", inside.sum(), "= ha", inside.sum() / 100)
c06, c12, c25 = cons(arr[2006]), cons(arr[2012]), cons(arr[2025])
nodata25 = arr[2025] == 255
new1 = (~c06) & c12 & inside
rest1 = c06 & (~c12) & inside
new2 = (~c12) & c25 & inside
rest2 = c12 & (~c25) & inside
# da cantiere/terra battuta (122) o altro consumato? new2 e' per definizione da non consumato: distinguiamo la classe 2 (campo/verde) dalle 2xx
old12 = arr[2012]
free = (old12 == 2)  # suolo libero
other2xx = (old12 >= 201) & (old12 <= 206)
print("nuovo 2012-25 ha:", new2.sum() / 100, "ripristini:", rest2.sum() / 100, "netto:", (new2.sum() - rest2.sum()) / 100)
print("nuovo 2006-12 ha:", new1.sum() / 100, "ripristini:", rest1.sum() / 100)

# per NIL
ids = [i for i, _, _ in nils]
names = {i: n for i, n, _ in nils}
chg_old, chg_new = chg // 1000, chg % 1000
chg_old = np.where(chg > 1000, chg // 1000, 0)
chg_new_cls = np.where(chg > 1000, chg % 1000, 0)
# codici a 4 cifre (2111 = 2->111): chg//1000 = 2, chg%1000 = 111. A 6 cifre: 122002 -> 122,2. OK.
c_old, c_new = cons(chg_old), cons(chg_new_cls)
n24 = (chg > 0) & (~c_old) & c_new & inside
r24 = (chg > 0) & c_old & (~c_new) & inside

rows = []
for i in ids:
    m = nilid == i
    ar = m.sum()
    rows.append({
        "id_nil": i, "nil": names[i], "area_ha": ar / 100,
        "consumato_2006_ha": (c06 & m).sum() / 100, "consumato_2012_ha": (c12 & m).sum() / 100, "consumato_2025_ha": (c25 & m).sum() / 100,
        "pct_2006": 100 * (c06 & m).sum() / ar, "pct_2012": 100 * (c12 & m).sum() / ar, "pct_2025": 100 * (c25 & m).sum() / ar,
        "nuovo_2006_2012_ha": (new1 & m).sum() / 100, "ripristino_2006_2012_ha": (rest1 & m).sum() / 100,
        "nuovo_2012_2025_ha": (new2 & m).sum() / 100, "ripristino_2012_2025_ha": (rest2 & m).sum() / 100,
        "netto_2012_2025_ha": ((new2 & m).sum() - (rest2 & m).sum()) / 100,
        "nuovo_da_suolo_libero_2012_2025_ha": (new2 & free & m).sum() / 100,
        "nuovo_da_altre_aree_naturali_2012_2025_ha": (new2 & other2xx & m).sum() / 100,
        "nuovo_2024_2025_ha_da_carta_cambiamenti": (n24 & m).sum() / 100, "ripristino_2024_2025_ha": (r24 & m).sum() / 100,
        "pixel_senza_dato_2025": int((nodata25 & m).sum()),
    })
import pandas as pd
df = pd.DataFrame(rows).sort_values("nuovo_2012_2025_ha", ascending=False)
df["quota_nuovo_su_totale_%"] = 100 * df.nuovo_2012_2025_ha / df.nuovo_2012_2025_ha.sum()
df["nuovo_ha_per_100ha_nil"] = 100 * df.nuovo_2012_2025_ha / df.area_ha
df.round(3).to_csv(os.path.join(OUT, "nil_suolo.csv"), sep=";", index=False)
tot = df.sum(numeric_only=True)
print("TOT consumato 2006/2012/2025 ha:", tot.consumato_2006_ha, tot.consumato_2012_ha, tot.consumato_2025_ha)

# composizione 2025 per NIL (classi)
cls = [1, 111, 112, 113, 114, 115, 116, 117, 118, 121, 122, 123, 124, 125, 126, 12, 11, 2, 201, 202, 203, 204, 205, 206, 255]
rows = []
for i in ids:
    m = (nilid == i)
    v, c = np.unique(arr[2025][m], return_counts=True)
    dd = dict(zip(v.tolist(), c.tolist()))
    rows.append({"id_nil": i, "nil": names[i], **{f"cl{k}_ha": dd.get(k, 0) / 100 for k in cls}})
pd.DataFrame(rows).round(2).to_csv(os.path.join(OUT, "nil_suolo_classi_2025.csv"), sep=";", index=False)

# transizioni 2012 -> 2025 (classi) dentro Milano
v12 = arr[2012][inside & (new2 | rest2 | (c12 != c25))]
tab = pd.crosstab(arr[2012][inside], arr[2025][inside])
tab = (tab / 100).round(2)
tab.stack().rename("ha").reset_index().rename(columns={"row_0": "classe_2012", "col_0": "classe_2025"}).query("ha>0").to_csv(
    os.path.join(OUT, "transizioni_classi_2012_2025.csv"), sep=";", index=False)

# anelli dal Duomo (45.4642, 9.1900)
dx, dy = tr.transform(9.1900, 45.4642)
H, W = shape0
cols = np.arange(W); rws = np.arange(H)
X = trf.c + (cols + 0.5) * trf.a
Y = trf.f + (rws + 0.5) * trf.e
dist = np.hypot(X[None, :] - dx, Y[:, None] - dy) / 1000
ring = np.minimum((dist).astype(int), 12)
rows = []
for k in range(13):
    m = inside & (ring == k)
    ar = m.sum()
    if ar == 0:
        continue
    rows.append({"anello_km_dal_duomo": f"{k}-{k+1}" if k < 12 else "12+", "area_ha": ar / 100,
                 "consumato_2012_ha": (c12 & m).sum() / 100, "consumato_2025_ha": (c25 & m).sum() / 100,
                 "pct_2012": 100 * (c12 & m).sum() / ar, "pct_2025": 100 * (c25 & m).sum() / ar,
                 "nuovo_2012_2025_ha": (new2 & m).sum() / 100, "ripristino_2012_2025_ha": (rest2 & m).sum() / 100})
pd.DataFrame(rows).round(2).to_csv(os.path.join(OUT, "anelli_duomo.csv"), sep=";", index=False)

# patch di nuovo consumo 2012-2025 (>= 0,5 ha)
lab, nlab = ndimage.label(new2, structure=np.ones((3, 3)))
sizes = ndimage.sum(new2, lab, index=np.arange(1, nlab + 1))
keep = [k + 1 for k, s in enumerate(sizes) if s >= 50]
REF = {  # punti di riferimento INDICATIVI (lon, lat), da conoscenza generale, non verificati: precisione circa 500 m
    "Santa Giulia / Rogoredo": (9.2380, 45.4330), "Scalo Farini": (9.1760, 45.4905), "Scalo Romana / Symbiosis": (9.2090, 45.4420),
    "Scalo Porta Genova": (9.1670, 45.4520), "Portello": (9.1530, 45.4950), "CityLife (ex Fiera)": (9.1560, 45.4785),
    "Bovisa gasometri": (9.1600, 45.5035), "Cascina Merlata": (9.1230, 45.5130), "MIND (ex Expo)": (9.1040, 45.5185),
    "Lambrate scalo": (9.2370, 45.4850), "Bicocca": (9.2110, 45.5190), "Linate aeroporto": (9.2767, 45.4450),
}
refxy = {k: tr.transform(*v) for k, v in REF.items()}
cents = ndimage.center_of_mass(new2, lab, keep)
rows = []
for k, (cy, cx) in zip(keep, cents):
    m = lab == k
    X0 = trf.c + (cx + 0.5) * trf.a
    Y0 = trf.f + (cy + 0.5) * trf.e
    lon, lat = inv.transform(X0, Y0)
    nl = np.bincount(nilid[m]).argmax()
    ov, oc = np.unique(arr[2012][m], return_counts=True)
    nv, nc = np.unique(arr[2025][m], return_counts=True)
    near = min(((np.hypot(X0 - x, Y0 - y), n) for n, (x, y) in refxy.items()))
    rows.append({"patch": k, "area_ha": m.sum() / 100, "lon": round(lon, 5), "lat": round(lat, 5), "nil": names.get(int(nl), ""),
                 "km_dal_duomo": round(float(np.hypot(X0 - dx, Y0 - dy)) / 1000, 2),
                 "prima_2012": " / ".join(f"{int(a)}:{b/100:.1f}" for a, b in sorted(zip(ov, oc), key=lambda t: -t[1])[:3]),
                 "dopo_2025": " / ".join(f"{int(a)}:{b/100:.1f}" for a, b in sorted(zip(nv, nc), key=lambda t: -t[1])[:3]),
                 "riferimento_vicino_indicativo": near[1] if near[0] < 700 else "", "dist_riferimento_m": int(near[0]) if near[0] < 700 else ""})
pat = pd.DataFrame(rows).sort_values("area_ha", ascending=False)
pat.round({"area_ha": 2, "km_dal_duomo": 2}).to_csv(os.path.join(OUT, "patch_nuovo_consumo_2012_2025.csv"), sep=";", index=False)
print("patch >=0,5 ha:", len(pat), "area:", pat.area_ha.sum(), "su totale", new2.sum() / 100)
print(pat.head(15).to_string())
