"""Estrae dall'estratto Geofabrik (.osm.pbf) tutti i nodi/way con nome e con tag shop/craft/amenity/office/tourism/leisure
dentro il Comune di Milano (unione poligoni NIL). Per i way: baricentro dei nodi. Le relazioni NON sono lette.
Uso: python -I -X utf8 estrai_osm.py <file.pbf> <milano-in-dati_abs> <out.json>"""
import sys, os, json
import osmium, shapely
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.prepared import prep
pbf, P, out = sys.argv[1:4]
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
milano = unary_union([shape(f["geometry"]).buffer(0) for f in g["features"]])
pm = prep(milano); minx, miny, maxx, maxy = milano.bounds
CH = ("shop", "craft", "amenity", "office", "tourism", "leisure", "healthcare")
fp = osmium.FileProcessor(pbf).with_locations().with_filter(osmium.filter.KeyFilter("name"))
els, seen = [], {"node": 0, "way": 0}
for o in fp:
    if o.is_node(): kind = "node"
    elif o.is_way(): kind = "way"
    else: continue
    t = o.tags
    if not any(k in t for k in CH) and not any(k.startswith(("disused:", "was:", "old_")) for k in (x.k for x in t)):
        continue
    if kind == "node":
        if not o.location.valid(): continue
        lon, lat = o.location.lon, o.location.lat
    else:
        pts = [(n.lon, n.lat) for n in o.nodes if n.location.valid()]
        if not pts: continue
        lon = sum(p[0] for p in pts) / len(pts); lat = sum(p[1] for p in pts) / len(pts)
    if not (minx <= lon <= maxx and miny <= lat <= maxy): continue
    if not pm.contains(shapely.Point(lon, lat)): continue
    seen[kind] += 1
    els.append({"type": kind, "id": o.id, "ts": o.timestamp.strftime("%Y-%m-%d"), "lat": round(lat, 7), "lon": round(lon, 7), "tags": {k.k: k.v for k in t}})
json.dump({"fonte": "Geofabrik " + os.path.basename(pbf) + " (OpenStreetMap, ODbL 1.0)", "elements": els}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print(len(els), "elementi", seen)
