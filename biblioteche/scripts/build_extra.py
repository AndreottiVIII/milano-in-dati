"""Fase 1 - secondo passaggio sui file mensili: anno di edizione e editore dei libri prestati (per misurare quanto sono 'freschi' i libri letti).
Uso: python -I -X utf8 build_extra.py <biblioteche_abs>
Scrive pulito/mensili_parquet/ed_<AAAA-MM>.parquet: (mese_inizio, anno_edizione, editore, eta_fascia, n) per prestiti validi (non annullati, bibliotecario o interbibliotecario) di materiale a stampa."""
import sys, os, re, glob, zipfile, io
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
base = sys.argv[1]
raw = os.path.join(base, "raw"); out = os.path.join(base, "pulito", "mensili_parquet")
def one(f):
    m = re.search(r"prestiti-(\d\d)-(\d{4})", f); ym = f"{m.group(2)}-{m.group(1)}"
    op = os.path.join(out, f"ed_{ym}.parquet")
    if os.path.exists(op): return ym
    if f.endswith(".zip"):
        z = zipfile.ZipFile(f); n = [x for x in z.namelist() if x.lower().endswith(".csv")][0]; fh = io.BytesIO(z.read(n))
    else: fh = open(f, "rb")
    d = pd.read_csv(fh, sep=";", dtype=str, encoding="utf-8-sig",
        usecols=["loan.loan_date_begin","loan.loan_status_classif","loan.loan_type_dec","patron.age_group_first","manifestation.edition_date","manifestation.publisher","manifestation.bib_type_first_dec","item.item_media_dec"])
    d = d[(d["loan.loan_status_classif"] != "Annullato") & d["loan.loan_type_dec"].isin(["Prestito bibliotecario","Prestito interbibliotecario"])
          & (d["manifestation.bib_type_first_dec"] == "MATERIALE A STAMPA") & (d["item.item_media_dec"] == "LIBRI E AUDIOLIBRI")]
    d = d.assign(mese_inizio=d["loan.loan_date_begin"].str.slice(0,7)).rename(columns={"manifestation.edition_date":"anno_edizione","manifestation.publisher":"editore","patron.age_group_first":"eta_fascia"})
    g = d.fillna("(vuoto)").groupby(["mese_inizio","anno_edizione","editore","eta_fascia"]).size().rename("n").reset_index()
    g.to_parquet(op, index=False); return ym
if __name__ == "__main__":
    files = sorted(f for f in glob.glob(os.path.join(raw, "comune_ds*", "ds*biblioteche-prestiti-??-20??.*")) if f.endswith((".zip",".csv")))
    with ProcessPoolExecutor(4) as ex: list(ex.map(one, files))
    print("fine", len(files))
