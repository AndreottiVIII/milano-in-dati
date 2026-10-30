#!/bin/bash
# Fase 2, passo 4: scarica da demo.istat.it (open, nessun login) i file di Milano: POSAS (residenti per eta/sesso/stato civile, 1 gennaio),
# STRASA (stranieri per eta/sesso/cittadinanza, 1 gennaio), D7B (bilancio demografico mensile, tutti i comuni). Riprendibile.
# Uso: bash h4_dl_demo.sh <cartella censimenti>
R="$1/raw/istat_demo"; UA="milano-in-dati-research/1.0 (open data study)"; mkdir -p "$R"
get() { f="$R/$(basename "$1")"; if [ -s "$f" ]; then echo "skip $f"; return; fi
  code=$(curl -s -m 120 -A "$UA" -o "$f" -w "%{http_code}" "$1"); echo "$1 -> $code $(stat -c %s "$f" 2>/dev/null)"; [ "$code" = 200 ] || rm -f "$f"; sleep 2; }
for y in 2018 2019 2020 2021 2022 2023 2024 2025 2026; do
  get "https://demo.istat.it/data/posas/POSAS_${y}_it_015_Milano.zip"
  get "https://demo.istat.it/data/strasa/STRASA_${y}_it_015_Milano.zip"
done
for y in 2019 2020 2021 2022 2023 2024; do get "https://demo.istat.it/data/d7b/D7B${y}.csv.zip"; done
