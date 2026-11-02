"""Scarica da dati.istruzione.it/opendata i file nazionali "Studenti primaria/sec. I grado per tempo scuola" (DS0090 statale, DS0100 paritaria),
a.s. 2015/16 - 2024/25. Si puo' rilanciare: salta i file gia' presenti. Scrive download_log.csv (url, byte, sha256, data) nella cartella di uscita.
Uso: python -I -X utf8 download_miur_tempo.py <cartella_raw_miur>"""
import sys, os, csv, hashlib, time, datetime, urllib.request
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
BASE = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
UA = {"User-Agent": "milano-in-dati-research/1.0 (dati aperti, uso non commerciale)"}
names = [f"ALUTEMPOSCUOLA{tag}{y}{str(y+1)[2:]}{y+1}0831.csv" for y in range(2015, 2025) for tag in ("STA", "PAR")]
logp = os.path.join(OUT, "download_log.csv")
new = not os.path.exists(logp)
lf = open(logp, "a", newline="", encoding="utf8"); w = csv.writer(lf)
if new: w.writerow(["file", "url", "status", "bytes", "sha256", "scaricato"])
for n in names:
    p = os.path.join(OUT, n)
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        continue
    url = BASE + n
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300)
        data = r.read(); st = r.status
    except Exception as e:
        print("ERR", n, e); w.writerow([n, url, str(e), 0, "", datetime.date.today()]); lf.flush(); continue
    open(p, "wb").write(data)
    w.writerow([n, url, st, len(data), hashlib.sha256(data).hexdigest(), datetime.date.today()]); lf.flush()
    print("ok", n, len(data), flush=True); time.sleep(2)
print("fine")
