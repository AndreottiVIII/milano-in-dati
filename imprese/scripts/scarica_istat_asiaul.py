"""Scarica da ISTAT (esploradati.istat.it, SDMX, licenza CC BY 4.0) le unita' locali e gli addetti per comune (ASIA-UL).

Uso: python -I -X utf8 scarica_istat_asiaul.py <imprese_dir>
Dataflow 183_285_DF_DICA_ASIAULP_1 "Unita' locali e addetti - Principali dati".
Una sola richiesta (comuni: Milano 015146, Roma 058091, Torino 001272, Napoli 063049, Bologna 037006), anni da 2012,
sezioni ATECO + totale, classe addetti TOTAL, tipi dato LU (unita' locali) e LUEMPD (addetti delle unita' locali).
Il servizio ISTAT limita le richieste (poche al minuto) e puo' bloccare l'indirizzo: qui un solo tentativo ogni 10 minuti,
al massimo 6 tentativi, mai in parallelo. Se non risponde, il programma esce senza scrivere nulla.
Scrive raw/istat_asiaul/asiaul_comuni.csv (SDMX-CSV) e raw/istat_asiaul/log.txt
"""
import sys, os, time, datetime, hashlib
import requests
D = sys.argv[1]
OUT = os.path.join(D, "raw", "istat_asiaul"); os.makedirs(OUT, exist_ok=True)
URL = ("https://esploradati.istat.it/SDMXWS/rest/data/IT1,183_285_DF_DICA_ASIAULP_1,1.0/"
       "A.015146+058091+001272+063049+037006.LU+LUEMPD.0010+A+B+C+D+E+F+G+H+I+J+K+L+M+N+O+P+Q+R+S+T+U.TOTAL")
HDR = {"User-Agent": "milano-in-dati research (dati aperti, uso divulgativo)", "Accept": "application/vnd.sdmx.data+csv;version=1.0.0"}
log = open(os.path.join(OUT, "log.txt"), "a", encoding="utf8")
for k in range(6):
    t0 = datetime.datetime.now().isoformat(timespec="seconds")
    try:
        r = requests.get(URL, params={"startPeriod": "2012"}, headers=HDR, timeout=(30, 300))
        log.write(f"{t0} tentativo {k+1}: HTTP {r.status_code} {len(r.content)} byte\n"); log.flush()
        if r.status_code == 200 and len(r.content) > 500:
            open(os.path.join(OUT, "asiaul_comuni.csv"), "wb").write(r.content)
            log.write(f"sha256 {hashlib.sha256(r.content).hexdigest()}\n"); log.flush()
            print("ok", len(r.content)); sys.exit(0)
    except requests.RequestException as e:
        log.write(f"{t0} tentativo {k+1}: errore {type(e).__name__}\n"); log.flush()
    time.sleep(600)
print("nessuna risposta utile"); sys.exit(1)
