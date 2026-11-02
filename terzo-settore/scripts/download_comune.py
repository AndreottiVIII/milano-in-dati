"""Scarica da dati.comune.milano.it (CKAN) i dataset del terzo settore. Uso: python -I -X utf8 download_comune.py <cartella_raw_comune_assoluta>
Salva, per ogni dataset, la cartella <id>/ con il file CSV e i metadati (package_show.json). Scrive download_log.csv."""
import sys, os, json, csv, hashlib, datetime, requests
OUT = sys.argv[1]
IDS = ["ds1332_registro-anagrafico-associazioni", "ds562_albo-cooperative-sociali-per-il-comune-di-milano",
       "ds606_elenco_persone_giuridiche_riconosciute_da_regione_lombardia_",
       "ds596_organizzazioni_non_governative_che_collaborano_con_regione_l",
       "ds273-economia-numero-istituzioni-personale-forma-giuridica-settore-attivita-2011c",
       "ds274-istituzioni-non-profit", "ds1301-case-delle-associazioni-e-del-volontariato",
       "ds1342_albo-comitati-gruppi-informali-formazioni-sociali", "ds76_infogeo_associazioni_localizzazione_"]
s = requests.Session(); s.headers["User-Agent"] = "milano-in-dati-research/1.0"
log = []
for i in IDS:
    d = os.path.join(OUT, i.split("_")[0].split("-")[0]); os.makedirs(d, exist_ok=True)
    p = s.get("https://dati.comune.milano.it/api/3/action/package_show", params={"id": i}, timeout=60).json()["result"]
    json.dump(p, open(os.path.join(d, "package_show.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    for r in p["resources"]:
        if r["format"].upper() != "CSV": continue
        b = s.get(r["url"], timeout=120).content
        f = os.path.join(d, r["url"].rsplit("/", 1)[1]); open(f, "wb").write(b)
        log.append([datetime.date.today().isoformat(), i, p["license_id"], r["url"], len(b), hashlib.sha256(b).hexdigest(), f])
        print(i, len(b))
w = csv.writer(open(os.path.join(OUT, "download_log.csv"), "w", newline="", encoding="utf8"))
w.writerow(["data", "dataset", "licenza", "url", "byte", "sha256", "file"]); w.writerows(log)
