"""Pulizia CASTEL Milano (ds718) -> tabelle ordinate.
Uso: python -I -X utf8 build.py <antenne_dir> <milano_in_dati_dir>
Legge:  <A>/raw/comune_ds718/castel.csv (versione attuale, file del Comune ricaricato 8/6/2025)
        <A>/raw/wayback_ds718/*  (copie storiche Wayback Machine)
        <P>/citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson (88 NIL, sola lettura)
Scrive: <A>/pulito/impianti.csv, snapshot_impianti.csv, controlli_pulizia.json"""
import sys, os, json, glob
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

A, P = sys.argv[1], sys.argv[2]
OUT = os.path.join(A, "pulito")
L = {}

# ---------------- versione attuale
d = pd.read_csv(os.path.join(A, "raw", "comune_ds718", "castel.csv"), sep=";", dtype=str, keep_default_na=False)
L["righe_grezze"] = len(d)
for c in d.columns:
    d[c] = d[c].map(fix_moji).str.strip()
L["id_duplicati"] = int(d.Sit_IDCodiceImpianto.duplicated().sum())
t = pd.DataFrame({
    "id_impianto": d.Sit_IDCodiceImpianto, "nome": d.Sit_NomeImpianto, "gestore": d.gestore, "tipo": d.Ti_TipoImpianto, "stato": d.Sit_StatoImpianto,
    "potenza_classe_W": d["Potenza (W)"].replace("", np.nan), "indirizzo": d.INDIRIZZO, "cap": d.CAP.replace("", np.nan), "municipio_file": d.MUNICIPIO.replace("", np.nan),
    "id_nil_file": d.ID_NIL.replace("", np.nan), "nil_file": d.NIL.replace("", np.nan),
    "lon": pd.to_numeric(d.LONG_X_4326), "lat": pd.to_numeric(d.LAT_Y_4326)})
gg = [classifica(g, tp) for g, tp in zip(t.gestore, t.tipo)]
t["gruppo_gestore"] = [x[0] for x in gg]
t["categoria"] = [x[1] for x in gg]
t["acceso"] = t.stato.str.startswith("Acceso")
t["previsto"] = t.stato.str.startswith("Previsto")
t["procedura_scia"] = t.stato.str.contains("SCIA")
t["segnalazione_parere"] = np.select([t.stato.str.contains("non rispetto limiti"), t.stato.str.contains("parere negativo"), t.stato.str.contains("incoerenza grave")],
                                      ["ultimo parere: non rispetto limiti", "ultimo parere negativo", "incoerenza grave"], "")
t["suffisso_id"] = t.id_impianto.str[-3:]
t["sito_id"] = (t.lon.round(6).astype(str) + "," + t.lat.round(6).astype(str)).where(t.lon.notna() & t.lat.notna())
L["siti_unici_per_coordinate"] = int(t.sito_id.nunique())
L["righe_senza_coordinate"] = int(t.lon.isna().sum())
L["coordinate_fuori_Milano_bbox"] = int(((t.lon.notna()) & (t.lon < 8.99) | (t.lon > 9.33) | (t.lat < 45.35) | (t.lat > 45.57)).sum())

polys, ids, names = load_nil(P)
nid, nn, meto, areas = assegna_nil(t.lon.values, t.lat.values, polys, ids, names)
t["id_nil"] = nid
t["nil"] = nn
t["metodo_nil"] = meto
L["nil_metodo"] = pd.Series(meto).value_counts().to_dict()
ok = t.id_nil_file.notna() & t.id_nil.notna()
L["nil_file_vs_poligono_coincidono_pct"] = round(float((t[ok].id_nil_file.astype(int) == t[ok].id_nil.astype(int)).mean() * 100), 2)
L["nil_file_vs_poligono_righe_diverse"] = int((t[ok].id_nil_file.astype(int) != t[ok].id_nil.astype(int)).sum())
L["righe_senza_nil_nel_file"] = int(t.id_nil_file.isna().sum())
L["righe_senza_nil_poligono"] = int(t.id_nil.isna().sum())
L["nil_distinti_con_impianti"] = int(t.id_nil.nunique())
L["gruppi_altro_elenco"] = sorted(t[t.categoria.str.startswith("altro")].gestore.unique().tolist())
L["gruppi_radiotv_elenco"] = sorted(t[t.categoria == "radio e TV"].gestore.unique().tolist())
L["categoria_conteggi"] = t.categoria.value_counts().to_dict()
t.to_csv(os.path.join(OUT, "impianti.csv"), sep=";", index=False, encoding="utf-8")

# ---------------- snapshot storici
snaps = []


def add(label, quando, nota, df):
    df = df.copy()
    df.insert(0, "snapshot", label)
    df.insert(1, "data_copia", quando)
    df.insert(2, "nota", nota)
    snaps.append(df)


def norm_csv(path):
    x = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)
    for c in x.columns:
        x[c] = x[c].map(fix_moji).str.strip()
    return pd.DataFrame({"id_impianto": x.Sit_IDCodiceImpianto, "nome": x.Sit_NomeImpianto, "gestore": x.gestore, "tipo": x.Ti_TipoImpianto, "stato": x.Sit_StatoImpianto,
                         "indirizzo": x.INDIRIZZO, "id_nil_file": x.ID_NIL, "lon": pd.to_numeric(x.LONG_X_4326), "lat": pd.to_numeric(x.LAT_Y_4326)})


W = os.path.join(A, "raw", "wayback_ds718")
j = pd.DataFrame(json.load(open(glob.glob(os.path.join(W, "wayback_20210122*"))[0], encoding="utf-8")))
s1 = pd.DataFrame({"id_impianto": "", "nome": j.Sit_NomeImpianto, "gestore": j.gestore, "tipo": j.Ti_TipoImpianto, "stato": j.Sit_StatoImpianto, "indirizzo": j.INDIRIZZO,
                   "id_nil_file": j.ID_NIL.astype(str).replace("nan", ""), "lon": pd.to_numeric(j.LONG_X_WGS84), "lat": pd.to_numeric(j.LAT_Y_WGS84)})
add("2020-21", "2021-01-22", "copia Wayback 22/1/2021 (la copia del 27/9/2020 ha gli stessi 1.793 impianti); senza codice impianto", s1)
add("2023-01", "2024-05-02", "file del Comune 'impianti_20230124' (data nel nome), copia Wayback 2/5/2024", norm_csv(glob.glob(os.path.join(W, "wayback_20240502*"))[0]))
add("2024-05", "2024-05-15", "copia Wayback 15/5/2024", norm_csv(glob.glob(os.path.join(W, "wayback_20240515*"))[0]))
add("2024-06", "2024-06-15", "copia Wayback 15/6/2024", norm_csv(glob.glob(os.path.join(W, "wayback_20240615*"))[0]))
add("2025-06", "2025-06-08", "file attuale del Comune (ricaricato 8/6/2025); uguale byte per byte alla copia Wayback 24/2/2026",
    t[["id_impianto", "nome", "gestore", "tipo", "stato", "indirizzo", "id_nil_file", "lon", "lat"]])
S = pd.concat(snaps, ignore_index=True)
gg = [classifica(g, tp) for g, tp in zip(S.gestore, S.tipo)]
S["gruppo_gestore"] = [x[0] for x in gg]
S["categoria"] = [x[1] for x in gg]
S["acceso"] = S.stato.str.startswith("Acceso")
S["previsto"] = S.stato.str.startswith("Previsto")
S["procedura_scia"] = S.stato.str.contains("SCIA")
S["tipo"] = S.tipo.replace({"WiFi": "Wireless"})
L["snapshot_righe"] = S.groupby("snapshot").size().to_dict()
L["snapshot_tipi"] = {k: v.tipo.value_counts().to_dict() for k, v in S.groupby("snapshot")}
S.to_csv(os.path.join(OUT, "snapshot_impianti.csv"), sep=";", index=False, encoding="utf-8")
json.dump(L, open(os.path.join(OUT, "controlli_pulizia.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in L.items() if k not in ("gruppi_altro_elenco", "gruppi_radiotv_elenco", "snapshot_tipi")}, ensure_ascii=False, indent=1))
print("ALTRO:", L["gruppi_altro_elenco"])
print("RADIOTV:", L["gruppi_radiotv_elenco"])
