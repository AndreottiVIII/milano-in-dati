"""Controlli di completezza sulla tabella delle schede di Milano.
uso: python -I 04_controlli.py <beni_culturali_milano.csv> <file_conteggi_nazionali.json> <output_txt>
"""
import json
import sys
import pandas as pd

csv_path, nat_path, out_path = sys.argv[1:4]
df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
nat = json.load(open(nat_path, encoding="utf-8"))
out = []


def p(*a):
    out.append(" ".join(str(x) for x in a))


def vuoto(col):
    return (df[col].str.strip() == "")


for c in ["cov_milano", "indirizzo_milano", "loc_attuale_mi", "loc_altra_mi"]:
    df[c] = df[c].astype(int)

p("== TOTALI ==")
p("schede nel dump (soggetti con dc:identifier):", nat["proprieta_nazionali_totale"])
p("schede Milano, almeno un criterio:", len(df))
p("ambito:\n" + df["ambito"].value_counts().to_string())
p("combinazioni (cov, indirizzo, loc_attuale, loc_altra):")
p(df.groupby(["cov_milano", "indirizzo_milano", "loc_attuale_mi", "loc_altra_mi"]).size().to_string())
sede = df[df["ambito"] == "sede_milano"]
p("schede sede_milano:", len(sede))
p("di cui con localizzazione attuale a Milano:", int((df["loc_attuale_mi"] == 1).sum()))
p("di cui cov_milano ma localizzazione attuale NON a Milano:", int(((df.cov_milano == 1) & (df.loc_attuale_mi == 0)).sum()))
p("di cui loc_attuale a Milano ma cov_milano=0:", int(((df.cov_milano == 0) & (df.loc_attuale_mi == 1)).sum()))
p("di cui indirizzo_milano=0 e loc_attuale_mi=1:", int(((df.indirizzo_milano == 0) & (df.loc_attuale_mi == 1)).sum()))

for nome, d in [("TUTTE (sede + collegate)", df), ("SOLO sede_milano", sede)]:
    p(f"\n== {nome}: PER TIPO DI SCHEDA (CatalogueRecord<tipo>) ==")
    p(d["tipo_scheda"].replace("", "(vuoto)").value_counts().to_string())
    p(f"\n== {nome}: PER CLASSE DEL BENE (percorso IRI) ==")
    p(d["classe_bene"].value_counts().to_string())
    p(f"\n== {nome}: PRIMI 20 ISTITUZIONI (campo istituzione) ==")
    inst = d["istituzione"].str.split(r" \| ").explode()
    inst = inst[inst.str.strip() != ""]
    p(inst.value_counts().head(20).to_string())
    p("schede senza istituzione:", int(vuoto("istituzione").loc[d.index].sum()), "su", len(d))
    p(f"\n== {nome}: CAMPI MANCANTI ==")
    for col, lab in [("datazione", "datazione"), ("autore", "autore"), ("titolo", "titolo"),
                     ("soggetto", "soggetto"), ("materia_tecnica", "materia/tecnica"),
                     ("localizzazione_attuale", "localizzazione attuale"), ("indirizzo_bene", "indirizzo bene"),
                     ("lat", "coordinate"), ("url_catalogo", "link catalogo"), ("istituzione", "istituzione")]:
        n = int(vuoto(col).loc[d.index].sum())
        p(f"{lab:26s} mancanti {n:6d} su {len(d)}  ({100*n/len(d):.1f}%)")

p("\n== ULTIMO AGGIORNAMENTO (anno), sede_milano ==")
p(sede["ultimo_aggiornamento"].str[:4].replace("", "(vuoto)").value_counts().sort_index().to_string())
p("\n== ID e URL duplicati ==")
p("id duplicati:", int(df["id"].duplicated().sum()), " url duplicati:", int(df[df.url_catalogo != ""]["url_catalogo"].duplicated().sum()))
p("\n== ente catalogatore (hash) top 5, sede_milano ==")
p(sede["ente_catalogatore"].value_counts().head(5).to_string())
open(out_path, "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
