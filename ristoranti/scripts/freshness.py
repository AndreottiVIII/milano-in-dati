"""Fase 1: freschezza e copertura. OpenStreetMap (Overpass, con meta) vs registro del Comune (ds58 in piano, ds59 fuori piano, ds250 artigianato alimentare).
Uso: python -I -X utf8 freshness.py <ristoranti_abs> <milano-in-dati_abs> [file osm in raw/osm]
Scrive in pulito/: osm_poi.csv, registro.csv, freschezza_osm.csv, confronto_nil.csv, campione_100.csv, freschezza.json"""
import sys, os, json, re
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from pyproj import Transformer

R_, P = sys.argv[1], sys.argv[2]
RAW, OUT = os.path.join(R_, "raw"), os.path.join(R_, "pulito")
NOW = pd.Timestamp("2026-11-01", tz="UTC")
R = {}
SIX = ["restaurant", "fast_food", "cafe", "bar", "pub", "ice_cream"]

# ---------- NIL (poligoni vigenti, stessa fonte del filone alberi)
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
polys = [shape(f["geometry"]) for f in g["features"]]
ids = [int(f["properties"]["ID_NIL"]) for f in g["features"]]
names = [f["properties"]["NIL"] for f in g["features"]]
tree = STRtree(polys)
d205 = pd.read_csv(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "pop_caratteristiche_quartiere", "ds205_dati_quartieri_2011_2024_.csv"), sep=None, engine="python")
d205 = d205[d205.NIL.notna()].copy()
d205["id_nil"] = d205.NIL.astype(int)
pop = d205[d205.Anno == 2024].set_index("id_nil")["Totale"]
Tu = Transformer.from_crs(4326, 32632, always_xy=True)


def assign_nil(lon, lat):
    pts = shapely.points(lon, lat)
    pi, gi = tree.query(pts, predicate="within")
    out = np.full(len(lon), -1)
    out[pi] = [ids[j] for j in gi]
    return out


# ---------- OSM
OSMF = sys.argv[3] if len(sys.argv) > 3 else "osm_milano_food_geofabrik.json"
d = json.load(open(os.path.join(RAW, "osm", OSMF), encoding="utf-8"))
R["osm_timestamp_base"] = d.get("osm3s", {}).get("timestamp_osm_base")
rows = []
for e in d["elements"]:
    t = e.get("tags", {})
    lat = e.get("lat", e.get("center", {}).get("lat"))
    lon = e.get("lon", e.get("center", {}).get("lon"))
    rows.append(dict(osm_type=e["type"], osm_id=e["id"], lon=lon, lat=lat, timestamp=e.get("timestamp"), version=e.get("version"), uid=e.get("uid"), changeset=e.get("changeset"),
                     amenity=t.get("amenity"), name=t.get("name"), cuisine=t.get("cuisine"), opening_hours=t.get("opening_hours"),
                     check_date=t.get("check_date") or t.get("survey:date") or t.get("check_date:opening_hours"),
                     website=t.get("website") or t.get("contact:website"), phone=t.get("phone") or t.get("contact:phone"),
                     street=t.get("addr:street"), housenumber=t.get("addr:housenumber"), brand=t.get("brand"), takeaway=t.get("takeaway"),
                     outdoor_seating=t.get("outdoor_seating"), diet_vegan=t.get("diet:vegan"), wheelchair=t.get("wheelchair")))
o = pd.DataFrame(rows)
o["ts"] = pd.to_datetime(o.timestamp, utc=True)
o["eta_anni"] = (NOW - o.ts).dt.days / 365.25
o["nil_id"] = assign_nil(o.lon.values, o.lat.values)
R["osm_elementi_totali"] = len(o)
R["osm_per_tipo_elemento"] = o.osm_type.value_counts().to_dict()
R["osm_per_amenity_tutti"] = o.amenity.value_counts().to_dict()
R["osm_fuori_da_ogni_NIL"] = int((o.nil_id < 0).sum())
oo = o[o.nil_id > 0].copy().reset_index(drop=True)


def fr(df):
    r = {"n": len(df), "mediana_eta_anni": round(float(df.eta_anni.median()), 2)}
    for y in (1, 2, 3, 5):
        r[f"modificati_ultimi_{y}_anni_pct"] = round(100 * (df.eta_anni <= y).mean(), 1)
    r["con_cuisine_pct"] = round(100 * df.cuisine.notna().mean(), 1)
    r["con_opening_hours_pct"] = round(100 * df.opening_hours.notna().mean(), 1)
    r["con_check_date_pct"] = round(100 * df.check_date.notna().mean(), 1)
    cd = pd.to_datetime(df.check_date, errors="coerce", utc=True)
    r["check_date_ultimi_3_anni_pct"] = round(100 * ((NOW - cd).dt.days / 365.25 <= 3).mean(), 1)
    r["con_sito_o_telefono_pct"] = round(100 * (df.website.notna() | df.phone.notna()).mean(), 1)
    r["con_indirizzo_pct"] = round(100 * (df.street.notna() & df.housenumber.notna()).mean(), 1)
    r["con_nome_pct"] = round(100 * df.name.notna().mean(), 1)
    r["versione_1_pct"] = round(100 * (df.version == 1).mean(), 1)
    return r


fa = {"TUTTI_8_tipi": fr(oo), "SEI_tipi_(rist,fast,cafe,bar,pub,gelato)": fr(oo[oo.amenity.isin(SIX)])}
for a, grp in oo.groupby("amenity"):
    fa[a] = fr(grp)
pd.DataFrame(fa).T.to_csv(os.path.join(OUT, "freschezza_osm.csv"), sep=";", encoding="utf-8-sig")
R["freschezza_osm"] = fa
R["osm_anno_ultima_modifica"] = {int(k): int(v) for k, v in oo.ts.dt.year.value_counts().sort_index().items()}
R["osm_ultima_modifica_massima"] = str(oo.ts.max())

# ---------- Registro del Comune
def rd(fn, kind):
    x = pd.read_csv(os.path.join(RAW, fn), sep=";", dtype=str)
    x["registro"] = kind
    return x


r58 = rd("comune_ds58/ds58_commercio_pubblici_esercizi_in_piano.csv", "ds58_in_piano")
r59 = rd("comune_ds59/ds59_commercio_pubblici_esercizi_fuori_piano.csv", "ds59_fuori_piano")
r250 = rd("comune_ds250/ds250_artigianato_settore_alimentare.csv", "ds250_artigianato_alim")
reg = pd.concat([r58, r59, r250], ignore_index=True)
reg["lon"] = pd.to_numeric(reg.LONG_X_4326, errors="coerce")
reg["lat"] = pd.to_numeric(reg.LAT_Y_4326, errors="coerce")
reg["id_nil"] = pd.to_numeric(reg.ID_NIL, errors="coerce")
R["registro_righe"] = reg.registro.value_counts().to_dict()
R["registro_senza_coordinate"] = reg[reg.lon.isna()].registro.value_counts().to_dict()
R["registro_senza_NIL"] = reg[reg.id_nil.isna()].registro.value_counts().to_dict()
reg.to_csv(os.path.join(OUT, "registro.csv"), sep=";", index=False, encoding="utf-8-sig")

# ---------- Confronto per NIL
cmp_ = pd.DataFrame({"nil": pd.Series(dict(zip(ids, names)))})
cmp_["abitanti_2024"] = pop
cmp_["osm_tutti"] = oo.groupby("nil_id").size()
cmp_["osm_6tipi"] = oo[oo.amenity.isin(SIX)].groupby("nil_id").size()
for k, nm in (("ds58_in_piano", "reg_ds58"), ("ds59_fuori_piano", "reg_ds59"), ("ds250_artigianato_alim", "reg_ds250")):
    cmp_[nm] = reg[reg.registro == k].groupby("id_nil").size()
cmp_[["osm_tutti", "osm_6tipi", "reg_ds58", "reg_ds59", "reg_ds250"]] = cmp_[["osm_tutti", "osm_6tipi", "reg_ds58", "reg_ds59", "reg_ds250"]].fillna(0)
cmp_["reg_58_59"] = cmp_.reg_ds58 + cmp_.reg_ds59
cmp_["reg_58_59_250"] = cmp_.reg_58_59 + cmp_.reg_ds250
for k in ("reg_ds58", "reg_58_59", "reg_58_59_250"):
    cmp_[f"diff_pct_{k}"] = (100 * (cmp_.osm_6tipi / cmp_[k].replace(0, np.nan) - 1)).round(1)
cmp_["osm_per_1000ab"] = (1000 * cmp_.osm_6tipi / cmp_.abitanti_2024).round(2)
cmp_["reg58_per_1000ab"] = (1000 * cmp_.reg_ds58 / cmp_.abitanti_2024).round(2)
cmp_.index.name = "id_nil"
cmp_.to_csv(os.path.join(OUT, "confronto_nil.csv"), sep=";", encoding="utf-8-sig")
tot = {k: int(cmp_[k].sum()) for k in ("osm_6tipi", "osm_tutti", "reg_ds58", "reg_ds59", "reg_ds250")}
R["totali_nei_NIL"] = tot
R["rapporto_osm6_su_ds58"] = round(tot["osm_6tipi"] / tot["reg_ds58"], 3)
R["rapporto_osm6_su_ds58_59"] = round(tot["osm_6tipi"] / (tot["reg_ds58"] + tot["reg_ds59"]), 3)
R["rapporto_osm6_su_ds58_59_250"] = round(tot["osm_6tipi"] / (tot["reg_ds58"] + tot["reg_ds59"] + tot["reg_ds250"]), 3)
for k in ("reg_ds58", "reg_58_59", "reg_58_59_250"):
    dd = cmp_[f"diff_pct_{k}"].dropna()
    R[f"NIL_{k}"] = {"totali": int(len(dd)), "entro_20pct": int((dd.abs() <= 20).sum()), "entro_30pct": int((dd.abs() <= 30).sum()), "entro_50pct": int((dd.abs() <= 50).sum()),
                     "mediana_diff_pct": round(float(dd.median()), 1), "correlazione": round(float(np.corrcoef(cmp_.osm_6tipi, cmp_[k])[0, 1]), 3)}
mm = reg[reg.lon.notna() & reg.id_nil.notna()].copy()
mm["nil_calc"] = assign_nil(mm.lon.values, mm.lat.values)
R["registro_NIL_dichiarato_uguale_a_calcolato_pct"] = round(100 * (mm.nil_calc == mm.id_nil).mean(), 2)


# ---------- Abbinamenti OSM -> registro (spazio 50 m, oppure via+civico uguali)
def xy(df):
    x, y = Tu.transform(df.lon.values, df.lat.values)
    return np.column_stack([x, y])


regm = reg[reg.lon.notna()].reset_index(drop=True)
rxy = xy(regm)
rtree = STRtree(shapely.points(rxy))
STOP = r"\b(via|viale|piazza|piazzale|corso|largo|vicolo|alzaia|foro|bastioni|strada|galleria|ripa|di|del|della|dei|delle|degli|dello|dell|de|d|san|santa|sant|s|dal|da|al)\b"


def norm_street(s):
    s = str(s).lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(STOP, " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(sorted(w for w in s.split() if len(w) > 1))


def reg_addr(u):
    m = re.match(r"^(.*?)\s+N\.\s*([0-9]+[A-Za-z]?)", str(u))
    return (norm_street(m.group(1)), m.group(2).lower()) if m else (None, None)


ad = [reg_addr(u) for u in regm.Ubicazione]
addr_index = {}
for i, (s_, n_) in enumerate(ad):
    if s_:
        addr_index.setdefault((s_, n_), []).append(i)
pts = xy(oo)
tp = shapely.points(pts)
dmin, aok = [], []
for k in range(len(oo)):
    near = rtree.query(tp[k].buffer(50))
    dmin.append(min((float(np.hypot(*(rxy[j] - pts[k]))) for j in near), default=np.inf))
    r_ = oo.iloc[k]
    aok.append(isinstance(r_.street, str) and isinstance(r_.housenumber, str) and (norm_street(r_.street), r_.housenumber.lower().replace(" ", "")) in addr_index)
oo["dist_registro_m"] = dmin
oo["indirizzo_in_registro"] = aok
oo["match_50m"] = oo.dist_registro_m <= 50
oo["match_ok"] = oo.match_50m | oo.indirizzo_in_registro
oo.to_csv(os.path.join(OUT, "osm_poi.csv"), sep=";", index=False, encoding="utf-8-sig")

rest = oo[oo.amenity == "restaurant"]
samp = rest.sample(100, random_state=20261101)
samp[["osm_type", "osm_id", "name", "cuisine", "street", "housenumber", "timestamp", "dist_registro_m", "indirizzo_in_registro", "match_50m", "match_ok"]].to_csv(os.path.join(OUT, "campione_100.csv"), sep=";", index=False, encoding="utf-8-sig")
R["campione100_restaurant"] = {"match_50m": int(samp.match_50m.sum()), "indirizzo_in_registro": int(samp.indirizzo_in_registro.sum()), "match_ok": int(samp.match_ok.sum()),
                                "mediana_dist_m_se_trovato": round(float(samp.dist_registro_m[samp.match_50m].median()), 1),
                                "modificati_ultimi_3_anni": int((samp.eta_anni <= 3).sum())}


def mrate(df):
    return {"n": len(df), "match_ok_pct": round(100 * df.match_ok.mean(), 1), "match_50m_pct": round(100 * df.match_50m.mean(), 1)}


s6 = oo[oo.amenity.isin(SIX)].copy()
R["match_tutti_osm_6tipi"] = mrate(s6)
R["match_per_amenity"] = {a: mrate(gp) for a, gp in oo.groupby("amenity")}
s6["fascia_eta"] = pd.cut(s6.eta_anni, [0, 1, 3, 5, 8, 30], labels=["<=1a", "1-3a", "3-5a", "5-8a", ">8a"])
R["match_per_fascia_ultima_modifica_osm"] = {str(a): mrate(gp) for a, gp in s6.groupby("fascia_eta", observed=True)}

# ---------- registro (in piano) -> OSM entro 50 m, e per anzianita' del codice
oxy = xy(oo)
otree = STRtree(shapely.points(oxy))
rm58 = regm[regm.registro == "ds58_in_piano"].copy()
rm58["osm50"] = [len(otree.query(shapely.Point(rxy[i]), predicate="dwithin", distance=50)) > 0 for i in rm58.index]
rm58["num"] = rm58.Codice.str.extract(r"^PE/(\d+)")[0].astype(float)
R["registro_ds58_con_POI_OSM_entro_50m_pct"] = round(100 * rm58.osm50.mean(), 1)
R["registro_ds58_PE_registrati_dopo_lug2019_(>29144)"] = {"n": int((rm58.num > 29144).sum()), "con_OSM_pct": round(100 * rm58[rm58.num > 29144].osm50.mean(), 1)}
R["registro_ds58_ultimi_500_codici_PE"] = {"con_OSM_pct": round(100 * rm58.dropna(subset=["num"]).sort_values("num").tail(500).osm50.mean(), 1)}
R["registro_ds58_altri_codici"] = {"n": int((~(rm58.num > 29144)).sum()), "con_OSM_pct": round(100 * rm58[~(rm58.num > 29144)].osm50.mean(), 1)}
json.dump(R, open(os.path.join(OUT, "freschezza.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
