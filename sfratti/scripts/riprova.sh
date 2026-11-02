#!/bin/bash
# Riprova (pochi tentativi, distanziati) i file della cartella 2025-09 del sito UCS che prima non rispondevano.
cd "$1/raw/ministero_interno" || exit 1
for f in "2021_Dati_Sfratti_al_31-12-2020-Provinciali.xlsx" "2021_Dati_Sfratti_Serie_storica_2002-2020.xlsx" "2021_Dati_Sfratti_al_31-12-2020-Regionali.xlsx" "INT00004_Nota_metodologica_PROCEDURE_RILASCIO_IMMOBILI_USO_ABITATIVOed2024.pdf"; do
  for t in 1 2 3 4 5 6; do
    [ -s "$f" ] && break
    code=$(curl -sS -L --max-time 60 -A "milano-in-dati/1.0 (ricerca open data)" -o "$f.part" -w "%{http_code}" "https://ucs.interno.gov.it/sites/default/files/2025-09/$f" 2>/dev/null)
    if [ "$code" = "200" ] && [ -s "$f.part" ]; then mv "$f.part" "$f"; echo "ok $f"; else rm -f "$f.part"; echo "tentativo $t fallito $f ($code)"; sleep 120; fi
  done
done
