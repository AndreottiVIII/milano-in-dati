"""Scarica in raw/ i dataset sul turismo per provenienza.
uso: python -I -X utf8 03_scarica.py <turisti assoluto>
Comune di Milano (CKAN): ds210..ds220, ds681; Regione Lombardia (Socrata): xzck-giqt (provincia Milano), c9ae-qhbj (comune Milano).
Pausa 3 s tra richieste, User-Agent dichiarato, nessun account. I file di affitti-brevi/raw (ds213, vyxt-7jdx, mzxz-sz25) si copiano con 04_copia."""
import sys, os, json, time, urllib.request, urllib.parse, datetime
base = sys.argv[1]
UA = {"User-Agent": "milano-in-dati research (turisti fase 1)"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120) as f:
        return f.read()
log = open(os.path.join(base, "raw", "download_log.csv"), "a", encoding="utf-8")
def reg(src, path, n): 
    log.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M};{src};{os.path.relpath(path, base)};{n}\n"); log.flush()
ck = json.load(open(os.path.join(base, "raw", "ricerche", "ckan_milano_turismo.json"), encoding="utf-8"))
want = ["ds210", "ds211", "ds212", "ds214", "ds215", "ds217", "ds218", "ds219", "ds220", "ds681", "ds526"]
d = os.path.join(base, "raw", "comune_milano"); os.makedirs(d, exist_ok=True)
for k, v in ck.items():
    if k.split("-")[0].split("_")[0] in want:
        # metadati
        m = get("https://dati.comune.milano.it/api/3/action/package_show?id=" + k)
        open(os.path.join(d, k.split("-")[0].split("_")[0] + ".meta.json"), "wb").write(m); time.sleep(3)
        for fmt, url in v["res"]:
            if fmt == "CSV":
                b = get(url); p = os.path.join(d, k.split("-")[0].split("_")[0] + ".csv")
                open(p, "wb").write(b); reg(url, p, len(b)); print(k, len(b)); time.sleep(3)
                break
d = os.path.join(base, "raw", "lombardia"); os.makedirs(d, exist_ok=True)
for i, where in [("xzck-giqt", "provincia='Milano'"), ("c9ae-qhbj", "comune='Milano'")]:
    q = urllib.parse.urlencode({"$where": where, "$limit": 50000})
    u = f"https://dati.lombardia.it/resource/{i}.csv?{q}"
    b = get(u); p = os.path.join(d, i + "_milano.csv"); open(p, "wb").write(b); reg(u, p, len(b)); print(i, len(b)); time.sleep(3)
