"""Scarica i dati grezzi di "BikeMi e bici in citta'" in <bici>/raw (solo se mancano; --force per rifare).

Uso: python -I -X utf8 scarica.py <bici_dir> [--force]
Fonti (nessun account, nessuna chiave, nessun accesso aggirato):
  - Comune di Milano, portale CKAN dati.comune.milano.it (API pubblica): ds574 (sharing), ds65 (stazioni BikeMi), ds60 (itinerari ciclabili)
  - BikeMi, feed GBFS pubblico (https://gbfs.urbansharing.com/bikemi.com/), con l'intestazione Client-Identifier chiesta dalla pagina
    ufficiale https://bikemi.com/en/open-data/realtime ; UNA sola copia (fotografia), nessun campionamento ripetuto
  - Zenodo 1209115, "Scraped Data BikeMI 2011-2014" (A. Trentini, CC BY 4.0), 4 file CSV, controllo md5
"""
import sys, os, hashlib, urllib.request, json, time
B = sys.argv[1]; FORCE = "--force" in sys.argv
LOG = []
def get(url, dest, headers=None, md5=None):
    dest = os.path.join(B, "raw", dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and not FORCE:
        print("c'e' gia'", dest); return
    req = urllib.request.Request(url, headers=headers or {})
    data = urllib.request.urlopen(req, timeout=900).read()
    open(dest, "wb").write(data)
    h = hashlib.md5(data).hexdigest()
    ok = (md5 is None) or (h == md5)
    LOG.append({"url": url, "file": dest, "bytes": len(data), "md5": h, "md5_atteso": md5, "ok": ok, "quando": time.strftime("%Y-%m-%d %H:%M")})
    print(dest, len(data), "md5 ok" if ok else "MD5 DIVERSO")
CK = "https://dati.comune.milano.it/dataset/"
get(CK + "f9a2a420-d358-46ef-bced-cf2048864d00/resource/1b750768-5f8b-43d2-b67d-7b5aabe83a43/download/ds574-sharing-veicoli-2011-2025.csv", "comune/ds574_1.csv")
get(CK + "cc065002-cd21-4dcb-b84f-bba2fd9e0c86/resource/4c31029c-22c9-49f7-b145-91374feac41c/download/bikemi_stazioni.csv", "comune/ds65_1.csv")
get(CK + "ceda0264-24f3-4869-9a2d-411906f0abab/resource/18b0480e-5e7d-4a7d-902f-30cc76ad4f9f/download/bike_ciclabili.csv", "comune/ds60_itinerari_ciclabili.csv")
get(CK + "ceda0264-24f3-4869-9a2d-411906f0abab/resource/56515ac3-e260-4ebb-bfce-698347f07e1e/download/bike_ciclabili.geojson", "comune/ds60_itinerari_ciclabili.geojson")
H = {"Client-Identifier": "milano-in-dati-snapshot"}
for f in ("gbfs", "system_information", "station_information", "station_status"):
    get("https://gbfs.urbansharing.com/bikemi.com/%s.json" % f, "gbfs/%s.json" % f, H)
MD5 = {"11": "c5cdfc9537f44ab27d489f75bf67636f", "12": "0ae0855aad7bf2987ee928e6ef65fbf6", "13": "cf0f621fda8b30be8f1944a0380a8060", "14": "c29dd3104729c590d373ed46e26aa7ce"}
for y, m in MD5.items():
    get("https://zenodo.org/api/records/1209115/files/%s.csv/content" % y, "zenodo_bikemi/%s.csv" % y, None, m)
if LOG:
    p = os.path.join(B, "raw", "download_log.json")
    old = json.load(open(p)) if os.path.exists(p) else []
    json.dump(old + LOG, open(p, "w"), indent=1)
