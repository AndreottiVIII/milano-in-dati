"""Scarica da IstatData (API SDMX pubblica) TFR ed eta' media delle madri per provincia, 2000-2025, in raw/istat/.
Uso: python -I -X utf8 scarica_istat.py <nascite_dir>      (una richiesta ogni 15 s, User-Agent dichiarato)"""
import sys, os, time, urllib.request
N = sys.argv[1]
OUT = os.path.join(N, "raw", "istat")
os.makedirs(OUT, exist_ok=True)
FILES = {"25_326_DF_DCIS_FECONDITA1_5": "istat_FECONDITA1_5_TFR_province.csv",
         "25_326_DF_DCIS_FECONDITA1_6": "istat_FECONDITA1_6_eta_media_madri_province.csv"}
for flow, fn in FILES.items():
    dst = os.path.join(OUT, fn)
    if os.path.exists(dst):
        continue
    rq = urllib.request.Request(f"https://esploradati.istat.it/SDMXWS/rest/data/IT1,{flow},1.0/ALL/?startPeriod=2000",
                                headers={"User-Agent": "milano-in-dati/nascite (ricerca open data)", "Accept": "application/vnd.sdmx.data+csv;version=1.0.0"})
    open(dst, "wb").write(urllib.request.urlopen(rq, timeout=180).read())
    print(fn, os.path.getsize(dst))
    time.sleep(15)
