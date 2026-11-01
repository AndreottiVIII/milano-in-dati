"""Scarica i file MEF 'REG_calcolo_irpef_<anno>.csv' (per regione e classe di reddito complessivo, dichiarazioni 2017-2025,
cioe' anni d'imposta 2016-2024) in raw/mef_nazionale/. Uso: python -I -X utf8 scarica_mef_regioni.py <percorso assoluto redditi>"""
import sys, os, time, hashlib, csv, datetime, urllib.request
base = sys.argv[1]; raw = os.path.join(base, "raw", "mef_nazionale"); os.makedirs(raw, exist_ok=True)
U = "https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/"
rows = []
for y in range(2017, 2026):
    name = f"REG_calcolo_irpef_{y}.csv"; dest = os.path.join(raw, name)
    if not (os.path.exists(dest) and os.path.getsize(dest) > 1000):
        req = urllib.request.Request(U + name, headers={"User-Agent": "Mozilla/5.0 (ricerca open data, uso locale)"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f: f.write(r.read())
        time.sleep(2)
    b = open(dest, "rb").read()
    rows.append([name, U + name, len(b), hashlib.sha256(b).hexdigest()[:16], datetime.date.today().isoformat()]); print(rows[-1])
with open(os.path.join(raw, "download_log.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["file", "url", "byte", "sha256_16", "data_scarico"]); w.writerows(rows)
