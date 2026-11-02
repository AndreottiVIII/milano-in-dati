"""Parcheggi a Milano: riepiloghi (FASE 1). Si puo' rilanciare.
Uso (percorsi assoluti):
  python -I -X utf8 analisi.py <parcheggi_dir> <milano_in_dati_dir>
Legge: parcheggi/pulito/osm_parcheggi.pkl (da osm_parcheggi.py), parcheggi/raw/comune_ds83 (ambiti), ds342 (parcheggi pubblici),
ds45 (interscambio), ds60 (itinerari ciclabili), ds51 (aree pedonali), comune_veicoli/ds529 (parco veicolare), aci_autoritratto_2024 (estratto Milano),
alberi/pulito/nil_alberi.csv (abitanti e superficie per NIL), censimenti/pulito/nil_2021_anagrafica.csv (nomi NIL), poligoni NIL di citta-15-minuti.
Scrive in parcheggi/pulito/: riepilogo.json, nil_parcheggi.csv, ambiti.csv, offstreet_nil.csv, parcheggi_ufficiali.csv, interscambio.csv, ciclabili_nil.csv
Ipotesi (tutte nel JSON, sezione "ipotesi"): stallo su strada = 12 m2 (parametro M2_STALLO), ripartizione dei posti per lunghezza di strada.
"""
import sys, os, json, pickle, collections
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, Polygon, LineString, Point
from shapely.ops import unary_union
from pyproj import Transformer

PD, MD = sys.argv[1], sys.argv[2]
PU = os.path.join(PD, "pulito"); RAW = os.path.join(PD, "raw")
M2_STALLO = 12.0                    # ipotesi di Davide: circa 12 m2 per stallo (5 m x 2,2 m + un po' di manovra)
TOT_STALLI = 297000                 # circa 297.000 stalli su strada: presentazione "La sosta a Milano" (Comune), riportata da Sicurauto 7/2/2025 ("circa 300 mila")
QUOTE = {"blu": 37.2, "gialli_residenti": 18.2, "disabili": 1.9, "carico_scarico": 1.5, "autorizzati": 2.0}   # % sul totale (somma 60,8% = circa 180.000 regolamentati)
QUOTE["liberi"] = round(100 - sum(QUOTE.values()), 1)            # 39,2% = "poco piu' di 100 mila" strisce bianche
tr = Transformer.from_crs(4326, 32632, always_xy=True)
def utm_ll(lon, lat):
    return tr.transform(lon, lat)
def to_utm(g):
    return shapely.transform(g, lambda a: np.column_stack(tr.transform(a[:, 0], a[:, 1])))

RIEP = {"ipotesi": {"m2_per_stallo": M2_STALLO, "stalli_su_strada_totale": TOT_STALLI, "quote_percento": QUOTE}}

# ---------------------------------------------------------------- NIL
nilgeo = json.load(open(os.path.join(MD, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
NIL = {int(f["properties"]["ID_NIL"]): to_utm(shape(f["geometry"])) for f in nilgeo["features"]}
ana = pd.read_csv(os.path.join(MD, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
nomi = dict(zip(ana.nil, ana.nil_nome))
base = pd.read_csv(os.path.join(MD, "alberi", "pulito", "nil_alberi.csv"), sep=";")[["id_nil", "nil", "area_km2", "abitanti_2024"]]
base["nome"] = [nomi.get(int(i)) or str(n).title() for i, n in zip(base.id_nil, base.nil)]
base = base.set_index("id_nil")
assert len(base) == 88 and set(base.index) == set(NIL)
CITY = unary_union(list(NIL.values()))
nil_ids = list(NIL)
nil_geoms = np.array([NIL[i] for i in nil_ids], dtype=object)
shapely.prepare(nil_geoms)
tree = shapely.STRtree(nil_geoms)
city_km2 = CITY.area / 1e6
print("area citta' km2", round(city_km2, 2))
RIEP["citta"] = {"area_km2": round(city_km2, 2), "abitanti_2024": int(base.abitanti_2024.sum())}

def nil_of_points(x, y):
    """id NIL per punti UTM (NaN se fuori)"""
    pts = shapely.points(x, y)
    out = np.full(len(pts), -1)
    ii, jj = tree.query(pts, predicate="within")
    out[ii] = np.array(nil_ids)[jj]
    return out

# ---------------------------------------------------------------- ambiti della sosta (ds83)
amb = json.load(open(os.path.join(RAW, "comune_ds83", "sosta_ambiti.geojson"), encoding="utf8"))
CERCHIA = {}
for a in (1, 3, 4, 5, 6, 7, 901): CERCHIA[a] = "Area C / Bastioni"
for a in (2,) + tuple(range(9, 24)): CERCHIA[a] = "Cerchia filoviaria"
for a in (8, 25, 30, 31, 32, 33, 34, 35, 36, 40, 42, 43): CERCHIA[a] = "Extra-filoviaria"
CERCHIA[38] = "Interscambio (via Impastato)"
TARIFFA = {"Area C / Bastioni": 3.0, "Cerchia filoviaria": 2.0, "Extra-filoviaria": 1.2, "Interscambio (via Impastato)": None}
amb_rows, amb_geoms = [], []
for f in amb["features"]:
    g = to_utm(shape(f["geometry"]))
    n = int(f["properties"]["ambito"])
    amb_geoms.append(g)
    amb_rows.append({"ambito": n, "nome": f["properties"]["nome"], "cerchia": CERCHIA.get(n, "n.d."), "tariffa_eur_h": TARIFFA.get(CERCHIA.get(n)), "area_km2": g.area / 1e6})
AMB_U = unary_union(amb_geoms).intersection(CITY)
shapely.prepare(AMB_U)
amb_df = pd.DataFrame(amb_rows).sort_values("ambito")
amb_df["area_km2"] = amb_df.area_km2.round(3)
amb_df.to_csv(os.path.join(PU, "ambiti.csv"), index=False, sep=";")
assert (amb_df.cerchia != "n.d.").all(), amb_df[amb_df.cerchia == "n.d."]
RIEP["ambiti"] = {"n": len(amb_df), "area_unione_km2": round(AMB_U.area / 1e6, 2), "quota_citta_pct": round(100 * AMB_U.area / CITY.area, 1),
                  "per_cerchia_km2": {k: round(v, 2) for k, v in amb_df.groupby("cerchia").area_km2.sum().items()},
                  "campi_posti_vuoti": "posti_pagamento e posti_residenti sono vuoti in tutti i 36 ambiti (ds83)"}
print(RIEP["ambiti"])

# ---------------------------------------------------------------- OSM
osm = pickle.load(open(os.path.join(PU, "osm_parcheggi.pkl"), "rb"))

# strade su cui si puo' parcheggiare (esclusi service/pedonali/autostrade)
ELIG = {"residential", "tertiary", "secondary", "primary", "unclassified", "living_street", "trunk", "tertiary_link", "secondary_link", "primary_link", "trunk_link"}
lines, tags = [], []
for h in osm["highways"]:
    if h["tags"].get("highway") in ELIG and len(h["lon"]) >= 2:
        x, y = utm_ll(np.array(h["lon"]), np.array(h["lat"]))
        lines.append(LineString(np.column_stack([x, y]))); tags.append(h["tags"])
lines = np.array(lines, dtype=object)
ii, jj = tree.query(lines, predicate="intersects")
pieces = shapely.intersection(lines[ii], nil_geoms[jj])
plen = shapely.length(pieces)
keep = plen > 0.01
ii, jj, pieces, plen = ii[keep], jj[keep], pieces[keep], plen[keep]
mid = shapely.line_interpolate_point(pieces, 0.5, normalized=True)
inamb = shapely.contains_xy(AMB_U, shapely.get_x(mid), shapely.get_y(mid))   # appartenenza decisa dal punto medio del pezzo (approssimazione)
pn = np.array(nil_ids)[jj]
st = pd.DataFrame({"nil": pn, "len": plen, "in_ambito": inamb})
st_nil = st.pivot_table(index="nil", columns="in_ambito", values="len", aggfunc="sum", fill_value=0).reindex(nil_ids, fill_value=0)
st_nil.columns = ["km_fuori_ambiti", "km_in_ambiti"]
st_nil = st_nil / 1000.0
tot_in, tot_out = st_nil.km_in_ambiti.sum(), st_nil.km_fuori_ambiti.sum()
RIEP["strade"] = {"km_totali_entro_comune": round(tot_in + tot_out, 1), "km_in_ambiti": round(tot_in, 1), "km_fuori_ambiti": round(tot_out, 1),
                  "nota": "strade OSM con highway in " + ",".join(sorted(ELIG)) + " tagliate sui NIL; in/fuori ambiti dal punto medio di ogni pezzo"}
print(RIEP["strade"])

# copertura dei tag parking:* sulle strade (quanto OSM sa)
tagged = np.array([any(k.startswith("parking") for k in t) for t in tags])
len_by_line = pd.Series(plen).groupby(ii).sum()
tag_len = float(len_by_line[tagged[len_by_line.index]].sum()) / 1000
RIEP["osm_tag_parcheggio_su_strade"] = {"km_con_tag": round(tag_len, 1), "quota_pct": round(100 * tag_len / (tot_in + tot_out), 1)}
print(RIEP["osm_tag_parcheggio_su_strade"])

# ---------------------------------------------------------------- stima dei posti su strada per NIL (modello)
# Ipotesi: densita' di stalli uniforme lungo le strade (stalli per km di strada). Gli stalli regolamentati (circa 180.000) stanno tutti dentro gli ambiti;
# quindi dentro gli ambiti la quota regolamentata e' f_in = regolamentati / (stalli dentro gli ambiti), fuori dagli ambiti tutti gli stalli sono liberi.
tot_km = tot_in + tot_out
reg = TOT_STALLI * (1 - QUOTE["liberi"] / 100)
dens = TOT_STALLI / tot_km
st_nil["posti_strada_stima"] = (st_nil.km_in_ambiti + st_nil.km_fuori_ambiti) * dens
st_nil["posti_regolamentati_stima"] = st_nil.km_in_ambiti * dens * (reg / (tot_in * dens))
st_nil["posti_liberi_stima"] = st_nil.posti_strada_stima - st_nil.posti_regolamentati_stima
RIEP["modello"] = {"posti_per_km_di_strada": round(dens, 1), "metri_di_strada_per_posto": round(1000 / dens, 2),
                   "quota_regolamentata_dentro_gli_ambiti_pct": round(100 * reg / (tot_in * dens), 1),
                   "descrizione": "densita' uniforme: ogni km di strada (OSM, esclusi service/pedonali/autostrade) ha lo stesso numero di stalli; i regolamentati (circa 180.000) sono tutti nei 36 ambiti"}
print(RIEP["modello"])
# controllo indipendente (parziale) con i tag OSM parking:* sulle strade che li hanno
SIDE_OK = {"yes", "lane", "street_side", "on_kerb", "half_on_kerb", "shoulder", "parallel", "diagonal", "perpendicular", "marked", "separate"}
def side_state(t, side):
    for key in (f"parking:{side}", f"parking:lane:{side}", "parking:both", "parking:lane:both"):
        v = t.get(key)
        if v is not None:
            return v in SIDE_OK
    return None
ok_len = 0.0; known_len = 0.0; sides_known = 0.0
for k, (ln, t) in enumerate(zip(lines, tags)):
    if not tagged[k]:
        continue
    L = len_by_line.get(k, 0.0)
    for side in ("left", "right"):
        s = side_state(t, side)
        if s is None:
            continue
        known_len += L; ok_len += L * s
RIEP["controllo_osm_tag"] = {"lati_strada_km_con_informazione": round(known_len / 1000, 1), "quota_lati_con_sosta_ammessa_pct": round(100 * ok_len / known_len, 1) if known_len else None}
frac = ok_len / known_len if known_len else 0
for m_stallo in (5.5, 6.0):
    RIEP["controllo_osm_tag"][f"stalli_se_estesi_a_tutte_le_strade_{m_stallo}m_per_stallo"] = round(2 * tot_km * 1000 * frac / m_stallo)
RIEP["controllo_osm_tag"]["nota"] = "le strade con tag parking:* sono il 15% e non sono un campione casuale: serve solo come ordine di grandezza (confronto con 297.000)"
print(RIEP["controllo_osm_tag"])

# ---------------------------------------------------------------- OSM: parcheggi fuori strada, posti mappati
def geom_of(w):
    x, y = utm_ll(np.array(w["lon"]), np.array(w["lat"]))
    c = np.column_stack([x, y])
    if w["closed"] and len(c) >= 4:
        g = Polygon(c)
        return g if g.is_valid else shapely.make_valid(g)
    return LineString(c)

OFF = []   # parcheggi fuori strada (amenity=parking, parking diverso da street_side/lane)
ON = []    # parcheggi su strada mappati come aree
SP = []    # stalli singoli mappati (parking_space)
for w in osm["parking_ways"]:
    t = w["tags"]; am = t.get("amenity"); pk = t.get("parking")
    if am not in ("parking", "parking_space"):
        continue
    g = geom_of(w)
    if g.geom_type not in ("Polygon", "MultiPolygon"):
        continue
    cap = int(t["capacity"]) if str(t.get("capacity", "")).isdigit() else None
    rec = {"id": w["id"], "geom": g, "area": g.area, "cap": cap, "tipo": pk or "n.d.", "access": t.get("access"), "fee": t.get("fee"), "name": t.get("name")}
    if am == "parking_space":
        SP.append(rec)
    elif pk in ("street_side", "lane", "on_kerb"):
        ON.append(rec)
    else:
        OFF.append(rec)

def df_geoms(rows):
    d = pd.DataFrame([{k: v for k, v in r.items() if k != "geom"} for r in rows])
    c = shapely.centroid(np.array([r["geom"] for r in rows], dtype=object))
    d["x"], d["y"] = shapely.get_x(c), shapely.get_y(c)
    d["nil"] = nil_of_points(d.x.values, d.y.values)
    return d
off = df_geoms(OFF); on = df_geoms(ON); sp = df_geoms(SP)
off = off[off.nil >= 0]; on = on[on.nil >= 0]; sp = sp[sp.nil >= 0]
# centri dei parcheggi con il baricentro in citta' ma poligoni grandissimi (es. fiera) restano: l'area e' quella del poligono intero (puo' sporgere di poco)
off["classe"] = off.tipo.map(lambda t: "in struttura/sotterraneo" if t in ("multi-storey", "underground", "rooftop") else ("coperto (carport/garage)" if t in ("carports", "garage_boxes", "sheds") else "a raso"))
_u = unary_union([g for g in (r["geom"] for r in OFF) if True]).intersection(CITY)
RIEP["osm_fuori_strada_unione_km2"] = round(_u.area / 1e6, 2)
RIEP["osm_fuori_strada"] = {
    "n_poligoni": int(len(off)), "area_km2": round(off.area.sum() / 1e6, 2),
    "per_classe": {c: {"n": int(len(g)), "area_km2": round(g.area.sum() / 1e6, 3), "capacita_dichiarata": int(g.cap.fillna(0).sum()), "n_con_capacita": int(g.cap.notna().sum())} for c, g in off.groupby("classe")},
    "access_privato_o_clienti_quota_area_pct": round(100 * off[off.access.isin(["private", "customers", "permit", "no", "delivery"])].area.sum() / off.area.sum(), 1),
    "access_non_indicato_quota_area_pct": round(100 * off[off.access.isna()].area.sum() / off.area.sum(), 1)}
RIEP["osm_su_strada_mappata"] = {
    "aree_street_side_lane_n": int(len(on)), "aree_area_km2": round(on.area.sum() / 1e6, 3), "stalli_equivalenti_a_12m2": round(on.area.sum() / M2_STALLO),
    "capacita_dichiarata": int(on.cap.fillna(0).sum()), "stalli_singoli_parking_space_in_citta": int(len(sp)),
    "stalli_singoli_street_side_o_lane": int(sp.tipo.isin(["street_side", "lane"]).sum())}
print(json.dumps(RIEP["osm_fuori_strada"], ensure_ascii=False)); print(json.dumps(RIEP["osm_su_strada_mappata"], ensure_ascii=False))
# nodi parcheggio: ingressi di parcheggi sotterranei e in struttura (nessuna capacita')
ent = [n for n in osm["parking_nodes"] if n["tags"].get("amenity") == "parking_entrance"]
ex, ey = utm_ll(np.array([n["lon"] for n in ent]), np.array([n["lat"] for n in ent]))
ent_nil = nil_of_points(ex, ey)
RIEP["osm_ingressi_parcheggi"] = {"n_in_citta": int((ent_nil >= 0).sum())}
gar = [w for w in osm["parking_ways"] if w["tags"].get("building") in ("garages",) or w["tags"].get("landuse") == "garages"]
gg = [geom_of(w) for w in gar]; gg = [g for g in gg if g.geom_type in ("Polygon", "MultiPolygon")]
gc = shapely.centroid(np.array(gg, dtype=object)); gn = nil_of_points(shapely.get_x(gc), shapely.get_y(gc))
RIEP["osm_garage_edifici"] = {"n_in_citta": int((gn >= 0).sum()), "area_km2": round(float(sum(g.area for g, n in zip(gg, gn) if n >= 0)) / 1e6, 3), "nota": "building=garages: box/garage privati mappati; la mappatura e' molto incompleta"}

# per NIL OSM
def agg_nil(df, col="area"):
    return df.groupby("nil")[col].sum().reindex(nil_ids, fill_value=0)
st_nil["osm_fuori_strada_a_raso_km2"] = agg_nil(off[off.classe == "a raso"]) / 1e6
st_nil["osm_fuori_strada_struttura_km2"] = agg_nil(off[off.classe != "a raso"]) / 1e6
st_nil["osm_fuori_strada_capacita_dichiarata"] = off.groupby("nil").cap.sum().reindex(nil_ids, fill_value=0)
st_nil["osm_su_strada_mappato_stalli_equiv"] = agg_nil(on) / M2_STALLO
st_nil["osm_ingressi_parcheggi"] = pd.Series(ent_nil[ent_nil >= 0]).value_counts().reindex(nil_ids, fill_value=0)

# ---------------------------------------------------------------- parcheggi ufficiali (Comune)
pk = pd.read_csv(os.path.join(RAW, "comune_ds342", "ds342_park_pub.csv"), sep=";")
px, py = utm_ll(pk.LONG_X_4326.values, pk.LAT_Y_4326.values); pk["nil"] = nil_of_points(px, py)
ic = pd.read_csv(os.path.join(RAW, "comune_ds45", "ds45_park_interscambio.csv"), sep=";")
ic["posti"] = ic.TAB1.str.extract(r"(\d+)")[0].astype(int)
ix, iy = utm_ll(ic.LONG_X_4326.values, ic.LAT_Y_4326.values); ic["nil"] = nil_of_points(ix, iy)
assert (pk.nil >= 0).all()
pk_out = pk[["id", "nome", "n_posti", "indirizzo", "tipo", "nil"]].copy()
pk_out.to_csv(os.path.join(PU, "parcheggi_ufficiali.csv"), index=False, sep=";")
ic_out = ic[["Nome", "posti", "TAB1", "INFO", "Zona", "indirizzo", "nil", "LONG_X_4326", "LAT_Y_4326"]].copy()
ic_out.to_csv(os.path.join(PU, "interscambio.csv"), index=False, sep=";")
st_nil["posti_parcheggi_pubblici_ds342"] = pk.groupby("nil").n_posti.sum().reindex(nil_ids, fill_value=0)
st_nil["posti_interscambio_ds45"] = ic[ic.nil >= 0].groupby("nil").posti.sum().reindex(nil_ids, fill_value=0)
RIEP["ufficiali"] = {
    "ds342_parcheggi_pubblici": {"n": int(len(pk)), "posti": int(pk.n_posti.sum()), "per_tipo": {t: {"n": int(len(g)), "posti": int(g.n_posti.sum())} for t, g in pk.groupby("tipo")}},
    "ds45_interscambio": {"n_totale": int(len(ic)), "posti_totale": int(ic.posti.sum()), "n_in_citta": int((ic.nil >= 0).sum()), "posti_in_citta": int(ic[ic.nil >= 0].posti.sum()),
                          "fuori_comune": ic[ic.nil < 0].Nome.tolist(), "posti_fuori_comune": int(ic[ic.nil < 0].posti.sum()), "occupazione_pubblicata": False}}
print(json.dumps(RIEP["ufficiali"], ensure_ascii=False))

# ---------------------------------------------------------------- ciclabili (ds60) e aree pedonali (ds51)
cy = json.load(open(os.path.join(RAW, "comune_ds60", "bike_ciclabili.geojson"), encoding="utf8"))
LARG = {("ciclabile segnaletica", "monodirezionale"): 1.5, ("ciclabile segnaletica", "bidirezionale"): 2.5,
        ("ciclabile sede propria", "monodirezionale"): 1.5, ("ciclabile sede propria", "bidirezionale"): 2.5}
cg, cmeta = [], []
for f in cy["features"]:
    p = f["properties"]
    if p["tipologia"] not in ("ciclabile segnaletica", "ciclabile sede propria") or p["sede"] == "attraversamento":
        continue
    cg.append(to_utm(shape(f["geometry"]))); cmeta.append((p["tipologia"], "bidirezionale" if p["marcia"] == "bidirezionale" else "monodirezionale"))
cg = np.array(cg, dtype=object)
ci, cj = tree.query(cg, predicate="intersects")
cp = shapely.intersection(cg[ci], nil_geoms[cj]); cl = shapely.length(cp)
cdf = pd.DataFrame({"nil": np.array(nil_ids)[cj], "tipologia": [cmeta[i][0] for i in ci], "marcia": [cmeta[i][1] for i in ci], "len": cl})
cdf["larg"] = [LARG[(a, b)] for a, b in zip(cdf.tipologia, cdf.marcia)]
cdf["area"] = cdf.len * cdf.larg
RIEP["ciclabili"] = {"km_totali": round(cdf.len.sum() / 1000, 1), "area_stimata_km2": round(cdf.area.sum() / 1e6, 3),
                     "per_tipologia_km": {k: round(v / 1000, 1) for k, v in cdf.groupby("tipologia").len.sum().items()},
                     "larghezze_ipotizzate_m": {f"{a} / {b}": v for (a, b), v in LARG.items()},
                     "nota": "ds60 Itinerari ciclabili: solo 'ciclabile segnaletica' (corsie) e 'ciclabile sede propria' (piste), escluse le traversate; i percorsi promiscui con i pedoni non contano. Larghezze ipotizzate da me (dati del Comune non le contengono)."}
st_nil["ciclabili_km"] = cdf.groupby("nil").len.sum().reindex(nil_ids, fill_value=0) / 1000
st_nil["ciclabili_area_stima_km2"] = cdf.groupby("nil").area.sum().reindex(nil_ids, fill_value=0) / 1e6
print(json.dumps(RIEP["ciclabili"], ensure_ascii=False))

pe = json.load(open(os.path.join(RAW, "comune_ds51", "disciplina_aree.geojson"), encoding="utf8"))
ap = unary_union([to_utm(shape(f["geometry"])) for f in pe["features"] if f["properties"]["tipo"] == "AP"]).intersection(CITY)
ztl = unary_union([to_utm(shape(f["geometry"])) for f in pe["features"] if f["properties"]["tipo"] in ("ZTL", "AREA_C")]).intersection(CITY)
RIEP["aree_pedonali"] = {"area_km2": round(ap.area / 1e6, 3), "n_aree": int(sum(1 for f in pe["features"] if f["properties"]["tipo"] == "AP")),
                         "nota": "ds51 tipo AP (aree pedonali urbane), unione dei poligoni; sono i poligoni del Comune, vere strade/piazze chiuse alle auto, non i marciapiedi"}
st_nil["aree_pedonali_km2"] = [AP_i.area / 1e6 if not AP_i.is_empty else 0.0 for AP_i in (ap.intersection(NIL[i]) for i in nil_ids)]
print(RIEP["aree_pedonali"])

# ---------------------------------------------------------------- veicoli e verde
v529 = pd.read_csv(os.path.join(RAW, "comune_veicoli", "ds529.csv"), sep=";")
v = v529[(v529["Tipo consistenza veicoli"] == "Parco veicolare circolante") & v529.Attributo.str.contains("Autovetture")].set_index("Anno").Valore
RIEP["auto"] = {"autovetture_2025_ds529": int(v[2025]), "autovetture_2024_ds529": int(v[2024]), "autovetture_2023_ds529": int(v[2023]), "autovetture_2024_aci": 699002,
                "motocicli_2025_ds529": int(v529[(v529.Anno == 2025) & (v529["Tipo consistenza veicoli"] == "Parco veicolare circolante") & v529.Attributo.str.contains("Motocicli")].Valore.iloc[0]),
                "serie_autovetture": {int(a): int(b) for a, b in v.sort_index().items()},
                "nota": "autovetture del PRA iscritte nel Comune (ds529 del Comune = ACI Autoritratto 2024: 699.002). Dato per quartiere: non esiste in forma aperta"}
verde = pd.read_csv(os.path.join(MD, "alberi", "raw", "comune_ds2926", "mq_verde_urbano_per_abitante_milano.csv"), sep=";")
RIEP["verde_mq_per_abitante_2023"] = float(verde.set_index("Anno").loc[2023].iloc[0])
ab = RIEP["citta"]["abitanti_2024"]
area_tot = TOT_STALLI * M2_STALLO / 1e6
RIEP["sintesi"] = {
    "area_stalli_su_strada_km2": round(area_tot, 2), "quota_citta_pct": round(100 * area_tot / city_km2, 2),
    "campi_calcio_7140m2": round(TOT_STALLI * M2_STALLO / 7140), "m2_per_abitante": round(TOT_STALLI * M2_STALLO / ab, 2),
    "m2_per_autovettura": round(TOT_STALLI * M2_STALLO / RIEP["auto"]["autovetture_2025_ds529"], 2),
    "stalli_su_strada_per_autovettura": round(TOT_STALLI / RIEP["auto"]["autovetture_2025_ds529"], 3),
    "autovetture_per_stallo": round(RIEP["auto"]["autovetture_2025_ds529"] / TOT_STALLI, 2),
    "autovetture_per_1000_abitanti": round(1000 * RIEP["auto"]["autovetture_2025_ds529"] / ab, 0),
    "rapporto_stalli_strada_su_ciclabili_area": round(area_tot / RIEP["ciclabili"]["area_stimata_km2"], 1),
    "rapporto_stalli_su_aree_pedonali_area": round(area_tot / RIEP["aree_pedonali"]["area_km2"], 1),
    "stalli_per_tipo": {k: round(TOT_STALLI * q / 100) for k, q in QUOTE.items()},
    "area_per_tipo_km2": {k: round(TOT_STALLI * q / 100 * M2_STALLO / 1e6, 3) for k, q in QUOTE.items()},
    "parcheggi_ufficiali_posti": RIEP["ufficiali"]["ds342_parcheggi_pubblici"]["posti"] + RIEP["ufficiali"]["ds45_interscambio"]["posti_in_citta"],
    "sensibilita_area_km2": {str(m): round(TOT_STALLI * m / 1e6, 2) for m in (10, 12, 15)}}
print(json.dumps(RIEP["sintesi"], ensure_ascii=False))

# ---------------------------------------------------------------- tabella per NIL
out = st_nil.copy()
out.insert(0, "nil", base.nome.reindex(out.index))
out["area_km2"] = base.area_km2.reindex(out.index); out["abitanti_2024"] = base.abitanti_2024.reindex(out.index)
inter = [NIL[i].intersection(AMB_U).area / 1e6 for i in out.index]
out["quota_area_in_ambiti_pct"] = np.minimum(100.0, 100 * np.array(inter) / (out.area_km2.values))
out["in_classifica"] = (out.abitanti_2024 >= 5000).astype(int)
out["area_stalli_stima_km2"] = out.posti_strada_stima * M2_STALLO / 1e6
out["quota_area_stalli_pct"] = 100 * out.area_stalli_stima_km2 / out.area_km2
out["m2_stalli_per_abitante"] = out.area_stalli_stima_km2 * 1e6 / out.abitanti_2024.replace(0, np.nan)
out["posti_per_abitante"] = out.posti_strada_stima / out.abitanti_2024.replace(0, np.nan)
out["km_strade_per_km2"] = (out.km_in_ambiti + out.km_fuori_ambiti) / out.area_km2
out.index.name = "id_nil"
out.round(4).to_csv(os.path.join(PU, "nil_parcheggi.csv"), sep=";")
print("somma stalli stimati", round(out.posti_strada_stima.sum()), "| area NIL sum", round(out.area_km2.sum(), 2))
top = out[out.in_classifica == 1].sort_values("quota_area_stalli_pct", ascending=False)
RIEP["nil_estremi"] = {"piu_alta_quota_area": top[["nil", "quota_area_stalli_pct", "posti_strada_stima"]].head(5).round(2).to_dict("records"),
                       "piu_bassa_quota_area": top[["nil", "quota_area_stalli_pct", "posti_strada_stima"]].tail(5).round(2).to_dict("records")}
cl = out[out.in_classifica == 1]
RIEP["nil_estremi"]["n_in_classifica"] = int(len(cl))
RIEP["nil_estremi"]["m2_per_abitante_mediano"] = round(float(cl.m2_stalli_per_abitante.median()), 2)
RIEP["nil_estremi"]["m2_per_abitante_min_max"] = [cl.nil[cl.m2_stalli_per_abitante.idxmin()], round(float(cl.m2_stalli_per_abitante.min()), 2), cl.nil[cl.m2_stalli_per_abitante.idxmax()], round(float(cl.m2_stalli_per_abitante.max()), 2)]
json.dump(RIEP, open(os.path.join(PU, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("ok")
