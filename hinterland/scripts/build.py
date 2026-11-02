"""Hinterland di Milano: legge raw/ e i dati gia puliti degli altri filoni, scrive docs/hinterland/data/ e hinterland/out/controlli.txt.

Uso: python -I -X utf8 hinterland/scripts/build.py <percorso assoluto di milano-in-dati>

Perimetro: 187 comuni = 132 della Citta metropolitana di Milano senza Milano (codice provincia 015)
+ 55 di Monza e Brianza (108). Milano (015146) sempre a confronto.
Geografia unica = comuni al 1/1/2021 (pendolari/pulito/comuni_2021.csv), codici ISTAT a 6 cifre.
Tutti i file in raw/ sono dati non fidati: si leggono come testo/CSV, mai eseguiti.
"""
import sys, os, io, csv, json, zipfile, re, unicodedata, math, statistics, collections, datetime, hashlib
import pandas as pd
import numpy as np
from shapely.geometry import shape, Point

BASE = os.path.abspath(sys.argv[1])
H = os.path.join(BASE, "hinterland")
RAW = os.path.join(H, "raw")
OUTD = os.path.join(H, "out")
DATA = os.path.join(BASE, "docs", "hinterland", "data")
os.makedirs(OUTD, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

CTRL = []          # righe di controlli.txt
def ctrl(txt=""):
    CTRL.append(txt)
    print(txt)

def P(*a):
    return os.path.join(BASE, *a)

def num(x):
    if x is None: return None
    x = str(x).strip().replace('"', '')
    if x in ("", "-", "nan", "NaN"): return None
    return float(x.replace(",", "."))

def norm(s):
    s = unicodedata.normalize("NFD", str(s).upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def dec(raw):
    for enc in ("utf-8-sig", "cp1252"):
        try: return raw.decode(enc)
        except UnicodeDecodeError: pass
    return raw.decode("latin-1")

# ---------------------------------------------------------------- 0. geografia unica
c21 = pd.read_csv(P("pendolari", "pulito", "comuni_2021.csv"))
c21 = c21[c21.sigla.isin(["MI", "MB"])].copy()
c21["cod"] = c21.pro_com.map(lambda v: f"{int(v):06d}")
MILANO = "015146"
COM = {}                                   # cod -> dict
for r in c21.itertuples():
    g = "MILANO" if r.cod == MILANO else r.sigla       # MI = Citta metropolitana senza Milano, MB = Monza e Brianza
    COM[r.cod] = dict(cod=r.cod, nome=r.nome, gruppo=g, lat=float(r.lat), lon=float(r.lon), pop2021=int(r.pop_2021))
HINT = [c for c in COM if c != MILANO]
MI132 = [c for c in HINT if COM[c]["gruppo"] == "MI"]
MB55 = [c for c in HINT if COM[c]["gruppo"] == "MB"]
GRUPPI = {"MILANO": [MILANO], "HINT": HINT, "MI": MI132, "MB": MB55}
ALLC = [MILANO] + HINT

ctrl("CONTROLLI hinterland/scripts/build.py   (generato %s)" % datetime.date.today().isoformat())
ctrl("")
ctrl("1. COMUNI PER GRUPPO (comuni_2021.csv, geografia 1/1/2021)")
ctrl(f"   Citta metropolitana di Milano senza Milano (prov. 015): {len(MI132)}  (attesi 132)  -> {'OK' if len(MI132)==132 else 'ERRORE'}")
ctrl(f"   Monza e Brianza (prov. 108): {len(MB55)}  (attesi 55)  -> {'OK' if len(MB55)==55 else 'ERRORE'}")
ctrl(f"   Hinterland totale: {len(HINT)}  (attesi 187)  -> {'OK' if len(HINT)==187 else 'ERRORE'}")
ctrl(f"   Milano {MILANO}: {'presente' if MILANO in COM else 'MANCANTE'}")

# catastale (per i redditi MEF, che usano la geografia dell'anno): Elenco comuni ISTAT
ele = pd.read_excel(P("pendolari", "raw", "istat_codici", "Elenco-comuni-italiani.xlsx"), dtype=str)
ele.columns = [c.strip().split("\n")[0] for c in ele.columns]
CAT = {}
for _, r in ele.iterrows():
    cod = r["Codice Comune formato alfanumerico"]
    if cod in COM: CAT[r["Codice Catastale del Comune"]] = cod
VZ = "015251"                                  # Vermezzo con Zelo (fusione 2019)
CAT["L768"] = VZ                               # Vermezzo
CAT["M160"] = VZ                               # Zelo Surrigone
BAR = "015250"; BOL = "015027"                 # Baranzate nasce da Bollate nel 2004
UNIT = {c: c for c in ALLC}; UNIT[BAR] = BOL   # unita di confronto: Bollate+Baranzate insieme (crescita, voto)
ctrl(f"   Codici catastali agganciati: {len(CAT)} (188 comuni attuali + Vermezzo e Zelo Surrigone, fusi nel 2019)")
for c in COM.values():
    c["unita"] = UNIT[c["cod"]]

dist = pd.read_csv(P("pendolari", "pulito", "mappa_comuni.csv"))
dist["cod"] = dist.pro_com.map(lambda v: f"{int(v):06d}")
DIST = dist.set_index("cod")
for c in COM.values():
    c["km"] = None if c["cod"] == MILANO else float(DIST.loc[c["cod"], "km"])
    c["min"] = None if c["cod"] == MILANO else float(DIST.loc[c["cod"], "min"])

# ---------------------------------------------------------------- 1. popolazione al 1 gennaio, per eta (POSAS 2019-2026)
YEARS_POP = list(range(2001, 2027))
POP = {y: {} for y in YEARS_POP}       # 2001 = censimento 21/10/2001; 2002.. = 1 gennaio
STR = {y: {} for y in YEARS_POP}
ETA = {}                               # (y, cod) -> dict(u15, o65, sumage, tot)
rawlog = []
REMAP19 = {"015235": VZ, "015246": VZ}       # Vermezzo, Zelo Surrigone nei file 2019

def leggi_csv_zip(path, usecols=None, skip=0, sep=";"):
    z = zipfile.ZipFile(path)
    name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
    return pd.read_csv(z.open(name), sep=sep, skiprows=skip, encoding="utf-8-sig", dtype=str, usecols=usecols, low_memory=False)

ctrl("")
ctrl("2. POSAS (residenti per eta, 1 gennaio 2019-2026) e STRASA (stranieri)")
for y in range(2019, 2027):
    df = leggi_csv_zip(P("hinterland", "raw", "posas", f"POSAS_{y}_it_Comuni.zip"), skip=1,
                       usecols=lambda c: c in ("Codice comune", "Età", "Totale"))
    df["Codice comune"] = df["Codice comune"].replace(REMAP19)       # 2019: Vermezzo e Zelo Surrigone ancora separati
    df = df[df["Codice comune"].isin(COM)]
    df["eta"] = df["Età"].astype(int); df["n"] = df["Totale"].astype(float)
    df = df.groupby(["Codice comune", "eta"], as_index=False)["n"].sum()
    tot = df[df.eta == 999].set_index("Codice comune")["n"]
    ag = df[df.eta <= 100]
    s = ag.groupby("Codice comune")["n"].sum()
    mism = int((tot.reindex(s.index) != s).sum())
    ctrl(f"   POSAS {y}: comuni trovati {tot.shape[0]}/188; righe di totale (eta 999) diverse dalla somma delle eta: {mism}")
    for cod in ALLC:
        if cod not in tot.index: continue
        POP[y][cod] = float(tot[cod])
    u15 = ag[ag.eta <= 14].groupby("Codice comune")["n"].sum()
    o65 = ag[ag.eta >= 65].groupby("Codice comune")["n"].sum()
    sa = (ag.eta * ag.n).groupby(ag["Codice comune"]).sum()
    for cod in tot.index:
        ETA[(y, cod)] = dict(u15=float(u15.get(cod, 0)), o65=float(o65.get(cod, 0)), sa=float(sa[cod]), tot=float(tot[cod]))
    df2 = leggi_csv_zip(P("hinterland", "raw", "strasa", f"STRASA_{y}_it_Comuni.zip"), skip=1,
                        usecols=lambda c: c in ("Codice comune", "Età", "Maschi", "Femmine"))
    df2["Codice comune"] = df2["Codice comune"].replace(REMAP19)
    df2 = df2[df2["Codice comune"].isin(COM)]
    df2["eta"] = df2["Età"].astype(int); df2["n"] = df2["Maschi"].astype(float) + df2["Femmine"].astype(float)
    df2 = df2.groupby(["Codice comune", "eta"], as_index=False)["n"].sum()
    t2 = df2[df2.eta == 999].set_index("Codice comune")["n"]
    for cod in t2.index: STR[y][cod] = float(t2[cod])
    ctrl(f"   STRASA {y}: comuni trovati {t2.shape[0]}/188")

# ---------------------------------------------------------------- 2. bilancio: RBD 2001-2018, D7B 2019-2024, P2 2025
BIL = {}                                # (y, cod) -> dict nati, morti, iscr_int, canc_int, iscr_est, canc_est, acq, inizio, fine
BILS = {}                               # stranieri: (y, cod) -> dict inizio, fine, acq
ctrl("")
ctrl("3. BILANCIO DEMOGRAFICO: RBD 2001-2018 (ricostruzione ISTAT), D7B mensile 2019-2024, P2 2025")
colmap = {"Popolazione inizio periodo": "inizio", "Nati": "nati", "Morti": "morti", "Iscritti dall'interno": "iscr_int",
          "Cancellati per l'interno": "canc_int", "Iscritti dall'estero": "iscr_est", "Cancellati per l'estero": "canc_est",
          "Acquisizioni di cittadinanza italiana": "acq", "Popolazione fine periodo": "fine"}
for y in range(2001, 2019):
    df = leggi_csv_zip(P("popolazione", "raw", "istat_demo", f"RBD-Dataset-{y}.csv.zip"), sep=";")
    df = df[(df["Codice comune"].isin(COM)) & (df["Sesso"] == "Maschi e femmine")]
    for cit, store in (("Tutte", BIL), ("Straniera", BILS)):
        d = df[df["Cittadinanza"] == cit]
        n = d["Codice comune"].nunique()
        if cit == "Tutte": ctrl(f"   RBD {y}: comuni trovati {n}/188")
        for _, r in d.iterrows():
            store[(y, r["Codice comune"])] = {v: float(r[k]) for k, v in colmap.items()}
BILADJ = {}                              # aggiustamento statistico (mese 13 del D7B)
for y in range(2019, 2025):
    df = leggi_csv_zip(P("censimenti", "raw", "istat_demo", f"D7B{y}.csv.zip"), sep=";",
                       usecols=lambda c: c in ("Anno", "Mese", "Sesso", "Popolazione inizio periodo", "Nati vivi", "Morti",
                                               "Immigrati da altro comune", "Emigrati per altro comune", "Immigrati dall'estero",
                                               "Emigrati per l'estero", "Popolazione fine periodo", "Codice comune"))
    df["Codice comune"] = df["Codice comune"].replace(REMAP19)
    df = df[df["Codice comune"].isin(COM)]
    for c in df.columns:
        if c not in ("Sesso", "Codice comune"): df[c] = df[c].astype(float)
    mf = df[df.Sesso.isin(["Maschi", "Femmine"])]
    tt = df[(df.Sesso == "Totale") & (df.Mese <= 12)]
    mm = mf[mf.Mese <= 12]
    cols_f = ["Nati vivi", "Morti", "Immigrati da altro comune", "Emigrati per altro comune", "Immigrati dall'estero", "Emigrati per l'estero"]
    diff = float(abs(mm.groupby("Codice comune")[cols_f].sum() - tt.groupby("Codice comune")[cols_f].sum()).to_numpy().sum())
    ctrl(f"   D7B {y}: comuni {mm['Codice comune'].nunique()}/188; mesi 1-12 per comune min {mm.groupby('Codice comune')['Mese'].nunique().min():.0f}; maschi+femmine contro righe 'Totale': differenza {diff:.0f}")
    ini = mm[mm.Mese == 1].groupby("Codice comune")["Popolazione inizio periodo"].sum()
    fin = mf[mf.Mese == 15].groupby("Codice comune")["Popolazione fine periodo"].sum()          # popolazione censita al 31 dicembre
    adj = mf[mf.Mese == 13].groupby("Codice comune")["Popolazione fine periodo"].sum()          # aggiustamento statistico
    fl = mm.groupby("Codice comune")[cols_f].sum()
    for cod in fl.index:
        BIL[(y, cod)] = dict(inizio=float(ini[cod]), nati=float(fl.loc[cod, "Nati vivi"]), morti=float(fl.loc[cod, "Morti"]),
                             iscr_int=float(fl.loc[cod, "Immigrati da altro comune"]), canc_int=float(fl.loc[cod, "Emigrati per altro comune"]),
                             iscr_est=float(fl.loc[cod, "Immigrati dall'estero"]), canc_est=float(fl.loc[cod, "Emigrati per l'estero"]),
                             acq=None, fine=float(fin[cod]), adj=float(adj.get(cod, 0)))
df = leggi_csv_zip(P("hinterland", "raw", "p2", "P2_2025_Comuni.zip"), skip=1, sep=";")
df = df[df["Codice comune"].isin(COM)]
ctrl(f"   P2 2025: comuni trovati {df['Codice comune'].nunique()}/188")
for _, r in df.iterrows():
    BIL[(2025, r["Codice comune"])] = dict(inizio=float(r["Popolazione censita al 1° gennaio - Totale"]), nati=float(r["Nati vivi - Totale"]),
        morti=float(r["Morti - Totale"]), iscr_int=float(r["Immigrati da altro comune - Totale"]), canc_int=float(r["Emigrati per altro comune - Totale"]),
        iscr_est=float(r["Immigrati dall'estero - Totale"]), canc_est=float(r["Emigrati per l'estero - Totale"]), acq=None,
        fine=float(r["Popolazione al 31 dicembre - Totale"]))

# popolazione al 1 gennaio dalle RBD (2001: censimento; 2002-2018: fine periodo dell'anno prima)
for cod in ALLC:
    POP[2001][cod] = BIL[(2001, cod)]["inizio"]
    STR[2001][cod] = BILS[(2001, cod)]["inizio"]
    for y in range(2002, 2019):
        POP[y][cod] = BIL[(y - 1, cod)]["fine"]
        STR[y][cod] = BILS[(y - 1, cod)]["fine"]

def somma(codes, f):
    return sum(f(c) for c in codes)

# ---------------------------------------------------------------- 3. redditi MEF
ctrl("")
ctrl("4. REDDITI MEF (anno d'imposta 2000-2024, euro correnti)")
m = pd.read_csv(P("redditi", "pulito", "mef_comuni_2000_2024.csv"), dtype={"istat": str, "catastale": str})
m = m[m.catastale.isin(CAT)].copy()
CL = ["cl0_le0_eur", "cl1_0_10k_eur", "cl2_10_15k_eur", "cl3_15_26k_eur", "cl4_26_55k_eur", "cl5_55_75k_eur", "cl6_75_120k_eur", "cl7_oltre120k_eur"]
CL_OK = CL[1:]
m["cod"] = m.catastale.map(CAT)
m["somma_classi"] = m[CL].sum(axis=1, min_count=1)
m["red"] = m["reddito_complessivo_eur"].where(m["reddito_complessivo_eur"].notna(), m["somma_classi"])
m["fonte_red"] = np.where(m["reddito_complessivo_eur"].notna(), "campo", "classi")
m["manca"] = m[CL_OK].isna().sum(axis=1)                 # classi (escluso <=0) senza importo: celle oscurate
m.loc[m["fonte_red"] == "campo", "manca"] = 0
RED = {}                                                   # (y, cod) -> contrib, red, manca
for (y, cod), g in m.groupby(["anno", "cod"]):
    RED[(int(y), cod)] = dict(contr=float(g.contribuenti.sum()), red=float(g.red.sum()), manca=int(g.manca.sum()))
for y in (2000, 2003, 2010, 2018, 2024):
    n = len({cod for (yy, cod) in RED if yy == y})
    ctrl(f"   MEF {y}: unita comunali trovate {n} (attese {188 if y>=2004 else 187}) {'(Baranzate esiste dal 2004)' if y<2004 else ''}")

# ---------------------------------------------------------------- 4. pendolari 1991-2021 (gia puliti dal filone pendolari)
ctrl("")
ctrl("5. PENDOLARI (pendolari/pulito: ISTAT matrici 1991, 2001, 2011; 2021 stima da modello)")
fl = pd.read_csv(P("pendolari", "pulito", "flussi_milano.csv"))
fl["cod"] = fl.altro.map(lambda v: f"{int(v):06d}" if v > 0 else None)
YP = [1991, 2001, 2011, 2021]
ENTRA = {y: collections.defaultdict(float) for y in YP}
ESCE = {y: collections.defaultdict(float) for y in YP}
for r in fl[fl.direzione.isin(["entra", "esce"])].itertuples():
    if r.cod is None: continue
    (ENTRA if r.direzione == "entra" else ESCE)[r.anno][r.cod] += r.n
TOT = {y: {} for y in YP}
for y in YP:
    for c in HINT:
        TOT[y][c] = float(DIST.loc[c, f"tot_{y}"]) if not pd.isna(DIST.loc[c, f"tot_{y}"]) else None
tot21 = {"MI": sum(ENTRA[2021][c] for c in MI132), "MB": sum(ENTRA[2021][c] for c in MB55)}
ctrl(f"   Entrano a Milano nel 2021 (lavoro+studio) dal resto della Citta metropolitana: {tot21['MI']:.0f}  (atteso 269.466) -> {'OK' if round(tot21['MI'])==269466 else 'ERRORE'}")
ctrl(f"   Entrano a Milano nel 2021 da Monza e Brianza: {tot21['MB']:.0f}  (atteso 72.265) -> {'OK' if round(tot21['MB'])==72265 else 'ERRORE'}")
og = pd.read_csv(P("pendolari", "pulito", "origini_gruppi.csv"))
og21 = og[og.anno == 2021].groupby("gruppo").n.sum()
ctrl(f"   Stessi totali da origini_gruppi.csv: resto CM {og21['Resto della città metropolitana di Milano']}, MB {og21['Monza e Brianza']}")
mapp = pd.read_csv(P("pendolari", "pulito", "mappa_comuni.csv"))
mapp["cod"] = mapp.pro_com.map(lambda v: f"{int(v):06d}")
diffs = [(c, ENTRA[y][c], float(DIST.loc[c, f"entra_{y}"])) for y in YP for c in HINT if abs(ENTRA[y][c] - float(DIST.loc[c, f"entra_{y}"])) > 0.6]
ctrl(f"   Entrate per comune: flussi_milano.csv contro mappa_comuni.csv, differenze > 0,6 persone: {len(diffs)}")

# cambi di residenza di Milano con la provincia 2020-2024
cr = pd.read_csv(P("popolazione", "pulito", "flussi_luogo_2020_2024.csv"))
cr = cr[cr.luogo.isin(["Prov. MI", "Altre prov. Lombardia"])]
CAMBI = {l: {int(r.anno): dict(isc=int(r.isc), canc=int(r.canc), saldo=int(r.saldo)) for r in cr[cr.luogo == l].itertuples()} for l in ("Prov. MI", "Altre prov. Lombardia")}
sal = [CAMBI["Prov. MI"][y]["saldo"] for y in range(2020, 2025)]
ctrl(f"   Saldo cambi di residenza Milano con 'Prov. MI' 2020-2024: {sal}  (attesi -5988, -7149, -7754, -8169, -10413) -> {'OK' if sal==[-5988,-7149,-7754,-8169,-10413] else 'ERRORE'}")

# ---------------------------------------------------------------- 5. metropolitana: fermate nei confini
ctrl("")
ctrl("6. METROPOLITANA (metro/pulito/stazioni_metro.csv, fermate collocate nei confini ISTAT 2021)")
gj = json.load(open(P("docs", "pendolari", "data", "comuni.geojson"), encoding="utf-8"))
polys = {f"{f['properties']['i']:06d}": shape(f["geometry"]) for f in gj["features"]}
st = pd.read_csv(P("metro", "pulito", "stazioni_metro.csv"))
STAZ = []
for r in st.itertuples():
    pt = Point(r.lon_gtfs, r.lat_gtfs)
    hit = [c for c, pg in polys.items() if pg.contains(pt)]
    cod = hit[0] if hit else None
    dmin = None
    if cod:
        dmin = min(pg.distance(pt) for c, pg in polys.items() if c != cod) * 78000      # metri, approssimato a 45,5 N
    ap = [int(x.split(":")[1][:4]) for x in str(r.apertura_per_linea_wikipedia).split(",") if ":" in x and x.split(":")[1][:4].isdigit()]
    STAZ.append(dict(nome=r.stazione, linee=r.linee, cod=cod, anno=min(ap) if ap else None, dist_confine_m=None if dmin is None else round(dmin)))
nst = len(STAZ); nfuori = sum(1 for s in STAZ if s["cod"] is None)
ctrl(f"   Stazioni lette {nst}; non collocate in nessun comune lombardo: {nfuori}")
FERM = collections.defaultdict(list)
for s in STAZ:
    if s["cod"] in HINT: FERM[s["cod"]].append(s)
ctrl(f"   Comuni dell'hinterland con almeno una fermata: {len(FERM)} -> " + ", ".join(sorted(COM[c]['nome'] for c in FERM)))
nM = sum(1 for s in STAZ if s["cod"] == MILANO)
ctrl(f"   Stazioni dentro Milano: {nM}; nell'hinterland: {sum(len(v) for v in FERM.values())}")
sandon = [s for s in STAZ if s["nome"] == "San Donato"]
ctrl(f"   Nota: stazione 'San Donato' (M3) risulta in {COM[sandon[0]['cod']]['nome']} a {sandon[0]['dist_confine_m']} m dal confine con San Donato Milanese: nel confronto base non conta come fermata del comune; vedi sensibilita.")

# ---------------------------------------------------------------- 6. voto: Camera dei deputati (Eligendo, Ministero dell'Interno)
ctrl("")
ctrl("7. VOTO: Camera dei deputati, voti di lista per comune (Eligendo)")
ANNI_V = [1976, 1979, 1987, 1992, 1996, 2001, 2006, 2008, 2013, 2018, 2022]
FILEV = {1976: ("elezioni/raw/eligendo/camera/camera-19760620.zip", "camera-19760620.txt"),
         1979: ("elezioni/raw/eligendo/camera/camera-19790603.zip", None),
         1987: ("hinterland/raw/eligendo/camera-19870614.zip", "Camera-19870614.txt"),
         1992: ("hinterland/raw/eligendo/camera-19920405.zip", "camera-19920405.txt"),
         1996: ("hinterland/raw/eligendo/camera-19960421.zip", "camera-19960421_Proporzionale.txt"),
         2001: ("hinterland/raw/eligendo/camera-20010513.zip", "camera-20010513_Proporzionale.txt"),
         2006: ("hinterland/raw/eligendo/camera-20060409.zip", "camera_italia-20060409.txt"),
         2008: ("hinterland/raw/eligendo/camera-20080413.zip", "camera_italia-20080413.txt"),
         2013: ("hinterland/raw/eligendo/camera-20130224.zip", "camera_italia-20130224.txt"),
         2018: ("hinterland/raw/eligendo/camera-20180304.zip", "Camera2018_livComune.txt"),
         2022: ("hinterland/raw/eligendo/camera-20220925.zip", "camera2022_Italia_LivComune.csv")}
NOMI = {norm(c["nome"]): cod for cod, c in COM.items()}
NOMI.update({"VERMEZZO": VZ, "ZELO SURRIGONE": VZ, "BARANZATE": BAR, "TRUGGIO": NOMI["TRIUGGIO"]})      # TRUGGIO: refuso del file 2006
FAMIGLIE = ["Centrosinistra", "Sinistra", "Centro", "Centrodestra", "Destra", "Lega", "M5S", "Altri"]
RULES = [   # (famiglia, espressione sul nome normalizzato); vince la prima che corrisponde
    ("M5S", r"^MOVIMENTO 5 STELLE"),
    ("Lega", r"^LEGA (NORD|LOMBARDA|PER SALVINI|SALVINI)|^LEGA$"),
    ("Centro", r"RINNOVAMENTO IT|LISTA DINI"),
    ("Centrosinistra", r"^PDS$|^PARTITO DEMOCRATICO|^DEMOCRATICI SINISTRA|ULIVO|LA MARGHERITA|PRODI|DI PIETRO|ROSA NEL PUGNO|^PSI$|PARTITO SOCIALISTA|IL GIRASOLE|^I DEMOCRATICI|IMPEGNO CIVICO|CIVICA POPOLARE|^INSIEME|ITALIA EUROPA INSIEME|CENTRO DEMOCRATICO"),
    ("Sinistra", r"^PCI$|RIFONDAZIONE|COMUNIST|VERDI|LISTA VERDE|PDUP|DEM PROL|NUOVA SIN|^LA RETE|SINISTRA|RIVOLUZIONE CIVILE|UNIONE POPOLARE|POTERE AL POPOLO|LIBERI E UGUALI|ARCOBALENO|PSIUP|MANIFESTO"),
    ("Destra", r"^MSI|MOV SOC TRICOLORE|ALLEANZA NAZIONALE|FIAMMA|FRATELLI D ITALIA|^LA DESTRA|FORZA NUOVA|CASAPOUND|ALTERNATIVA SOCIALE|^DN CD|DEMOCRAZIA NAZIONALE"),
    ("Centrodestra", r"FORZA ITALIA|POPOLO DELLA LIBERTA|^CCD|^CDU|NUOVO PSI|DEM CRIST|NOI MODERATI|NUOVO CENTRO|NOI CON L ITALIA|FUTURO E LIBERTA"),
    ("Centro", r"^DC$|^PRI$|^PLI$|^PSDI$|^PRI PLI|UNITA SOCIALISTA|UNITA SOC PRI|UNIONE DI CENTRO|^UDC|SCELTA CIVICA|^AZIONE|ITALIA VIVA|^EUROPA$|FARE PER FERMARE|DEMOCRAZIA EUROPEA|U D EUR|STATI UNITI"),
    ("Altri", r"^P RAD|PANNELLA|BONINO|PENSIONATI|SGARBI|POE$|OPERAI EUROPEI"),      # attribuite esplicitamente ad Altri
]
RULES_C = [(f, re.compile(r)) for f, r in RULES]
def famiglia(lista):
    n = norm(lista)
    for f, rx in RULES_C:
        if rx.search(n): return f, True
    return "Altri", False        # lista non attribuita

def leggi_camera(y):
    """Restituisce (voti, elettori, trovati): voti[(unita, lista)] = voti di lista; per unita di confronto."""
    p, nome = FILEV[y]
    z = zipfile.ZipFile(P(*p.split("/")))
    if nome is None: nome = [i.filename for i in z.infolist() if "preferenz" not in i.filename.lower() and i.filename.lower().endswith(".txt")][0]
    rows = csv.DictReader(io.StringIO(dec(z.open(nome).read())), delimiter=";")
    voti = collections.defaultdict(float); elet = {}; visti = set(); trovati = set()
    for r in rows:
        com = r.get("COMUNE") or ""
        n = norm(com)
        if y <= 1992: ok = r["PROVINCIA"] == "MILANO"
        elif y in (1996, 2001): ok = r["CIRCOSCRIZIONE"] == "LOMBARDIA 1"
        elif y in (2006, 2008, 2013): ok = r["PROVINCIA"] in ("MILANO", "MONZA", "MONZA E DELLA BRIANZA")
        else: ok = (r.get("CIRCOSCRIZIONE") or r.get("CIRC-REG") or "").startswith("LOMBARDIA")
        if not ok: continue
        if y == 2001 and re.fullmatch(r"MILANO \d+", n): cod = MILANO
        elif n == "MILANO": cod = MILANO
        elif n in NOMI: cod = UNIT[NOMI[n]]
        else: continue
        coll = r.get("COLLEGIOUNINOMINALE") or r.get("COLLUNINOM") or r.get("COLLEGIO") or ""
        lista = r.get("LISTA") if "LISTA" in r else r.get("DESCRLISTA")
        v = r.get("VOTI_LISTA") or r.get("VOTILISTA")
        k = (com, coll, lista)
        if k in visti: continue
        visti.add(k)
        voti[(cod, lista)] += float(v or 0)
        trovati.add(cod)
        ek = (com, coll)
        if ek not in elet:
            elet[ek] = (cod, num(r.get("ELETTORI") or r.get("ELETTORITOT")), num(r.get("VOTANTI") or r.get("VOTANTITOT")))
    return voti, elet, trovati

VOTO = {}       # (y, unita) -> {famiglia: voti}
VALIDI = {}
ELET = {}
NONATTR = {}
LISTE_NA = collections.defaultdict(collections.Counter)
mism_csv = collections.Counter()
fam_csv = {}
for r in csv.DictReader(open(P("elezioni", "famiglie_partiti.csv"), encoding="utf-8-sig"), delimiter=";"):
    fam_csv[norm(r["lista"])] = r["famiglia"]
UNITS_H = sorted({UNIT[c] for c in HINT})
for y in ANNI_V:
    voti, elet, trovati = leggi_camera(y)
    mancanti = [c for c in UNITS_H if c not in trovati]
    ctrl(f"   Camera {y}: unita trovate {len(trovati & set(UNITS_H))}/{len(UNITS_H)} dell'hinterland (Bollate con Baranzate, Vermezzo con Zelo), Milano {'si' if MILANO in trovati else 'NO'}; mancanti: {[COM[c]['nome'] for c in mancanti]}")
    for (cod, lista), v in voti.items():
        f, att = famiglia(lista)
        d = VOTO.setdefault((y, cod), collections.Counter())
        d[f] += v
        if not att:
            LISTE_NA[y][lista] += v
        cf = fam_csv.get(norm(lista))
        if cf is not None and cf != f:
            mism_csv[(y, lista, cf, f)] += v
    for cod in {c for (c, l) in voti}:
        VALIDI[(y, cod)] = sum(VOTO[(y, cod)].values())
    for (com, coll), (cod, e, vt) in elet.items():
        ELET[(y, cod)] = ELET.get((y, cod), 0) + (e or 0)
    NONATTR[y] = sum(LISTE_NA[y].values()) / sum(v for (yy, c), v in VALIDI.items() if yy == y)
ctrl("   Quota di voti validi di lista in liste non attribuite a nessuna famiglia (finiscono in 'Altri'), tutta l'area: " + ", ".join(f"{y}: {NONATTR[y]*100:.1f}%" for y in ANNI_V))
tot_m = sum(mism_csv.values())
ctrl(f"   Confronto con elezioni/famiglie_partiti.csv: liste con famiglia diversa dalla mia regola, voti coinvolti {tot_m:.0f} su {sum(VALIDI.values()):.0f} (tutti gli anni, tutta l'area):")
agg_m = collections.Counter()
for (y, l, cf, f), v in mism_csv.items(): agg_m[(cf, f)] += v
for (cf, f), v in agg_m.most_common(8): ctrl(f"      file famiglie_partiti.csv = {cf}, qui = {f}: {v:.0f} voti")
nomi_m = collections.Counter()
for (y, l, cf, f), v in mism_csv.items(): nomi_m[(l, cf, f)] += v
for (l, cf, f), v in nomi_m.most_common(6): ctrl(f"         es. '{l}': csv {cf}, qui {f} ({v:.0f} voti)")

# cintura: comuni dell'hinterland dove il PCI superava la soglia nel 1976
SOGLIA_PCI = 0.45
voti76, _, _ = leggi_camera(1976)
pci76 = {}
for cod in UNITS_H:
    tot = sum(v for (c, l), v in voti76.items() if c == cod)
    pci = sum(v for (c, l), v in voti76.items() if c == cod and l == "PCI")
    pci76[cod] = pci / tot
CINTURA = sorted(c for c in UNITS_H if pci76[c] >= SOGLIA_PCI)
pci76_mi = sum(v for (c, l), v in voti76.items() if c == MILANO and l == "PCI") / sum(v for (c, l), v in voti76.items() if c == MILANO)
ctrl(f"   Cintura 'rossa' = comuni dell'hinterland con PCI >= {SOGLIA_PCI*100:.0f}% dei voti di lista alla Camera 1976: {len(CINTURA)} su {len(UNITS_H)} unita (Milano: {pci76_mi*100:.1f}%)")

# ---------------------------------------------------------------- 7. serie per gruppo, per comune, confronti
ctrl("")
ctrl("8. SERIE, SOMME E CONFRONTI")
ANNI_P = YEARS_POP
UN_MEMBERS = collections.defaultdict(list)
for c in ALLC: UN_MEMBERS[UNIT[c]].append(c)

def gs(g, D, y):        # somma di un dizionario anno->cod->valore sul gruppo
    return sum(D[y].get(c, 0) for c in GRUPPI[g])

def up(u, y, D=None):
    D = POP if D is None else D
    return sum(D[y][c] for c in UN_MEMBERS[u])

def r1(x, d=1):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), d)

# --- somma comuni + Milano contro totale provincia (>= 3 anni), da D7B/RBD gia pulito dei filoni popolazione e censimenti
ctrl("   Controllo: somma dei comuni (hinterland + Milano) contro il totale della provincia, dai file ISTAT originali:")
# totali provinciali: RBD ha le righe con codice comune vuoto (totale provincia 015 e 108); POSAS 2020-2022 Milano provincia
def tot_prov_rbd(y):
    df = leggi_csv_zip(P("popolazione", "raw", "istat_demo", f"RBD-Dataset-{y}.csv.zip"), sep=";")
    d = df[(df["Sesso"] == "Maschi e femmine") & (df["Cittadinanza"] == "Tutte") & (df["Codice provincia"].isin(["015", "108"]))]
    out = {}
    for pv in ("015", "108"):
        x = d[(d["Codice provincia"] == pv) & ((d["Codice comune"].isna()) | (d["Codice comune"] == ""))]
        out[pv] = float(x["Popolazione fine periodo"].iloc[0]) if len(x) else None
    return out
for y in (2005, 2012, 2018):
    tp = tot_prov_rbd(y)
    s015 = sum(BIL[(y, c)]["fine"] for c in [MILANO] + MI132)
    s108 = sum(BIL[(y, c)]["fine"] for c in MB55)
    ok = tp["015"] is not None and tp["108"] is not None and round(tp["015"]) == round(s015) and round(tp["108"]) == round(s108)
    ctrl(f"      RBD {y} (31/12): Milano + 132 comuni = {s015:.0f}, totale provincia 015 = {tp['015']}; 55 comuni di Monza e Brianza = {s108:.0f}, totale provincia 108 = {tp['108']} -> {'OK' if ok else 'ERRORE'}")
for y in (2020, 2021, 2022):
    z = zipfile.ZipFile(P("censimenti", "raw", "istat_demo", f"POSAS_{y}_it_015_Milano.zip"))
    nm = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
    dfp = pd.read_csv(z.open(nm), sep=";", skiprows=1, encoding="utf-8-sig", dtype=str, usecols=lambda c: c in ("Codice comune", "Età", "Totale"))
    dfp = dfp[dfp["Età"] == "999"]
    totp = dfp["Totale"].astype(float).sum()
    sm = sum(POP[y][c] for c in ALLC if c == MILANO or COM[c]["gruppo"] == "MI")
    ctrl(f"      POSAS {y} Milano (provincia 015, file del filone censimenti): somma dei suoi comuni {totp:.0f}; Milano + 132 comuni qui {sm:.0f} -> {'OK' if round(totp)==round(sm) else 'ERRORE'}")

# --- stranieri mai piu dei residenti
nbad = sum(1 for y in ANNI_P for c in ALLC if STR[y][c] > POP[y][c])
ctrl(f"   Stranieri maggiori dei residenti (188 comuni x 26 anni): {nbad} casi -> {'OK' if nbad==0 else 'ERRORE'}")
nvuoti = [(y, c) for y in ANNI_P for c in ALLC if c not in POP[y] or c not in STR[y]]
ctrl(f"   Comuni mancanti per anno nelle serie di popolazione e stranieri (attesi 188 per anno, 26 anni): {len(nvuoti)} mancanze -> {'OK' if not nvuoti else 'ERRORE'}")
ctrl(f"   Serie 2001-2018 (RBD) contro 1/1/2019 (POSAS): fine 2018 meno POSAS 2019, Milano {gs('MILANO',POP,2019)-sum(BIL[(2018,c)]['fine'] for c in GRUPPI['MILANO']):.0f}, hinterland {gs('HINT',POP,2019)-sum(BIL[(2018,c)]['fine'] for c in GRUPPI['HINT']):.0f} (nessun salto); stranieri RBD 2018 contro STRASA 2019: Milano {gs('MILANO',STR,2019)-sum(BILS[(2018,c)]['fine'] for c in GRUPPI['MILANO']):.0f}, hinterland {gs('HINT',STR,2019)-sum(BILS[(2018,c)]['fine'] for c in GRUPPI['HINT']):.0f}")
adj = {g: {y: sum(BIL[(y, c)].get("adj", 0) for c in GRUPPI[g]) for y in range(2019, 2025)} for g in ("MILANO", "HINT")}
ctrl("   Aggiustamento statistico (D7B, mese 13) che spiega i salti 2019-2024 (persone): Milano " + str({y: int(v) for y, v in adj['MILANO'].items()}) + "; hinterland " + str({y: int(v) for y, v in adj['HINT'].items()}))
ctrl(f"   Salto del 1 gennaio 2022: Milano {gs('MILANO',POP,2022)-gs('MILANO',POP,2021):+.0f} (di cui aggiustamento {adj['MILANO'][2021]:+.0f}); hinterland {gs('HINT',POP,2022)-gs('HINT',POP,2021):+.0f} (aggiustamento {adj['HINT'][2021]:+.0f}). Il salto del 1 gennaio 2021: Milano {gs('MILANO',POP,2021)-gs('MILANO',POP,2020):+.0f} (aggiustamento {adj['MILANO'][2020]:+.0f}); hinterland {gs('HINT',POP,2021)-gs('HINT',POP,2020):+.0f} (aggiustamento {adj['HINT'][2020]:+.0f})")

# --- reddito medio per gruppo
def red_g(g, y):
    cs = [c for c in GRUPPI[g] if (y, c) in RED]
    return sum(RED[(y, c)]["red"] for c in cs) / sum(RED[(y, c)]["contr"] for c in cs)
mi24 = red_g("MILANO", 2024)
ctrl(f"   Reddito medio per contribuente, Milano 2024: {mi24:,.0f} euro (atteso 40.316 dalla nota dei redditi) -> {'OK' if abs(mi24-40316)<0.6 else 'ERRORE'}")
j22, j23 = red_g("HINT", 2022), red_g("HINT", 2023)
# controllo di continuita 2022-2023: nel 2023 si passa dalla somma delle classi al campo 'reddito complessivo'
m23 = m[(m.anno == 2023) & m.cod.isin(HINT)]
sc23 = m23["somma_classi"].sum() / m23["contribuenti"].sum()
ctrl(f"   Hinterland 2023: con il campo 'reddito complessivo' {j23:,.0f} euro; con la somma delle classi {sc23:,.0f} euro (la somma delle classi sottostima di {100*(1-sc23/j23):.1f}% per le celle oscurate): per questo dal 2023 si usa il campo")
ncelle = {y: sum(1 for c in HINT if (y, c) in RED and RED[(y, c)]["manca"] > 0) for y in range(2000, 2025)}
ctrl("   Comuni dell'hinterland con almeno una classe di reddito oscurata (esclusa la classe <= 0), per anno: " + ", ".join(f"{y}:{n}" for y, n in ncelle.items() if n))

# --- gruppi.json
# --- eta 2002-2018 dalla ricostruzione ISTAT (residenti al 1 gennaio, tutte le cittadinanze), per allungare anziani e bambini
ETA_L = {}                             # (y, cod) -> dict(u15, o65, tot)
_zr = zipfile.ZipFile(P("redditi", "raw", "istat_pop", "ricostruzione_2002_2019_comuni.zip"))
for _n in _zr.namelist():
    _m = re.search(r"Comune_(\d{6})-", _n)
    if not _m or _m.group(1) not in COM: continue
    _righe = _zr.read(_n).decode("utf-8", "replace").splitlines()
    _i = next(i for i, x in enumerate(_righe) if x.startswith("Età/Anno") or x.startswith("Et\ufffd/Anno"))
    _anni = [int(x) for x in _righe[_i].split(";")[1:]]
    _acc = {y: dict(u15=0, o65=0, tot=0) for y in _anni}
    for _r in _righe[_i + 2:]:                       # il primo blocco e' maschi e femmine insieme; finisce con la riga Totale
        _c = _r.split(";")
        if _c[0] == "Totale":
            for y, v in zip(_anni, _c[1:]): _acc[y]["somma_file"] = int(v or 0)
            break
        _e = 100 if _c[0].startswith("100") else int(_c[0])
        for y, v in zip(_anni, _c[1:]):
            v = int(v or 0); _acc[y]["tot"] += v
            if _e <= 14: _acc[y]["u15"] += v
            if _e >= 65: _acc[y]["o65"] += v
    for y in _anni: ETA_L[(y, _m.group(1))] = _acc[y]
ctrl("")
ctrl("   Eta lunga: ricostruzione ISTAT 2002-2019 per comune contro le altre serie")
_bad = [k for k, v in ETA_L.items() if v["tot"] != v["somma_file"]]
ctrl(f"   Righe Totale del file diverse dalla somma delle eta: {len(_bad)}; comuni letti {len({k[1] for k in ETA_L})}/188")
for _g in ("MILANO", "HINT"):
    for _y in (2002, 2010, 2018, 2019):
        _t = sum(ETA_L[(_y, c)]["tot"] for c in GRUPPI[_g]); ctrl(f"      {_g} {_y}: ricostruzione {_t}, serie della pagina {gs(_g, POP, _y):.0f}, differenza {_t - gs(_g, POP, _y):.0f}")
    _t = sum(ETA_L[(2019, c)]["o65"] for c in GRUPPI[_g]); _q = sum(ETA[(2019, c)]["o65"] for c in GRUPPI[_g]); ctrl(f"      {_g} over 65 nel 2019: ricostruzione {_t}, POSAS {_q:.0f}")
def eta_lunga(g, k):
    a = [100 * sum(ETA_L[(y, c)][k] for c in GRUPPI[g]) / sum(ETA_L[(y, c)]["tot"] for c in GRUPPI[g]) for y in range(2002, 2019)]
    a += [100 * sum(ETA[(y, c)][k] for c in GRUPPI[g]) / sum(ETA[(y, c)]["tot"] for c in GRUPPI[g]) for y in range(2019, 2027)]
    return [r1(x, 2) for x in a]

def serie(g):
    out = {}
    out["pop"] = [int(gs(g, POP, y)) for y in ANNI_P]
    out["stran"] = [int(gs(g, STR, y)) for y in ANNI_P]
    nat, it, es, altro, acq = [], [], [], [], []
    for y in range(2001, 2026):
        b = {k: sum(BIL[(y, c)][k] for c in GRUPPI[g]) for k in ("nati", "morti", "iscr_int", "canc_int", "iscr_est", "canc_est")}
        n_, i_, e_ = b["nati"] - b["morti"], b["iscr_int"] - b["canc_int"], b["iscr_est"] - b["canc_est"]
        nat.append(int(n_)); it.append(int(i_)); es.append(int(e_))
        altro.append(int(gs(g, POP, y + 1) - gs(g, POP, y) - n_ - i_ - e_))
    for y in range(2001, 2019):
        acq.append(int(sum(BILS[(y, c)]["acq"] for c in GRUPPI[g])))
    out["nat"] = nat; out["int"] = it; out["est"] = es; out["altro"] = altro; out["acq"] = acq
    out["eta"] = {"anni": list(range(2019, 2027)),
                  "u15": [r1(100 * sum(ETA[(y, c)]["u15"] for c in GRUPPI[g]) / sum(ETA[(y, c)]["tot"] for c in GRUPPI[g]), 2) for y in range(2019, 2027)],
                  "o65": [r1(100 * sum(ETA[(y, c)]["o65"] for c in GRUPPI[g]) / sum(ETA[(y, c)]["tot"] for c in GRUPPI[g]), 2) for y in range(2019, 2027)],
                  "em": [r1(sum(ETA[(y, c)]["sa"] for c in GRUPPI[g]) / sum(ETA[(y, c)]["tot"] for c in GRUPPI[g]), 2) for y in range(2019, 2027)]}
    out["eta_l"] = {"anni": list(range(2002, 2027)), "o65": eta_lunga(g, "o65"), "u15": eta_lunga(g, "u15")}
    out["red"] = {"anni": list(range(2000, 2025)), "medio": [r1(red_g(g, y), 0) for y in range(2000, 2025)],
                  "contr": [int(sum(RED[(y, c)]["contr"] for c in GRUPPI[g] if (y, c) in RED)) for y in range(2000, 2025)]}
    out["pend"] = {"anni": YP, "entra": [int(sum(ENTRA[y][c] for c in GRUPPI[g])) for y in YP], "esce": [int(sum(ESCE[y][c] for c in GRUPPI[g])) for y in YP]}
    return out
GR = {g: serie(g) for g in ("MILANO", "HINT", "MI", "MB")}

# --- per comune
def pend_c(c):
    if c == MILANO: return None
    e = [int(ENTRA[y][c]) for y in YP]
    x = [int(ESCE[y][c]) for y in YP]
    t = [TOT[y][c] for y in YP]
    q = [r1(100 * ENTRA[y][c] / TOT[y][c], 1) if TOT[y][c] else None for y in YP]
    return dict(e=e, x=x, t=[None if v is None else int(v) for v in t], q=q)

def red_c(c):
    out = []
    for y in range(2000, 2025):
        d = RED.get((y, c))
        out.append(None if d is None or d["contr"] == 0 else [r1(d["red"] / d["contr"], 0), d["manca"], int(d["contr"])])
    return out

CJ = []
for c in ALLC:
    u = UNIT[c]; mem = UN_MEMBERS[u]
    p01, p19, p26 = up(u, 2001), up(u, 2019), up(u, 2026)
    d = dict(cod=c, nome=COM[c]["nome"], g=COM[c]["gruppo"], lat=r1(COM[c]["lat"], 5), lon=r1(COM[c]["lon"], 5), km=r1(COM[c]["km"], 1), min=r1(COM[c]["min"], 0),
             unita=u, insieme=len(mem) > 1,
             pop=[int(POP[y][c]) for y in ANNI_P], stran=[int(STR[y][c]) for y in ANNI_P],
             cr=r1(100 * (p26 / p01 - 1), 2), cr19=r1(100 * (p19 / p01 - 1), 2), cr26=r1(100 * (p26 / p19 - 1), 2),
             u15=[r1(100 * ETA[(y, c)]["u15"] / ETA[(y, c)]["tot"], 2) for y in range(2019, 2027)],
             o65=[r1(100 * ETA[(y, c)]["o65"] / ETA[(y, c)]["tot"], 2) for y in range(2019, 2027)],
             em=[r1(ETA[(y, c)]["sa"] / ETA[(y, c)]["tot"], 2) for y in range(2019, 2027)],
             red=red_c(c), pend=pend_c(c),
             fermata=sorted({s["linee"] for s in FERM.get(c, [])}) if c in FERM else [],
             ferm_n=len(FERM.get(c, [])), ferm_anno=min((s["anno"] for s in FERM.get(c, []) if s["anno"]), default=None))
    CJ.append(d)
CD = {d["cod"]: d for d in CJ}

# --- confronto metropolitana: comuni con fermata contro comuni senza fermata a distanza simile da Milano
def q21(u):
    e = sum(ENTRA[2021][c] for c in UN_MEMBERS[u]); t = sum(TOT[2021][c] for c in UN_MEMBERS[u])
    return 100 * e / t
def kmu(u): return COM[u]["km"]
def metrics(u):
    p01, p19, p26 = up(u, 2001), up(u, 2019), up(u, 2026)
    return dict(cr=100 * (p26 / p01 - 1), cr19=100 * (p19 / p01 - 1), q21=q21(u), pop=int(up(u, 2026)))
UH = UNITS_H
CON = {u: {c for c in UN_MEMBERS[u] if c in FERM} for u in UH}
STOP_U = sorted({UNIT[c] for c in FERM})
NOSTOP_U = [u for u in UH if u not in STOP_U]
def confronto(stop_units, nctrl=5):
    out = []
    cs_ok = [u for u in UH if u not in stop_units]
    for s in stop_units:
        ctl = sorted(cs_ok, key=lambda u: (abs(kmu(u) - kmu(s)), u))[:nctrl]
        ms = metrics(s); mc = [metrics(u) for u in ctl]
        out.append(dict(cod=s, nome=COM[s]["nome"], km=r1(kmu(s), 1), anno=min((x["anno"] for c in UN_MEMBERS[s] for x in FERM.get(c, []) if x["anno"]), default=None),
                        linee=sorted({x["linee"] for c in UN_MEMBERS[s] for x in FERM.get(c, [])}),
                        cr=r1(ms["cr"], 1), cr19=r1(ms["cr19"], 1), q21=r1(ms["q21"], 1), pop=ms["pop"],
                        ctl=[dict(cod=u, nome=COM[u]["nome"], km=r1(kmu(u), 1)) for u in ctl],
                        ctl_cr=r1(statistics.median(x["cr"] for x in mc), 1), ctl_cr19=r1(statistics.median(x["cr19"] for x in mc), 1),
                        ctl_q21=r1(statistics.median(x["q21"] for x in mc), 1)))
    return out
MET = confronto(STOP_U)
def sintesi(M):
    n = len(M)
    return dict(n=n, cr_mediana=r1(statistics.median(x["cr"] for x in M), 1), ctl_cr_mediana=r1(statistics.median(x["ctl_cr"] for x in M), 1),
                cr19_mediana=r1(statistics.median(x["cr19"] for x in M), 1), ctl_cr19_mediana=r1(statistics.median(x["ctl_cr19"] for x in M), 1),
                q21_mediana=r1(statistics.median(x["q21"] for x in M), 1), ctl_q21_mediana=r1(statistics.median(x["ctl_q21"] for x in M), 1),
                cr_sopra=sum(1 for x in M if x["cr"] > x["ctl_cr"]), cr19_sopra=sum(1 for x in M if x["cr19"] > x["ctl_cr19"]), q21_sopra=sum(1 for x in M if x["q21"] > x["ctl_q21"]))
MET_S = sintesi(MET)
# sensibilita: con San Donato Milanese contato come comune con fermata (stazione a 68 m dal confine, dentro Milano)
SD = [u for u in UH if COM[u]["nome"] == "San Donato Milanese"][0]
MET_S2 = sintesi(confronto(sorted(set(STOP_U) | {SD})))
# sensibilita 2: solo fermate aperte prima del 2001 (la crescita 2001-2026 puo riflettere una fermata gia presente)
MET_S3 = sintesi([x for x in MET if x["anno"] and x["anno"] < 2001])
# per fasce di distanza da Milano (km stradali)
FASCE = [(0, 10), (10, 15), (15, 20), (20, 30), (30, 200)]
BANDE = []
for a, b in FASCE:
    s_ = [u for u in STOP_U if a <= kmu(u) < b]; n_ = [u for u in NOSTOP_U if a <= kmu(u) < b]
    BANDE.append(dict(da=a, a=b, n_stop=len(s_), n_senza=len(n_),
                      cr_stop=r1(statistics.median(metrics(u)["cr"] for u in s_), 1) if s_ else None,
                      cr_senza=r1(statistics.median(metrics(u)["cr"] for u in n_), 1) if n_ else None,
                      q_stop=r1(statistics.median(metrics(u)["q21"] for u in s_), 1) if s_ else None,
                      q_senza=r1(statistics.median(metrics(u)["q21"] for u in n_), 1) if n_ else None))
ctrl(f"   Metro: {len(STOP_U)} unita con fermata; confronto con i 5 comuni senza fermata piu vicini per distanza: crescita 2001-2026 mediana {MET_S['cr_mediana']}% contro {MET_S['ctl_cr_mediana']}%; la crescita e sopra il confronto in {MET_S['cr_sopra']} casi su {MET_S['n']}")

# ---------------------------------------------------------------- 8. voto: tabelle per unita e per gruppo
def sign_p(k, n):
    """Probabilita (bilaterale) di vedere almeno k successi su n lanciando una moneta equa (test dei segni)."""
    kk = max(k, n - k)
    p = sum(math.comb(n, i) for i in range(kk, n + 1)) / 2 ** n
    return min(1.0, 2 * p)
MET_S["p_cr"] = r1(sign_p(MET_S["cr_sopra"], MET_S["n"]), 2)
MET_S["p_q21"] = r1(sign_p(MET_S["q21_sopra"], MET_S["n"]), 2)

def quote(y, units):
    t = collections.Counter()
    for u in units: t.update(VOTO[(y, u)])
    s = sum(t.values())
    return [r1(100 * t[f] / s, 2) for f in FAMIGLIE], int(s)
RESTO = [u for u in UNITS_H if u not in CINTURA]
SESTO = [u for u in UNITS_H if COM[u]["nome"] == "Sesto San Giovanni"][0]
GV = {"MILANO": [MILANO], "CINTURA": CINTURA, "RESTO": RESTO, "HINT": UNITS_H, "SESTO": [SESTO]}
VJ = {"famiglie": FAMIGLIE, "anni": ANNI_V, "soglia_pci": SOGLIA_PCI, "cintura": CINTURA,
      "nonattr": {y: r1(100 * NONATTR[y], 2) for y in ANNI_V},
      "sistema": {"1976": "proporzionale", "1979": "proporzionale", "1987": "proporzionale", "1992": "proporzionale",
                  "1996": "misto: qui solo la parte proporzionale (25% dei seggi)", "2001": "misto: qui solo la parte proporzionale (25% dei seggi)",
                  "2006": "proporzionale con premio di maggioranza", "2008": "proporzionale con premio di maggioranza", "2013": "proporzionale con premio di maggioranza",
                  "2018": "misto: qui i voti di lista (parte proporzionale)", "2022": "misto: qui i voti di lista (parte proporzionale)"},
      "gruppi": {}, "unita": {}, "pci76": {u: r1(100 * pci76[u], 1) for u in UNITS_H}, "pci76_milano": r1(100 * pci76_mi, 1)}
for g, us in GV.items():
    VJ["gruppi"][g] = {"p": [], "v": []}
    for y in ANNI_V:
        p, v = quote(y, us)
        VJ["gruppi"][g]["p"].append(p); VJ["gruppi"][g]["v"].append(v)
for u in UNITS_H + [MILANO]:
    VJ["unita"][u] = {"p": [quote(y, [u])[0] for y in ANNI_V], "v": [quote(y, [u])[1] for y in ANNI_V]}
VJ["liste_non_attribuite"] = {str(y): [[l, int(v)] for l, v in LISTE_NA[y].most_common(4)] for y in ANNI_V}
VJ["elettori_sezioni"] = None
ctrl("   Liste non attribuite, le piu grandi per anno: " + "; ".join(f"{y}: " + ", ".join(f"{l} {v:.0f}" for l, v in LISTE_NA[y].most_common(2)) for y in ANNI_V if LISTE_NA[y]))
nz = [(y, u) for y in ANNI_V for u in UNITS_H if VALIDI.get((y, u), 0) <= 0]
ctrl(f"   Unita senza voti validi (186 unita x 11 elezioni): {len(nz)} -> {'OK' if not nz else 'ERRORE'}")

# ---------------------------------------------------------------- 9. file di uscita
def jdump(obj, name, indent=None):
    p = os.path.join(DATA, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":") if indent is None else None, indent=indent)
    return os.path.getsize(p)

# comuni.json (+ cintura, fermata e voto 1976)
for d in CJ:
    d["cintura"] = 1 if d["unita"] in CINTURA else 0
    d["pci76"] = VJ["pci76"].get(d["unita"])
jdump(CJ, "comuni.json")

# comuni.csv piatto
with open(os.path.join(DATA, "comuni.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cod", "comune", "gruppo", "unita_confronto", "km_strada_da_milano", "pop_2001_censimento", "pop_2019", "pop_2026_stima", "crescita_2001_2026_pc", "crescita_2001_2019_pc",
                "crescita_2019_2026_pc", "stranieri_2019", "stranieri_2026", "stranieri_2019_pc", "stranieri_2026_pc", "under15_2026_pc", "over65_2026_pc", "eta_media_2026", "reddito_medio_2024_euro", "contribuenti_2024",
                "quota_verso_milano_2021_pc", "entrano_a_milano_2021", "escono_da_milano_verso_il_comune_2021", "fermata_metro", "cintura_pci1976", "pci_1976_pc"])
    for d in CJ:
        r24 = d["red"][24]
        w.writerow([d["cod"], d["nome"], d["g"], d["unita"], d["km"], d["pop"][0], d["pop"][18], d["pop"][25], d["cr"], d["cr19"], d["cr26"],
                    d["stran"][18], d["stran"][25], r1(100 * d["stran"][18] / d["pop"][18], 2), r1(100 * d["stran"][25] / d["pop"][25], 2), d["u15"][7], d["o65"][7], d["em"][7],
                    None if r24 is None else r24[0], None if r24 is None else r24[2],
                    None if d["pend"] is None else d["pend"]["q"][3], None if d["pend"] is None else d["pend"]["e"][3], None if d["pend"] is None else d["pend"]["x"][3],
                    "+".join(d["fermata"]), d["cintura"], d["pci76"]])

# gruppi_serie.csv lungo
with open(os.path.join(DATA, "gruppi_serie.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["gruppo", "anno_1_gennaio", "residenti", "stranieri", "nati_meno_morti_anno_seguente", "iscritti_meno_cancellati_italia_anno_seguente", "iscritti_meno_cancellati_estero_anno_seguente", "altro_rettifiche_anno_seguente"])
    for g in ("MILANO", "HINT", "MI", "MB"):
        for i, y in enumerate(ANNI_P):
            j = i
            w.writerow([g, y, GR[g]["pop"][i], GR[g]["stran"][i]] + ([GR[g]["nat"][j], GR[g]["int"][j], GR[g]["est"][j], GR[g]["altro"][j]] if y <= 2025 else ["", "", "", ""]))

GJ = {"anni": ANNI_P, "anni_bil": list(range(2001, 2026)), "anni_acq": list(range(2001, 2019)), "g": GR,
      "aggiustamento": {g: {str(y): int(v) for y, v in adj[g].items()} for g in adj},
      "cambi": CAMBI, "pend_anni": YP, "famiglie": FAMIGLIE}
jdump(GJ, "gruppi.json")
jdump(VJ, "voto.json")
MJ = {"stazioni": [s for s in STAZ if s["cod"] != MILANO], "stazioni_milano": sum(1 for s in STAZ if s["cod"] == MILANO), "stazioni_tot": len(STAZ),
      "confronto": MET, "sintesi": MET_S, "sintesi_con_san_donato": MET_S2, "sintesi_aperte_prima_2001": MET_S3, "fasce": BANDE, "san_donato_m": sandon[0]["dist_confine_m"]}
for s in MJ["stazioni"]: s["comune"] = COM[s["cod"]]["nome"] if s["cod"] in COM else None
jdump(MJ, "metro.json")

# geojson (confini ISTAT 1/1/2021 gia semplificati dal filone pendolari)
feat = []
for f in gj["features"]:
    cod = f"{f['properties']['i']:06d}"
    if cod in COM:
        feat.append({"type": "Feature", "properties": {"i": cod, "n": COM[cod]["nome"], "g": COM[cod]["gruppo"]}, "geometry": f["geometry"]})
ctrl(f"   Poligoni nel geojson: {len(feat)} (attesi 188) -> {'OK' if len(feat)==188 else 'ERRORE'}")
sz = jdump({"type": "FeatureCollection", "features": feat}, "comuni.geojson")

# ---------------------------------------------------------------- 10. cosa sorprende: numeri calcolati, poi ricalcolati rileggendo i file scritti
def sorprese_memoria():
    s = {}
    s["str_hint"] = int(gs("HINT", STR, 2026)); s["str_mi"] = int(gs("MILANO", STR, 2026))
    s["str_q_hint"] = 100 * gs("HINT", STR, 2026) / gs("HINT", POP, 2026); s["str_q_mi"] = 100 * gs("MILANO", STR, 2026) / gs("MILANO", POP, 2026)
    s["str_hint_2019"] = int(gs("HINT", STR, 2019)); s["str_mi_2019"] = int(gs("MILANO", STR, 2019))
    s["n_q_sopra_mi"] = sum(1 for c in HINT if STR[2026][c] / POP[2026][c] > STR[2026][MILANO] / POP[2026][MILANO])
    s["o65_hint_19"] = GR["HINT"]["eta"]["o65"][0]; s["o65_mi_19"] = GR["MILANO"]["eta"]["o65"][0]
    s["o65_hint_26"] = GR["HINT"]["eta"]["o65"][7]; s["o65_mi_26"] = GR["MILANO"]["eta"]["o65"][7]
    s["em_hint_26"] = GR["HINT"]["eta"]["em"][7]; s["em_mi_26"] = GR["MILANO"]["eta"]["em"][7]
    cs = {y: GV for y in ANNI_V}
    def sc(y, units):
        p, _ = quote(y, units)
        return p[0] + p[1]            # centrosinistra + sinistra
    s["sx_cint_76"] = sc(1976, CINTURA); s["sx_resto_76"] = sc(1976, RESTO); s["sx_mi_76"] = sc(1976, [MILANO])
    s["sx_cint_22"] = sc(2022, CINTURA); s["sx_resto_22"] = sc(2022, RESTO); s["sx_mi_22"] = sc(2022, [MILANO])
    s["n_cintura"] = len(CINTURA)
    s["red_hint_24"] = red_g("HINT", 2024); s["red_mi_24"] = red_g("MILANO", 2024)
    s["red_hint_00"] = red_g("HINT", 2000); s["red_mi_00"] = red_g("MILANO", 2000)
    s["n_sopra_mi"] = [COM[c]["nome"] for c in HINT if RED[(2024, c)]["red"] / RED[(2024, c)]["contr"] > mi24]
    return s
SM = sorprese_memoria()

def sorprese_file():
    """Stesso calcolo, rileggendo comuni.csv e gruppi.json appena scritti (percorso indipendente)."""
    d = pd.read_csv(os.path.join(DATA, "comuni.csv"), dtype={"cod": str})
    g = json.load(open(os.path.join(DATA, "gruppi.json"), encoding="utf-8"))
    v = json.load(open(os.path.join(DATA, "voto.json"), encoding="utf-8"))
    h = d[d.gruppo != "MILANO"]; mi = d[d.gruppo == "MILANO"].iloc[0]
    s = {}
    s["str_hint"] = int(h.stranieri_2026.sum()); s["str_mi"] = int(mi.stranieri_2026)
    s["n_q_sopra_mi"] = int((h.stranieri_2026_pc > mi.stranieri_2026_pc).sum())
    s["o65_hint_19"] = g["g"]["HINT"]["eta"]["o65"][0]; s["o65_mi_19"] = g["g"]["MILANO"]["eta"]["o65"][0]
    s["o65_hint_26"] = g["g"]["HINT"]["eta"]["o65"][7]; s["o65_mi_26"] = g["g"]["MILANO"]["eta"]["o65"][7]
    s["n_cintura"] = int(d[(d.cintura_pci1976 == 1) & (d.gruppo != "MILANO")].unita_confronto.nunique())
    ix76, ix22 = v["anni"].index(1976), v["anni"].index(2022)
    f = v["famiglie"]
    def sc2(gname, ix):
        p = v["gruppi"][gname]["p"][ix]
        return p[f.index("Centrosinistra")] + p[f.index("Sinistra")]
    s["sx_cint_76"] = sc2("CINTURA", ix76); s["sx_resto_76"] = sc2("RESTO", ix76); s["sx_mi_76"] = sc2("MILANO", ix76)
    s["sx_cint_22"] = sc2("CINTURA", ix22); s["sx_resto_22"] = sc2("RESTO", ix22); s["sx_mi_22"] = sc2("MILANO", ix22)
    hh = d[(d.gruppo != "MILANO") & d.reddito_medio_2024_euro.notna()]
    s["n_sopra_mi"] = int((hh.reddito_medio_2024_euro > mi.reddito_medio_2024_euro).sum())
    s["red_hint_24"] = float((hh.reddito_medio_2024_euro * hh.contribuenti_2024).sum() / hh.contribuenti_2024.sum())
    s["red_mi_24"] = float(mi.reddito_medio_2024_euro)
    return s
SF = sorprese_file()
ctrl("")
ctrl("9. RIQUADRO 'COSA SORPRENDE': ogni numero ricalcolato due volte (dalla memoria del programma e rileggendo i file scritti)")
def conf(nome, a, b, tol):
    ok = abs(a - b) <= tol
    ctrl(f"   {nome}: programma {a:,.2f} | dai file {b:,.2f} -> {'OK' if ok else 'ERRORE'}")
    return ok
allok = True
allok &= conf("Stranieri hinterland 1/1/2026", SM["str_hint"], SF["str_hint"], 0)
allok &= conf("Stranieri Milano 1/1/2026", SM["str_mi"], SF["str_mi"], 0)
allok &= conf("Comuni dell'hinterland con quota stranieri oltre Milano", SM["n_q_sopra_mi"], SF["n_q_sopra_mi"], 0)
allok &= conf("Anziani (65+) % hinterland 2019", SM["o65_hint_19"], SF["o65_hint_19"], 0.001)
allok &= conf("Anziani (65+) % Milano 2019", SM["o65_mi_19"], SF["o65_mi_19"], 0.001)
allok &= conf("Anziani (65+) % hinterland 2026", SM["o65_hint_26"], SF["o65_hint_26"], 0.001)
allok &= conf("Anziani (65+) % Milano 2026", SM["o65_mi_26"], SF["o65_mi_26"], 0.001)
allok &= conf("Comuni della cintura", SM["n_cintura"], SF["n_cintura"], 0)
for k in ("sx_cint_76", "sx_resto_76", "sx_mi_76", "sx_cint_22", "sx_resto_22", "sx_mi_22"):
    allok &= conf("Sinistra + centrosinistra % " + k, SM[k], SF[k], 0.011)
allok &= conf("Comuni dell'hinterland sopra il reddito medio di Milano 2024", len(SM["n_sopra_mi"]), SF["n_sopra_mi"], 0)
allok &= conf("Reddito medio hinterland 2024 (euro)", SM["red_hint_24"], SF["red_hint_24"], 1.0)
allok &= conf("Reddito medio Milano 2024 (euro)", SM["red_mi_24"], SF["red_mi_24"], 0.6)
ctrl(f"   Comuni sopra Milano nei redditi 2024: {', '.join(SM['n_sopra_mi'])}")
ctrl(f"   Tutti i numeri del riquadro ricalcolati: {'OK' if allok else 'ALMENO UN ERRORE'}")
foi = {int(r["anno"]): float(r["indice_raccordato_2025_100"]) for r in csv.DictReader(open(P("prezzi-case", "pulito", "foi_annuale.csv"), encoding="utf-8"))}
FOI_0024 = foi[2024] / foi[2000] - 1
ctrl(f"   Inflazione 2000-2024 (indice FOI, prezzi-case/pulito/foi_annuale.csv): {100*FOI_0024:.1f}%  (la nota dei redditi dice circa +57%) -> {'OK' if abs(100*FOI_0024-57)<0.6 else 'DA CONTROLLARE'}")
# peso dei redditi molto alti (oltre 120.000 euro) nel 2022, ultimo anno con le fasce complete anche per i comuni piccoli
ALTI = {}
for g in ("MILANO", "HINT"):
    z = m[(m.anno == 2022) & m.cod.isin(GRUPPI[g])]
    ALTI[g] = dict(pc_contr=100 * z["cl7_oltre120k_n"].sum() / z["contribuenti"].sum(), pc_red=100 * z["cl7_oltre120k_eur"].sum() / z["red"].sum(),
                   comuni_senza_cella=int(z["cl7_oltre120k_eur"].isna().sum()))
    ctrl(f"   Redditi 2022, {g}: contribuenti sopra 120.000 euro = {ALTI[g]['pc_contr']:.1f}% dei contribuenti, {ALTI[g]['pc_red']:.1f}% del reddito totale (comuni con cella oscurata: {ALTI[g]['comuni_senza_cella']})")
RJ = {"alti_2022": ALTI, "foi_2000_2024": FOI_0024, "generato": datetime.date.today().isoformat(), "n_hint": len(HINT), "n_mi": len(MI132), "n_mb": len(MB55), "sorprese": {k: v for k, v in SM.items()},
      "sogli_pci": SOGLIA_PCI, "controlli_ok": bool(allok)}
jdump(RJ, "riepilogo.json")

# ---------------------------------------------------------------- 11. chiusura controlli
ctrl("")
ctrl("10. COMPLETEZZA PER ANNO (nessun comune mancante)")
mancano = {}
for y in ANNI_P:
    mancano[y] = [c for c in ALLC if c not in POP[y] or c not in STR[y]]
ctrl(f"   Popolazione e stranieri 2001-2026: comuni mancanti per anno = {sum(len(v) for v in mancano.values())} -> {'OK' if not any(mancano.values()) else 'ERRORE'}")
mb_ = [(y, c) for y in range(2001, 2026) for c in ALLC if (y, c) not in BIL]
ctrl(f"   Bilancio demografico 2001-2025: coppie anno-comune mancanti = {len(mb_)} -> {'OK' if not mb_ else 'ERRORE'}")
me_ = [(y, c) for y in range(2019, 2027) for c in ALLC if (y, c) not in ETA]
ctrl(f"   Eta 2019-2026: coppie mancanti = {len(me_)} -> {'OK' if not me_ else 'ERRORE'}")
mr_ = [(y, c) for y in range(2004, 2025) for c in ALLC if (y, c) not in RED] + [(y, c) for y in range(2000, 2004) for c in ALLC if c != BAR and (y, c) not in RED]
ctrl(f"   Redditi 2000-2024 (Baranzate dal 2004): coppie mancanti = {len(mr_)} -> {'OK' if not mr_ else 'ERRORE'}")
mp_ = [(y, c) for y in YP for c in HINT if TOT[y][c] is None and not (c == BAR and y < 2004)]
ctrl(f"   Pendolari 1991/2001/2011/2021: comuni senza totale (Baranzate non esiste prima del 2004, i suoi pendolari 1991 e 2001 stanno in Bollate) = {len(mp_)} -> {'OK' if not mp_ else 'ERRORE'}")
ctrl("")
ctrl(f"File scritti in docs/hinterland/data/: " + ", ".join(sorted(os.listdir(DATA))))
with open(os.path.join(OUTD, "controlli.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(CTRL) + "\n")
nerr = sum(1 for l in CTRL if "ERRORE" in l)
print(f"\nFINE. Righe di controllo con ERRORE: {nerr}")
