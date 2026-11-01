#!/bin/bash
# vincoli disponibili (dimensioni e valori) dei dataflow ISTAT usati; pausa 20 s tra le richieste (ISTAT limita le richieste)
B="C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/costo-vita"
for d in 144_125_DF_DCSP_NICDUE_1 167_33_DF_DCSP_NICUNOBB2010_2 167_744_DF_DCSP_NIC1B2015_3 167_745_DF_DCSP_NIC1B2025_3 144_125_DF_DCSP_NICDUE_3; do
  python -I -X utf8 "$B/scripts/scarica.py" "https://esploradati.istat.it/SDMXWS/rest/availableconstraint/$d" "$B/raw/istat_sdmx/avail_$d.xml" "application/xml" 300
  sleep 20
done
