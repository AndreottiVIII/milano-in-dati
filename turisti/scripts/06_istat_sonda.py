"""Sonda i dataflow ISTAT DCSC_TUR (esploradati SDMX): nome di ciascuno. Max 5 richieste/minuto: pausa 15 s.
uso: python -I -X utf8 06_istat_sonda.py <cartella raw/istat assoluta> n1 n2 ..."""
import sys, os, re, time, urllib.request
out = sys.argv[1]
UA = {"User-Agent": "milano-in-dati research (turisti fase 1)"}
for n in sys.argv[2:]:
    u = f"https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1/122_54_DF_DCSC_TUR_{n}/latest"
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read().decode("utf-8")
        open(os.path.join(out, f"df_TUR_{n}.xml"), "w", encoding="utf-8").write(b)
        print(n, re.findall(r'xml:lang="it">([^<]+)<', b)[:1], flush=True)
    except Exception as e:
        print(n, "ERRORE", e, flush=True)
    time.sleep(15)
