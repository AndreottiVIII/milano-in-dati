"""Scarica da IstatData (API SDMX pubblica) il tasso di fecondita' per eta' della madre, province, 2000-2025,
in raw/istat/. Uso: python -I -X utf8 02_scarica_fecondita_eta.py <cartella nascite>
(una sola richiesta, User-Agent dichiarato; flusso IT1,25_326_DF_DCIS_FECONDITA1_7)."""
import sys, os, urllib.request
N = sys.argv[1]
OUT = os.path.join(N, "raw", "istat")
os.makedirs(OUT, exist_ok=True)
dst = os.path.join(OUT, "istat_FECONDITA1_7_fecondita_per_eta_province.csv")
if not os.path.exists(dst):
    rq = urllib.request.Request("https://esploradati.istat.it/SDMXWS/rest/data/IT1,25_326_DF_DCIS_FECONDITA1_7,1.0/ALL/?startPeriod=2000",
                                headers={"User-Agent": "milano-in-dati/nascite (ricerca open data)", "Accept": "application/vnd.sdmx.data+csv;version=1.0.0"})
    open(dst, "wb").write(urllib.request.urlopen(rq, timeout=300).read())
print(dst, os.path.getsize(dst))
