"""Scarica i dataset del Comune di Milano scelti (solo CSV, o zip del CSV) in raw/comune_<id>/.
Uso: python -I -X utf8 download_comune.py <raw_dir_assoluto>
Legge <raw>/search_all.json (da search.py). Pausa 1 s. User-Agent dichiarato. Log in <raw>/download_log.csv."""
import sys, os, json, re, time, urllib.request, hashlib, csv, datetime
raw = sys.argv[1]
d = json.load(open(os.path.join(raw, "search_all.json"), encoding="utf-8"))
WANT = "27 29 71 73 74 75 131 137 205 221 223 230 231 355 595_po 1494 1595 1596 1599 1600 1938 1940 1941 1942 1943 1946 1953 1954 1955 1956 1957 1958 1959 1960 1961 1962 1963 1964 1440 135".split()
log = []
for k, v in d.items():
    m = re.match(r"ds(\w+?)(?:-|_posas|_infogeo|$)", k)
    if not m or m.group(1).replace("_po","_po") not in WANT and m.group(1) not in WANT:
        continue
    dsid = "ds" + m.group(1)
    for fmt, size, url, name in v["res"]:
        if fmt != "CSV":
            continue
        out = os.path.join(raw, "comune_" + dsid)
        os.makedirs(out, exist_ok=True)
        fn = os.path.join(out, url.rsplit("/", 1)[-1])
        if os.path.exists(fn) and os.path.getsize(fn) > 0:
            status = "gia_presente"
        else:
            req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0 (ricerca open data)"})
            try:
                data = urllib.request.urlopen(req, timeout=180).read()
                open(fn, "wb").write(data)
                status = "ok"
            except Exception as e:
                status = "ERRORE " + str(e)
            time.sleep(1)
        sz = os.path.getsize(fn) if os.path.exists(fn) else 0
        sha = hashlib.sha256(open(fn, "rb").read()).hexdigest()[:16] if sz else ""
        log.append([dsid, k, v["title"], v["license"], v["modified"][:10], url, os.path.basename(fn), sz, sha, status, datetime.date.today().isoformat()])
        print(dsid, status, sz, flush=True)
with open(os.path.join(raw, "download_log.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["id", "package", "titolo", "licenza", "modificato_portale", "url", "file", "byte", "sha256_16", "esito", "data_scarico"])
    w.writerows(log)
