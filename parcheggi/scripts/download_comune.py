"""Scarica i dataset del Comune per il filone parcheggi. Uso: python -I -X utf8 download_comune.py <search_all.json> <raw_dir>
Per ogni dataset: CSV e GeoJSON se presenti (CC-BY). Log in raw/download_log.csv"""
import sys, json, os, urllib.request, csv, datetime
S, RAW = sys.argv[1], sys.argv[2]
IDS = ["ds83-infogeo-sosta-ambiti-localizzazione","ds342-trafficotrasporti-parcheggi-pubblici-localizzazione","ds45_infogeo_parcheggi_interscambio_localizzazione_",
 "ds740_sosta_bus_gt_turistici","ds51_trafficotrasporti_aree_pedonali_ztl","ds670-trasporto-pubblico-sosta-biciclette","ds79_infogeo_aree_sosta_car_sharing_localizzazione_","ds540_colonnine-di-ricarica"]
d = json.load(open(S, encoding="utf8"))
log = []
for i in IDS:
    p = d[i]
    sid = i.split("_")[0].split("-")[0]
    os.makedirs(os.path.join(RAW, "comune_" + sid), exist_ok=True)
    for fmt, size, url in p["res"]:
        if fmt not in ("CSV", "GeoJSON"): continue
        fn = os.path.join(RAW, "comune_" + sid, os.path.basename(url.split("?")[0]) or (sid + "." + fmt.lower()))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (milano-in-dati)"})
            b = urllib.request.urlopen(req, timeout=120).read()
            open(fn, "wb").write(b)
            log.append([i, fmt, url, fn, len(b), datetime.date.today().isoformat(), "ok"])
        except Exception as e:
            log.append([i, fmt, url, fn, 0, datetime.date.today().isoformat(), str(e)])
        print(log[-1])
w = csv.writer(open(os.path.join(RAW, "download_log.csv"), "w", newline="", encoding="utf8"))
w.writerow(["dataset", "formato", "url", "file", "byte", "data", "esito"]); w.writerows(log)
