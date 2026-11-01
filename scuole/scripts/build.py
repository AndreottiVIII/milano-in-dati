"""Pulizia filone Scuole (fase 1).
Uso: python -I -X utf8 build.py <abs scuole> <abs milano-in-dati>
Legge raw/ (mai eseguito), scrive pulito/*.csv e pulito/controlli_pulizia.json.
Nessun valore viene corretto o cancellato: le stranezze sono segnalate con flag."""
import sys, os, re, json, glob, unicodedata
import pandas as pd, numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import addr_key

S, P = sys.argv[1], sys.argv[2]
RAW, OUT = f"{S}/raw", f"{S}/pulito"
os.makedirs(OUT, exist_ok=True)
CK = {}  # controlli

def as_label(y):  # 2024 -> 2024/2025
    return f"{y}/{y+1}"

# ------------------------------------------------------------------ NIL
nilj = json.load(open(f"{P}/citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson", encoding="utf-8"))
NIL_GEOMS = [shape(f["geometry"]) for f in nilj["features"]]
NIL_IDS = [int(f["properties"]["ID_NIL"]) for f in nilj["features"]]
NIL_NAMES = {int(f["properties"]["ID_NIL"]): f["properties"]["NIL"] for f in nilj["features"]}
TREE = STRtree(NIL_GEOMS)
def nil_pip(lon, lat):
    """(id_nil, metodo) -- punto in poligono; se fuori, il NIL piu' vicino entro 150 m."""
    if lon is None or lat is None or (isinstance(lon, float) and np.isnan(lon)): return None, "senza_coordinate"
    pt = Point(lon, lat)
    for i in TREE.query(pt):
        if NIL_GEOMS[i].contains(pt): return NIL_IDS[i], "poligono"
    j = TREE.nearest(pt)
    d = NIL_GEOMS[j].distance(pt) * 111000 * 0.8  # gradi -> metri circa a questa latitudine
    if d <= 150: return NIL_IDS[j], "vicinanza_150m"
    return None, "fuori_dai_NIL"

# ------------------------------------------------------------------ Comune: localizzazioni
def rd(path, sep=";"):
    d = pd.read_csv(path, sep=sep, dtype=str, encoding="utf-8")
    d.columns = [c.strip() for c in d.columns]
    return d
loc = []
for ds, ordine in [("ds671", "infanzia"), ("ds3014", "infanzia"), ("ds40", "primaria"), ("ds3015", "primaria"), ("ds46", "sec1"), ("ds3016", "sec1")]:
    f = glob.glob(f"{RAW}/comune_{ds}/*.csv")[0]
    d = rd(f)
    d = d.rename(columns={"ANNOSCOL": "anno", "CODICE": "codice", "INDIRIZZO": "indirizzo", "LONG_X_4326": "lon", "LAT_Y_4326": "lat", "ID_NIL": "id_nil_file", "DENOMINAZIONE": "den", "TIPO": "tipo", "PARITARIA": "paritaria_flag", "CAPIENZA": "capienza"})
    d["ordine"] = ordine; d["fonte_loc"] = ds
    loc.append(d[["anno", "codice", "indirizzo", "lon", "lat", "id_nil_file", "den", "tipo", "paritaria_flag", "ordine", "fonte_loc", "capienza"]])
LOC = pd.concat(loc, ignore_index=True)
LOC["lon"] = pd.to_numeric(LOC.lon, errors="coerce"); LOC["lat"] = pd.to_numeric(LOC.lat, errors="coerce")
LOC["anno_i"] = LOC.anno.str[:4].astype(int)
LOCL = LOC.sort_values("anno_i").groupby(["ordine", "codice"], as_index=False).last()  # ultima apparizione
CK["localizzazioni_comune_righe"] = int(len(LOC)); CK["localizzazioni_codici_unici"] = int(len(LOCL))

# ------------------------------------------------------------------ Comune ANASCO (ds224/225/226)
def norm_gest(g):
    g = g.strip().lower()
    return {"statale": "statale", "comunale": "comunale", "privata paritaria": "privata_paritaria", "privata non paritaria": "privata_non_paritaria"}[g]
GGRP = {"statale": "statale", "comunale": "paritaria", "privata_paritaria": "paritaria", "privata_non_paritaria": "non_paritaria"}
frames = []
for ds, ordine in [("ds224", "infanzia"), ("ds225", "primaria"), ("ds226", "sec1")]:
    f = glob.glob(f"{RAW}/comune_{ds}/*.csv")[0]
    d = rd(f)
    ren = {"Anno Scolastico": "anno_scolastico", "AnnoScolastico": "anno_scolastico", "Cod_Scuola": "codice_comune", "CodScuola": "codice_comune",
           "NIL_Scuola": "nil_file", "NilScuola": "nil_file", "MunicipioScuola": "municipio", "Numero_Classi": "classi", "Totale_Alunni": "iscritti", "Alunni_Tot": "iscritti",
           "Alunni_M": "maschi", "Alunni_F": "femmine", "Alunni_Resid_Milano": "residenti_milano", "Alunni_Resid": "residenti_milano", "Alunni_NonResid": "non_residenti",
           "Alunni_Nati_Italia": "nati_italia", "Alunni_NazNasc_Italia": "nati_italia",
           "Alunni _Cittadin_Italiana": "cittadinanza_italiana", "Alunni_Cittad_Ita": "cittadinanza_italiana",
           "Alunni_Cittad_Non_Ital": "cittadinanza_non_italiana", "Alunni_Cittad_Non_Ita": "cittadinanza_non_italiana", "Alunni_Cittad_NonDisp": "cittadinanza_nd",
           "Capienza": "capienza_file"}
    d = d.rename(columns=ren)
    # nati all'estero = tutte le colonne di area di nascita tranne Italia e "Altro/NonDisp"
    nasc = [c for c in d.columns if re.search(r"Nati|NazNasc", c) and c not in ("nati_italia",)]
    altro = [c for c in nasc if re.search(r"Altr[oi].*(Non|ND)|Altro_NonDisp|Altri Paesi/NonDisp", c)]
    estero = [c for c in nasc if c not in altro]
    num = lambda cols: d[cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
    d["nati_estero_aree_note"] = num(estero)
    d["nati_altro_o_nd"] = num(altro)
    for c in ["classi", "iscritti", "maschi", "femmine", "residenti_milano", "non_residenti", "nati_italia", "cittadinanza_italiana", "cittadinanza_non_italiana", "cittadinanza_nd"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)
    d["gestione"] = d.Gestione.map(norm_gest)
    d["gruppo_gestione"] = d.gestione.map(GGRP)
    d["ordine"] = ordine
    d["anno_inizio"] = d.anno_scolastico.str[:4].astype(int)
    d["id_nil_file"] = pd.to_numeric(d.nil_file.str.extract(r"\((\d+)\)\s*$")[0], errors="coerce")
    d["denominazione"] = d.Denominazione.str.strip(); d["indirizzo"] = d.Indirizzo.str.strip()
    if "capienza_file" in d: d["capienza"] = pd.to_numeric(d.capienza_file, errors="coerce")
    else: d["capienza"] = np.nan
    keep = ["anno_scolastico", "anno_inizio", "ordine", "codice_comune", "denominazione", "indirizzo", "gestione", "gruppo_gestione", "municipio", "nil_file", "id_nil_file",
            "classi", "iscritti", "maschi", "femmine", "residenti_milano", "non_residenti", "cittadinanza_italiana", "cittadinanza_non_italiana", "cittadinanza_nd",
            "nati_italia", "nati_estero_aree_note", "nati_altro_o_nd", "capienza"]
    frames.append(d[keep])
C = pd.concat(frames, ignore_index=True)
C["codice_comune"] = C.codice_comune.astype(str)
# controlli di coerenza
C["flag_somma_cittadinanza"] = (C.cittadinanza_italiana + C.cittadinanza_non_italiana + C.cittadinanza_nd) != C.iscritti
C["flag_somma_genere"] = (C.maschi + C.femmine) != C.iscritti
C["flag_somma_residenza"] = (C.residenti_milano + C.non_residenti) != C.iscritti
C["flag_zero_iscritti"] = C.iscritti == 0
CK["comune_righe"] = int(len(C)); CK["comune_righe_per_ordine"] = C.ordine.value_counts().to_dict()
CK["comune_somma_cittadinanza_diversa_da_totale"] = int(C.flag_somma_cittadinanza.sum())
CK["comune_somma_genere_diversa_da_totale"] = int(C.flag_somma_genere.sum())
CK["comune_somma_residenza_diversa_da_totale"] = int(C.flag_somma_residenza.sum())
CK["comune_righe_con_zero_iscritti"] = int(C.flag_zero_iscritti.sum())
CK["comune_duplicati_anno_ordine_codice"] = int(C.duplicated(["anno_scolastico", "ordine", "codice_comune"]).sum())

# anagrafica per codice (ultima apparizione) + coordinate + NIL
A = C.sort_values("anno_inizio").groupby(["ordine", "codice_comune"], as_index=False).last()[["ordine", "codice_comune", "denominazione", "indirizzo", "gestione", "gruppo_gestione", "municipio", "nil_file", "id_nil_file", "anno_inizio"]]
A = A.rename(columns={"anno_inizio": "ultimo_anno"})
first = C.groupby(["ordine", "codice_comune"]).anno_inizio.min().rename("primo_anno").reset_index()
A = A.merge(first, on=["ordine", "codice_comune"])
A = A.merge(LOCL[["ordine", "codice", "lon", "lat", "id_nil_file", "fonte_loc"]].rename(columns={"codice": "codice_comune", "id_nil_file": "id_nil_loc"}), on=["ordine", "codice_comune"], how="left")
res = [nil_pip(r.lon, r.lat) for r in A.itertuples()]
A["id_nil_poligono"] = [r[0] for r in res]; A["metodo_nil"] = [r[1] for r in res]
# NIL finale: poligono se c'e'; altrimenti quello scritto nel file Comune
A["id_nil"] = A.id_nil_poligono.fillna(A.id_nil_file)
A.loc[A.id_nil_poligono.isna() & A.id_nil_file.notna(), "metodo_nil"] = "dal_file_Comune"
A["nil"] = A.id_nil.map(lambda x: NIL_NAMES.get(int(x)) if pd.notna(x) else None)
both = A.id_nil_poligono.notna() & A.id_nil_file.notna()
CK["comune_anagrafica_codici"] = int(len(A))
CK["comune_codici_con_coordinate"] = int(A.lon.notna().sum())
CK["comune_codici_senza_coordinate_(chiusi_prima_del_2014)"] = int(A.lon.isna().sum())
CK["comune_nil_poligono_vs_file_coincidono"] = int((A.id_nil_poligono[both] == A.id_nil_file[both]).sum())
CK["comune_nil_poligono_vs_file_confrontabili"] = int(both.sum())
CK["comune_codici_senza_nil"] = int(A.id_nil.isna().sum())
CK["comune_metodo_nil"] = A.metodo_nil.value_counts().to_dict()
C = C.merge(A[["ordine", "codice_comune", "lon", "lat", "id_nil", "nil"]], on=["ordine", "codice_comune"], how="left")
# NIL del file di quell'anno quando manca quello finale
C["flag_senza_nil"] = C.id_nil.isna()
C.drop(columns=["nil_file"]).to_csv(f"{OUT}/comune_scuole_anno.csv", index=False, sep=";")
A.to_csv(f"{OUT}/comune_scuole_anagrafica.csv", index=False, sep=";")

# ------------------------------------------------------------------ MIUR
def anag():
    out = []
    for kind, lab in [("STAT", "statale"), ("PAR", "paritaria")]:
        for f in sorted(glob.glob(f"{RAW}/miur/SCUANAGRAFE{kind}*.csv")):
            d = pd.read_csv(f, dtype=str)
            d = d[d["CODICECOMUNESCUOLA"] == "F205"].copy()
            d["tipo"] = lab; d["file"] = os.path.basename(f)
            d["anno_inizio"] = int(re.search(r"SCUANAGRAFE\w+?(\d{4})\d{2}\d{8}\.csv", os.path.basename(f)).group(1))
            out.append(d)
    return pd.concat(out, ignore_index=True)
AN = anag()
AN = AN.rename(columns={"CODICESCUOLA": "codice_mecc", "DENOMINAZIONESCUOLA": "denominazione", "INDIRIZZOSCUOLA": "indirizzo", "CAPSCUOLA": "cap", "DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA": "tipologia"})
CK["miur_anagrafe_righe_milano"] = int(len(AN)); CK["miur_codici_milano"] = int(AN.codice_mecc.nunique())
codes = set(AN.codice_mecc)

def load(prefix):
    out = []
    for f in sorted(glob.glob(f"{RAW}/miur/{prefix}*.csv")):
        d = pd.read_csv(f, dtype=str)
        d = d[d.CODICESCUOLA.isin(codes)].copy()
        d["fonte_file"] = os.path.basename(f)
        out.append(d)
    return pd.concat(out, ignore_index=True)
def fix_year(d):
    d["anno_inizio"] = d.ANNOSCOLASTICO.str[:4].astype(int)
    d["anno_scolastico"] = d.anno_inizio.map(as_label)
    return d
ORD = {"SCUOLA PRIMARIA": "primaria", "SCUOLA SECONDARIA I GRADO": "sec1", "SCUOLA SECONDARIA II GRADO": "sec2"}
rows = []
for sfx, tipo in [("STA", "statale"), ("PAR", "paritaria")]:
    E = fix_year(load(f"ALUCORSOETA{sfx}"))
    E["alunni"] = pd.to_numeric(E.ALUNNI, errors="coerce")
    E["ordine"] = E.ORDINESCUOLA.map(ORD)
    E["primo_anno"] = np.where(E.ANNOCORSO == "1", E.alunni, 0)
    g = E.groupby(["anno_inizio", "anno_scolastico", "CODICESCUOLA", "ordine"], as_index=False).agg(iscritti=("alunni", "sum"), iscritti_anno_corso_1=("primo_anno", "sum"), righe_eta=("alunni", "size"), alunni_nan=("alunni", lambda s: s.isna().sum()))
    CK[f"miur_{sfx}_alunni_vuoti"] = int(E.alunni.isna().sum())
    X = fix_year(load(f"ALUITASTRACIT{sfx}"))
    for c in ["ALUNNI", "ALUNNICITTADINANZAITALIANA", "ALUNNICITTADINANZANONITALIANA", "ALUNNICITTADINANZANONITALIANAPAESIUE", "ALUNNICITTADINANZANONITALIANAPAESINONUE"]:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    X["ordine"] = X.ORDINESCUOLA.map(ORD)
    gx = X.groupby(["anno_inizio", "CODICESCUOLA", "ordine"], as_index=False).agg(tot_cittadinanza=("ALUNNI", "sum"), cittadinanza_italiana=("ALUNNICITTADINANZAITALIANA", "sum"),
                                                                                  cittadinanza_non_italiana=("ALUNNICITTADINANZANONITALIANA", "sum"), non_it_ue=("ALUNNICITTADINANZANONITALIANAPAESIUE", "sum"), non_it_non_ue=("ALUNNICITTADINANZANONITALIANAPAESINONUE", "sum"))
    K = fix_year(load(f"ALUCORSOINDCLA{sfx}"))
    K["ordine"] = K.ORDINESCUOLA.map(ORD)
    for c in ["CLASSI", "ALUNNIMASCHI", "ALUNNIFEMMINE"]: K[c] = pd.to_numeric(K[c], errors="coerce")
    gk = K.groupby(["anno_inizio", "CODICESCUOLA", "ordine"], as_index=False).agg(classi=("CLASSI", "sum"), maschi=("ALUNNIMASCHI", "sum"), femmine=("ALUNNIFEMMINE", "sum"))
    m = g.merge(gx, on=["anno_inizio", "CODICESCUOLA", "ordine"], how="left").merge(gk, on=["anno_inizio", "CODICESCUOLA", "ordine"], how="left")
    m["tipo"] = tipo
    rows.append(m)
    # infanzia
    I = fix_year(load(f"INFANZIAETA{sfx}"))
    I["bambini"] = pd.to_numeric(I.BAMBINI, errors="coerce")
    gi = I.groupby(["anno_inizio", "anno_scolastico", "CODICESCUOLA"], as_index=False).agg(iscritti=("bambini", "sum"))
    ix = fix_year(load(f"INFANZIASTRACIT{sfx}"))
    ix["ita"] = pd.to_numeric(ix.BAMBINICITTADINANZAITALIANA, errors="coerce"); ix["non"] = pd.to_numeric(ix.BAMBINICITTADINANZANONITALIANA, errors="coerce")
    gix = ix.groupby(["anno_inizio", "CODICESCUOLA"], as_index=False).agg(cittadinanza_italiana=("ita", "sum"), cittadinanza_non_italiana=("non", "sum"))
    ik = fix_year(load(f"INFANZIACLA{sfx}"))
    for c in ["CLASSI", "BAMBINIMASCHI", "BAMBINIFEMMINE"]: ik[c] = pd.to_numeric(ik[c], errors="coerce")
    gik = ik.groupby(["anno_inizio", "CODICESCUOLA"], as_index=False).agg(classi=("CLASSI", "sum"), maschi=("BAMBINIMASCHI", "sum"), femmine=("BAMBINIFEMMINE", "sum"))
    mi = gi.merge(gix, on=["anno_inizio", "CODICESCUOLA"], how="left").merge(gik, on=["anno_inizio", "CODICESCUOLA"], how="left")
    mi["ordine"] = "infanzia"; mi["tipo"] = tipo
    mi["tot_cittadinanza"] = mi.cittadinanza_italiana + mi.cittadinanza_non_italiana
    rows.append(mi)
M = pd.concat(rows, ignore_index=True).rename(columns={"CODICESCUOLA": "codice_mecc"})
M["stranieri_quota_pct"] = np.where(M.tot_cittadinanza > 0, (100 * M.cittadinanza_non_italiana / M.tot_cittadinanza).round(2), np.nan)
M["flag_cittadinanza_diversa_da_eta"] = (M.tot_cittadinanza.notna()) & (M.tot_cittadinanza != M.iscritti)
CK["miur_righe"] = int(len(M))
CK["miur_righe_cittadinanza_totale_diverso_da_totale_eta"] = int(M.flag_cittadinanza_diversa_da_eta.sum())
CK["miur_righe_senza_dato_cittadinanza"] = int(M.tot_cittadinanza.isna().sum())

# anagrafica MIUR per codice: ultima riga + tipologia
ANL = AN.sort_values("anno_inizio").groupby("codice_mecc", as_index=False).last()[["codice_mecc", "denominazione", "indirizzo", "cap", "tipologia", "tipo", "anno_inizio"]].rename(columns={"anno_inizio": "ultimo_anno_anagrafe"})
M = M.merge(ANL[["codice_mecc", "denominazione", "indirizzo", "cap", "tipologia"]], on="codice_mecc", how="left")
CK["miur_righe_senza_anagrafe"] = int(M.denominazione.isna().sum())

# ---- coordinate per le scuole MIUR: aggancio per indirizzo alle localizzazioni del Comune (infanzia/primaria/sec1) e ds78 (sec2)
ds78 = rd(glob.glob(f"{RAW}/comune_ds78/*.csv")[0])
ds78 = ds78.rename(columns={"LONG_X_4326": "lon", "LAT_Y_4326": "lat", "INDIRIZZO": "indirizzo", "DENOMINAZ": "den"})
ds78["lon"] = pd.to_numeric(ds78.lon, errors="coerce"); ds78["lat"] = pd.to_numeric(ds78.lat, errors="coerce")
ENT = []  # (ordine, parole, civico, lon, lat, fonte)
def add(ordine, addr, lon, lat, fonte, cod=None):
    if pd.isna(lon): return
    w, c = addr_key(addr)
    if not w: return
    ENT.append((ordine, w, c, lon, lat, fonte, cod))
for r in LOCL.itertuples(): add(r.ordine, r.indirizzo, r.lon, r.lat, r.fonte_loc, r.codice)
for r in ds78.itertuples(): add("sec2", r.indirizzo, r.lon, r.lat, "ds78")
BYC = {}
for e in ENT: BYC.setdefault(e[2], []).append(e)
def close(a, b): return abs(a[3] - b[3]) < 0.0025 and abs(a[4] - b[4]) < 0.0025
def pick(cands, ordine):
    if not cands: return None
    same = [c for c in cands if c[0] == ordine]
    return (same or cands)[0]
def geoloc(ordine, addr):
    w, c = addr_key(addr)
    if not w: return None, None, None, "senza_indirizzo", None
    if c is not None:
        exact = [e for e in BYC.get(c, []) if e[1] == w]
        if exact:
            e = pick(exact, ordine); return e[3], e[4], e[5], ("indirizzo_stesso_ordine" if e[0] == ordine else "indirizzo_altro_ordine"), (e[6] if e[0] == ordine else None)
        sub = [e for e in BYC.get(c, []) if (w <= e[1] or e[1] <= w)]
        if sub and all(close(sub[0], x) for x in sub):
            e = pick(sub, ordine); return e[3], e[4], e[5], "indirizzo_simile", (e[6] if e[0] == ordine else None)
        jac = [(len(w & e[1]) / len(w | e[1]), e) for e in BYC.get(c, [])]
        jac = [x for x in jac if x[0] >= 0.5]
        if jac:
            e = max(jac, key=lambda x: x[0])[1]; return e[3], e[4], e[5], "indirizzo_simile", (e[6] if e[0] == ordine else None)
        return None, None, None, "nessun_aggancio", None
    # senza civico: solo se la via e' univoca (tutte le occorrenze entro ~250 m)
    cands = [e for lst in BYC.values() for e in lst if (w <= e[1] or e[1] <= w)]
    if cands and all(close(cands[0], x) for x in cands):
        e = pick(cands, ordine); return e[3], e[4], e[5], "solo_via_senza_civico", None
    return None, None, None, "senza_civico_non_agganciabile", None
G = M[["codice_mecc", "ordine", "indirizzo", "tipo"]].drop_duplicates(["codice_mecc", "ordine"])
res = [geoloc(r.ordine, r.indirizzo) if isinstance(r.indirizzo, str) else (None, None, None, "senza_indirizzo", None) for r in G.itertuples()]
G["lon"] = [r[0] for r in res]; G["lat"] = [r[1] for r in res]; G["fonte_coordinate"] = [r[2] for r in res]; G["metodo_coordinate"] = [r[3] for r in res]; G["codice_comune_corrispondente"] = [r[4] for r in res]
nn = [nil_pip(r.lon, r.lat) for r in G.itertuples()]
G["id_nil"] = [x[0] for x in nn]; G["metodo_nil"] = [x[1] for x in nn]
G["nil"] = G.id_nil.map(lambda x: NIL_NAMES.get(int(x)) if pd.notna(x) else None)
M = M.merge(G[["codice_mecc", "ordine", "lon", "lat", "fonte_coordinate", "metodo_coordinate", "id_nil", "nil"]], on=["codice_mecc", "ordine"], how="left")
CK["miur_scuole_ordine_codice_unici"] = int(len(G))
CK["miur_metodo_coordinate_per_scuola"] = G.metodo_coordinate.value_counts().to_dict()
CK["miur_metodo_coordinate_per_ordine"] = G.groupby("ordine").metodo_coordinate.value_counts().unstack(fill_value=0).to_dict("index")
# righe MIUR con almeno un'iscritto agganciate a NIL (ultimo anno)
last = M[M.anno_inizio == 2024]
CK["miur_2024_iscritti_totali"] = int(last.iscritti.sum()); CK["miur_2024_iscritti_con_nil"] = int(last[last.id_nil.notna()].iscritti.sum())
M["flag_senza_nil"] = M.id_nil.isna()
cols = ["anno_scolastico", "anno_inizio", "ordine", "tipo", "codice_mecc", "denominazione", "indirizzo", "cap", "tipologia", "classi", "iscritti", "iscritti_anno_corso_1", "maschi", "femmine",
        "cittadinanza_italiana", "cittadinanza_non_italiana", "non_it_ue", "non_it_non_ue", "tot_cittadinanza", "stranieri_quota_pct", "lon", "lat", "fonte_coordinate", "metodo_coordinate", "id_nil", "nil", "flag_senza_nil", "flag_cittadinanza_diversa_da_eta"]
M[cols].sort_values(["anno_inizio", "ordine", "codice_mecc"]).to_csv(f"{OUT}/miur_scuole_anno.csv", index=False, sep=";")
G.to_csv(f"{OUT}/miur_scuole_anagrafica.csv", index=False, sep=";")

# ---- tabella unica "pulita" (anno, codice, ordine, statale/paritaria, iscritti, stranieri, lon/lat/NIL), fonte Comune per infanzia/primaria/sec1, fonte MIUR per sec2
T1 = C[["anno_scolastico", "anno_inizio", "ordine", "codice_comune", "denominazione", "indirizzo", "gestione", "gruppo_gestione", "classi", "iscritti", "cittadinanza_non_italiana", "cittadinanza_italiana", "cittadinanza_nd", "lon", "lat", "id_nil", "nil"]].copy()
T1["codice"] = "C" + T1.codice_comune; T1["fonte"] = "Comune ANASCO (ds224/225/226)"; T1 = T1.drop(columns="codice_comune")
T1["stranieri"] = T1.cittadinanza_non_italiana
T2 = M[M.ordine == "sec2"].copy()
T2["codice"] = T2.codice_mecc; T2["gestione"] = T2.tipo; T2["gruppo_gestione"] = T2.tipo; T2["fonte"] = "MIM open data (ALUCORSOETA, ALUITASTRACIT, ALUCORSOINDCLA)"
T2["stranieri"] = T2.cittadinanza_non_italiana; T2["cittadinanza_nd"] = np.nan
cols2 = ["anno_scolastico", "anno_inizio", "ordine", "codice", "denominazione", "indirizzo", "gestione", "gruppo_gestione", "classi", "iscritti", "stranieri", "cittadinanza_italiana", "cittadinanza_non_italiana", "cittadinanza_nd", "lon", "lat", "id_nil", "nil", "fonte"]
T = pd.concat([T1[cols2], T2[cols2]], ignore_index=True).sort_values(["anno_inizio", "ordine", "codice"])
T.to_csv(f"{OUT}/scuole_anno_tidy.csv", index=False, sep=";")
CK["tidy_righe"] = int(len(T))

# ---- Residenti per eta' (ds223) e nascite -> tabella di appoggio
R = rd(glob.glob(f"{RAW}/comune_ds223/*.csv")[0])
R["Eta"] = pd.to_numeric(R.Eta, errors="coerce")
R["tot"] = pd.to_numeric(R.nonsposati_stima, errors="coerce")
R = R[R.Eta <= 19].groupby(["Anno", "Eta", "Cittadinanza"], as_index=False).tot.sum()
R.rename(columns={"Anno": "anno", "Eta": "eta", "Cittadinanza": "cittadinanza", "tot": "residenti"}).to_csv(f"{OUT}/residenti_per_eta_ds223.csv", index=False, sep=";")

# ---- serie lunga per ordine e gestione (somma dei municipi), ds102-105 (Comune, fonte: ANASCO / milanostatistica)
sl = []
for ds, ordine in [("ds102", "infanzia"), ("ds103", "primaria"), ("ds104", "sec1"), ("ds105", "sec2")]:
    d = rd(glob.glob(f"{RAW}/comune_{ds}/*.csv")[0])
    d["gest"] = d.Gestione.str.strip().str.lower().replace({"pubbliche": "pubblica (statale+comunale)", "private": "privata", "non statale": "non statale"})
    for c in ["Classi", "Alunni_MF"]: d[c] = pd.to_numeric(d[c], errors="coerce")
    uc = [c for c in d.columns if c.startswith("Unit")][0]
    d[uc] = pd.to_numeric(d[uc], errors="coerce")
    g = d.groupby(["Anno scolastico", "gest"], as_index=False).agg(unita=(uc, "sum"), classi=("Classi", "sum"), alunni=("Alunni_MF", "sum"))
    g["ordine"] = ordine; g["fonte"] = ds
    sl.append(g)
SL = pd.concat(sl).rename(columns={"Anno scolastico": "anno_scolastico", "gest": "gestione"})
SL["anno_inizio"] = SL.anno_scolastico.str[:4].astype(int)
SL[["anno_scolastico", "anno_inizio", "ordine", "gestione", "unita", "classi", "alunni", "fonte"]].to_csv(f"{OUT}/serie_lunga_ordine_gestione.csv", index=False, sep=";")
# verifica: la somma del file per scuola (ANASCO) coincide con la somma dei municipi?
chk = C.groupby(["anno_inizio", "ordine"]).iscritti.sum().rename("per_scuola").reset_index().merge(SL.groupby(["anno_inizio", "ordine"]).alunni.sum().rename("per_municipio").reset_index(), on=["anno_inizio", "ordine"])
chk["diff"] = chk.per_scuola - chk.per_municipio
CK["verifica_scuole_vs_municipi_righe_con_differenza"] = int((chk["diff"] != 0).sum()); CK["verifica_scuole_vs_municipi_righe"] = int(len(chk))
CK["verifica_scuole_vs_municipi_diff_assoluta_max"] = int(chk["diff"].abs().max())

# ---- residenti per NIL, fascia d'eta' e cittadinanza (ds27, anni 1999-)
import zipfile
z = zipfile.ZipFile(f"{RAW}/comune_ds27/ds27_pop_sto_quartiere.zip")
parts = []
for ch in pd.read_csv(z.open("ds27_pop_sto_quartiere.csv"), sep=";", chunksize=500000, dtype={"Eta": str}):
    ch = ch[ch.Anno >= 2009].copy()
    ch["Eta"] = pd.to_numeric(ch.Eta.str.extract(r"(\d+)")[0], errors="coerce")  # "100 e piu'" -> 100
    ch["fascia"] = pd.cut(ch.Eta, [-1, 2, 5, 10, 13, 18, 200], labels=["0-2", "3-5", "6-10", "11-13", "14-18", "19+"])
    ch["italiana"] = ch.Cittadinanza.str.strip().str.lower().eq("italia")
    parts.append(ch.groupby(["Anno", "IdNil", "Nil", "fascia", "italiana"], observed=True, as_index=False).Residenti.sum())
RN = pd.concat(parts).groupby(["Anno", "IdNil", "Nil", "fascia", "italiana"], observed=True, as_index=False).Residenti.sum()
RN = RN.pivot_table(index=["Anno", "IdNil", "Nil", "fascia"], columns="italiana", values="Residenti", aggfunc="sum", fill_value=0, observed=True).reset_index()
RN.columns = ["anno", "id_nil", "nil", "fascia_eta", "stranieri", "italiani"]
RN.to_csv(f"{OUT}/residenti_nil_fascia_cittadinanza_ds27.csv", index=False, sep=";")
CK["ds27_anni"] = [int(RN.anno.min()), int(RN.anno.max())]

json.dump(CK, open(f"{OUT}/controlli_pulizia.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(CK, ensure_ascii=False, indent=1, default=str))
