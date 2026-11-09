"""Una sola richiesta a Overpass (OpenStreetMap, ODbL): ospedali e pronto soccorso nel rettangolo di Milano."""
import subprocess, pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent / "dati_grezzi" / "osm_ospedali_milano.json"
Q = """[out:json][timeout:90];
(
 nwr["amenity"="hospital"](45.36,9.00,45.56,9.32);
 nwr["emergency"="yes"](45.36,9.00,45.56,9.32);
 nwr["healthcare"="hospital"](45.36,9.00,45.56,9.32);
 nwr["name"~"pronto soccorso",i](45.36,9.00,45.56,9.32);
);
out center tags;"""
import time
for tent in range(5):
    for ep in ("https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"):
        r = subprocess.run(["curl","-sS","--fail","-A","milano-in-dati/1.0","--data-urlencode","data="+Q,ep,"-o",str(OUT)])
        if r.returncode == 0:
            print(ep, OUT.stat().st_size); raise SystemExit
        time.sleep(15)
raise SystemExit("Overpass non risponde")
