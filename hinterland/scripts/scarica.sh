#!/bin/sh
# Scarica i file ISTAT comunali mancanti (demo.istat.it, CC BY 4.0). Pausa 6 s, User-Agent dichiarato.
# Uso: sh scarica.sh <cartella hinterland>
R="$1/raw"; UA="MilanoInDati-ricerca-personale"
get() { d="$R/$(dirname "$2")"; mkdir -p "$d"; [ -s "$R/$2" ] || { curl -sS -f -A "$UA" -m 300 -o "$R/$2" "$1" && echo "ok $2 $(wc -c < "$R/$2")" || echo "ERRORE $1"; sleep 6; }; }
for y in 2019 2020 2021 2022 2023 2024 2025 2026; do
  get "https://demo.istat.it/data/posas/POSAS_${y}_it_Comuni.zip" "posas/POSAS_${y}_it_Comuni.zip"
  get "https://demo.istat.it/data/strasa/STRASA_${y}_it_Comuni.zip" "strasa/STRASA_${y}_it_Comuni.zip"
done
get "https://demo.istat.it/data/p2/P2_2025_it_Comuni.zip" "p2/P2_2025_Comuni.zip"
