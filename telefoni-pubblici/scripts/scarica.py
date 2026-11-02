"""Scarica i dati grezzi per la pagina sui telefoni pubblici di Milano.
Uso: python -I -X utf8 scarica.py <cartella raw assoluta> [<file POSAS_2026_it_Comuni.zip gia' scaricato>]
Scrive nella cartella raw (non tracciata da git, perche' l'elenco TIM non si puo' ripubblicare):
  tim_cabine.json     elenco TIM (file pubblico caricato dalla pagina tim.it/assistenza/trova-telefono)
  osm_telefoni.json   OpenStreetMap, amenity=telephone dentro il Comune di Milano (Overpass)
  POSAS_2026_it_Comuni.zip   ISTAT, popolazione residente al 1 gennaio 2026 (stima)
  scarico.json        date e dimensioni dei file scaricati
Se una fonte rifiuta la richiesta il programma si ferma e lo scrive: non si insiste e non si aggira."""
import sys, os, json, shutil, hashlib, datetime, urllib.request, urllib.parse, urllib.error

UA = "milano-in-dati/1.0"
TIM = "https://www.tim.it/content/dam/flytoco-areapubblica-aemfe/tim_it/json/trova-telefono/cabine01072026.json"
OVERPASS = "https://overpass-api.de/api/interpreter"
ISTAT = "https://demo.istat.it/data/posas/POSAS_2026_it_Comuni.zip"
Q = """[out:json][timeout:120];
area["boundary"="administrative"]["admin_level"="8"]["wikidata"="Q490"]->.a;
nwr(area.a)["amenity"="telephone"];
out center tags;"""

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=180).read()

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    raw = sys.argv[1]
    os.makedirs(raw, exist_ok=True)
    oggi = datetime.date.today().isoformat()
    log = {}
    try:
        b = get(TIM)
        json.loads(b.decode("utf-8-sig"))  # controlla che sia JSON
        open(os.path.join(raw, "tim_cabine.json"), "wb").write(b)
        log["tim"] = dict(url=TIM, data_scarico=oggi, byte=len(b), sha256=sha(b))
        print("TIM ok", len(b))
    except Exception as e:
        print("TIM RIFIUTATO O ERRORE:", e); sys.exit(1)
    try:
        b = get(OVERPASS, urllib.parse.urlencode({"data": Q}).encode())
        d = json.loads(b)
        open(os.path.join(raw, "osm_telefoni.json"), "wb").write(b)
        log["osm"] = dict(url=OVERPASS, query=Q, data_scarico=oggi, byte=len(b), elementi=len(d["elements"]),
                          timestamp_osm_base=d.get("osm3s", {}).get("timestamp_osm_base"))
        print("OSM ok", len(d["elements"]), log["osm"]["timestamp_osm_base"])
    except Exception as e:
        print("OSM RIFIUTATO O ERRORE:", e); sys.exit(1)
    dst = os.path.join(raw, "POSAS_2026_it_Comuni.zip")
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        shutil.copyfile(sys.argv[2], dst)
        log["istat"] = dict(url=ISTAT, copiato_da="file gia' scaricato il 2026-11-01", byte=os.path.getsize(dst))
    else:
        try:
            b = get(ISTAT); open(dst, "wb").write(b)
            log["istat"] = dict(url=ISTAT, data_scarico=oggi, byte=len(b))
        except Exception as e:
            print("ISTAT RIFIUTATO O ERRORE:", e); sys.exit(1)
    print("ISTAT ok", os.path.getsize(dst))
    json.dump(log, open(os.path.join(raw, "scarico.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

main()
