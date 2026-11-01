"""Scarica da Overpass i POI food&drink dentro il Comune di Milano (relazione OSM 44915) con meta (timestamp ultima modifica).
Uso: python -I -X utf8 download_osm.py <raw_dir>   (una sola richiesta, user agent identificato, pausa gentile)"""
import sys, os, json, urllib.request, urllib.parse, time
raw = sys.argv[1]
Q = """[out:json][timeout:300];
rel(44915);map_to_area->.a;
nwr["amenity"~"^(restaurant|fast_food|cafe|bar|pub|ice_cream|biergarten|food_court)$"](area.a);
out meta center;"""
EPS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
for ep in EPS:
    try:
        req = urllib.request.Request(ep, data=urllib.parse.urlencode({"data": Q}).encode(), headers={"User-Agent": "milano-in-dati-research/1.0 (davide.caniatti@gmail.com)"})
        t0 = time.time()
        b = urllib.request.urlopen(req, timeout=290).read()
        d = json.loads(b)
        print(ep, "ok", len(d["elements"]), "elementi", round(time.time() - t0), "s;", d.get("osm3s", {}).get("timestamp_osm_base"))
        open(os.path.join(raw, "osm_milano_food_overpass.json"), "wb").write(b)
        break
    except Exception as e:
        print(ep, "errore", e); time.sleep(10)
