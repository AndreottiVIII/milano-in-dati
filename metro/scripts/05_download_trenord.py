"""Scarica da dati.lombardia.it (CC0) le frequentazioni stazioni ferroviarie (Trenord): m2u2-frtq (2015-2023) e ut63-s688 (aggiornata).
Uso: python -I -X utf8 05_download_trenord.py <raw_dir>"""
import sys, os, json, urllib.request, csv, datetime
raw = sys.argv[1]; os.makedirs(raw, exist_ok=True)
today = datetime.date.today().isoformat()
for ds in ("m2u2-frtq", "ut63-s688"):
    rows, off = [], 0
    while True:
        u = f"https://www.dati.lombardia.it/resource/{ds}.json?$limit=50000&$offset={off}&$order=:id"
        req = urllib.request.Request(u, headers={"User-Agent": "milano-in-dati research"})
        part = json.load(urllib.request.urlopen(req, timeout=180))
        rows += part; off += 50000
        if len(part) < 50000: break
    keys = sorted({k for r in rows for k in r if not k.startswith(":@") and k != "location"})
    with open(os.path.join(raw, ds + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(ds, len(rows), "righe", today)
    meta = urllib.request.urlopen(urllib.request.Request(f"https://www.dati.lombardia.it/api/views/{ds}.json", headers={"User-Agent": "milano-in-dati research"}), timeout=60).read()
    open(os.path.join(raw, ds + "_meta.json"), "wb").write(meta)
