#!/bin/bash
# vincoli disponibili dei dataflow ISTAT sui permessi di costruire; pausa 20 s (limite ISTAT 5 richieste/minuto)
B="C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/costruzioni"
for d in 11_111_DF_DCSC_RESID_CONSTR_1 111_111_DF_DCSC_PERM_RAP1_1 22_222_DF_DCSC_NONRESID_CONSTR_1; do
  python -I -X utf8 "$B/scripts/scarica_url.py" "https://esploradati.istat.it/SDMXWS/rest/availableconstraint/$d" "$B/raw/istat/avail_$d.xml" "application/xml" 400
  sleep 20
done
