"""Rilancia tutto il lavoro nell'ordine giusto e salva i log in out/. Circa 20-30 minuti.
Uso: python -I -X utf8 lancia_tutto.py"""
import os
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(QUI), "out")
ORDINE = ["00_censimento_file", "00b_estrai_limiti_note", "01_tabella_nil", "02_screening_nil", "03_tabella_tempo", "04_serie_tempo", "05_candidati_nil", "06_tipi_e_anomali", "07_approfondimenti_nil", "07b_controlli_finali_nil", "08_approfondimenti_tempo", "09_ultimi_controlli"]
for n in ORDINE:
    log = os.path.join(OUT, "log_" + n.split("_")[0] + ".txt")
    print("->", n)
    with open(log, "w", encoding="utf8") as h:
        r = subprocess.run([sys.executable, "-I", "-X", "utf8", "-W", "ignore", os.path.join(QUI, n + ".py")], cwd=QUI, stdout=h, stderr=subprocess.STDOUT)
    if r.returncode:
        sys.exit(f"errore in {n}: vedi {log}")
print("fatto")
