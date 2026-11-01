"""Scarica dataset dei decessi dal CKAN del Comune di Milano in raw/. Uso: python -I -X utf8 download_comune.py <raw_dir>
File non fidati: solo letti come dati. User-Agent onesto, nessun trucco."""
import sys, os, json, urllib.request, datetime, hashlib
raw = sys.argv[1]
IDS = ["ds1937-popolazione-decessi-dei-residenti-a-milano-per-municipio","ds1938-popolazione-decessi-dei-residenti-a-milano-per-genere-ed-eta",
 "ds1940-popolazione-decessi-dei-residenti-a-milano-per-quartiere","ds131-popolazione-residenti-decessi-municipio","ds137-popolazione-residenti-decessi-quartiere",
 "ds222-popolazione-decessi-milano","ds1939-popolazione-decessi-avvenuti-a-milano-per-genere-ed-eta","ds2918-tassi-natalita-mortalita-dal-1880",
 "ds337-popolazione-decessi-causa-morte-milano-2003-2011","ds338-popolazione-residenti-decessi-causa-morte-2012-2013"]
UA = {"User-Agent": "milano-in-dati/1.0 (ricerca open data)"}
os.makedirs(raw, exist_ok=True)
log = open(os.path.join(raw, "download_log.csv"), "a", encoding="utf-8")
for pid in IDS:
    req = urllib.request.Request("https://dati.comune.milano.it/api/3/action/package_show?id=" + pid, headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=60))["result"]
    folder = os.path.join(raw, "comune_" + pid.split("-")[0]); os.makedirs(folder, exist_ok=True)
    json.dump(d, open(os.path.join(folder, "_metadati.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in d["resources"]:
        fn = r["url"].rsplit("/", 1)[-1]
        if r["format"] != "CSV": continue
        dst = os.path.join(folder, fn)
        if not os.path.exists(dst):
            urllib.request.urlretrieve(r["url"] if False else r["url"], dst) if False else open(dst, "wb").write(urllib.request.urlopen(urllib.request.Request(r["url"], headers=UA), timeout=120).read())
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
        log.write(f"{datetime.date.today()};{pid};{r['format']};{r['url']};{os.path.getsize(dst)};{h};{r.get('last_modified')};{d.get('license_id')}\n"); log.flush()
        print(pid, fn, os.path.getsize(dst), d.get("license_id"))
