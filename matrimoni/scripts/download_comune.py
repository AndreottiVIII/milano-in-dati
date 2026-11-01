"""Scarica i dataset del Comune (CKAN) in raw/. Uso: python -I -X utf8 download_comune.py <raw_dir>"""
import sys, os, json, urllib.request, datetime, hashlib
raw = sys.argv[1]
IDS = ["ds138-popolazione-matrimoni-celebrati","ds1496-popolazione-censimenti-storici-matrimoni-dal-1948",
 "ds132-popolazione-matrimoni-coniuge-residente","ds705_popolazione_scioglimenti_dei_matrimoni_a_milano_nel_2018",
 "ds1947-popolazione-matrimoni-celebrati-a-milano-per-rito-e-cittadinanza",
 "ds1949-popolazione-matrimoni-con-almeno-un-coniuge-residente-a-milano-per-rito-e-cittadinanza",
 "ds1950-popolazione-matrimoni-celebrati-a-milano-per-classi-di-eta",
 "ds1952-popolazione-matrimoni-con-almeno-un-coniuge-residente-a-milano-suddivisi-per-classi-di-eta",
 "ds398-popolazione-unioni-civili-celebrate-a-milano",
 "ds361-popolazione-indicatori-caratteristiche-famiglie-coppie-censimenti"]
log = open(os.path.join(raw, "download_log.csv"), "a", encoding="utf-8")
for pid in IDS:
    d = json.load(urllib.request.urlopen("https://dati.comune.milano.it/api/3/action/package_show?id=" + pid, timeout=60))["result"]
    folder = os.path.join(raw, "comune_" + pid.split("_")[0].split("-")[0]); os.makedirs(folder, exist_ok=True)
    json.dump(d, open(os.path.join(folder, "_metadati.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in d["resources"]:
        fn = r["url"].rsplit("/", 1)[-1]
        if r["format"] != "CSV": continue
        dst = os.path.join(folder, fn)
        if not os.path.exists(dst):
            urllib.request.urlretrieve(r["url"], dst)
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
        log.write(f"{datetime.date.today()};{pid};{r['format']};{r['url']};{os.path.getsize(dst)};{h};{r.get('last_modified')};{d.get('license_id')}\n"); log.flush()
        print(pid, fn, os.path.getsize(dst))
