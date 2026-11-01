"""Scrive pulito/inventario.csv (fonti, licenze, date, cosa manca) con sha256 dei file grandi. Uso: python -I -X utf8 inventario.py <costruzioni (assoluto)>"""
import sys, os, csv, hashlib
C = sys.argv[1]
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
rows = [
 ("Comune di Milano ds270", "Edilizia: nuovi fabbricati residenziali - serie storica", "raw/comune_ds270/ds270_edilizia_nuovi_fabbricati_uso_residenziale.csv", "1 record per fabbricato (modello ISTAT permessi di costruire); anno ritiro titolo 2014-2024 (+3 ritardi 2011-2012); Comune di Milano, indirizzo, NIL, municipio, coordinate", "cc-by (CKAN license_id; versione non scritta)", "728 righe; 66 senza coordinate; Abbattimento/ricostruzione compilato solo dal 2021; manca nome progetto, manca il numero del titolo"),
 ("Comune di Milano ds2984", "Edilizia: nuovi fabbricati non residenziali", "raw/comune_ds2984/ds2984_edilizia_nuovi_fabbricati_uso_non_residenziale.csv", "come sopra, uso non residenziale (superfici per attivita', destinazione economica)", "cc-by", "214 righe; 28 senza coordinate"),
 ("Comune di Milano ds271", "Edilizia: ampliamenti residenziali", "raw/comune_ds271/ds271_edilizia_ampliamenti_uso_residenziale.csv", "ampliamenti di volume (solo la parte ampliata)", "cc-by", "204 righe; 6 senza coordinate"),
 ("Comune di Milano ds2985", "Edilizia: ampliamenti non residenziali", "raw/comune_ds2985/ds2985_edilizia_ampliamenti_uso_non_residenziale.csv", "ampliamenti non residenziali", "cc-by", "150 righe; 2 senza coordinate"),
 ("Comune di Milano ds2983", "Edilizia: fabbricati destinati a collettivita'", "raw/comune_ds2983/ds2983_edilizia_fabbricati_collettivita.csv", "nuovi e ampliamenti, residenze per comunita'", "cc-by", "19 righe"),
 ("Comune di Milano ds503", "Edifici degradati, abbandonati o dismessi 2014-2017", "raw/comune_ds503/ds503_aree_edifici_degradati_abbandonati_0_final.csv", "174 edifici/aree privati degradati con indirizzo e NIL (solo contesto)", "cc-by", "solo 2014-2017; indirizzi di proprieta' private (non da pubblicare)"),
 ("Comune di Milano DBT 2020 (ds2889)", "Database Topografico 2020, shapefile, volo marzo-aprile 2020, scala 1:1.000", "raw/dbt2020/DBT_2020.zip", "unita' volumetriche con altezza (UN_VOL), tutta la citta'", "cc-by (CKAN); gisportal.comune.milano.it, download libero senza login, robots.txt non vieta area_download", "nessun anno di costruzione; nessun dato su titoli"),
 ("Comune di Milano DBT 2012 (ds2892)", "Database Topografico 2012 (restituzione 2006 per il 96% delle unita', aggiornata 2012 per il resto)", "raw/dbt2012/DBT2012_ALL_SHP_E0.zip", "unita' volumetriche A020101 con altezza e ID_EDIF", "cc-by (CKAN)", "il campo ID_ZRIL dice MI_2006 per 203.745 unita' su 213.076 e MI_2012 per 9.331: e' quasi un confronto 2006-2020"),
 ("ISTAT esploradati RESID_CONSTR_1", "Fabbricati residenziali nuovi e abitazioni - province e classi di comune", "raw/istat/resid_constr_1_milano.csv", "annuale 2010-2025; Milano e' presente solo come Citta' metropolitana (ITC45), come 'capoluoghi di provincia' e come classe '> 500.000 ab. capoluoghi' (6 citta')", "CC BY (dichiarata da ISTAT per IstatData; non ricontrollata nel file SDMX)", "NON esiste il solo comune di Milano: ISTAT scrive che l'analisi territoriale arriva al livello provinciale"),
 ("ISTAT esploradati NONRESID_CONSTR_1", "Fabbricati non residenziali nuovi e relative abitazioni", "raw/istat/nonresid_constr_1_milano.csv", "annuale 2010-2025, stesso livello territoriale", "come sopra", "come sopra"),
 ("ISTAT dataflow e vincoli", "elenco dataflow IT1 e availableconstraint", "raw/istat/dataflow_IT1.xml", "per trovare i codici", "-", "-"),
]
os.makedirs(os.path.join(C, "pulito"), exist_ok=True)
with open(os.path.join(C, "pulito", "inventario.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["fonte", "titolo", "file", "contenuto", "licenza", "limiti", "data_download", "byte", "sha256"])
    for r in rows:
        p = os.path.join(C, r[2]); ok = os.path.exists(p)
        w.writerow(list(r) + ["2026-11-01", os.path.getsize(p) if ok else "", sha(p) if ok else ""])
print("ok")
