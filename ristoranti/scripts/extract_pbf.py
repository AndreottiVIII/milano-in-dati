"""Estrae da un estratto Geofabrik (.osm.pbf) i POI food&drink dentro il Comune di Milano (unione dei poligoni NIL).
Scrive un JSON con la stessa forma di Overpass (elements con meta), cosi' freshness.py non cambia.
Uso: python -I -X utf8 extract_pbf.py <file.pbf> <milano-in-dati_abs> <out.json>
Limite: le relazioni (multipoligoni) non sono lette; i poligoni (way chiusi) sono ridotti al baricentro dei nodi."""
import sys, os, json
import osmium
import shapely
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.prepared import prep

pbf, P, out = sys.argv[1:4]
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
milano = unary_union([shape(f["geometry"]).buffer(0) for f in g["features"]])
pm = prep(milano)
minx, miny, maxx, maxy = milano.bounds
AM = ("restaurant", "fast_food", "cafe", "bar", "pub", "ice_cream", "biergarten", "food_court")
fp = osmium.FileProcessor(pbf).with_locations().with_filter(osmium.filter.KeyFilter("amenity"))
els, seen = [], {"node": 0, "way": 0}
for o in fp:
    if o.is_node():
        kind = "node"
    elif o.is_way():
        kind = "way"
    else:
        continue
    am = o.tags.get("amenity")
    if am not in AM:
        continue
    if kind == "node":
        if not o.location.valid():
            continue
        lon, lat = o.location.lon, o.location.lat
    else:
        pts = [(n.lon, n.lat) for n in o.nodes if n.location.valid()]
        if not pts:
            continue
        lon = sum(p[0] for p in pts) / len(pts)
        lat = sum(p[1] for p in pts) / len(pts)
    if not (minx <= lon <= maxx and miny <= lat <= maxy):
        continue
    if not pm.contains(shapely.Point(lon, lat)):
        continue
    seen[kind] += 1
    e = {"type": kind, "id": o.id, "timestamp": o.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"), "version": o.version, "changeset": o.changeset, "uid": o.uid,
         "tags": {t.k: t.v for t in o.tags}}
    if kind == "node":
        e["lat"], e["lon"] = lat, lon
    else:
        e["center"] = {"lat": lat, "lon": lon}
    els.append(e)
json.dump({"osm3s": {"timestamp_osm_base": "Geofabrik " + os.path.basename(pbf)}, "elements": els}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print(len(els), "elementi", seen)
