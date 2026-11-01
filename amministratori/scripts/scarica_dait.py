"""Scarica dal DAIT (Ministero dell'Interno) gli amministratori comunali a fine anno 2007-2025 + gli "in carica" attuali.
Uso: python -I -X utf8 scarica_dait.py <cartella_raw_dait>   (percorso assoluto; si puo' rilanciare: salta i file gia' presenti)
Solo i file dei comuni (province e regioni non servono). Log in download_log.csv.
"""
import sys, os, re, csv, time, urllib.request, hashlib, datetime
RAW = sys.argv[1]
BASE = "https://dait.interno.gov.it"
UA = {"User-Agent": "Mozilla/5.0 (ricerca open data; contatto: davide.caniatti@gmail.com)"}
def get(url, dest=None):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    if dest:
        open(dest, "wb").write(data)
    return data
log = []
todo = [(f"in_carica_{n}", f"{BASE}/documenti/{n}.csv") for n in ["ammcom", "sindaciincarica", "maggiororgano", "organistraordinariincarica"]]
for y in range(2007, 2026):
    pg = get(f"{BASE}/elezioni/open-data/dati-amministratori-locali-in-carica-al-31-dicembre-{y}").decode("utf8", "replace")
    m = re.findall(r'href="(/documenti/storico_amministratori_comuni[^"]*\.csv)"', pg)
    assert len(m) == 1, (y, m)
    todo.append((f"comuni_31dic{y}", BASE + m[0]))
for nome, url in todo:
    dest = os.path.join(RAW, nome + ".csv")
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        continue
    t0 = time.time()
    try:
        d = get(url, dest)
        log.append([nome, url, len(d), hashlib.sha256(d).hexdigest(), datetime.date.today().isoformat(), "ok"])
        print("ok", nome, len(d), round(time.time() - t0), "s", flush=True)
    except Exception as e:
        log.append([nome, url, 0, "", datetime.date.today().isoformat(), repr(e)])
        print("ERR", nome, e, flush=True)
    time.sleep(2)
new = not os.path.exists(os.path.join(RAW, "download_log.csv"))
with open(os.path.join(RAW, "download_log.csv"), "a", newline="", encoding="utf8") as f:
    w = csv.writer(f)
    if new: w.writerow(["nome", "url", "byte", "sha256", "data_download", "esito"])
    w.writerows(log)
