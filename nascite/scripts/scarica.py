"""Scarica i dataset sulle nascite del Comune di Milano (CKAN) in raw/comune/. Solo CSV, una volta (se il file c'e' non lo riscarica).
Uso: python -I -X utf8 scarica.py <nascite_dir>
Scrive anche raw/comune/_metadati_<id>.json e raw/download_log.csv (data;dataset;url;byte;impronta;licenza)."""
import sys, os, json, urllib.request, datetime, hashlib, time
N = sys.argv[1]
raw = os.path.join(N, "raw", "comune")
os.makedirs(raw, exist_ok=True)
IDS = ["ds141-popolazione-nascite-quartiere", "ds140-popolazione-nascite-municipio",
       "ds1943-popolazione-nascite-dei-residenti-per-quartiere", "ds1942-popolazione-nascite-dei-residenti-per-municipio",
       "ds1944-popolazione-nascite-dei-residenti-per-classi-di-eta-tipo-di-parto-filiazione",
       "ds1945-popolazione-nascite-avvenute-a-milano-per-classi-di-eta-tipo-parto-e-filiazione",
       "ds1946-popolazione-nascite-avvenute-a-milano-per-cittadinanza-e-luogo-di-residenza-genitori",
       "ds289-popolazione-nascite", "ds2918-tassi-natalita-mortalita-dal-1880",
       "ds1495-popolazione-censimenti-storici-nati-vivi-residenti-nel-comune-di-milano-dal-1880",
       "ds72_popolazione_nascite_parti_gemellari-1979-avanti"]
UA = {"User-Agent": "milano-in-dati/nascite (ricerca su open data; contatto: davide.caniatti@gmail.com)"}
log = open(os.path.join(N, "raw", "download_log.csv"), "a", encoding="utf-8")
for pid in IDS:
    rq = urllib.request.Request("https://dati.comune.milano.it/api/3/action/package_show?id=" + pid, headers=UA)
    d = json.load(urllib.request.urlopen(rq, timeout=60))["result"]
    short = pid.split("_")[0].split("-")[0]
    json.dump(d, open(os.path.join(raw, f"_metadati_{short}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in d["resources"]:
        if r["format"] != "CSV":
            continue
        fn = r["url"].rsplit("/", 1)[-1]
        dst = os.path.join(raw, fn)
        if not os.path.exists(dst):
            time.sleep(2)
            data = urllib.request.urlopen(urllib.request.Request(r["url"], headers=UA), timeout=120).read()
            open(dst, "wb").write(data)
        h = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
        log.write(f"{datetime.date.today()};{short};{r['url']};{os.path.getsize(dst)};{h};{d.get('license_id')}\n"); log.flush()
        print(short, fn, os.path.getsize(dst))
