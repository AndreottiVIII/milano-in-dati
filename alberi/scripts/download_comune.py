"""Scarica i dataset del Comune (CKAN) in raw/. Uso: python -I download_comune.py <raw_dir>"""
import sys, os, json, urllib.request, datetime, hashlib
raw = sys.argv[1]
IDS = ["ds2484_infogeo_alberi_localizzazione","ds2489-gli-alberi-monumentali-nel-comune-di-milano",
 "ds3018-spazi-freschi-parchi-ed-aree-verdi","ds2813-indice-di-verde-urbano-nil-07-2024",
 "ds2926-disponibilita-di-verde-urbano-in-mq-per-abitante-2011-avanti","ds1323-verde-urbano-dal-2011-avanti",
 "ds2927-densita-di-verde-urbano-e-incidenza-percentuale-sulla-superficie-comunale-2011-avanti",
 "ds339-territorioambiente-aree-verdi-zona-superficie-2014","ds2810-indice-di-verde-urbano-municipi-07-2024"]
log = open(os.path.join(raw, "download_log.csv"), "a", encoding="utf-8")
for pid in IDS:
    d = json.load(urllib.request.urlopen("https://dati.comune.milano.it/api/3/action/package_show?id=" + pid, timeout=60))["result"]
    folder = os.path.join(raw, "comune_" + pid.split("_")[0].split("-")[0]); os.makedirs(folder, exist_ok=True)
    json.dump(d, open(os.path.join(folder, "_metadati.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in d["resources"]:
        fn = r["url"].rsplit("/", 1)[-1]
        if r["format"] not in ("CSV", "GeoJSON", "JSON"): continue
        if pid.startswith("ds2484") and r["format"] == "JSON": continue  # copia del CSV
        dst = os.path.join(folder, fn)
        if not os.path.exists(dst):
            urllib.request.urlretrieve(r["url"], dst)
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
        log.write(f"{datetime.date.today()};{pid};{r['format']};{r['url']};{os.path.getsize(dst)};{h};{r.get('last_modified')};{d.get('license_id')}\n"); log.flush()
        print(pid, fn, os.path.getsize(dst))
