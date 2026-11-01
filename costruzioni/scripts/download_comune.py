"""Scarica i dataset del Comune (CKAN) in raw/comune_<id>/ e scrive download_log.csv.
Uso: python -I -X utf8 download_comune.py <raw_dir> <id1,id2,...> [formati=CSV]"""
import sys, os, json, hashlib, urllib.request, datetime, csv, time
raw = sys.argv[1]; ids = sys.argv[2].split(","); fmts = (sys.argv[3] if len(sys.argv) > 3 else "CSV").split(",")
UA = {"User-Agent": "milano-in-dati research (davide.caniatti@gmail.com)"}
logp = os.path.join(raw, "download_log.csv")
new = not os.path.exists(logp)
lf = open(logp, "a", newline="", encoding="utf-8"); w = csv.writer(lf)
if new: w.writerow(["data_download", "dataset", "titolo", "licenza", "metadata_modified", "formato", "url", "file", "byte", "sha256"])
for i in ids:
    r = urllib.request.urlopen(urllib.request.Request("https://dati.comune.milano.it/api/3/action/package_show?id=" + i, headers=UA), timeout=90)
    p = json.load(r)["result"]
    short = i.split("-")[0].split("_")[0]
    d = os.path.join(raw, "comune_" + short); os.makedirs(d, exist_ok=True)
    json.dump(p, open(os.path.join(d, "_metadati.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for res in p["resources"]:
        if res["format"].upper() not in fmts: continue
        fn = os.path.join(d, os.path.basename(res["url"]))
        data = urllib.request.urlopen(urllib.request.Request(res["url"], headers=UA), timeout=300).read()
        open(fn, "wb").write(data)
        w.writerow([datetime.date.today().isoformat(), p["name"], p["title"], p.get("license_id"), p["metadata_modified"], res["format"], res["url"], fn, len(data), hashlib.sha256(data).hexdigest()])
        lf.flush(); print(p["name"], res["format"], len(data)); time.sleep(2)
