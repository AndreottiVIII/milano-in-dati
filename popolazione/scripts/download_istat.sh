#!/bin/bash
# Scarica da demo.istat.it (file aperti, nessun login, CC BY 4.0) i file per il filone popolazione. Pausa 6 s tra richieste, User-Agent dichiarato. Riprendibile.
# Uso: bash download_istat.sh <cartella popolazione assoluta>
R="$1/raw/istat_demo"; UA="milano-in-dati-research/1.0 (open data study)"; mkdir -p "$R"
LOG="$R/download_log.txt"
get() { f="$R/$(basename "$1")"; if [ -s "$f" ]; then echo "skip $f"; return; fi
  code=$(curl -s -m 180 -A "$UA" -o "$f" -w "%{http_code}" "$1"); echo "$(date +%F) $1 -> $code $(stat -c %s "$f" 2>/dev/null)" | tee -a "$LOG"; [ "$code" = 200 ] || rm -f "$f"; sleep 6; }
get "https://demo.istat.it/data/ricostruzione/Nota_metodologica_Ricostruzione2002_2018.pdf"
for y in $(seq 2001 2018); do get "https://demo.istat.it/data/ricostruzione/RBD-Dataset-${y}.csv.zip"; done
get "https://demo.istat.it/data/p2/P2_2025_it_015_Milano.zip"
get "https://demo.istat.it/data/p3/P3_2025_it_015_Milano.zip"
get "https://demo.istat.it/data/ssc/ssc_2009-2025_provinciale.xls"
