"""Aggrega i microdati Banca d'Italia (viaggiatori stranieri, variabili principali, 1997-2025) per Milano.
uso: python -I -X utf8 08_bdi_microdati.py <cartella turisti assoluta>
Legge i zip in raw/bancaditalia/microdati_stranieri, scrive in pulito/:
  bdi_milano_paese_anno.csv   anno, ambito (comune_milano|provincia_milano|italia), stato_codice, stato, interviste, viaggiatori, notti, spesa_euro
  bdi_milano_mese.csv         anno, mese, ambito (comune_milano|provincia_milano), interviste, viaggiatori, notti, spesa_euro
  bdi_milano_alloggio.csv     anno, ambito, alloggio_codice, alloggio, interviste, viaggiatori, notti, spesa_euro
  bdi_controlli.txt
Valori espansi (FPD_VIAG = viaggiatori a destinazione, FPD_NOTTI = notti, FPD_SPESA_FMI = spesa in euro). Sono STIME da campione: vedi NOTE.md.
Provincia Milano = codice 16; comune di Milano = codice comune 1600 (tabelle TPROVINCE e TCOMUNI dei metadati della Banca)."""
import sys, os, zipfile, glob, csv, collections
import pandas as pd
base = sys.argv[1]
SRC = os.path.join(base, "raw", "bancaditalia", "microdati_stranieri")
META = os.path.join(base, "raw", "bancaditalia", "meta_x")
OUT = os.path.join(base, "pulito")
stati = {}
for r in csv.DictReader(open(os.path.join(META, "TSTATI.csv"), encoding="latin-1"), delimiter=";"):
    stati.setdefault(int(r["ELEM_DOMINIO"]), []).append((r["D_EL_DOMINIO"], r["D_NASC_EL_DOM"], r["D_MORTE_EL_DOM"]))
alloggi = {}
for r in csv.DictReader(open(os.path.join(META, "TALLOGGIO.csv"), encoding="latin-1"), delimiter=";"):
    alloggi.setdefault(int(r["CODICE"]), []).append((r["DESCRIZIONE"], r["DATA_INIZIO_VAL"], r["DATA_FINE_VAL"]))
def nome_stato(c, anno):
    L = stati.get(int(c), [])
    for n, a, b in L:
        if a[:4] <= str(anno) <= b[:4]: return n
    return L[-1][0] if L else "?"
def nome_all(c, anno):
    L = alloggi.get(int(c), [])
    for n, a, b in L:
        if a[:4] <= str(anno) <= b[:4]: return n
    return L[-1][0] if L else "?"
log = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.append(s)
A, M, L = [], [], []
for f in sorted(glob.glob(os.path.join(SRC, "*.zip"))):
    anno = int(os.path.basename(f)[:4])
    z = zipfile.ZipFile(f)
    nm = [i.filename for i in z.infolist() if i.filename.lower().endswith(".csv")][0]
    df = pd.read_csv(z.open(nm), encoding="latin-1", low_memory=False)
    df.columns = [c.upper() for c in df.columns]
    alc = [c for c in df.columns if c.startswith("ALLOGGIO_PRINC")]
    alc = "ALLOGGIO_PRINC_08" if "ALLOGGIO_PRINC_08" in df.columns else (alc[0] if alc else None)
    need = ["DATA_CONTABILE", "COMUNE_VISITATO", "PROVINCIA_VISITATA", "STATO_RESIDENZA", "FPD_VIAG", "FPD_NOTTI", "FPD_SPESA_FMI"]
    miss = [c for c in need if c not in df.columns]
    if miss: P(anno, "COLONNE MANCANTI", miss, "colonne:", list(df.columns)[:30]); continue
    anni_cont = sorted(set(df.DATA_CONTABILE.astype(str).str[:4]))
    df["ANNO_C"] = df.DATA_CONTABILE.astype(str).str[:4].astype(int)
    df["MESE"] = df.DATA_CONTABILE.astype(str).str[4:6].astype(int)
    df["SPESA"] = df.FPD_SPESA_FMI.fillna(0.0)
    ambiti = {"italia": df, "provincia_milano": df[df.PROVINCIA_VISITATA == 16], "comune_milano": df[df.COMUNE_VISITATO == 1600]}
    P(anno, "righe", len(df), "anni contabili", anni_cont, "| prov. Milano", len(ambiti["provincia_milano"]), "comune", len(ambiti["comune_milano"]),
      "| alloggio col", alc, "| tot viagg Italia %.0f notti %.0f spesa %.0f" % (df.FPD_VIAG.sum(), df.FPD_NOTTI.sum(), df.SPESA.sum()))
    for amb, d in ambiti.items():
        g = d.groupby("STATO_RESIDENZA").agg(interviste=("SPESA", "size"), viaggiatori=("FPD_VIAG", "sum"), notti=("FPD_NOTTI", "sum"), spesa=("SPESA", "sum"))
        for c, r in g.iterrows():
            A.append([anno, amb, int(c), nome_stato(c, anno), int(r.interviste), round(r.viaggiatori, 1), round(r.notti, 1), round(r.spesa, 0)])
        if amb != "italia":
            g = d.groupby("MESE").agg(interviste=("SPESA", "size"), viaggiatori=("FPD_VIAG", "sum"), notti=("FPD_NOTTI", "sum"), spesa=("SPESA", "sum"))
            for c, r in g.iterrows():
                M.append([anno, int(c), amb, int(r.interviste), round(r.viaggiatori, 1), round(r.notti, 1), round(r.spesa, 0)])
            if alc:
                g = d.groupby(alc).agg(interviste=("SPESA", "size"), viaggiatori=("FPD_VIAG", "sum"), notti=("FPD_NOTTI", "sum"), spesa=("SPESA", "sum"))
                for c, r in g.iterrows():
                    L.append([anno, amb, int(c), nome_all(c, anno), int(r.interviste), round(r.viaggiatori, 1), round(r.notti, 1), round(r.spesa, 0)])
def scrivi(nome, head, rows):
    with open(os.path.join(OUT, nome), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo); w.writerow(head); w.writerows(rows)
scrivi("bdi_milano_paese_anno.csv", ["anno", "ambito", "stato_codice", "stato", "interviste", "viaggiatori", "notti", "spesa_euro"], A)
scrivi("bdi_milano_mese.csv", ["anno", "mese", "ambito", "interviste", "viaggiatori", "notti", "spesa_euro"], M)
scrivi("bdi_milano_alloggio.csv", ["anno", "ambito", "alloggio_codice", "alloggio", "interviste", "viaggiatori", "notti", "spesa_euro"], L)
open(os.path.join(OUT, "bdi_controlli.txt"), "w", encoding="utf-8").write("\n".join(log))
