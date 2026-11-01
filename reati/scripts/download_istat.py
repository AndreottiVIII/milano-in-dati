"""Scarica da ISTAT (esploradati, SDMX CSV) i dataflow sui delitti denunciati. Max ~4 richieste/minuto.
Uso: download_istat.py <cartella raw/istat> """
import sys, time, os, urllib.request, csv, io
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
BASE = "https://esploradati.istat.it/SDMXWS/rest/data/"
JOBS = [
    # (file, dataflow, chiave)  chiave = FREQ.AREA.DATA_TYPE.TYPE_CRIME.KNOWN.PERIOD
    ("df1_CRIMEN_tutte_aree_TOT.csv", "73_67_DF_DCCV_DELITTIPS_1", "A..CRIMEN.TOT.."),
    ("df9_CRIMET_tutte_aree.csv", "73_67_DF_DCCV_DELITTIPS_9", "A..CRIMET..."),
    ("df5_grandi_comuni_CRIMEN.csv", "73_67_DF_DCCV_DELITTIPS_5", "A....."),
    ("df8_grandi_comuni_CRIMET.csv", "73_67_DF_DCCV_DELITTIPS_8", "A....."),
]
log = open(os.path.join(out, "download_log.csv"), "a", encoding="utf8")
for fn, flow, key in JOBS:
    path = os.path.join(out, fn)
    if os.path.exists(path):
        print("gia presente", fn); continue
    url = f"{BASE}IT1,{flow},1.0/{key}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.sdmx.data+csv;version=1.0.0",
                                               "User-Agent": "Mozilla/5.0 (milano-in-dati research)"})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=300)
        d = r.read()
        open(path, "wb").write(d)
        msg = f"OK,{fn},{len(d)},{r.status},{time.strftime('%Y-%m-%d %H:%M:%S')},{url}"
    except Exception as e:
        msg = f"ERR,{fn},0,{e!r},{time.strftime('%Y-%m-%d %H:%M:%S')},{url}"
    print(msg, round(time.time() - t, 1), "s")
    log.write(msg + "\n"); log.flush()
    time.sleep(20)
