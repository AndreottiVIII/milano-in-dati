"""Scarica metadati e risorse dei dataset scelti da dati.comune.milano.it (CKAN).
uso: python -I -X utf8 download_comune.py <abs scuole>"""
import sys, os, json, csv, hashlib, datetime, requests, re
S = sys.argv[1]
DS = ["ds224","ds225","ds226","ds105","ds188","ds187","ds102","ds103","ds104","ds294","ds295","ds296","ds297","ds298","ds299",
 "ds1736","ds1737","ds1738","ds1739","ds1740","ds1741","ds1742","ds1743",
 "ds3014","ds3015","ds3016","ds40","ds46","ds671","ds78","ds47","ds709","ds672","ds678","ds223","ds2427","ds2428","ds27","ds551"]
UA = {"User-Agent": "milano-in-dati/1.0"}
names = json.load(open(f"{S}/raw/search_comune.json", encoding="utf-8")).keys()
rows = []
for d in DS:
    cand = [n for n in names if re.match(re.escape(d) + r"[-_]", n)]
    if not cand: print("manca", d); continue
    name = cand[0]
    meta = requests.get("https://dati.comune.milano.it/api/3/action/package_show", params={"id": name}, headers=UA, timeout=90).json()["result"]
    od = f"{S}/raw/comune_{d}"; os.makedirs(od, exist_ok=True)
    json.dump(meta, open(f"{od}/_metadati.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in meta["resources"]:
        fmt = (r.get("format") or "").upper()
        if fmt not in ("CSV", "GEOJSON", "JSON", "XLS", "XLSX", "ZIP"): continue
        if fmt == "JSON" and any(x["format"].upper() == "CSV" for x in meta["resources"]) : continue
        fn = r["url"].split("/")[-1].split("?")[0]
        dest = f"{od}/{fn}"
        if os.path.exists(dest): continue
        try:
            resp = requests.get(r["url"], headers=UA, timeout=300); data = resp.content
            ok = resp.status_code == 200 and len(data) > 100
            if ok: open(dest, "wb").write(data)
            rows.append(dict(dataset=d, name=name, license=meta.get("license_id"), file=fn, url=r["url"], status=resp.status_code, bytes=len(data), sha256=hashlib.sha256(data).hexdigest() if ok else "", downloaded=datetime.date.today().isoformat()))
        except Exception as e:
            rows.append(dict(dataset=d, name=name, license=meta.get("license_id"), file=fn, url=r["url"], status="ERR "+str(e)[:60], bytes=0, sha256="", downloaded=datetime.date.today().isoformat()))
        print(rows[-1]["dataset"], rows[-1]["file"], rows[-1]["status"], rows[-1]["bytes"], flush=True)
with open(f"{S}/raw/comune_download_log.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
