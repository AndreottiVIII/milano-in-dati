"""Fase 1 - pulizia dei dati Movimprese (InfoCamere/Unioncamere) e delle tabelle del Rapporto Milano Produttiva.

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 build.py <imprese_dir>

Legge:   raw/movimprese/<anno>_a_2d.zip   (2000-2025; 1997-1999 sono eseguibili .exe: mai aperti)
         raw/camera_commercio/mp*_cap_imprese.txt  (testo estratto dai PDF del Rapporto Milano Produttiva, ed. 2019-2026)
         raw/comune_ds691, ds1481, ds1482 (Comune di Milano, CC BY)
Scrive:  pulito/mov_province_totale.csv     una riga per anno e per territorio (provincia o regione), solo "TOTALE"
         pulito/mov_milano_settori.csv      Milano, anno, codice ATECO (sezioni, divisioni, NC, TOT) 2000-2025
         pulito/camera_milano_flussi.csv     Milano: iscritte/cessate per settore, forma, tipologia (2018-2025)
         pulito/camera_milano_stock.csv      Milano: imprese ATTIVE giovanili/femminili/straniere (2018-2025)
         pulito/controlli.json               confronti tra fonti diverse
Nessun valore viene corretto: cessazioni "non d'ufficio" = cessazioni - cessazioni d'ufficio (CDU) come nel glossario Movimprese.
"""
import sys, os, re, io, json, zipfile, warnings
import pandas as pd

warnings.filterwarnings("ignore")
D = sys.argv[1]
RAW = os.path.join(D, "raw")
PUL = os.path.join(D, "pulito")
os.makedirs(PUL, exist_ok=True)
CONTROLLI = {}

FORME = ["TOT", "SC", "SP", "DI", "AF"]
FLOW = ["REG", "ATT", "ISC", "CES", "VAR"]


def leggi_zip(y):
    return zipfile.ZipFile(os.path.join(RAW, "movimprese", f"{y}_a_2d.zip"))


def trova(z, pattern):
    cand = [i.filename for i in z.infolist() if re.search(pattern, i.filename, re.I) and not i.filename.startswith("var/")]
    assert cand, pattern
    return cand[0]


def parse_movi(y):
    z = leggi_zip(y)
    n = trova(z, r"(^|/)movi_\d\d\.txt$")
    txt = z.read(n).decode("latin-1")
    rows = [[c.strip().strip('"').strip() for c in l.split("\t")] for l in txt.splitlines()]
    head = [h for h in rows[0] if h != ""]
    df = pd.DataFrame([r[: len(head)] for r in rows[1:]], columns=head)
    for c in head[4:]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    df["PROV"] = df["PROV"].str.strip()
    df["CODAT"] = df["CODAT"].str.strip()
    df["anno"] = y
    return df


def parse_cdu(y):
    """cancellazioni d'ufficio per REG, PROV, CODAT (2006-2025). Ritorna df con CDU_TOT, CDU_SC, CDU_SP, CDU_DI, CDU_AF."""
    z = leggi_zip(y)
    n = trova(z, r"(^|/)cdu\d{4}\.xlsx?$")
    data = z.read(n)
    xl = pd.ExcelFile(io.BytesIO(data))
    sh = "ANNO" if "ANNO" in xl.sheet_names else xl.sheet_names[0]
    df = xl.parse(sh, dtype=str, keep_default_na=False)  # "NA" e' Napoli: non e' un valore mancante
    df.columns = [str(c).strip() for c in df.columns]
    out = pd.DataFrame({"REG": df["REG"].str.strip(), "PROV": df["PROV"].fillna("0").str.strip().replace("", "0"),
                        "CODAT": df["CODAT"].str.strip()})
    for f in FORME:
        out["CDU_" + f] = pd.to_numeric(df["CESSUFF" + f], errors="coerce").fillna(0).astype(int)
    out["anno"] = y
    # il file CDU ripete alcune righe (Campania): tengo la prima e verifico che le ripetizioni siano uguali
    dup = out[out.duplicated(["REG", "PROV", "CODAT"], keep=False)]
    chk = dup.groupby(["REG", "PROV", "CODAT"]).nunique().max().max() if len(dup) else 1
    assert chk == 1, (y, "righe ripetute con valori diversi nel file CDU")
    CONTROLLI[f"{y}_cdu_righe_ripetute_nel_file"] = int(out.duplicated(["REG", "PROV", "CODAT"]).sum())
    return out.drop_duplicates(["REG", "PROV", "CODAT"])


# ------------------------------------------------------------------ Movimprese
tot_rows, mi_rows = [], []
for y in range(2000, 2026):
    m = parse_movi(y)
    if y < 2009:
        # fino al 2008 i settori sono ATECO 2002 (non confrontabili con ATECO 2007): tengo solo le righe TOT
        m = m[m["CODAT"] == "TOT"].copy()
    if y >= 2006:
        c = parse_cdu(y)
        m = m.merge(c.drop(columns="anno"), on=["REG", "PROV", "CODAT"], how="left")
        if y < 2009:
            assert m["CDU_TOT"].notna().all(), y
    if y >= 2009:
        # il file CDU non ha la riga "NC" (imprese non classificate): la ricavo per differenza (riga TOT - somma delle sezioni)
        sez = m["CODAT"].str.fullmatch(r"[A-Z]") & ~m["CODAT"].isin(["NC"])
        for f in FORME:
            somma = m[sez].groupby(["REG", "PROV"])["CDU_" + f].sum()
            tot_f = m[m["CODAT"] == "TOT"].set_index(["REG", "PROV"])["CDU_" + f]
            resto = (tot_f - somma).rename("resto")
            assert (resto.dropna() >= 0).all(), (y, f, resto[resto < 0])
            idx = m["CODAT"] == "NC"
            keys = list(zip(m.loc[idx, "REG"], m.loc[idx, "PROV"]))
            m.loc[idx, "CDU_" + f] = [resto.get(k) for k in keys]
        mancanti = m[m["CDU_TOT"].isna()]
        CONTROLLI[f"{y}_righe_senza_cdu_dopo_NC"] = mancanti[["PROV", "CODAT"]].drop_duplicates().values.tolist()[:10]
        assert len(mancanti) == 0, (y, len(mancanti))
        for f in FORME:
            m["CDU_" + f] = m["CDU_" + f].astype(int)
        # confronto con le colonne "NOUFF" pubblicate dal 2021
        if y >= 2021:
            for f in FORME:
                pub = m["CES" + f + "NOUFF"] if f != "TOT" else m["CESTOTNOUFF"]
                mio = m["CES" + f] - m["CDU_" + f]
                CONTROLLI[f"{y}_{f}_cesnouff_pubblicato_vs_calcolato_righe_diverse"] = int((pub != mio).sum())
    if y < 2006:
        for f in FORME:
            m["CDU_" + f] = pd.NA
    # tabella province/regioni: solo righe TOT
    t = m[m["CODAT"] == "TOT"].copy()
    tot_rows.append(t)
    mi_rows.append(m[(m["PROV"] == "MI")].copy())

# regione = codice a 3 lettere (colonna REG del file); la colonna "REGTOT" e' lo stock: rinomino per evitare confusioni
tot = pd.concat(tot_rows, ignore_index=True)
tot = tot.rename(columns={"REG": "regione_cod", "PROV": "prov"})
nrep = int(tot.duplicated(["anno", "regione_cod", "prov"]).sum())
CONTROLLI["righe_TOT_ripetute_nei_file_movi (es. Campania)"] = nrep
tot = tot.drop_duplicates(["anno", "regione_cod", "prov"])
keep = ["anno", "regione_cod", "prov"] + [c for c in tot.columns if re.match(r"^(REG|ATT|ISC|CES|VAR)(TOT|SC|SP|DI|AF)$", c) or c.startswith("CDU_")]
tot = tot[keep]
tot["CES_NOUFF_TOT"] = tot["CESTOT"] - tot["CDU_TOT"].astype("Float64")
tot.to_csv(os.path.join(PUL, "mov_province_totale.csv"), index=False, encoding="utf8")

mi = pd.concat(mi_rows, ignore_index=True).rename(columns={"REG": "regione_cod", "PROV": "prov"})
mi = mi.drop_duplicates(["anno", "CODAT"])
keep = ["anno", "CODAT", "DESC"] + [c for c in mi.columns if re.match(r"^(REG|ATT|ISC|CES|VAR)(TOT|SC|SP|DI|AF)$", c) or c.startswith("CDU_")]
mi = mi[keep]
mi["CES_NOUFF_TOT"] = mi["CESTOT"] - mi["CDU_TOT"].astype("Float64")
mi.to_csv(os.path.join(PUL, "mov_milano_settori.csv"), index=False, encoding="utf8")

# ------------------------------------------------------------------ controlli Movimprese
T = tot
it = T[T.prov == "0"].groupby("anno")[["REGTOT", "ATTTOT", "ISCTOT", "CESTOT"]].sum()
CONTROLLI["italia_2025_registrate"] = int(it.loc[2025, "REGTOT"])
CONTROLLI["atteso_italia_2025_registrate_(Camera, tab.1 ed.2026)"] = 5849524
lom = T[(T.regione_cod == "LOM") & (T.prov == "0") & (T.anno == 2025)]
CONTROLLI["lombardia_2025_registrate"] = int(lom.REGTOT.iloc[0])
CONTROLLI["atteso_lombardia_2025_registrate"] = 940477
m25 = T[(T.prov == "MI") & (T.anno == 2025)].iloc[0]
CONTROLLI["milano_2025_iscrizioni_cesnouff"] = [int(m25.ISCTOT), int(m25.CES_NOUFF_TOT)]
CONTROLLI["atteso_milano_2025_(Camera tab.1)"] = [26262, 17083]

# ------------------------------------------------------------------ Camera di commercio: parsing dei testi estratti
EDIZ = {2019: 2018, 2020: 2019, 2021: 2020, 2022: 2021, 2023: 2022, 2024: 2023, 2025: 2024, 2026: 2025}


def num(s):
    s = s.replace(" ", "").replace(".", "")
    return int(s)


def milano_numeri(riga, n):
    """prende i primi n numeri interi della riga (formato italiano, es. '26.262 4.514 922')."""
    t = riga.replace(" .", ".").replace(". ", ".")
    t = re.sub(r"(\d) (\.)", r"\1\2", t)
    t = re.sub(r"(\d)\s*\.\s*(\d{3})", r"\1.\2", t)
    vals = re.findall(r"\d{1,3}(?:\.\d{3})*", t)
    return [int(v.replace(".", "")) for v in vals][:n]


flussi = []
stock = []
for ed, anno in EDIZ.items():
    path = os.path.join(RAW, "camera_commercio", f"mp{ed}_cap_imprese.txt")
    t = open(path, encoding="utf8").read()
    # --- tabella 2 (flussi): righe con 6 numeri (Milano, Monza, Lodi iscritte; Milano, Monza, Lodi cessate)
    i0 = t.find("Settori")
    # la tabella inizia dopo "Imprese iscritte e cessate" / "Iscrizioni e cessazioni per settore"
    m0 = re.search(r"tabella 2 – (Imprese iscritte e cessate|Iscrizioni e cessazioni)", t)
    seg = t[m0.start(): m0.start() + 3800]
    # dalla tabella 2 prendo solo Totale, forme giuridiche e tipologie: i settori li prendo da Movimprese
    # (il testo estratto dal PDF per alcune righe dei servizi ha cifre spezzate)
    etichette = [
        ("Totale", r"^Totale"),
        ("Società di capitali", r"^Società di capitali"), ("Società di persone", r"^Società di persone"),
        ("Ditte individuali", r"^Ditte [Ii]ndividuali"), ("Altre forme", r"^Altre forme"),
        ("Artigiane", r"^Artigiane"), ("Giovanili", r"^Giovanili"), ("Femminili", r"^Femminili"), ("Straniere", r"^Straniere"),
    ]
    righe = seg.splitlines()
    trovate = {}
    for k, (nome, pat) in enumerate(etichette):
        for j, r in enumerate(righe):
            if re.match(pat, r.strip()):
                # i numeri possono stare nella riga dopo (etichette spezzate su due righe: es. "Commercio all'ingrosso\ne al dettaglio 3.133 ...")
                cand = r
                if len(milano_numeri(re.sub(r"^[^\d]*", "", r), 6)) < 6 and j + 1 < len(righe):
                    cand = r + " " + righe[j + 1]
                nn = milano_numeri(re.sub(r"^[^\d]*", "", cand), 6)
                if len(nn) == 6:
                    trovate[nome] = nn
                    break
    # per il Commercio nel 2019/2020 l'etichetta e' "Commercio all'ingrosso e al dettaglio" su 2 righe: gestita sopra
    for nome, nn in trovate.items():
        flussi.append({"anno": anno, "edizione": ed, "voce": nome, "milano_iscritte": nn[0], "milano_cessate": nn[3]})
    assert "Totale" in trovate, (ed, "Totale non trovato")
    miss = [e[0] for e in etichette if e[0] not in trovate]
    # alcune edizioni non hanno 'Altre industrie' separato o hanno nomi diversi: segnalo
    CONTROLLI[f"camera_ed{ed}_voci_mancanti"] = miss
    # --- stock imprese attive (tabella 'Imprese giovanili, femminili e straniere ... per area geografica')
    mm = re.search(r"tabella \d+ – Imprese giovanili, femminili e straniere[^\n]*(?:\n[^\n]*){0,3}?\n?[^\n]*per area", t)
    mm = re.search(r"tabella \d+ – Imprese giovanili, femminili e straniere[^\n]*(?:attive|addetti)[^\n]*\n?[^\n]*per area[^\n]*", t) or mm
    seg2 = t[mm.start(): mm.start() + 1200]
    mil = [r for r in seg2.splitlines() if r.startswith("Milano")][0]
    nn = milano_numeri(mil, 6)
    assert len(nn) == 6, (ed, mil)
    stock.append({"anno": anno, "edizione": ed, "giovanili_attive": nn[0], "giovanili_addetti": nn[1],
                  "femminili_attive": nn[2], "femminili_addetti": nn[3], "straniere_attive": nn[4], "straniere_addetti": nn[5]})

fl = pd.DataFrame(flussi)
st = pd.DataFrame(stock)
fl.to_csv(os.path.join(PUL, "camera_milano_flussi.csv"), index=False, encoding="utf8")
st.to_csv(os.path.join(PUL, "camera_milano_stock.csv"), index=False, encoding="utf8")

# confronto Camera vs Movimprese: Totale iscritte e cessate (al netto d'ufficio) per Milano
conf = []
for _, r in fl[fl.voce == "Totale"].iterrows():
    a = int(r.anno)
    row = T[(T.prov == "MI") & (T.anno == a)].iloc[0]
    conf.append({"anno": a, "camera_iscritte": int(r.milano_iscritte), "movimprese_iscritte": int(row.ISCTOT),
                 "camera_cessate": int(r.milano_cessate), "movimprese_cessate_non_ufficio": int(row.CES_NOUFF_TOT),
                 "movimprese_cessate_lorde": int(row.CESTOT)})
conf = pd.DataFrame(conf)
CONTROLLI["confronto_camera_vs_movimprese"] = conf.to_dict("records")
conf.to_csv(os.path.join(PUL, "controllo_camera_vs_movimprese.csv"), index=False, encoding="utf8")

# somma delle forme giuridiche = totale (Camera)
for a in sorted(fl.anno.unique()):
    f = fl[fl.anno == a].set_index("voce")
    forme = ["Società di capitali", "Società di persone", "Ditte individuali", "Altre forme"]
    CONTROLLI[f"camera_{a}_somma_forme_iscritte_vs_totale"] = [int(sum(f.loc[v, "milano_iscritte"] for v in forme)), int(f.loc["Totale", "milano_iscritte"])]
    CONTROLLI[f"camera_{a}_somma_forme_cessate_vs_totale"] = [int(sum(f.loc[v, "milano_cessate"] for v in forme)), int(f.loc["Totale", "milano_cessate"])]

# ------------------------------------------------------------------ Comune di Milano
for ds, fn in [("ds691", "ds691_imprese-settore-merceologico.csv"), ("ds1481", "ds1481_imprese-per-forma-giuridica.csv"),
               ("ds1482", "ds1482_addetti-alle-imprese-per-forma-giuridica.csv")]:
    df = pd.read_csv(os.path.join(RAW, "comune_" + ds, fn), sep=";", encoding="utf8")
    df.to_csv(os.path.join(PUL, f"comune_{ds}.csv"), index=False, encoding="utf8")
    CONTROLLI[f"comune_{ds}_righe"] = len(df)

json.dump(CONTROLLI, open(os.path.join(PUL, "controlli.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in CONTROLLI.items() if "righe_diverse" not in k or v}, ensure_ascii=False, indent=1)[:6000])
