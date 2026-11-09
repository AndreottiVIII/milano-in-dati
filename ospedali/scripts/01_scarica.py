"""Scarica gli archivi interi (una volta sola) in dati_grezzi/. User-Agent dichiarato."""
import subprocess, pathlib, urllib.parse, time
UA = "milano-in-dati/1.0"
OUT = pathlib.Path(__file__).resolve().parent.parent / "dati_grezzi"
MS = "https://www.dati.salute.gov.it"
FILES = {
 "min_regione_2010_2019.csv": MS + "/sites/default/files/imported/C_17_dataset_17_0_upFile.csv",
 "min_regione_2020.csv": MS + "/sites/default/files/imported/C_17_dataset_113_0_upFile.csv",
 "min_regione_2021.csv": MS + "/sites/default/files/imported/C_17_dataset_151_0_upFile.csv",
 "min_regione_2022.csv": MS + "/sites/default/files/imported/C_17_dataset_197_0_upFile.csv",
 "min_regione_2023.csv": MS + "/sites/default/files/2025-07/" + urllib.parse.quote("Posti letto per Regione e disciplina_2023_0.csv"),
 "min_struttura_2010_2019.csv": MS + "/sites/default/files/imported/C_17_dataset_18_0_upFile.csv",
 "min_struttura_2020.csv": MS + "/sites/default/files/imported/C_17_dataset_114_0_upFile.csv",
 "min_struttura_2021.csv": MS + "/sites/default/files/2024-12/" + urllib.parse.quote("Posti letto per struttura ospedaliera_2021.csv"),
 "min_struttura_2022.csv": MS + "/sites/default/files/2024-12/" + urllib.parse.quote("Posti letto per struttura ospedaliera_2022_0.csv"),
 "min_struttura_2023.csv": MS + "/sites/default/files/2025-07/" + urllib.parse.quote("Posti letto per struttura ospedaliera_2023.csv"),
}
for n, u in FILES.items():
    p = OUT / n
    if p.exists(): continue
    # curl: il sito del Ministero chiude le connessioni di urllib (TLS), curl passa
    subprocess.run(["curl","-sSL","--fail","-A",UA,"-o",str(p),u],check=True)
    print(n, p.stat().st_size); time.sleep(1)
