#!/bin/bash
B="C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/costruzioni"
I="https://esploradati.istat.it/SDMXWS/rest/data/IT1"
get() { python -I -X utf8 "$B/scripts/scarica_url.py" "$I,$2,1.0/$3?startPeriod=2010" "$B/raw/istat/$1.csv" "application/vnd.sdmx.data+csv;version=1.0.0" 900; sleep 25; }
get resid_constr_1_milano 11_111_DF_DCSC_RESID_CONSTR_1 "A.ITC45+ITC4+ITC+IT+PROVCAPM+NPROVCAPM+INH_GE500001_CAP............"
