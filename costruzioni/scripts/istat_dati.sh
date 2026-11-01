#!/bin/bash
# Dati ISTAT SDMX (CSV) sui permessi di costruire: Milano provincia (ITC45), classe capoluoghi >500k, capoluoghi/non capoluoghi della provincia; pausa 25 s
B="C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/costruzioni"
I="https://esploradati.istat.it/SDMXWS/rest/data/IT1"
get() { python -I -X utf8 "$B/scripts/scarica_url.py" "$I,$2,1.0/$3?startPeriod=2010" "$B/raw/istat/$1.csv" "application/vnd.sdmx.data+csv;version=1.0.0" 900; sleep 25; }
get resid_constr_1_milano 11_111_DF_DCSC_RESID_CONSTR_1 "A.ITC45+ITC4+ITC+IT+PROVCAPM+NPROVCAPM+INH_GE500001_CAP.........."
get nonresid_constr_1_milano 22_222_DF_DCSC_NONRESID_CONSTR_1 "A.ITC45+ITC4+ITC+IT+PROVCAPM+NPROVCAPM+INH_GE500001_CAP........."
get resid_constr_2_ampliamenti_milano 11_111_DF_DCSC_RESID_CONSTR_2 "A.ITC45+ITC4+ITC+IT+PROVCAPM+NPROVCAPM+INH_GE500001_CAP.........."
