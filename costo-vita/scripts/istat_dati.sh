#!/bin/bash
# Scarica da ISTAT SDMX (CSV) gli indici NIC di Milano (ITC45) e Italia (IT); pausa 25 s tra le richieste.
B="C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/costo-vita"
I="https://esploradati.istat.it/SDMXWS/rest/data/IT1"
get() { # nome flow chiave
  python -I -X utf8 "$B/scripts/scarica.py" "$I,$2,1.0/$3" "$B/raw/istat_sdmx/$1.csv" "application/vnd.sdmx.data+csv;version=1.0.0" 900
  sleep 25
}
get nic_1999_2010_ITC45_IT_coicop2 144_125_DF_DCSP_NICDUE_1 "M.ITC45+IT...."
get nic_2011_2015_ITC45_IT_coicop3 167_33_DF_DCSP_NICUNOBB2010_2 "M.ITC45+IT...."
get nic_2016_2025_ITC45_IT_ecoicop3 167_744_DF_DCSP_NIC1B2015_3 "M.ITC45+IT...."
get nic_2016_2025_ITC45_IT_principali 167_744_DF_DCSP_NIC1B2015_1 "M.ITC45+IT...."
get nic_2026_ITC45_IT_principali 167_745_DF_DCSP_NIC1B2025_1 "M.ITC45+IT...."
get nic_2026_ITC45_IT_ecoicop3 167_745_DF_DCSP_NIC1B2025_3 "M.ITC45+IT...."
echo FINE
