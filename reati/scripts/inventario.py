"""Inventario dei file scaricati (raw/) con dimensione, righe, sha256, fonte e licenza. Uso: inventario.py <reati>"""
import sys, os, csv, hashlib
R = sys.argv[1]
FONTI = {
 "istat/df1_CRIMEN_7aree_tutti_tipi.csv": ("ISTAT esploradati SDMX, dataflow 73_67_DF_DCCV_DELITTIPS_1, A.IT+ITC45+ITE43+ITC11+ITF33+ITD55+ITE14.CRIMEN...", "CC BY 4.0 (ISTAT)", "conteggi delitti per tipo, Italia e 6 province, 2006-2024"),
 "istat/df1_CRIMEN_6comuni_tutti_tipi.csv": ("ISTAT esploradati SDMX, 73_67_DF_DCCV_DELITTIPS_1, comuni 015146+058091+001272+063049+037006+048017", "CC BY 4.0 (ISTAT)", "conteggi per tipo, 6 comuni, 2006-2024"),
 "istat/df1_CRIMEN_tutte_aree_TOT.csv": ("ISTAT esploradati SDMX, 73_67_DF_DCCV_DELITTIPS_1, A..CRIMEN.TOT..", "CC BY 4.0 (ISTAT)", "totale delitti, 242 aree (province, regioni, capoluoghi), 2006-2024"),
 "istat/df9_CRIMET_tutte_aree.csv": ("ISTAT esploradati SDMX, 73_67_DF_DCCV_DELITTIPS_9, A..CRIMET...", "CC BY 4.0 (ISTAT)", "tassi per 100.000 abitanti, 56 tipi, tutte le province, 2006-2024"),
 "istat/df5_grandi_comuni_CRIMEN.csv": ("ISTAT esploradati SDMX, 73_67_DF_DCCV_DELITTIPS_5", "CC BY 4.0 (ISTAT)", "ATTENZIONE: contiene CRIMEP = % di delitti con autore scoperto (grandi comuni), non usato"),
 "istat/df8_grandi_comuni_CRIMET.csv": ("ISTAT esploradati SDMX, 73_67_DF_DCCV_DELITTIPS_8", "CC BY 4.0 (ISTAT)", "tassi per 100.000, 12 grandi comuni, 2006-2024"),
 "istat/tur7_6aree.csv": ("ISTAT esploradati SDMX, 122_54_DF_DCSC_TUR_7, A.IT+ITE43+ITC11+ITF33+ITD55+ITE14", "CC BY 4.0 (ISTAT)", "arrivi e notti turistiche per provincia (Milano assente)"),
 "comune_ds564/ds564_reati_denunciati_2004_2023.csv": ("Comune di Milano CKAN ds564, risorsa CSV", "CC-BY (license_id cc-by)", "delitti nel comune di Milano per tipo, 2004-2023"),
 "comune_ds395/ds395.zip": ("Comune di Milano CKAN ds395, risorsa CSV (zip)", "CC-BY", "Censimento 2011: pendolari in entrata a Milano"),
 "comune_ds345/ds345.csv": ("Comune di Milano CKAN ds345", "CC-BY", "Censimento 2011: pendolari in uscita da Milano"),
 "probe/dataflow_IT1.xml": ("ISTAT esploradati SDMX, catalogo dataflow", "n/a", "elenco dataflow (consultazione)"),
 "probe/dsd_DELITTIPS.xml": ("ISTAT esploradati SDMX, datastructure DCCV_DELITTIPS + codelist", "n/a", "dimensioni e codici"),
 "probe/codelists.json": ("estratto da dsd_DELITTIPS.xml (mio, parse_dsd.py)", "n/a", "nomi dei codici"),
}
rows = []
for rel, (src, lic, nota) in FONTI.items():
    p = os.path.join(R, "raw", rel)
    if not os.path.exists(p):
        continue
    b = open(p, "rb").read()
    rows.append({"file": "raw/" + rel, "byte": len(b), "righe": b.count(b"\n"), "sha256": hashlib.sha256(b).hexdigest()[:16], "fonte": src, "licenza": lic, "contenuto": nota})
with open(os.path.join(R, "pulito", "inventario_fonti.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "file")
