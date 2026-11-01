#!/bin/bash
# Italia, indici NIC 1996-2025 per ECOICOP 2 (tutte le basi): un'unica richiesta
B="C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/costo-vita"
python -I -X utf8 "$B/scripts/scarica.py" "https://esploradati.istat.it/SDMXWS/rest/data/IT1,167_745_DF_DCSP_NIC1B2025_5,1.0/M.IT...." "$B/raw/istat_sdmx/nic_1996_2025_IT_ecoicop2_tuttebasi.csv" "application/vnd.sdmx.data+csv;version=1.0.0" 1800
echo FINE
