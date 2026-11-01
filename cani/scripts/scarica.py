"""Scarica ds52 aree cani (Comune di Milano) + metadati CKAN + OSM dog_park (Overpass).
Uso: python -I -X utf8 scarica.py <cartella raw assoluta>"""
import sys, os, json, urllib.request, urllib.parse, hashlib, datetime, time
raw = sys.argv[1]
UA = {"User-Agent": "milano-in-dati/1.0 (ricerca open data, uso personale)"}
log = []
def fetch(url, dest, data=None):
    req = urllib.request.Request(url, headers=UA, data=data)
    b = urllib.request.urlopen(req, timeout=180).read()
    open(dest, "wb").write(b)
    log.append((datetime.datetime.now().isoformat(timespec="seconds"), url, dest, len(b), hashlib.sha256(b).hexdigest()))
    print(dest, len(b))
d = os.path.join(raw, "comune_ds52"); os.makedirs(d, exist_ok=True)
fetch("https://dati.comune.milano.it/api/3/action/package_show?id=ds52_infogeo_aree_cani_localizzazione", os.path.join(d, "package_show.json"))
pk = json.load(open(os.path.join(d, "package_show.json"), encoding="utf-8"))["result"]
for r in pk["resources"]:
    fn = r["url"].rsplit("/", 1)[1]
    fetch(r["url"], os.path.join(d, fn))
time.sleep(2)
# OSM: aree cani nel rettangolo di Milano (stesso rettangolo del filone 9). Overpass e' spesso instabile: 3 tentativi per due server.
q = '[out:json][timeout:120];(nwr["leisure"="dog_park"](45.36,9.00,45.56,9.32););out center tags;'
ok = False
for srv in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    for t in range(3):
        try:
            fetch(srv, os.path.join(raw, "osm", "dog_park.json"), data=urllib.parse.urlencode({"data": q}).encode()); ok = True; break
        except Exception as ex:
            print("overpass", srv, t, ex); time.sleep(15)
    if ok: break
with open(os.path.join(raw, "download_log.csv"), "a", encoding="utf-8") as f:
    for l in log: f.write(";".join(map(str, l)) + "\n")
