"""Scarica da OpenStreetMap (Overpass) i poligoni leisure=park|garden|playground|dog_park del rettangolo di Milano. Solo per controllo (ODbL).
Uso: python -I -X utf8 osm_parchi.py <raw_dir>   Scrive raw/osm/overpass_verde_milano.json e osm/LOG.txt (data, endpoint, byte)."""
import sys, os, urllib.request, urllib.parse, datetime, time
raw = os.path.join(sys.argv[1], "osm"); os.makedirs(raw, exist_ok=True)
q = """[out:json][timeout:180];
(way["leisure"~"^(park|garden|playground|dog_park)$"](45.36,9.00,45.56,9.32);
 relation["leisure"~"^(park|garden|playground|dog_park)$"](45.36,9.00,45.56,9.32););
out geom tags;"""
fn = os.path.join(raw, "overpass_verde_milano.json")
if not os.path.exists(fn):
    for url in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "milano-in-dati/1.0 (ricerca open data)"})
            b = urllib.request.urlopen(req, timeout=240).read()
            open(fn, "wb").write(b)
            open(os.path.join(raw, "LOG.txt"), "a").write(f"{datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat()}Z {url} {len(b)} byte\n")
            break
        except Exception as e:
            print("errore", url, e); time.sleep(5)
print(os.path.exists(fn) and os.path.getsize(fn))
