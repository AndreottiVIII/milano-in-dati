"""Scarica dataset sport del Comune (CKAN) in raw/. Uso: python -I -X utf8 download_comune.py <raw_dir>"""
import sys, os, json, urllib.request, datetime, hashlib
raw = sys.argv[1]
IDS = ["ds34_infogeo_impianti_sportivi_localizzazione_", "ds1640_infogeo_impianti_sportivi_localizzazione", "ds2941_impianti-sportivi-comunali-in-concessione",
 "ds1491_sport_impianti_sportivi_gestiti_nel_2019_da_milanosport_spa", "ds292_sport_impianti_sportivi_gestiti_nel_2018_da_milanosport_spa",
 "ds32-infogeo-centri-balneari-localizzazione", "ds1867-destinazione-d-uso-degli-spazi-negli-edifici-scolastici-scuole-statali-as-2020-2021",
 "ds632-street-sport-orari-parchi-comunali-per-municipio"]
log = open(os.path.join(raw, "download_log.csv"), "a", encoding="utf-8")
for pid in IDS:
    d = json.load(urllib.request.urlopen("https://dati.comune.milano.it/api/3/action/package_show?id=" + pid, timeout=60))["result"]
    folder = os.path.join(raw, "comune_" + pid.split("_")[0].split("-")[0]); os.makedirs(folder, exist_ok=True)
    json.dump(d, open(os.path.join(folder, "_metadati.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in d["resources"]:
        fn = r["url"].rsplit("/", 1)[-1]
        if r["format"] not in ("CSV", "GeoJSON"): continue
        dst = os.path.join(folder, fn)
        if not os.path.exists(dst):
            urllib.request.urlretrieve(r["url"], dst)
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
        log.write(f"{datetime.date.today()};{pid};{r['format']};{r['url']};{os.path.getsize(dst)};{h};{r.get('last_modified')};{d.get('license_id')}\n"); log.flush()
        print(pid, fn, os.path.getsize(dst))
