"""Fase 1 - legge i 135 file mensili di prestiti (ds2493... ds2867, dettaglio prestito per prestito) e li riduce a aggregati.
Uso: python -I -X utf8 build_mensili.py <biblioteche_abs>
Per ogni file (zip o csv) scrive in pulito/mensili_parquet/:
  cubo_<AAAA-MM>.parquet  conteggi per (mese_file, mese_inizio, tipo, stato, da_bib, a_bib, tipo_a_bib, eta, eta_fascia, genere, media, supporto) 
  titoli_<AAAA-MM>.parquet conteggi per (mese_inizio, titolo, autore, media, supporto, lingua, eta_fascia) solo prestiti validi
Nessun valore viene corretto. Il file originale non è mai eseguito, solo letto come testo."""
import sys, os, re, glob, zipfile, io, json
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
base = sys.argv[1]
raw = os.path.join(base, "raw"); out = os.path.join(base, "pulito", "mensili_parquet")
os.makedirs(out, exist_ok=True)
COLS = {"loan.loan_date_begin":"inizio","loan.loan_status_classif":"stato","loan.loan_type_dec":"tipo","loan.from_library_dec":"da_bib",
        "loan.to_library_dec":"a_bib","loan.to_library_type":"tipo_a_bib","patron.gender":"genere","patron.age_group":"eta","patron.age_group_first":"eta_fascia",
        "item.title":"titolo","manifestation.author":"autore","item.item_media_dec":"media","manifestation.bib_type_first_dec":"supporto",
        "manifestation.edition_language":"lingua"}
def one(f):
    m = re.search(r"prestiti-(\d\d)-(\d{4})", f)
    ym = f"{m.group(2)}-{m.group(1)}"
    cp = os.path.join(out, f"cubo_{ym}.parquet"); tp = os.path.join(out, f"titoli_{ym}.parquet")
    if os.path.exists(cp) and os.path.exists(tp):
        return ym, None
    if f.endswith(".zip"):
        z = zipfile.ZipFile(f); names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        assert len(names) == 1, (f, z.namelist())
        fh = io.BytesIO(z.read(names[0]))
    else:
        fh = open(f, "rb")
    d = pd.read_csv(fh, sep=";", dtype=str, encoding="utf-8-sig")
    n_tot = len(d)
    miss = [c for c in COLS if c not in d.columns]
    assert not miss, (f, miss)
    d = d[list(COLS)].rename(columns=COLS)
    d["mese_inizio"] = d["inizio"].str.slice(0, 7)
    d["mese_file"] = ym
    key = ["mese_file","mese_inizio","tipo","stato","da_bib","a_bib","tipo_a_bib","eta","eta_fascia","genere","media","supporto"]
    cubo = d.fillna("(vuoto)").groupby(key).size().rename("n").reset_index()
    cubo.to_parquet(cp, index=False)
    v = d[(d["stato"] != "Annullato") & d["tipo"].isin(["Prestito bibliotecario","Prestito interbibliotecario"])]
    tit = v.fillna("(vuoto)").groupby(["mese_inizio","titolo","autore","media","supporto","lingua","eta_fascia"]).size().rename("n").reset_index()
    tit.to_parquet(tp, index=False)
    return ym, n_tot
if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join(raw, "comune_ds*", "ds*biblioteche-prestiti-??-20??.*")))
    files = [f for f in files if f.endswith((".zip", ".csv"))]
    print(len(files), "file")
    tot = {}
    with ProcessPoolExecutor(4) as ex:
        for ym, n in ex.map(one, files):
            tot[ym] = n
    json.dump(tot, open(os.path.join(base, "pulito", "righe_per_file_mensile.json"), "w"), indent=0)
    print("fine")
