"""Targhe in OpenStreetMap dentro il Comune di Milano (relazione admin_level 8, wikidata=Q490).
Uso: python -I -X utf8 02_overpass.py <file di uscita assoluto>"""
import sys, urllib.request, urllib.parse, json, time
q = """[out:json][timeout:120];
area["boundary"="administrative"]["admin_level"="8"]["wikidata"="Q490"]->.a;
(nwr(area.a)["memorial"="plaque"];
 nwr(area.a)["memorial:type"="plaque"];
 nwr(area.a)["historic"="memorial"]["memorial"~"plaque|tablet"];
 nwr(area.a)["tourism"="artwork"]["artwork_type"="plaque"];
 nwr(area.a)["plaque"];
 nwr(area.a)["inscription"]["historic"];
);
out center tags;"""
req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=urllib.parse.urlencode({"data": q}).encode(),
      headers={"User-Agent": "milano-in-dati research (milano-in-dati)"})
d = json.load(urllib.request.urlopen(req, timeout=180))
open(sys.argv[1], "w", encoding="utf8").write(json.dumps(d, ensure_ascii=False))
print(len(d["elements"]), d.get("osm3s", {}).get("timestamp_osm_base"))
