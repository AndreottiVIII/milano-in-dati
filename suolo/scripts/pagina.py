"""Scrive i file dati della pagina "Quanto suolo si consuma" (docs/suolo/data/).
Uso: python -I -X utf8 pagina.py <suolo_dir> <docs_dir> <nil_geojson>
  <suolo_dir>   .../milano-in-dati/suolo   (servono pulito/ gia' prodotto dagli altri script e raw/raster/*.tif)
  <docs_dir>    .../milano-in-dati/docs
  <nil_geojson> .../citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson
Scrive in <docs_dir>/suolo/data/: riepilogo.json, nil.geojson, png/*.png (strati di nuovo consumo, nessun raster ISPRA ripubblicato),
  e copie dei CSV aggregati. Rilanciabile: sovrascrive.
"""
import sys, os, json, shutil
import numpy as np, pandas as pd, pyproj, shapely, rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from PIL import Image

base, docs, nilp = sys.argv[1], sys.argv[2], sys.argv[3]
P = os.path.join(base, "pulito"); R = os.path.join(base, "raw", "raster")
OUT = os.path.join(docs, "suolo", "data"); os.makedirs(os.path.join(OUT, "png"), exist_ok=True)
rd = lambda f: pd.read_csv(os.path.join(P, f), sep=";")
def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating, float)): return None if (o != o) else round(float(o), 3)
    return o

# ---------------- raster: periodi per NIL e strati PNG ----------------
nf = json.load(open(nilp, encoding="utf8"))
t4326_7794 = pyproj.Transformer.from_crs(4326, 7794, always_xy=True)
proj = lambda g: shapely.transform(g, lambda a: np.column_stack(t4326_7794.transform(a[:, 0], a[:, 1])))
nils = [(int(f["properties"]["ID_NIL"]), f["properties"]["NIL"], proj(shape(f["geometry"])), shape(f["geometry"])) for f in nf["features"]]
bnd = unary_union([g for _, _, g, _ in nils]).bounds
MAPS = {2006: "SC_2006_RDN_v6.tif", 2012: "SC_2012_RDN_v6.tif", 2015: "SC_2015_RDN_v6.tif", 2018: "SC_2018_RDN_v6.tif", 2025: "SC_2025_RDN_v8.tif"}
cons = lambda a: (a == 1) | (a == 11) | (a == 12) | ((a >= 111) & (a <= 126))
C, org = {}, {}
for y, fn in MAPS.items():
    with rasterio.open(os.path.join(R, fn)) as r:
        w = from_bounds(*bnd, transform=r.transform).round_offsets().round_lengths()
        a = r.read(1, window=w); t = r.window_transform(w)
    C[y] = cons(a); org[y] = (t.c, t.f); trf = t; shp = a.shape
assert len(set(org.values())) == 1
nid = rasterize([(g, i) for i, _, g, _ in nils], out_shape=shp, transform=trf, fill=0, dtype="int32")
inside = nid > 0
PER = {"0612": (2006, 2012), "1215": (2012, 2015), "1518": (2015, 2018), "1825": (2018, 2025), "1225": (2012, 2025)}
NEW = {k: (~C[a]) & C[b] & inside for k, (a, b) in PER.items()}
REST = {k: C[a] & (~C[b]) & inside for k, (a, b) in PER.items()}
per_nil = {}
for i, n, _, _ in nils:
    m = nid == i
    per_nil[i] = {"area_ha": m.sum() / 100, **{f"n{k}": (NEW[k] & m).sum() / 100 for k in PER}, **{f"r{k}": (REST[k] & m).sum() / 100 for k in PER},
                  **{f"c{y}": (C[y] & m).sum() / 100 for y in MAPS}}

# nomi dei NIL con maiuscole/accenti leggibili (dalla pagina Alberi, solo lettura; se manca restano maiuscoli)
PRETTY = {}
try:
    for f in json.load(open(os.path.join(docs, "alberi", "data", "nil.geojson"), encoding="utf8"))["features"]:
        PRETTY[int(f["properties"]["i"])] = f["properties"]["n"]
except Exception:
    pass
UP2PR = {n: PRETTY.get(i, n) for i, n, _, _ in nils}
pr = lambda n: UP2PR.get(n, n)

# PNG in Web Mercator (6 m), niente raster ISPRA ripubblicato: solo maschere "nuovo" e "restituito" in colore
to3857 = pyproj.Transformer.from_crs(4326, 3857, always_xy=True)
t3857_7794 = pyproj.Transformer.from_crs(3857, 7794, always_xy=True)
allg = unary_union([g for _, _, _, g in nils]); b4 = allg.bounds
x0, y0 = to3857.transform(b4[0], b4[1]); x1, y1 = to3857.transform(b4[2], b4[3])
res = 6.0
W = int(np.ceil((x1 - x0) / res)); H = int(np.ceil((y1 - y0) / res))
xs = x0 + (np.arange(W) + .5) * res; ys = y1 - (np.arange(H) + .5) * res
X, Y = np.meshgrid(xs, ys)
ex, ey = t3857_7794.transform(X.ravel(), Y.ravel())
col = np.floor((np.array(ex) - trf.c) / trf.a).astype(int).reshape(H, W)
row = np.floor((np.array(ey) - trf.f) / trf.e).astype(int).reshape(H, W)
ok = (col >= 0) & (col < shp[1]) & (row >= 0) & (row < shp[0])
col = np.clip(col, 0, shp[1] - 1); row = np.clip(row, 0, shp[0] - 1)
inv3857 = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)
lon0, lat1 = inv3857.transform(x0, y1 - H * res + H * res)  # angolo alto-sinistra: (x0, y1)
lon_w, lat_n = inv3857.transform(x0, y1); lon_e, lat_s = inv3857.transform(x0 + W * res, y1 - H * res)
overlay = {"bounds": [[round(lat_s, 6), round(lon_w, 6)], [round(lat_n, 6), round(lon_e, 6)]]}
def png(mask, rgb, name):
    m = mask[row, col] & ok
    img = np.zeros((H, W, 4), np.uint8)
    img[m] = (*rgb, 255)
    Image.fromarray(img, "RGBA").save(os.path.join(OUT, "png", name), optimize=True)
    return os.path.getsize(os.path.join(OUT, "png", name))
sizes = {}
for k in PER:
    sizes["nuovo_" + k] = png(NEW[k], (143, 45, 10), f"nuovo_{k}.png")
sizes["restituito_1225"] = png(REST["1225"], (0, 105, 92), "restituito_1225.png")
overlay["byte"] = sizes
print("PNG", W, "x", H, sizes)

# ---------------- NIL geojson semplificato ----------------
sc = rd("nil_suolo.csv").set_index("id_nil"); ser = rd("nil_suolo_serie.csv").set_index("id_nil"); cls = rd("nil_suolo_classi_2025.csv").set_index("id_nil")
cost = rd("confronto_costruzioni_nil.csv").set_index("id_nil")
feats = []
for (i, n, _, g), f in zip(nils, nf["features"]):
    s = g.simplify(0.00006, preserve_topology=True)
    p = per_nil[i]
    prop = {"i": i, "n": PRETTY.get(i, n), "ha": round(p["area_ha"], 1),
            "p06": round(100 * p["c2006"] / p["area_ha"], 1), "p12": round(100 * p["c2012"] / p["area_ha"], 1), "p25": round(100 * p["c2025"] / p["area_ha"], 1)}
    for k in PER:
        prop["n" + k] = round(p["n" + k], 2); prop["r" + k] = round(p["r" + k], 2)
    prop["c122"] = round(float(cls.loc[i, "cl122_ha"]), 1)
    prop["abit_nuove"] = None if i not in cost.index or pd.isna(cost.loc[i, "nuove_abitazioni_2014_2024"]) else int(cost.loc[i, "nuove_abitazioni_2014_2024"])
    feats.append({"type": "Feature", "properties": prop, "geometry": json.loads(json.dumps(mapping(s), separators=(",", ":")))})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# ---------------- riepilogo ----------------
ser_m = rd("serie_milano.csv"); inc_m = rd("incrementi_milano_periodi.csv"); conf = rd("confronto_citta_2025.csv"); cs = rd("serie_citta.csv")
metro = rd("metro_comuni.csv"); mrc = rd("metro_raster_comuni.csv"); mcl = rd("metro_nuovo_per_comune_e_classe.csv"); log = pd.read_csv(os.path.join(P, "logistica_metro_comuni.csv"), sep=";")
logper = pd.read_csv(os.path.join(P, "logistica_metro_periodi.csv"), sep=";")
anelli = rd("anelli_duomo.csv"); trans = rd("transizioni_classi_2012_2025.csv"); mcls = rd("metro_nuovo_per_classe.csv"); grandi = rd("grandi_comuni_2025.csv")
riep_ind = json.load(open(os.path.join(P, "riepilogo_indicatori.json"), encoding="utf8")); ctrl = rd("controllo_raster_vs_ispra_milano.csv")
pot = pd.read_excel(os.path.join(base, "raw", "snpa", "potenziale_recupero_2026.xlsx"), sheet_name="Comuni")
pot = pot[pot.PRO_COM == 15146].iloc[0]
ed = rd("confronto_edizioni_2025_2026.csv")

mil = ser_m[["anno", "consumato_ha", "consumato_pct", "popolazione", "m2_per_ab"]]
r0 = mil[mil.anno == 2006].iloc[0]
mil_idx = [{"anno": int(r.anno), "suolo": round(100 * r.consumato_ha / r0.consumato_ha, 2), "pop": round(100 * r.popolazione / r0.popolazione, 2)} for r in mil.itertuples()]
cit = []
for r in conf.itertuples():
    g = cs[cs.pro_com == r.pro_com].set_index("anno")
    cit.append({"comune": r.comune, "pct": r.consumato_2025_pct, "ha": r.consumato_2025_ha, "m2ab06": r.m2_per_abitante_2006, "m2ab25": r.m2_per_abitante_2025,
                "suolo_06_25_pct": 100 * (g.loc[2025, "consumato_ha"] / g.loc[2006, "consumato_ha"] - 1), "suolo_12_25_pct": 100 * (g.loc[2025, "consumato_ha"] / g.loc[2012, "consumato_ha"] - 1),
                "pop_06_25_pct": 100 * (g.loc[2025, "popolazione"] / g.loc[2006, "popolazione"] - 1), "netto_12_25": r.netto_2012_2025_ha_pubblicato, "netto_24_25": r.netto_2024_2025_ha})

sc_all = sc.reset_index()
tot_new = sc_all.nuovo_2012_2025_ha.sum(); tot_rest = sc_all.ripristino_2012_2025_ha.sum()
top8 = sc_all.sort_values("nuovo_2012_2025_ha", ascending=False).head(8)
cm = cost.reset_index()
t8c = cm[cm.id_nil.isin(top8.id_nil)]
quota_suolo = 100 * top8.nuovo_2012_2025_ha.sum() / tot_new
quota_abit = 100 * t8c.nuove_abitazioni_2014_2024.sum() / cm.nuove_abitazioni_2014_2024.sum()
quota_vol = 100 * t8c.dbt_volume_nuove_m3.sum() / cm.dbt_volume_nuove_m3.sum()
zone = ["SCALO ROMANA", "FARINI", "PORTELLO", "TRE TORRI", "PORTA GARIBALDI - PORTA NUOVA", "ROGOREDO - SANTA GIULIA", "CASCINA MERLATA", "ISOLA", "PORTA GENOVA"]
zone_t = [{"nil": pr(z), "nuovo": float(sc.loc[sc.nil == z, "nuovo_2012_2025_ha"].iloc[0]), "restituito": float(sc.loc[sc.nil == z, "ripristino_2012_2025_ha"].iloc[0]),
           "pct25": float(sc.loc[sc.nil == z, "pct_2025"].iloc[0])} for z in zone]
cm_row = serie_nil = rd("nil_suolo_serie.csv")
t = trans[trans.classe_2012 != trans.classe_2025]
def tr(a, b_list): return float(t[(t.classe_2012.isin(a)) & (t.classe_2025.isin(b_list))].ha.sum())
cl25 = cls.sum(numeric_only=True)
mil_cls = mcls[mcls.ambito == "Milano"][["classe_2025", "descrizione", "ha", "quota_%"]].to_dict("records")
res_cls = mcls[mcls.ambito != "Milano"][["classe_2025", "descrizione", "ha", "quota_%"]].to_dict("records")
res_cave = float(mcls[(mcls.ambito != "Milano") & (mcls.classe_2025.isin([123, 124]))]["quota_%"].sum())
res_122 = float(mcls[(mcls.ambito != "Milano") & (mcls.classe_2025 == 122)]["quota_%"].sum())
nuovo_mi_comune = float(mrc[mrc.pro_com == 15146].nuovo_2012_2025_ha.iloc[0])
log_ge12 = float(log.ha_dal_2012.sum()); log_tot = float(log.totale_ha.sum())
raster_new_metro = float(mrc.nuovo_2012_2025_ha.sum())
ring_in = anelli[anelli.anello_km_dal_duomo.isin(["0-1", "1-2", "2-3"])]
ring_mid = anelli[anelli.anello_km_dal_duomo.isin(["4-5", "5-6", "6-7", "7-8", "8-9"])]

metro_tab = metro.merge(mcl[["pro_com", "nuovo_ha", "cave_ha", "cantieri_122_ha", "edifici_111_ha", "pavimentate_116_ha", "strade_112_ha"]], on="pro_com", how="left")
metro_tab = metro_tab.merge(log[["comune", "totale_ha", "ha_dal_2012"]].rename(columns={"totale_ha": "log_tot", "ha_dal_2012": "log_12"}), on="comune", how="left").fillna({"log_tot": 0, "log_12": 0})
mt = []
for r in metro_tab.itertuples():
    mt.append([int(r.pro_com), r.comune, r.superficie_ha, int(r.popolazione_2025), r.consumato_2025_pct, r.m2_per_abitante_2025, r.lordo_2012_2025_ha_pubblicato,
               r.netto_2012_2025_ha_pubblicato, r.nuovo_ha, r.edifici_111_ha, r.cantieri_122_ha, r.cave_ha, r.log_12])
m_ = riep_ind["metro"]
riep = {
 "data_download": "2026-11-01",
 "milano": {"serie": mil.to_dict("records"), "indice": mil_idx, "incrementi": inc_m[["periodo", "anni", "netto_ha", "lordo_ha", "ripristino_ha"]].to_dict("records"),
            "ha25": float(r0.consumato_ha * 0 + mil[mil.anno == 2025].consumato_ha.iloc[0]), "pct25": float(mil[mil.anno == 2025].consumato_pct.iloc[0]),
            "ha06": float(r0.consumato_ha), "superficie_ha": riep_ind["milano_2025"]["superficie_ha"], "m2ab25": float(mil[mil.anno == 2025].m2_per_ab.iloc[0]),
            "m2ab06": float(r0.m2_per_ab), "pop06": int(r0.popolazione), "pop25": int(mil[mil.anno == 2025].popolazione.iloc[0]),
            "netto_06_12": float(inc_m[inc_m.periodo == "2006-2012"].netto_ha.iloc[0]),
            "netto_12_25": float(inc_m[inc_m.periodo != "2006-2012"].netto_ha.sum()), "lordo_12_25": float(inc_m[inc_m.periodo != "2006-2012"].lordo_ha.sum()),
            "rip_12_25": float(inc_m[inc_m.periodo != "2006-2012"].ripristino_ha.sum()),
            "ultimo": inc_m[inc_m.periodo == "2024-2025"][["netto_ha", "lordo_ha", "ripristino_ha"]].iloc[0].to_dict(),
            "rango_grandi": riep_ind["milano_rango_grandi"], "n_grandi": riep_ind["grandi_comuni_n"], "rango_italia": riep_ind["milano_rango_pct_nazionale"],
            "n_comuni_italia": riep_ind["n_comuni_italia"], "italia_pct": 7.19, "isola_calore": float(riep_ind["milano_2025"]["isola_calore_2025_C"]),
            "densita_ab_ha": float(riep_ind["milano_2025"]["densita_ab_per_ha"])},
 "citta": cit,
 "grandi_top": grandi.head(10)[["comune", "consumato_2025_pct", "popolazione_2025"]].to_dict("records"),
 "raster": {"nuovo_1225": float(tot_new), "rip_1225": float(tot_rest), "netto_1225": float(tot_new - tot_rest), "nuovo_comune_istat": nuovo_mi_comune,
            "quota_top8_suolo": quota_suolo, "quota_top8_abitazioni": float(quota_abit), "quota_top8_volume": float(quota_vol), "top8": [pr(x) for x in top8.nil],
            "periodi": {k: {"nuovo": float(sum(v["n" + k] for v in per_nil.values())), "rip": float(sum(v["r" + k] for v in per_nil.values()))} for k in PER},
            "zone": zone_t, "anelli": anelli[["anello_km_dal_duomo", "area_ha", "pct_2025", "nuovo_2012_2025_ha", "ripristino_2012_2025_ha"]].to_dict("records"),
            "entro3km": {"nuovo": float(ring_in.nuovo_2012_2025_ha.sum()), "rip": float(ring_in.ripristino_2012_2025_ha.sum())},
            "tra4e9km": {"nuovo": float(ring_mid.nuovo_2012_2025_ha.sum())},
            "classi_milano": mil_cls, "quota_cantieri": float([c["quota_%"] for c in mil_cls if c["classe_2025"] == 122][0]),
            "quota_edifici": float([c["quota_%"] for c in mil_cls if c["classe_2025"] == 111][0]),
            "stock122_2012": float(trans[trans.classe_2012 == 122].ha.sum()), "stock122_2025": float(trans[trans.classe_2025 == 122].ha.sum()),
            "cantiere_a_libero": tr([122], [2, 201, 202, 203, 204, 205, 206]), "cantiere_a_costruito": tr([122], [111, 112, 113, 116]),
            "cantiere_resta": float(trans[(trans.classe_2012 == 122) & (trans.classe_2025 == 122)].ha.sum()),
            "libero_a_cantiere": tr([2], [122]), "libero_a_edifici": tr([2], [111]), "libero_a_piazzali": tr([2], [116]), "libero_a_strade": tr([2], [112]),
            "classe1_ha_2025": float(cl25["cl1_ha"]), "controllo": ctrl[["anno", "raster_ha", "ispra_ha", "diff_%"]].to_dict("records"),
            "nuovo_2024_25": float(sc_all.nuovo_2024_2025_ha_da_carta_cambiamenti.sum()), "rip_2024_25": float(sc_all.ripristino_2024_2025_ha.sum()),
            "restituiti_top": [{"nil": pr(r.nil), "rip": r.ripristino_2012_2025_ha, "nuovo": r.nuovo_2012_2025_ha} for r in sc_all.sort_values("ripristino_2012_2025_ha", ascending=False).head(8).itertuples()],
            "n_nil_oltre05": int((sc_all.nuovo_2012_2025_ha > 0.5).sum()), "n_nil_sotto01": int((sc_all.nuovo_2012_2025_ha < 0.1).sum()),
            "pixel_png": overlay},
 "metro": {"comuni": m_["comuni"], "superficie_ha": m_["superficie_ha"], "ha25": m_["consumato_2025_ha"], "pop25": m_["popolazione_2025"],
           "pct25": 100 * m_["consumato_2025_ha"] / m_["superficie_ha"], "resto_pct": 100 * m_["resto_senza_milano"]["consumato_2025_ha"] / m_["resto_senza_milano"]["superficie_ha"],
           "resto_m2ab": 1e4 * m_["resto_senza_milano"]["consumato_2025_ha"] / m_["resto_senza_milano"]["popolazione_2025"],
           "netto_12_25": m_["netto_2012_2025_ha_pubblicato"], "lordo_12_25": float(metro.lordo_2012_2025_ha_pubblicato.sum()),
           "milano_rango_pct": int((metro.consumato_2025_pct > 58.812).sum() + 1),
           "top_pct": metro.sort_values("consumato_2025_pct", ascending=False).head(6)[["comune", "consumato_2025_pct"]].to_dict("records"),
           "nuovo_raster_resto_classi": res_cls, "resto_cave_pct": res_cave, "resto_cantieri_pct": res_122, "nuovo_raster_tot": raster_new_metro,
           "logistica_ha_dal_2012": log_ge12, "logistica_ha_tot": log_tot, "logistica_quota_pct": 100 * log_ge12 / raster_new_metro,
           "logistica_periodi": logper.to_dict("records"),
           "logistica_top": log.sort_values("ha_dal_2012", ascending=False).head(8)[["comune", "totale_ha", "ha_dal_2012"]].to_dict("records"),
           "colonne": ["pro_com", "comune", "superficie_ha", "popolazione", "pct_consumato_2025", "m2_per_abitante", "lordo_2012_2025_ispra", "netto_2012_2025_ispra",
                       "nuovo_carta_2012_2025", "edifici", "cantieri", "cave", "logistica_dal_2012"],
           "tab": mt},
 "potenziale": {"spazi_verdi": float(pot["Potenziale_spazi_verdi_TOTALE [ettari]"]), "pubblico": float(pot["Potenziale_spazi_verdi_prevalentemente_pubblico [ettari]"]),
                "privato": float(pot["Potenziale_spazi_verdi_prevalentemente_privato [ettari]"]), "altre": float(pot["Potenziale_spazi_verdi_altre_aree_interne_perimetro_urbano [ettari]"]),
                "alberi": float(pot["Potenziale_copertura_arborea_TOTALE [ettari]"]), "tetti_min": float(pot["Potenziale_superficie_minima_disponibile_tetti_per_fotovoltaico [ettari]"]),
                "tetti_max": float(pot["Potenziale_superficie_massima_disponibile_tetti_per_fotovoltaico [ettari]"])},
 "edizioni": ed[ed.comune == "Milano"][["periodo", "netto_ed2025_ha", "netto_ed2026_ha"]].to_dict("records"),
}
json.dump(clean(riep), open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# copie dei CSV aggregati
for f in ["nil_suolo.csv", "nil_suolo_serie.csv", "serie_citta.csv", "confronto_citta_2025.csv", "anelli_duomo.csv", "metro_comuni.csv", "metro_raster_comuni.csv",
          "metro_nuovo_per_comune_e_classe.csv", "logistica_metro_comuni.csv", "confronto_costruzioni_nil.csv", "incrementi_milano_periodi.csv", "inventario_fonti.csv", "confronto_edizioni_2025_2026.csv"]:
    shutil.copy(os.path.join(P, f), os.path.join(OUT, f))
tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
print("scritti i file in", OUT, "totale byte", tot)
