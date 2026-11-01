"""Pulizia del censimento alberi del Comune di Milano (ds2484), 3 edizioni -> pulito/alberi.csv

Uso (percorsi assoluti):
  python -I -X utf8 build.py <alberi_dir> <progetto_milano_in_dati_dir>

Legge:
  <alberi_dir>/raw/comune_ds2484/wayback_ed2023/x/ds2484_alberi_20230331.csv   (edizione 31/3/2023, copia Wayback Machine)
  <alberi_dir>/raw/comune_ds2484/ed2024_geojson/ds2484_alberi_20240331.geojson (edizione 31/3/2024)
  <alberi_dir>/raw/comune_ds2484/ed2025_csv/ds2484_alberi_20250331.csv         (edizione 31/3/2025)
  <progetto>/citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson (88 NIL, sola lettura)
  <progetto>/citta-15-minuti/out/civici_tempi.csv (civici con CAP stimato, sola lettura)
Scrive: pulito/alberi.csv, pulito/controlli_pulizia.json
"""
import sys, os, json
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape
from shapely import STRtree
from pyproj import Transformer
from scipy.spatial import cKDTree

A, P = sys.argv[1], sys.argv[2]
RAW = os.path.join(A, "raw", "comune_ds2484")
ED = {
    "2023-03-31": ("csv", os.path.join(RAW, "wayback_ed2023", "x", "ds2484_alberi_20230331.csv"),
                   "ds2484 CSV edizione 31/3/2023 (copia Wayback Machine del file del Comune, snapshot 6/5/2024)"),
    "2024-03-31": ("geojson", os.path.join(RAW, "ed2024_geojson", "ds2484_alberi_20240331.geojson"),
                   "ds2484 GeoJSON edizione 31/3/2024 (dati.comune.milano.it, scaricato 1/11/2026)"),
    "2025-03-31": ("csv", os.path.join(RAW, "ed2025_csv", "ds2484_alberi_20250331.csv"),
                   "ds2484 CSV edizione 31/3/2025 (dati.comune.milano.it, scaricato 1/11/2026)"),
}
COLS = ["id_area", "municipio", "area", "localita", "obj_id", "codice", "data_ini", "genere", "specie", "varieta",
        "diam_tronc", "diam_chiom", "h_m", "LONG_X_4326", "LAT_Y_4326"]
log = {}


def load(ed):
    kind, path, _ = ED[ed]
    if kind == "csv":
        d = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False, usecols=COLS)
    else:
        g = json.load(open(path, encoding="utf-8"))
        rows = []
        for f in g["features"]:
            p = f["properties"]
            r = {c: p.get(c) for c in COLS}
            # la geometria e' la fonte piu' sicura per le coordinate (stesse del CSV a 1e-14)
            r["geom_lon"], r["geom_lat"] = f["geometry"]["coordinates"][:2]
            rows.append(r)
        d = pd.DataFrame(rows)
        log["geojson_2024_feature"] = len(d)
        diff = (pd.to_numeric(d.LONG_X_4326) - d.geom_lon).abs().max()
        log["geojson_2024_diff_max_lon_prop_vs_geom"] = float(diff)
        d = d.drop(columns=["geom_lon", "geom_lat"]).fillna("")
    d["edizione"] = ed
    return d


frames = []
for ed in ED:
    d = load(ed)
    log[f"righe_grezze_{ed}"] = len(d)
    frames.append(d)
t = pd.concat(frames, ignore_index=True)

# ---------- pulizia di base
for c in ["genere", "specie", "varieta", "localita", "id_area"]:
    t[c] = t[c].str.strip()
log["genere_vuoto"] = t[t.genere == ""].groupby("edizione").size().to_dict()
log["specie_con_maiuscola_o_punteggiatura (es. 'Red')"] = int(t.specie.str.contains(r"[A-Z.?/]").sum())
t["lon"] = pd.to_numeric(t.LONG_X_4326)
t["lat"] = pd.to_numeric(t.LAT_Y_4326)
t["diam_tronc_cm"] = pd.to_numeric(t.diam_tronc, errors="coerce")
t["diam_chioma_m"] = pd.to_numeric(t.diam_chiom, errors="coerce")
t["altezza_m"] = pd.to_numeric(t.h_m, errors="coerce")
t["data_ini"] = t.data_ini.str[:10]
t["id"] = t.obj_id
log["id_duplicati_nella_stessa_edizione"] = int(t.duplicated(["edizione", "id"]).sum())

# tassonomia
tx = pd.read_csv(os.path.join(A, "scripts", "taxonomia_genere.csv"), sep=";", dtype=str)
ns = pd.read_csv(os.path.join(A, "scripts", "nomi_specie.csv"), sep=";", dtype=str)
t = t.merge(tx, on="genere", how="left")
t = t.rename(columns={"nome_comune": "nome_comune_genere"})
t = t.merge(ns.rename(columns={"nome_comune": "nome_comune_specie"}), on=["genere", "specie"], how="left")
nd = t.genere == ""
t["famiglia"] = t.famiglia.fillna("n.d.")
t.loc[nd, "famiglia"] = "n.d."
t["specie_norm"] = t.specie_norm.fillna(t.specie)
t["specie_completa"] = np.where(nd, "n.d.", t.genere + " " + t.specie)
t["specie_norm_completa"] = np.where(nd, "n.d.", t.genere + " " + t.specie_norm)
gen_it = t.nome_comune_genere.fillna("")
t["nome_comune"] = np.where(nd, "n.d.",
                    np.where(t.nome_comune_specie.notna(), t.nome_comune_specie,
                    np.where(t.specie == "spp", gen_it + " (specie non indicata)", gen_it + " (" + t.genere + " " + t.specie + ")")))
log["genere_senza_famiglia_nel_dizionario"] = sorted(set(t[(~nd) & (t.famiglia == "n.d.")].genere))

# ---------- segnalazioni (valori non cancellati, solo marcati)
ed_date = t.edizione
t["flag_data"] = ""
t.loc[t.data_ini < "1900-01-01", "flag_data"] = "prima_del_1900"
t.loc[t.data_ini > ed_date, "flag_data"] = "dopo_edizione"
t["flag_misure"] = ""
t.loc[(t.diam_tronc_cm > 300), "flag_misure"] += "tronco>300cm;"
t.loc[(t.altezza_m > 50), "flag_misure"] += "altezza>50m;"
t.loc[(t.diam_chioma_m > 40), "flag_misure"] += "chioma>40m;"
t.loc[(t.diam_tronc_cm == 0), "flag_misure"] += "tronco=0;"
t.loc[(t.altezza_m == 0), "flag_misure"] += "altezza=0;"
t["flag_dup_posizione"] = t.duplicated(["edizione", "lon", "lat"], keep=False)
for ed in ED:
    s = t[t.edizione == ed]
    log[f"flag_{ed}"] = {"data_prima_1900": int((s.flag_data == "prima_del_1900").sum()),
                         "data_dopo_edizione": int((s.flag_data == "dopo_edizione").sum()),
                         "misure_segnalate": int((s.flag_misure != "").sum()),
                         "tronco_>300": int((s.diam_tronc_cm > 300).sum()),
                         "altezza_>50": int((s.altezza_m > 50).sum()),
                         "stessa_posizione_di_un_altro": int(s.flag_dup_posizione.sum()),
                         "senza_diam_tronc": int(s.diam_tronc_cm.isna().sum()),
                         "senza_altezza": int(s.altezza_m.isna().sum())}

# ---------- NIL (punto in poligono)
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
polys = [shape(f["geometry"]) for f in g["features"]]
ids = [int(f["properties"]["ID_NIL"]) for f in g["features"]]
names = [f["properties"]["NIL"] for f in g["features"]]
log["nil_poligoni"] = len(polys)
str_ = STRtree(polys)
u = t[["lon", "lat"]].drop_duplicates().reset_index(drop=True)
pts = shapely.points(u.lon.values, u.lat.values)
pi, gi = str_.query(pts, predicate="within")
nil_idx = np.full(len(u), -1)
cnt = np.zeros(len(u), int)
for a, b in zip(pi, gi):
    cnt[a] += 1
    nil_idx[a] = b
log["punti_unici"] = len(u)
log["punti_in_piu_di_un_NIL"] = int((cnt > 1).sum())
miss = np.where(cnt == 0)[0]
log["punti_fuori_da_ogni_NIL"] = int(len(miss))
# i fuori: NIL piu' vicino se entro 100 m
tr = Transformer.from_crs(4326, 32632, always_xy=True)
if len(miss):
    # distanza in metri: proiezione UTM 32N
    polys_m = [shapely.transform(p, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1]))) for p in polys]
    xm, ym = tr.transform(u.lon.values[miss], u.lat.values[miss])
    pmm = shapely.points(xm, ym)
    stm = STRtree(polys_m)
    ni, dm = stm.query_nearest(pmm, return_distance=True)
    # ni e' (2,n): indici input, indici albero
    out_m = []
    for a, j, d_ in zip(ni[0], ni[1], dm):
        out_m.append(d_)
        if d_ <= 100:
            nil_idx[miss[a]] = j
    out_m = np.array(out_m)
    log["fuori_NIL_ma_entro_100m_assegnati"] = int((out_m <= 100).sum())
    log["fuori_NIL_oltre_100m_non_assegnati"] = int((out_m > 100).sum())
    log["fuori_NIL_distanza_max_m"] = float(out_m.max())
u["ID_NIL"] = [ids[i] if i >= 0 else np.nan for i in nil_idx]
u["NIL"] = [names[i] if i >= 0 else "" for i in nil_idx]
u["assegnato_per_vicinanza"] = (cnt == 0) & (nil_idx >= 0)

# ---------- CAP stimato = CAP del civico piu' vicino (CAP dei civici gia' stimato dal filone 9)
cv = pd.read_csv(os.path.join(P, "citta-15-minuti", "out", "civici_tempi.csv"), usecols=["x", "y", "CAP", "CAP_dist_m"])
cv = cv[cv.CAP_dist_m <= 300]
log["civici_usati_per_CAP"] = len(cv)
kd = cKDTree(cv[["x", "y"]].values)
xu, yu = tr.transform(u.lon.values, u.lat.values)
dd, ii = kd.query(np.column_stack([xu, yu]), k=1)
u["CAP_stimato"] = cv.CAP.values[ii]
u.loc[dd > 250, "CAP_stimato"] = np.nan
u["dist_civico_m"] = dd.round(1)
log["punti_con_CAP"] = int(u.CAP_stimato.notna().sum())
log["distanza_civico_piu_vicino_mediana_m"] = float(np.median(dd))
t = t.merge(u, on=["lon", "lat"], how="left")

# ---------- coerenza con municipio dichiarato nel file
t["municipio_file"] = pd.to_numeric(t.municipio, errors="coerce")
log["controllo_municipio"] = "vedi analisi.py (confronto municipio_file con il municipio prevalente del NIL)"

t["fonte"] = "Comune di Milano ds2484 CC-BY"
out = t[["id", "edizione", "specie_completa", "specie_norm_completa", "genere", "specie", "varieta", "famiglia", "nome_comune",
         "lon", "lat", "diam_tronc_cm", "diam_chioma_m", "altezza_m", "data_ini", "municipio_file", "id_area", "localita",
         "ID_NIL", "NIL", "assegnato_per_vicinanza", "CAP_stimato", "flag_data", "flag_misure", "flag_dup_posizione", "fonte"]].copy()
out = out.rename(columns={"specie_completa": "specie_binomio", "specie_norm_completa": "specie_binomio_normalizzata",
                          "specie": "epiteto", "ID_NIL": "id_nil", "NIL": "nil", "CAP_stimato": "cap_stimato",
                          "data_ini": "data_inizio_scheda", "lon": "lon", "lat": "lat"})
out["id_nil"] = out.id_nil.astype("Int64")
out["cap_stimato"] = out.cap_stimato.astype("Int64")
os.makedirs(os.path.join(A, "pulito"), exist_ok=True)
out.to_csv(os.path.join(A, "pulito", "alberi.csv"), index=False, sep=";", encoding="utf-8")
for ed in ED:
    s = out[out.edizione == ed]
    log[f"righe_pulite_{ed}"] = len(s)
    log[f"senza_NIL_{ed}"] = int(s.id_nil.isna().sum())
json.dump(log, open(os.path.join(A, "pulito", "controlli_pulizia.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(log, ensure_ascii=False, indent=1, default=str))
