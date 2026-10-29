#!/bin/bash
# aspetta la fine del download, poi estrae i triple e costruisce la tabella Milano
cd "$(dirname "$0")/.."
until grep -q FINITO logs/download.log; do
  python -I scripts/02_estrai_triple.py raw/arco-2.0 work/tsv 6 logs/download.log >> logs/estrazione.log 2>&1
  sleep 60
done
python -I scripts/02_estrai_triple.py raw/arco-2.0 work/tsv 8 logs/download.log >> logs/estrazione.log 2>&1
python -I scripts/03_milano.py work/tsv beni_culturali_milano.csv work/conteggi_nazionali.json > logs/milano.log 2>&1
echo TUTTO_FATTO >> logs/milano.log
