"""Pulizia dei 5 dataset 'Edilizia' del Comune (ds270, ds271, ds2983, ds2984, ds2985) in una tabella unica.
Uso: python -I -X utf8 build_titoli.py <costruzioni (assoluto)> <milano-in-dati (assoluto)>
Scrive: pulito/titoli_edilizi.csv, pulito/controlli_titoli.json
Niente viene cancellato: le stranezze sono segnalate con flag. Nomi di persone: non esistono nei file (solo la categoria del titolare).
"""
import sys, os, re, json, glob
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from pyproj import Transformer

C, P = sys.argv[1], sys.argv[2]
log = {}

def fix(s):
    """mojibake 'Ã\xa0' -> 'à' ecc. (file UTF-8 salvato due volte)"""
    if not isinstance(s, str): return s
    if "Ã" in s or "Â" in s:
        try: return s.encode("latin1").decode("utf-8")
        except Exception: return s
    return s

def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", ".").str.strip(), errors="coerce")

# ---------------- lettura e unificazione
def read(path):
    d = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8")
    for c in d.columns: d[c] = d[c].map(fix)
    return d

F = {
    "ds270": ("raw/comune_ds270/ds270_edilizia_nuovi_fabbricati_uso_residenziale.csv", "residenziale", "nuovo_fabbricato"),
    "ds271": ("raw/comune_ds271/ds271_edilizia_ampliamenti_uso_residenziale.csv", "residenziale", "ampliamento"),
    "ds2984": ("raw/comune_ds2984/ds2984_edilizia_nuovi_fabbricati_uso_non_residenziale.csv", "non_residenziale", "nuovo_fabbricato"),
    "ds2985": ("raw/comune_ds2985/ds2985_edilizia_ampliamenti_uso_non_residenziale.csv", "non_residenziale", "ampliamento"),
    "ds2983": ("raw/comune_ds2983/ds2983_edilizia_fabbricati_collettivita.csv", "collettivita", None),
}
parts = []
for k, (rel, uso, interv) in F.items():
    d = read(os.path.join(C, rel))
    o = pd.DataFrame(index=d.index)
    o["dataset"] = k
    o["id_modello"] = d["Codice Modello"]
    o["anno"] = pd.to_numeric(d["Anno Ritiro"], errors="coerce").astype("Int64")
    o["mese"] = pd.to_numeric(d["Mese Ritiro"], errors="coerce").astype("Int64")
    o["uso"] = uso
    if interv: o["intervento"] = interv
    else: o["intervento"] = d["Tipologia Collettivita'"].map(lambda v: "ampliamento" if isinstance(v, str) and v.lower().startswith("amplia") else "nuovo_fabbricato")
    o["tipo_titolo"] = d["Titolo Abilitativo"].map(lambda v: {"permesso di costruire": "Permesso di costruire", "scia": "SCIA", "scia alternativa": "SCIA alternativa"}.get(str(v).strip().lower(), None))
    ab = d["Abbattimento e ricostruzione"] if "Abbattimento e ricostruzione" in d else pd.Series(np.nan, index=d.index)
    o["abbattimento_ricostruzione"] = ab.map(lambda v: {"si": "si", "no": "no"}.get(str(v).strip().lower(), ""))
    o["titolare_categoria"] = d["Titolare Titolo Abilitativo"].map(lambda v: re.sub(r"\s+", " ", str(v)).strip() if isinstance(v, str) else "")
    o["titolare_categoria"] = o["titolare_categoria"].replace({"Impresa / Societa": "Impresa / Società", "Impresa / SocietÃ": "Impresa / Società"})
    o["indirizzo"] = d["Indirizzo"].fillna("").str.strip()
    o["civico"] = d["Numero Civico"].fillna("").str.strip()
    o["sezione_censimento"] = d["Sezione Censimento"]
    o["municipio_file"] = pd.to_numeric(d["MUNICIPIO"], errors="coerce").astype("Int64")
    o["id_nil_file"] = pd.to_numeric(d["ID_NIL"], errors="coerce").astype("Int64")
    o["nil_file"] = d["NIL"].fillna("")
    o["lon"] = num(d["LONG_X_4326"]); o["lat"] = num(d["LAT_Y_4326"])
    if k == "ds270" or k == "ds2984":
        o["abitazioni"] = num(d["Numero Abitazioni"]); o["piani"] = num(d["Numero Piani"])
        o["volume_m3"] = num(d["Volume Totale V/p"]); o["superficie_m2"] = num(d["Superficie Totale Fabbricato"])
    elif k == "ds271":
        o["abitazioni"] = num(d["Numero Abitazioni Ampliamento B1"]); o["piani"] = np.nan
        o["volume_m3"] = num(d["Volume Ampliamento"]); o["superficie_m2"] = num(d["Superficie Totale Ampliamento"])
    elif k == "ds2985":
        o["abitazioni"] = num(d["Numero Abitazioni Ampliamento"]); o["piani"] = np.nan
        o["volume_m3"] = num(d["Volume Ampliamento"]); o["superficie_m2"] = num(d["Superficie Totale Ampliamento"])
    else:
        o["abitazioni"] = np.nan; o["piani"] = num(d["Numero Piani Collettivita'"])
        o["volume_m3"] = num(d["Volume Totale Collettivita'"]); o["superficie_m2"] = num(d["Superficie Totale Collettivita'"])
    o["sopraelevazione"] = d["Sopraelevazione"].map(lambda v: "si" if str(v).strip().lower() == "si" else "") if "Sopraelevazione" in d else ""
    o["destinazione_economica"] = d["Destinazione Economica Fabbricato"].fillna("") if "Destinazione Economica Fabbricato" in d else ""
    o["tipologia_fabbricato"] = d["Tipologia Fabbricato"].fillna("") if "Tipologia Fabbricato" in d else ""
    o["piano_casa"] = d["Piano Casa"].fillna("") if "Piano Casa" in d else ""
    parts.append(o)
t = pd.concat(parts, ignore_index=True)
log["righe_per_dataset"] = t.dataset.value_counts().to_dict()
log["righe_totali"] = len(t)
log["id_modello_duplicati"] = int(t.id_modello.duplicated().sum())
log["righe_completamente_duplicate"] = int(t.drop(columns=["dataset"]).duplicated().sum())

# ---------------- geocodifica dei record senza coordinate (strada + civico dai civici del filone citta-15-minuti)
cv = pd.read_csv(os.path.join(P, "citta-15-minuti", "out", "civici_tempi.csv"), usecols=["CODICE_VIA", "NUMEROCOMPLETO", "DENOMINAZIONE", "ID_NIL", "lon", "lat"], dtype={"NUMEROCOMPLETO": str})
STOP = {"via", "viale", "v", "vle", "piazza", "p", "piazzale", "pzza", "largo", "l", "go", "corso", "c", "so", "vicolo", "strada", "str", "alzaia", "bastioni", "foro", "ripa", "angolo", "san", "santa", "sant", "e", "ed", "del", "della", "di", "de", "dei", "degli", "delle", "da", "la", "lo", "il", "i", "gli", "le", "area", "ex", "snc", "lotto", "ang"}
def toks(s):
    s = re.sub(r"\(.*?\)", " ", str(s).lower())
    s = re.sub(r"[^a-zàèéìòù0-9 ]", " ", s)
    return [w for w in s.split() if w not in STOP and len(w) > 1 and not w.isdigit()]
cv["tk"] = cv.DENOMINAZIONE.map(lambda s: frozenset(toks(s)))
vie = cv.groupby("CODICE_VIA").agg(tk=("tk", "first"), n=("lon", "size")).reset_index()
def norm_civ(s):
    s = str(s).upper().strip()
    m = re.match(r"^0*(\d+)\s*([A-Z]?)", s)
    return (m.group(1) + m.group(2)) if m else ""
cv["civ"] = cv.NUMEROCOMPLETO.map(norm_civ)
t["geo_metodo"] = np.where(t.lon.notna(), "file", "")
miss = t.index[t.lon.isna()]
ok = {"civico": 0, "via": 0, "no": 0}
for i in miss:
    a = toks(t.at[i, "indirizzo"].split(" angolo ")[0].split("/")[0].split(" - ")[0])
    if not a: ok["no"] += 1; continue
    a = set(a)
    cand = vie[vie.tk.map(lambda s: len(s) > 0 and a <= s)]
    if len(cand) == 0:
        cand = vie[vie.tk.map(lambda s: len(s) > 0 and s <= a and len(s) >= 1 and len(a) <= len(s) + 1)]
    if len(cand) != 1: ok["no"] += 1; continue
    sub = cv[cv.CODICE_VIA == cand.iloc[0].CODICE_VIA]
    civ = norm_civ(t.at[i, "civico"])
    m = sub[sub.civ == civ] if civ and civ != "0" else sub.iloc[0:0]
    if len(m):
        t.at[i, "lon"], t.at[i, "lat"] = m.lon.iloc[0], m.lat.iloc[0]; t.at[i, "geo_metodo"] = "civico_da_indirizzo"; ok["civico"] += 1
    else:
        nn = sub.ID_NIL.dropna()
        if len(nn) and (nn.value_counts(normalize=True).iloc[0] >= 0.8):
            t.at[i, "lon"], t.at[i, "lat"] = sub.lon.median(), sub.lat.median(); t.at[i, "geo_metodo"] = "via_da_indirizzo"; ok["via"] += 1
        else: ok["no"] += 1
log["senza_coordinate_nel_file"] = int(len(miss)); log["geocodifica_da_indirizzo"] = ok

# ---------------- NIL (punto in poligono, 88 NIL vigenti, come in alberi/)
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
polys = [shape(f["geometry"]) for f in g["features"]]
ids = [int(f["properties"]["ID_NIL"]) for f in g["features"]]
names = [f["properties"]["NIL"] for f in g["features"]]
st = STRtree(polys)
has = t.lon.notna()
pts = shapely.points(t.lon[has].values, t.lat[has].values)
pi, gi = st.query(pts, predicate="within")
idx = np.full(has.sum(), -1)
for a, b in zip(pi, gi): idx[a] = b
tr = Transformer.from_crs(4326, 32632, always_xy=True)
out = np.where(idx < 0)[0]
near = 0
if len(out):
    polys_m = [shapely.transform(p, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1]))) for p in polys]
    xm, ym = tr.transform(t.lon[has].values[out], t.lat[has].values[out])
    ni, dm = STRtree(polys_m).query_nearest(shapely.points(xm, ym), return_distance=True)
    for a, j, d_ in zip(ni[0], ni[1], dm):
        if d_ <= 100: idx[out[a]] = j; near += 1
log["punti_fuori_da_ogni_NIL"] = int(len(out)); log["di_cui_assegnati_entro_100m"] = near
t["id_nil"] = pd.Series(pd.NA, index=t.index, dtype="Int64"); t["nil"] = ""
hi = t.index[has]
t.loc[hi, "id_nil"] = [ids[i] if i >= 0 else pd.NA for i in idx]
t.loc[hi, "nil"] = [names[i] if i >= 0 else "" for i in idx]
# controllo con il NIL scritto nel file
both = t[(t.geo_metodo == "file") & t.id_nil.notna() & t.id_nil_file.notna()]
log["controllo_nil_file_vs_calcolato"] = {"confrontati": int(len(both)), "uguali": int((both.id_nil == both.id_nil_file).sum()),
                                           "diversi": int((both.id_nil != both.id_nil_file).sum())}
log["senza_NIL_dopo_tutto"] = int(t.id_nil.isna().sum())

# ---------------- flag
t["flag_anno_fuori_serie"] = ((t.anno < 2014) | t.anno.isna()).astype(int)   # le serie dichiarano 2014-2024: i pochi record 2010-2012 sono ritardi
t["flag_titolo_mancante"] = t.tipo_titolo.isna().astype(int)
t["flag_abitazioni_oltre_300"] = (t.abitazioni > 300).astype(int)
t["flag_volume_zero_o_mancante"] = ((t.volume_m3.isna()) | (t.volume_m3 <= 0)).astype(int)
t["flag_stessa_posizione_anno_altro_record"] = t.duplicated(["indirizzo", "civico", "anno", "intervento", "uso"], keep=False).astype(int)
# indirizzo mostrabile in una pagina? No se il titolare e' una persona fisica o l'intervento e' un piccolo ampliamento residenziale (rischio di identificare privati)
t["indirizzo_pubblicabile"] = (~t.titolare_categoria.str.contains("Persona fisica", na=False) &
                               ~((t.uso == "residenziale") & (t.intervento == "ampliamento"))).astype(int)
log["flag"] = {c: int(t[c].sum()) for c in t.columns if c.startswith("flag_")}
log["indirizzo_non_pubblicabile"] = int((t.indirizzo_pubblicabile == 0).sum())

# titolare "Altro": specifica non tenuta (puo' contenere nomi): non copiata
t = t.drop(columns=["sezione_censimento"]) if False else t
cols = ["dataset", "id_modello", "anno", "mese", "uso", "intervento", "tipo_titolo", "abbattimento_ricostruzione", "titolare_categoria",
        "abitazioni", "piani", "volume_m3", "superficie_m2", "sopraelevazione", "destinazione_economica", "tipologia_fabbricato", "piano_casa",
        "indirizzo", "civico", "indirizzo_pubblicabile", "municipio_file", "id_nil_file", "nil_file", "id_nil", "nil", "lon", "lat", "geo_metodo",
        "sezione_censimento", "flag_anno_fuori_serie", "flag_titolo_mancante", "flag_abitazioni_oltre_300", "flag_volume_zero_o_mancante", "flag_stessa_posizione_anno_altro_record"]
os.makedirs(os.path.join(C, "pulito"), exist_ok=True)
t[cols].to_csv(os.path.join(C, "pulito", "titoli_edilizi.csv"), index=False, sep=";", encoding="utf-8")
json.dump(log, open(os.path.join(C, "pulito", "controlli_titoli.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(log, ensure_ascii=False, indent=1, default=str))
