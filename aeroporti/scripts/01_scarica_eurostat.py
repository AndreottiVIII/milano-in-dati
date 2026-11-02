"""Scarica da Eurostat (API di diffusione, JSON-stat, licenza CC BY 4.0) i dati sui tre aeroporti di Milano
e su tutti gli altri aeroporti (per il totale Italia e la classifica).

Dataset:
  avia_paoa  passeggeri per aeroporto (tra_meas PAS_CRD = passeggeri trasportati; CAF_PAS = voli commerciali con passeggeri)
  avia_gooa  merci e posta per aeroporto (tra_meas FRM_LD_NLD = merci e posta caricate e scaricate, tonnellate)
  avia_paoc  passeggeri per paese (Italia; solo per un controllo)
Aeroporti: tutti quelli europei (annuale), poi si tengono gli italiani (IT_*); mensile solo
           IT_LIML Linate, IT_LIMC Malpensa, IT_LIME Bergamo-Orio al Serio.

uso: python -I -X utf8 01_scarica_eurostat.py <cartella aeroporti assoluta>
Pausa 3 s tra richieste, User-Agent onesto, nessuna registrazione. Salva in raw/eurostat/ e aggiorna raw/download_log.csv.
"""
import sys, os, time, json, datetime, urllib.request, urllib.parse

base = sys.argv[1]
raw = os.path.join(base, "raw", "eurostat")
os.makedirs(raw, exist_ok=True)
UA = {"User-Agent": "milano-in-dati research (aeroporti fase 1)"}
API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
AIRP = ["IT_LIML", "IT_LIMC", "IT_LIME", "IT_LIRF", "IT_LIPZ", "IT_LIRN", "IT_LIPE"]
COV = ["TOTAL", "NAT", "INTL", "INTL_IEU27_2020", "INTL_XEU27_2020"]

jobs = []
# annuali: tutti gli aeroporti europei (poi si tengono quelli IT_*), un file per copertura
for c in COV:
    jobs.append((f"avia_paoa_A_pax_tutti_{c}", "avia_paoa", [("freq", "A"), ("tra_meas", "PAS_CRD"), ("schedule", "TOTAL"), ("unit", "PAS"), ("tra_cov", c)]))
jobs.append(("avia_paoa_A_voli_tutti", "avia_paoa", [("freq", "A"), ("tra_meas", "CAF_PAS"), ("schedule", "TOTAL"), ("unit", "FLIGHT"), ("tra_cov", "TOTAL")]))
jobs.append(("avia_gooa_A_merci_tutti", "avia_gooa", [("freq", "A"), ("tra_meas", "FRM_LD_NLD"), ("schedule", "TOTAL"), ("tra_cov", "TOTAL"), ("unit", "T")]))
# mensili: solo i tre aeroporti di Milano
ap = AIRP[:3]
jobs.append(("avia_paoa_M_pax", "avia_paoa", [("freq", "M"), ("tra_meas", "PAS_CRD"), ("schedule", "TOTAL")] + [("tra_cov", c) for c in COV] + [("rep_airp", a) for a in ap]))
jobs.append(("avia_paoa_M_voli", "avia_paoa", [("freq", "M"), ("tra_meas", "CAF_PAS"), ("schedule", "TOTAL")] + [("tra_cov", c) for c in COV] + [("rep_airp", a) for a in ap]))
jobs.append(("avia_gooa_M_merci", "avia_gooa", [("freq", "M"), ("tra_meas", "FRM_LD_NLD"), ("schedule", "TOTAL"), ("tra_cov", "TOTAL"), ("unit", "T")] + [("rep_airp", a) for a in ap]))
# totale per paese (Eurostat conta i passeggeri dei voli nazionali una volta sola: non e' la somma degli aeroporti)
jobs.append(("avia_paoc_A_pax_it", "avia_paoc", [("freq", "A"), ("tra_meas", "PAS_CRD"), ("schedule", "TOTAL"), ("geo", "IT")] + [("tra_cov", c) for c in COV]))

log = open(os.path.join(base, "raw", "download_log.csv"), "a", encoding="utf-8")
for name, ds, params in jobs:
    fn = os.path.join(raw, name + ".json")
    if os.path.exists(fn):
        continue
    url = API + ds + "?" + urllib.parse.urlencode(params + [("format", "JSON"), ("lang", "EN")])
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as f:
        data = f.read()
    j = json.loads(data)
    if "error" in j:
        print("ERRORE", name, j["error"])
        continue
    open(fn, "wb").write(data)
    log.write(f"{datetime.date.today()};{url};{fn};{len(data)};CC BY 4.0 (Eurostat); aggiornato {j.get('updated')}\n")
    log.flush()
    print(name, len(data), j.get("updated"), j["size"])
    time.sleep(3)
