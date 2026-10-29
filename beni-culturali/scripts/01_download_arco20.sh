#!/bin/bash
# Scarica le 97 parti del dump ArCo 2.0 (CNR-ISTC, 2023-12-01) in raw/arco-2.0/. Riprende i file interrotti.
# uso: bash 01_download_arco20.sh <cartella_destinazione>
DEST="$1"; BASE=http://arco.istc.cnr.it/arco-data/2.0
mkdir -p "$DEST"
curl -sS --retry 5 -o "$DEST/index.txt" $BASE/index.txt
for i in $(seq 0 96); do
  f=arco-knowledge-graph-2.0_part_$i.nt.gz
  want=$(curl -sSI $BASE/$f | tr -d '\r' | awk 'tolower($1)=="content-length:"{print $2}')
  have=0; [ -f "$DEST/$f" ] && have=$(stat -c %s "$DEST/$f")
  if [ "$have" != "$want" ]; then
    curl -sS --retry 5 --retry-delay 5 -C - -o "$DEST/$f" $BASE/$f || echo "ERRORE $f"
  fi
  echo "$(date +%T) $f $(stat -c %s "$DEST/$f") atteso $want"
  sleep 1
done
echo FINITO
