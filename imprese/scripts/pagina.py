"""Scrive i file dati e la pagina "Imprese che nascono e muoiono" (docs/imprese/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <imprese_dir> <docs_dir>

Legge:   imprese/pulito/*.csv (prodotti da build.py), imprese/scripts/index_template.html,
         imprese/raw/web_probe/downloadCsv.js (solo l'elenco sigle/nomi delle province)
Scrive:  <docs_dir>/imprese/index.html
         <docs_dir>/imprese/data/riepilogo.json, milano_annuale.csv, milano_settori.csv, province_tassi.csv,
         categorie_milano.csv, comune_imprese_attive_settore.csv, controlli.json
Dati aggregati (province, settori, anni). Fonti: Movimprese (InfoCamere per Unioncamere), Rapporto Milano Produttiva
(Camera di commercio di Milano Monza Brianza Lodi), Comune di Milano (CC BY). Ogni numero ha la sua origine in riepilogo.json.
Tassi (come Movimprese e Camera): natalita' = iscrizioni / registrate a fine anno precedente; mortalita' = cessazioni
non d'ufficio / registrate anno precedente; crescita = natalita' - mortalita'.
"""
import sys, os, re, json, shutil, datetime
import numpy as np
import pandas as pd

D, DOCS = sys.argv[1], sys.argv[2]
PUL = os.path.join(D, "pulito")
OUT = os.path.join(DOCS, "imprese", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []


def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")


def num(df):
    for c in df.columns:
        if c not in ("regione_cod", "prov", "CODAT", "DESC", "voce", "Attività economica", "Forma giuridica"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


T = num(pd.read_csv(os.path.join(PUL, "mov_province_totale.csv"), keep_default_na=False, dtype={"prov": str, "regione_cod": str}))
M = num(pd.read_csv(os.path.join(PUL, "mov_milano_settori.csv"), keep_default_na=False, dtype={"CODAT": str}))
FL = pd.read_csv(os.path.join(PUL, "camera_milano_flussi.csv"))
ST = pd.read_csv(os.path.join(PUL, "camera_milano_stock.csv"))
C691 = pd.read_csv(os.path.join(PUL, "comune_ds691.csv"))
C1481 = pd.read_csv(os.path.join(PUL, "comune_ds1481.csv"))
CONTR = json.load(open(os.path.join(PUL, "controlli.json"), encoding="utf8"))

# ---------------------------------------------------------------- nomi province
js = open(os.path.join(D, "raw", "web_probe", "downloadCsv.js"), encoding="utf8", errors="replace").read()
blob = re.search(r"JSON\.parse\('(.*?)'\);", js, flags=re.S).group(1).replace("\\u0027", "'")
RP = json.loads(blob)
NOME = {p["sigla"]: p["descProvincia"].title().replace("D'", "d'").replace("L'", "L'") for r in RP for p in r["province"]}
NOME.update({"FO": "Forlì-Cesena", "PS": "Pesaro e Urbino", "AO": "Aosta", "BZ": "Bolzano", "MB": "Monza e Brianza",
             "RN": "Rimini", "VB": "Verbano-Cusio-Ossola", "MS": "Massa-Carrara", "BT": "Barletta-Andria-Trani"})
REGNOME = {"PIE": "Piemonte", "VAO": "Valle d'Aosta", "LOM": "Lombardia", "TAA": "Trentino-Alto Adige", "VEN": "Veneto",
           "FVG": "Friuli-Venezia Giulia", "LIG": "Liguria", "EMI": "Emilia-Romagna", "TOS": "Toscana", "UMB": "Umbria",
           "MAR": "Marche", "LAZ": "Lazio", "ABR": "Abruzzo", "MOL": "Molise", "CAM": "Campania", "PUG": "Puglia",
           "BAS": "Basilicata", "CAL": "Calabria", "SIC": "Sicilia", "SAR": "Sardegna"}

# ---------------------------------------------------------------- tassi per tutte le province
P = T[T.prov != "0"].copy()
reg = P.pivot(index="anno", columns="prov", values="REGTOT")
rows = []
for _, r in P.iterrows():
    prev = reg.loc[r.anno - 1, r.prov] if (r.anno - 1) in reg.index and r.prov in reg.columns else np.nan
    ces = r.CES_NOUFF_TOT
    rows.append({"anno": int(r.anno), "sigla": r.prov, "provincia": NOME.get(r.prov, r.prov), "regione": REGNOME.get(r.regione_cod, r.regione_cod),
                 "registrate": int(r.REGTOT), "attive": int(r.ATTTOT), "iscrizioni": int(r.ISCTOT), "cessazioni_lorde": int(r.CESTOT),
                 "cancellazioni_ufficio": None if pd.isna(r.CDU_TOT) else int(r.CDU_TOT),
                 "cessazioni_non_ufficio": None if pd.isna(ces) else int(ces),
                 "registrate_anno_prec": None if pd.isna(prev) else int(prev)})
PT = pd.DataFrame(rows)
PT["tasso_natalita_pct"] = (PT.iscrizioni / PT.registrate_anno_prec * 100).round(2)
PT["tasso_mortalita_pct"] = (PT.cessazioni_non_ufficio / PT.registrate_anno_prec * 100).round(2)
PT["tasso_crescita_pct"] = ((PT.iscrizioni - PT.cessazioni_non_ufficio) / PT.registrate_anno_prec * 100).round(2)
PT = PT[PT.anno >= 2007]  # tassi con cancellazioni d'ufficio separate: dal 2006 (primo anno con registrate anno precedente: 2007)
missing_names = sorted(set(PT.loc[PT.provincia == PT.sigla, "sigla"]))
if missing_names:
    AVVISI.append(f"province senza nome: {missing_names}")
PT.to_csv(os.path.join(OUT, "province_tassi.csv"), index=False, encoding="utf8")

# Italia e Lombardia (somma delle righe regione)
RG = T[T.prov == "0"].copy()
IT = RG.groupby("anno")[["REGTOT", "ATTTOT", "ISCTOT", "CESTOT", "CES_NOUFF_TOT"]].sum(min_count=1)
LOMB = RG[RG.regione_cod == "LOM"].set_index("anno")[["REGTOT", "ATTTOT", "ISCTOT", "CESTOT", "CES_NOUFF_TOT"]]


def tassi(df):
    prev = df.REGTOT.shift(1)
    o = pd.DataFrame({"nat": df.ISCTOT / prev * 100, "mor": df.CES_NOUFF_TOT / prev * 100})
    o["cr"] = (df.ISCTOT - df.CES_NOUFF_TOT) / prev * 100
    return o.round(2)


TIT, TLO = tassi(IT), tassi(LOMB)

# ---------------------------------------------------------------- Milano: serie annuale (perimetro attuale 2007-2025)
MI = T[T.prov == "MI"].set_index("anno")
MB = T[T.prov == "MB"].set_index("anno")
FORME = ["SC", "SP", "DI", "AF"]
mi_anno = []
for a in range(2007, 2026):
    r = MI.loc[a]
    prev = MI.loc[a - 1, "REGTOT"] if (a - 1) in MI.index and a - 1 >= 2007 else None
    d = {"a": a, "reg": int(r.REGTOT), "att": int(r.ATTTOT), "isc": int(r.ISCTOT), "ces_lorde": int(r.CESTOT),
         "cdu": int(r.CDU_TOT), "ces": int(r.CES_NOUFF_TOT), "saldo": int(r.ISCTOT - r.CES_NOUFF_TOT)}
    if prev:
        d["nat"] = round(r.ISCTOT / prev * 100, 2)
        d["mor"] = round(r.CES_NOUFF_TOT / prev * 100, 2)
        d["cr"] = round((r.ISCTOT - r.CES_NOUFF_TOT) / prev * 100, 2)
    d["forme"] = {f: {"isc": int(r["ISC" + f]), "ces_lorde": int(r["CES" + f]), "cdu": int(r["CDU_" + f]),
                      "ces": int(r["CES" + f] - r["CDU_" + f]), "reg": int(r["REG" + f]), "att": int(r["ATT" + f])} for f in FORME}
    mi_anno.append(d)

# Milano + Monza e Brianza = vecchio perimetro della provincia di Milano (Monza e' provincia a se' dal 2007)
vecchio = []
for a in range(2000, 2026):
    r = MI.loc[a]
    isc, ces_l, reg_, att = r.ISCTOT, r.CESTOT, r.REGTOT, r.ATTTOT
    cdu = r.CDU_TOT
    if a >= 2007:
        b = MB.loc[a]
        isc += b.ISCTOT; ces_l += b.CESTOT; reg_ += b.REGTOT; att += b.ATTTOT; cdu = cdu + b.CDU_TOT
    vecchio.append({"a": a, "reg": int(reg_), "att": int(att), "isc": int(isc), "ces_lorde": int(ces_l),
                    "cdu": None if pd.isna(cdu) else int(cdu),
                    "ces": None if pd.isna(cdu) else int(ces_l - cdu)})
V = pd.DataFrame(vecchio)
V["nat"] = (V.isc / V.reg.shift(1) * 100).round(2)
V["lorda_pct"] = (V.ces_lorde / V.reg.shift(1) * 100).round(2)
V["mor"] = (V.ces / V.reg.shift(1) * 100).round(2)
vecchio = [{k: (None if (isinstance(v, float) and np.isnan(v)) else (int(v) if k in ("a", "reg", "att", "isc", "ces_lorde", "cdu", "ces") and v is not None and not (isinstance(v, float) and np.isnan(v)) else v))
            for k, v in row.items()} for row in V.to_dict("records")]

# CSV annuale
ma = []
for d in mi_anno:
    row = {"anno": d["a"], "perimetro": "provincia di Milano (senza Monza e Brianza)", "registrate": d["reg"], "attive": d["att"],
           "iscrizioni": d["isc"], "cessazioni_lorde": d["ces_lorde"], "cancellazioni_ufficio": d["cdu"], "cessazioni_non_ufficio": d["ces"],
           "saldo": d["saldo"], "tasso_natalita_pct": d.get("nat"), "tasso_mortalita_pct": d.get("mor"), "tasso_crescita_pct": d.get("cr")}
    for f, n in zip(FORME, ["societa_di_capitali", "societa_di_persone", "ditte_individuali", "altre_forme"]):
        row[f"iscrizioni_{n}"] = d["forme"][f]["isc"]
        row[f"cessazioni_non_ufficio_{n}"] = d["forme"][f]["ces"]
        row[f"cancellazioni_ufficio_{n}"] = d["forme"][f]["cdu"]
        row[f"attive_{n}"] = d["forme"][f]["att"]
    ma.append(row)
pd.DataFrame(ma).to_csv(os.path.join(OUT, "milano_annuale.csv"), index=False, encoding="utf8")
pd.DataFrame(vecchio).to_csv(os.path.join(OUT, "milano_piu_monza_brianza_2000_2025.csv"), index=False, encoding="utf8")

# ---------------------------------------------------------------- settori (Milano, ATECO 2007, 2009-2025)
SEZ = {"A": "Agricoltura, silvicoltura, pesca", "B": "Estrazione di minerali", "C": "Attività manifatturiere",
       "D": "Energia elettrica, gas", "E": "Acqua, rifiuti", "F": "Costruzioni", "G": "Commercio (ingrosso e dettaglio)",
       "H": "Trasporto e magazzinaggio", "I": "Alloggio e ristorazione", "J": "Informazione e comunicazione",
       "K": "Finanza e assicurazioni", "L": "Attività immobiliari", "M": "Attività professionali, scientifiche, tecniche",
       "N": "Noleggio, viaggi, servizi alle imprese", "O": "Pubblica amministrazione", "P": "Istruzione",
       "Q": "Sanità e assistenza sociale", "R": "Arte, sport, intrattenimento", "S": "Altri servizi (parrucchieri, riparazioni...)",
       "T": "Famiglie come datori di lavoro", "U": "Organismi extraterritoriali", "NC": "Imprese non classificate"}
S = M[(M.anno >= 2009) & (M.CODAT.isin(list(SEZ)))].copy()
sett = {}
for c in SEZ:
    s = S[S.CODAT == c].set_index("anno")
    sett[c] = {str(a): [int(r.ATTTOT), int(r.ISCTOT), int(r.CESTOT), int(r.CDU_TOT)] for a, r in s.iterrows()}
# controllo: somma settori = totale
for a in (2009, 2019, 2025):
    ss = S[S.anno == a]
    tot = M[(M.anno == a) & (M.CODAT == "TOT")].iloc[0]
    check(f"somma settori iscrizioni {a}", int(ss.ISCTOT.sum()), int(tot.ISCTOT))
    check(f"somma settori cancellazioni d'ufficio {a}", int(ss.CDU_TOT.sum()), int(tot.CDU_TOT))
    check(f"somma settori attive {a}", int(ss.ATTTOT.sum()), int(tot.ATTTOT))
sc = S[["anno", "CODAT", "ATTTOT", "REGTOT", "ISCTOT", "CESTOT", "CDU_TOT"]].copy()
sc["settore"] = sc.CODAT.map(SEZ)
sc["cessazioni_non_ufficio"] = sc.CESTOT - sc.CDU_TOT
sc = sc.rename(columns={"CODAT": "codice_ateco2007", "ATTTOT": "attive", "REGTOT": "registrate", "ISCTOT": "iscrizioni", "CESTOT": "cessazioni_lorde", "CDU_TOT": "cancellazioni_ufficio"})
sc[["anno", "codice_ateco2007", "settore", "registrate", "attive", "iscrizioni", "cessazioni_lorde", "cancellazioni_ufficio", "cessazioni_non_ufficio"]].to_csv(
    os.path.join(OUT, "milano_settori.csv"), index=False, encoding="utf8")

# alcune divisioni utili (commercio al dettaglio 47, ristorazione 56)
div = {}
for code, nome in [("G 47", "Commercio al dettaglio (escluso auto e moto)"), ("I 56", "Ristorazione (bar, ristoranti, mense)"), ("I 55", "Alloggio (alberghi e simili)")]:
    s = M[(M.anno >= 2009) & (M.CODAT == code)].set_index("anno")
    div[code] = {"n": nome, "d": {str(a): [int(r.ATTTOT), int(r.ISCTOT), int(r.CESTOT), int(r.CDU_TOT)] for a, r in s.iterrows()}}

# ---------------------------------------------------------------- province: tabelle per anno e serie
prov_anni = {}
for a in range(2008, 2026):
    x = PT[PT.anno == a].dropna(subset=["tasso_crescita_pct"])
    prov_anni[str(a)] = [[r.sigla, r.provincia, int(r.iscrizioni), int(r.cessazioni_non_ufficio), r.tasso_natalita_pct, r.tasso_mortalita_pct, r.tasso_crescita_pct, int(r.registrate)]
                         for r in x.itertuples()]
CONF = ["MI", "RM", "TO", "NA", "BO", "FI", "MB", "GE", "BG", "BS"]
serie = {}
for s in CONF:
    x = PT[(PT.sigla == s) & (PT.anno >= 2008)].sort_values("anno")
    serie[s] = {"n": NOME.get(s, s), "a": x.anno.tolist(), "nat": x.tasso_natalita_pct.tolist(), "mor": x.tasso_mortalita_pct.tolist(), "cr": x.tasso_crescita_pct.tolist()}
serie["IT"] = {"n": "Italia", "a": list(range(2008, 2026)), "nat": TIT.loc[2008:2025, "nat"].tolist(), "mor": TIT.loc[2008:2025, "mor"].tolist(), "cr": TIT.loc[2008:2025, "cr"].tolist()}
serie["LOM"] = {"n": "Lombardia", "a": list(range(2008, 2026)), "nat": TLO.loc[2008:2025, "nat"].tolist(), "mor": TLO.loc[2008:2025, "mor"].tolist(), "cr": TLO.loc[2008:2025, "cr"].tolist()}

# controlli contro il Rapporto della Camera (tab.1 ed.2026): Milano 2,37%, Monza 1,06%, Lodi 0,38%, Lombardia 1,41%, Italia 0,96%
x25 = PT[PT.anno == 2025].set_index("sigla")
check("tasso crescita Milano 2025 (Camera 2,37)", x25.loc["MI", "tasso_crescita_pct"], 2.37, 0.01)
check("tasso crescita Monza Brianza 2025 (Camera 1,06)", x25.loc["MB", "tasso_crescita_pct"], 1.06, 0.01)
check("tasso crescita Lodi 2025 (Camera 0,38)", x25.loc["LO", "tasso_crescita_pct"], 0.38, 0.01)
check("tasso crescita Lombardia 2025 (Camera 1,41)", float(TLO.loc[2025, "cr"]), 1.41, 0.01)
check("tasso crescita Italia 2025 (Camera 0,96)", float(TIT.loc[2025, "cr"]), 0.96, 0.01)
check("Italia iscrizioni 2025 (Camera 323.533)", int(IT.loc[2025, "ISCTOT"]), 323533)
check("Italia cessazioni non d'ufficio 2025 (Camera 266.934)", int(IT.loc[2025, "CES_NOUFF_TOT"]), 266934)
check("Lombardia registrate 2025 (Camera 940.477)", int(LOMB.loc[2025, "REGTOT"]), 940477)
for a, (ei, ec) in {2024: (26002, 18207), 2023: (25099, 17109), 2022: (25195, 17069), 2021: (24946, 16334), 2019: (24897, 18647), 2018: (23883, 18453)}.items():
    d = [x for x in mi_anno if x["a"] == a][0]
    check(f"Milano {a} iscrizioni (Camera)", d["isc"], ei)
    check(f"Milano {a} cessazioni non d'ufficio (Camera)", d["ces"], ec)

# ---------------------------------------------------------------- categorie (Camera di commercio)
cat_nomi = {"Artigiane": "artigiane", "Giovanili": "giovanili", "Femminili": "femminili", "Straniere": "straniere"}
categorie = {}
for k, nome in cat_nomi.items():
    f = FL[FL.voce == k].sort_values("anno")
    categorie[nome] = {"a": f.anno.tolist(), "isc": f.milano_iscritte.tolist(), "ces": f.milano_cessate.tolist()}
tot_f = FL[FL.voce == "Totale"].sort_values("anno")
categorie["totale"] = {"a": tot_f.anno.tolist(), "isc": tot_f.milano_iscritte.tolist(), "ces": tot_f.milano_cessate.tolist()}
stock = {"a": ST.anno.tolist()}
for k in ("giovanili", "femminili", "straniere"):
    stock[k] = ST[f"{k}_attive"].tolist()
    stock[k + "_addetti"] = ST[f"{k}_addetti"].tolist()
att_milano = {int(r.anno): int(r.ATTTOT) for r in MI.reset_index().itertuples()}
stock["att_tot"] = [att_milano[a] for a in ST.anno]
# controllo: attive 2025 (Camera tab.3: 314.726)
check("Milano attive 2025 (Camera)", att_milano[2025], 314726)
cat_rows = []
for k in ("artigiane", "giovanili", "femminili", "straniere", "totale"):
    for a, i_, c_ in zip(categorie[k]["a"], categorie[k]["isc"], categorie[k]["ces"]):
        row = {"anno": a, "categoria": k, "iscritte": i_, "cessate_non_ufficio": c_, "attive": None, "addetti_sedi": None}
        if k in stock:
            j = stock["a"].index(a)
            row["attive"] = stock[k][j]; row["addetti_sedi"] = stock[k + "_addetti"][j]
        cat_rows.append(row)
pd.DataFrame(cat_rows).to_csv(os.path.join(OUT, "categorie_milano.csv"), index=False, encoding="utf8")

# ---------------------------------------------------------------- Comune di Milano (ds691, ds1481)
tot_comune = C691.groupby("Anno").Imprese.sum().to_dict()
att_prov = {int(a): v for a, v in att_milano.items()}
comune_settori = {}
A24 = C691[C691.Anno <= 2024]
SHORT = {"Agricoltura, silvicoltura pesca": "Agricoltura", "Altre attività di servizi": "Altri servizi",
         "Amministrazione pubblica e difesa assicurazione sociale obbligatoria": "Pubblica amministrazione",
         "Attività artistiche, sportive e di divertimento": "Arte, sport, intrattenimento",
         "Attività dei servizi di alloggio e di ristorazione": "Alloggio e ristorazione",
         "Attività di organizzazioni ed organismi extraterritoriali": "Organismi extraterritoriali",
         "Attività estrattive": "Estrazione", "Attività finanziarie e assicurative": "Finanza e assicurazioni",
         "Attività immobiliari": "Attività immobiliari", "Attività manifatturiere": "Manifattura",
         "Attività per la salute umana e di assistenza sociale": "Sanità e assistenza",
         "Attività professionali, scientifiche e tecniche": "Attività professionali e tecniche",
         "Commercio all'ingrosso e al dettaglio riparazione di autoveicoli e motocicli": "Commercio",
         "Costruzioni": "Costruzioni",
         "Fornitura di acqua gestione di reti fognarie, attività di trattamento dei rifiuti e risanamento": "Acqua e rifiuti",
         "Fornitura di energia elettrica, gas, vapore e aria condizionata": "Energia", "Imprese non classificate": "Non classificate",
         "Istruzione e formazione": "Istruzione", "Noleggio, agenzie di viaggio, servizi di supporto alle imprese": "Noleggio, viaggi, servizi alle imprese",
         "Servizi di informazione e comunicazione": "Informazione e comunicazione", "Trasporto e magazzinaggio": "Trasporto e magazzinaggio",
         "Attività di famiglie e convivenze come datori di lavoro per personale domestico": "Famiglie datori di lavoro"}
for nome, g in A24.groupby("Attività economica"):
    comune_settori[SHORT.get(nome, nome)] = {str(int(a)): int(v) for a, v in zip(g.Anno, g.Imprese)}
for_g = C1481.pivot(index="Anno", columns="Forma giuridica", values="Numero di Imprese")
comune_forme = {"a": for_g.index.tolist(), "ind": for_g["Imprenditore individuale, libero professionista, lavoratore autonomo"].tolist(),
                "sp": for_g["Societa' di persone"].tolist(), "sc": for_g["Societa' di capitali"].tolist(),
                "coop": for_g["Societa' Cooperativa"].tolist(), "altro": for_g["Altro"].tolist()}
cs = C691.copy()
cs["settore"] = cs["Attività economica"].map(lambda s: SHORT.get(s, s))
cs.rename(columns={"Anno": "anno", "Imprese": "imprese_attive"})[["anno", "settore", "imprese_attive"]].to_csv(
    os.path.join(OUT, "comune_imprese_attive_settore.csv"), index=False, encoding="utf8")

# ---------------------------------------------------------------- riepilogo
today = datetime.date.today().isoformat()
RIEP = {
    "aggiornato": today,
    "ultimo_anno": 2025,
    "milano": mi_anno,
    "milano_vecchio_perimetro": vecchio,
    "settori": {"nomi": SEZ, "dati": sett, "divisioni": div},
    "province": {"anni": prov_anni, "serie": serie, "ordine_confronto": CONF + ["IT", "LOM"]},
    "categorie": categorie,
    "stock_categorie": stock,
    "comune": {"settori": comune_settori, "totale": {str(k): int(v) for k, v in tot_comune.items()},
               "attive_provincia": {str(k): v for k, v in att_prov.items()}, "forme_asia": comune_forme},
    "origine": {
        "milano/province/settori": "Movimprese (InfoCamere per Unioncamere), file annuali 'Totale imprese' 2000-2025 (raw/movimprese/<anno>_a_2d.zip: movi_YY.txt, CDUYYYY.xls)",
        "cessazioni non d'ufficio": "cessazioni (CES) meno cancellazioni d'ufficio (CDU) come nel glossario Movimprese; dal 2021 coincide con la colonna CES...NOUFF pubblicata (controlli.json)",
        "categorie": "Camera di commercio di Milano Monza Brianza Lodi, Rapporto Milano Produttiva ed. 2019-2026, capitolo 'Struttura e dinamica delle imprese locali' (tabelle 2 e 7/8)",
        "comune": "Comune di Milano, dati.comune.milano.it ds691 (imprese attive per settore) e ds1481 (imprese per forma giuridica, ASIA), CC BY",
    },
}
json.dump(RIEP, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump({"verifiche_pagina": AVVISI, "build": CONTR}, open(os.path.join(OUT, "controlli.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- pagina
tpl = open(os.path.join(D, "scripts", "index_template.html"), encoding="utf8").read()
open(os.path.join(DOCS, "imprese", "index.html"), "w", encoding="utf8", newline="\n").write(tpl)

print("\nAVVISI:", AVVISI if AVVISI else "nessuno")
sys.exit(1 if AVVISI else 0)
