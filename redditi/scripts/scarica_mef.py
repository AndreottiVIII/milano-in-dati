"""Scarica dal sito MEF Dip. Finanze i file open data 'Redditi e principali variabili IRPEF'
(comunale CSV 2000-2024, sub-comunale CSV 2011 e 2015; 2019-2024 sono gia' nel filone 9 ma si
riscaricano per coerenza di fonte) in raw/mef/.
Uso: python -I -X utf8 scarica_mef.py <percorso assoluto redditi>
I file scaricati sono dati non fidati: restano in raw/, mai eseguiti. Pausa tra una richiesta e l'altra."""
import sys, os, time, hashlib, csv, datetime, urllib.request, zipfile
base = sys.argv[1]
raw = os.path.join(base, "raw", "mef"); os.makedirs(raw, exist_ok=True)
U = "https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/"
jobs = [("comunale", y) for y in range(2000, 2025)] + [("subcomunale", y) for y in (2011, 2015, 2019, 2020, 2021, 2022, 2023, 2024)]
logp = os.path.join(raw, "download_log.csv")
rows = []
for kind, y in jobs:
    name = f"Redditi_e_principali_variabili_IRPEF_su_base_{kind}_CSV_{y}.zip"
    dest = os.path.join(raw, name)
    if os.path.exists(dest) and zipfile.is_zipfile(dest):
        st = "gia_presente"
    else:
        req = urllib.request.Request(U + name, headers={"User-Agent": "milano-in-dati/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                f.write(r.read())
            st = "ok" if zipfile.is_zipfile(dest) else "NON_ZIP"
        except Exception as e:
            st = "ERRORE " + repr(e)
        time.sleep(2)
    size = os.path.getsize(dest) if os.path.exists(dest) else 0
    sha = hashlib.sha256(open(dest, "rb").read()).hexdigest()[:16] if size else ""
    rows.append([name, U + name, st, size, sha, datetime.date.today().isoformat()])
    print(rows[-1], flush=True)
with open(logp, "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["file", "url", "stato", "byte", "sha256_16", "data_scarico"]); w.writerows(rows)
