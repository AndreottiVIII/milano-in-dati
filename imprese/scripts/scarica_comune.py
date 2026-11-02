"""Scarica da dati.comune.milano.it (CKAN, licenza cc-by) i dataset su imprese/attivita' commerciali.

Uso: python -I -X utf8 scarica_comune.py <imprese_dir>
Salva in raw/comune_<id>/ il CSV (primo CSV della scheda), il package_show.json, e scrive raw/comune_ckan/download_log.csv
Pausa 1,5 s, User-Agent dichiarato, salta i file gia' presenti.
"""
import sys, os, json, csv, time, hashlib, datetime
import requests
D = sys.argv[1]
UA = "milano-in-dati research (dati aperti, uso divulgativo)"
IDS = ["ds691-imprese-attive-per-settore-merceologico-2010-avanti",
       "ds1481-imprese-suddivise-per-forma-giuridica",
       "ds1482-personale-addetto-nelle-imprese-suddivise-per-forma-giuridica",
       "ds2954-attivita-commerciali-serie-storica",
       "ds512_commercio-al-dettaglio-esercizi-commerciali-e-superficie-di-vendita-2003-avanti",
       "ds202-aperture-chiusure-attivita-2018",
       ]
s = requests.Session(); s.headers["User-Agent"] = UA
logp = os.path.join(D, "raw", "comune_ckan", "download_log.csv")
new = not os.path.exists(logp)
lf = open(logp, "a", newline="", encoding="utf8"); w = csv.writer(lf)
if new: w.writerow(["dataset", "file", "url", "bytes", "sha256", "license_id", "metadata_modified", "data_download"])
for n in IDS:
    dd = os.path.join(D, "raw", "comune_" + n.split("-")[0].split("_")[0])
    os.makedirs(dd, exist_ok=True)
    pj = os.path.join(dd, "package_show.json")
    if not os.path.exists(pj):
        r = s.get("https://dati.comune.milano.it/api/3/action/package_show", params={"id": n}, timeout=60)
        r.raise_for_status(); open(pj, "wb").write(r.content); time.sleep(1.5)
    p = json.load(open(pj, encoding="utf8"))["result"]
    if n in SKIP_BIG: continue
    csvs = [x for x in p["resources"] if x["format"].upper() == "CSV"]
    for x in csvs[:1]:
        fn = os.path.join(dd, os.path.basename(x["url"]))
        if os.path.exists(fn): continue
        r = s.get(x["url"], timeout=120); r.raise_for_status()
        open(fn, "wb").write(r.content)
        w.writerow([n, os.path.basename(fn), x["url"], len(r.content), hashlib.sha256(r.content).hexdigest(), p.get("license_id"), p.get("metadata_modified"), datetime.date.today().isoformat()])
        lf.flush(); print("scaricato", fn, len(r.content)); time.sleep(1.5)
