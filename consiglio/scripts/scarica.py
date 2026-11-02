"""Scarica da CKAN dati.comune.milano.it i dataset sul consiglio comunale (solo CSV).
Uso: python -I -X utf8 scarica.py <consiglio_dir>
Scrive raw/<dsNNN>/*.csv, raw/<dsNNN>/_metadati_<ds>.json e raw/download_log.csv. Rilanciabile: salta i file già presenti."""
import sys, os, json, urllib.request, datetime, hashlib, time
base = sys.argv[1]
raw = os.path.join(base, "raw")
IDS = ["ds743-presenze-consiglieri-comunali-per-sedute-e-votazioni-2016-2021",
       "ds1643-presenze-consiglieri-comunali-per-sedute-e-votazioni-2021-2026",
       "ds1914_consiglio-comunale-2021-2026-dimissioni-o-surrogazioni-dei-consiglieri-riepilogo",
       # tre file mensili usati solo per controllare i cumulati di ds1643 (raw/verifica/)
       "ds2966_consiglio-comunale-20212026--presenze-consiglieri--dicembre-2025",
       "ds2967_consiglio-comunale-20212026--votazioni-consiglieri--dicembre-2025",
       "ds1648-consiglio-comunale-2021-2026-presenze-consiglieri-novembre-2021"]
hdr = {"User-Agent": "milano-in-dati/1.0 (ricerca open data)"}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=90).read()
log = open(os.path.join(raw, "download_log.csv"), "w", encoding="utf-8")   # riscritto a ogni lancio (data = giorno del lancio)
log.write("data;dataset;formato;url;byte;sha256;ultima_modifica;licenza\n")
for pid in IDS:
    d = json.loads(get("https://dati.comune.milano.it/api/3/action/package_show?id=" + pid))["result"]
    folder = os.path.join(raw, "verifica" if pid[:6] in ("ds2966", "ds2967", "ds1648-") or pid.startswith("ds1648") else pid.split("_")[0].split("-")[0]); os.makedirs(folder, exist_ok=True)
    json.dump(d, open(os.path.join(folder, "_metadati_" + pid.split("_")[0].split("-")[0] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in d["resources"]:
        if r["format"] != "CSV": continue
        fn = r["url"].rsplit("/", 1)[-1]
        dst = os.path.join(folder, fn)
        if not os.path.exists(dst):
            open(dst, "wb").write(get(r["url"])); time.sleep(0.5)
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()
        log.write(f"{datetime.date.today()};{pid.split('_')[0].split('-')[0]};CSV;{r['url']};{os.path.getsize(dst)};{h};{r.get('last_modified')};{d.get('license_id')}\n"); log.flush()
        print(pid[:6], fn, os.path.getsize(dst))
