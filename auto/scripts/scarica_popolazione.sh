#!/bin/bash
# Scarica da demo.istat.it (open, nessun login, ISTAT CC BY 4.0) la popolazione per eta' e sesso al 1 gennaio (POSAS)
# delle province dei grandi comuni, 2019-2026. Riprendibile (salta i file gia' scaricati), pausa 2 s.
# Uso: bash scarica_popolazione.sh <cartella auto>
R="$1/raw/istat_posas"; UA="milano-in-dati-research/1.0 (open data study)"; mkdir -p "$R"
get() { f="$R/$(basename "$1")"; if [ -s "$f" ]; then echo "skip $f"; return; fi
  code=$(curl -s -m 120 -A "$UA" -o "$f" -w "%{http_code}" "$1"); echo "$1 -> $code $(stat -c %s "$f" 2>/dev/null)"; [ "$code" = 200 ] || rm -f "$f"; sleep 2; }
for p in Regioni 015_Milano 058_Roma 001_Torino 063_Napoli 037_Bologna 048_Firenze 010_Genova 023_Verona 072_Bari 082_Palermo; do
  for y in 2019 2020 2021 2022 2023 2024 2025 2026; do
    get "https://demo.istat.it/data/posas/POSAS_${y}_it_${p}.zip"
  done
done
