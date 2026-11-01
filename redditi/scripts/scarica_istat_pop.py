"""Scarica da demo.istat.it la popolazione residente per comune al 1 gennaio:
 - ricostruzione 2002-2019 (PopolazioneEta-SingolaArea-Comuni.zip)
 - POSAS 2020-2026 (POSAS_<anno>_it_Comuni.zip)
Uso: python -I -X utf8 scarica_istat_pop.py <percorso assoluto redditi>
File non fidati: restano in raw/istat_pop/."""
import sys, os, time, zipfile, hashlib, csv, datetime, urllib.request
base = sys.argv[1]; raw = os.path.join(base, "raw", "istat_pop"); os.makedirs(raw, exist_ok=True)
U = "https://demo.istat.it/data/"
jobs = [("ricostruzione/PopolazioneEta-SingolaArea-Comuni.zip", "ricostruzione_2002_2019_comuni.zip")] + \
       [(f"posas/POSAS_{y}_it_Comuni.zip", f"POSAS_{y}_it_Comuni.zip") for y in range(2020, 2027)]
rows = []
for rel, name in jobs:
    dest = os.path.join(raw, name)
    st = "gia_presente"
    if not (os.path.exists(dest) and zipfile.is_zipfile(dest)):
        req = urllib.request.Request(U + rel, headers={"User-Agent": "Mozilla/5.0 (ricerca open data, uso locale)"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b: break
                    f.write(b)
            st = "ok" if zipfile.is_zipfile(dest) else "NON_ZIP"
        except Exception as e:
            st = "ERRORE " + repr(e)
        time.sleep(2)
    size = os.path.getsize(dest) if os.path.exists(dest) else 0
    rows.append([name, U + rel, st, size, datetime.date.today().isoformat()]); print(rows[-1], flush=True)
with open(os.path.join(raw, "download_log.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["file", "url", "stato", "byte", "data_scarico"]); w.writerows(rows)
