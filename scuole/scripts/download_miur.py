"""Scarica i CSV del Portale Unico dei Dati della Scuola (MIM) elencati nelle pagine di catalogo salvate.
uso: python -I -X utf8 download_miur.py <abs scuole> """
import sys, re, os, time, csv, hashlib, datetime, requests
S = sys.argv[1]
BASE = "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
UA = {"User-Agent": "milano-in-dati/1.0"}
want = {  # file in pagina -> prefissi
 "studenti.html": ["ALUCORSOETASTA","ALUCORSOETAPAR","ALUITASTRACITSTA","ALUITASTRACITPAR",
                   "INFANZIAETASTA","INFANZIAETAPAR","INFANZIASTRACITSTA","INFANZIASTRACITPAR",
                   "ALUCORSOINDCLASTA","ALUCORSOINDCLAPAR","INFANZIACLASTA","INFANZIACLAPAR"],
 "area_Scuole.html": ["SCUANAGRAFESTAT","SCUANAGRAFEPAR"],
 "area_Edilizia.html": ["EDIANAGRAFESTA"],
}
logp = f"{S}/raw/miur/download_log.csv"
os.makedirs(f"{S}/raw/miur", exist_ok=True)
done = {}
if os.path.exists(logp):
    for r in csv.DictReader(open(logp, encoding="utf-8")): done[r["file"]] = r
rows = list(done.values())
for page, prefs in want.items():
    t = open(f"{S}/raw/_pagine/{page}", encoding="utf-8").read()
    files = sorted(set(re.findall(r'href="([^"/]*\.csv)"', t)))
    for f in files:
        m = re.match(r'([A-Z]+)\d', f)
        if m.group(1) not in prefs: continue
        if f in done: continue
        dest = f"{S}/raw/miur/{f}"
        try:
            r = requests.get(BASE + f, timeout=300, headers=UA, stream=True)
            ct = r.headers.get("content-type", "")
            data = r.content
            ok = r.status_code == 200 and len(data) > 5000 and "html" not in ct
            if ok: open(dest, "wb").write(data)
            row = dict(file=f, url=BASE + f, status=r.status_code, bytes=len(data), ok=ok,
                       sha256=hashlib.sha256(data).hexdigest() if ok else "",
                       downloaded=datetime.date.today().isoformat())
        except Exception as e:
            row = dict(file=f, url=BASE + f, status="ERR " + str(e)[:80], bytes=0, ok=False, sha256="", downloaded=datetime.date.today().isoformat())
        rows.append(row); print(row["file"], row["status"], row["bytes"], flush=True)
        with open(logp, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(row.keys())); w.writeheader(); w.writerows(rows)
        time.sleep(0.5)
