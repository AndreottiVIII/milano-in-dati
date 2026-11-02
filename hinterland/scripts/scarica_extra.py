"""Scarichi extra per la pagina hinterland: Camere Eligendo + due prove (ISTAT esploradati, demo.istat.it).
Uso: python -I -X utf8 scarica_extra.py <percorso assoluto di milano-in-dati>
Regole: User-Agent dichiarato, pausa di 6 s tra le richieste, nessuna registrazione, nessun aggiramento di blocchi:
se un'indirizzo risponde con errore si registra e si passa oltre. I file scaricati sono dati non fidati (mai eseguiti)."""
import sys, os, time, urllib.request, urllib.error, hashlib, datetime
base = sys.argv[1]
UA = "MilanoInDati-ricerca-personale"
raw = os.path.join(base, "hinterland", "raw")
log = os.path.join(raw, "download_log_extra.csv")
os.makedirs(os.path.join(raw, "eligendo"), exist_ok=True)
os.makedirs(os.path.join(raw, "probe"), exist_ok=True)

def scrivi_log(riga):
    nuovo = not os.path.exists(log)
    with open(log, "a", encoding="utf-8") as f:
        if nuovo: f.write("quando;url;esito;byte;sha256;file\n")
        f.write(riga + "\n")

def get(url, dest, timeout):
    quando = datetime.datetime.now().isoformat(timespec="seconds")
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print("gia presente", dest); return True
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        with open(dest, "wb") as f: f.write(data)
        scrivi_log(f"{quando};{url};ok;{len(data)};{hashlib.sha256(data).hexdigest()};{os.path.relpath(dest, base)}")
        print("ok", dest, len(data)); return True
    except Exception as e:
        scrivi_log(f"{quando};{url};ERRORE {type(e).__name__} {e};0;;{os.path.relpath(dest, base)}")
        print("ERRORE", url, type(e).__name__, e); return False
    finally:
        time.sleep(6)

# 1) Camere Eligendo (nessuna registrazione)
for d in ["19870614", "19920405", "19960421", "20010513", "20060409", "20080413", "20130224", "20180304", "20220925"]:
    get(f"https://elezionistorico.interno.gov.it/daithome/documenti/opendata/camera/camera-{d}.zip",
        os.path.join(raw, "eligendo", f"camera-{d}.zip"), 120)

# 2) Una sola prova: catalogo ISTAT esploradati (attesa massima 90 s)
get("https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1?detail=allstubs",
    os.path.join(raw, "probe", "esploradati_dataflow.xml"), 90)

# 3) Una sola prova: pagina iniziale demo.istat.it (si cerca un file scaricabile con stranieri per cittadinanza e comune)
get("https://demo.istat.it/", os.path.join(raw, "probe", "demo_istat_home.html"), 60)
print("fine")
