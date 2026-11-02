"""Scarica in raw/ i dataset del Comune sul verde (CKAN, CC-BY). Uso: python -I -X utf8 scarica.py <raw_dir>
Scrive raw/comune_<id>/ (metadati + file) e raw/download_log.csv (data, id, formato, url, byte, sha256 corto, ultima modifica, licenza).
Solo risorse pubbliche; nessun login, nessun aggiramento."""
import sys, os, json, urllib.request, datetime, hashlib
raw = sys.argv[1]
IDS = [("ds89_infogeo_parchi_giardini_localizzazione_", ["GeoJSON", "CSV"]),
       ("ds52_infogeo_aree_cani_localizzazione", ["GeoJSON"]),
       ("ds724_infogeo_aree_gioco_localizzazione", ["GeoJSON"]),
       ("ds2187-infogeo-giardini-condivisi-localizzazione", ["GeoJSON"]),
       ("ds2186-infogeo-orti-urbani-localizzazione", ["GeoJSON"]),
       ("ds2811-esposizione-calore-urbano-nil-07-2024", ["CSV"])]
log_path = os.path.join(raw, "download_log.csv")
new = not os.path.exists(log_path)
log = open(log_path, "a", encoding="utf-8")
if new:
    log.write("data;dataset;formato;url;byte;sha256_16;ultima_modifica_risorsa;licenza\n")
for pid, fmts in IDS:
    d = json.load(urllib.request.urlopen("https://dati.comune.milano.it/api/3/action/package_show?id=" + pid, timeout=60))["result"]
    folder = os.path.join(raw, "comune_" + pid.split("_")[0].split("-")[0]); os.makedirs(folder, exist_ok=True)
    json.dump(d, open(os.path.join(folder, "_metadati.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in d["resources"]:
        if r["format"] not in fmts: continue
        fn = r["url"].rsplit("/", 1)[-1]
        dst = os.path.join(folder, fn)
        if not os.path.exists(dst):
            urllib.request.urlretrieve(r["url"], dst)
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
        log.write(f"{datetime.date.today()};{pid};{r['format']};{r['url']};{os.path.getsize(dst)};{h};{r.get('last_modified')};{d.get('license_id')}\n"); log.flush()
        print(pid, fn, os.path.getsize(dst))
