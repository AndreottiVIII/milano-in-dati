"""Dal .osm.pbf: POI food&drink marcati come chiusi (disused:/was:/abandoned:/removed: amenity=...) dentro Milano.
Uso: python -I -X utf8 extract_closed.py <file.pbf> <milano-in-dati_abs> <out.json>"""
import sys, os, json
import osmium, shapely
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.prepared import prep
pbf, P, out = sys.argv[1:4]
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
milano = unary_union([shape(f["geometry"]).buffer(0) for f in g["features"]]); pm = prep(milano)
minx, miny, maxx, maxy = milano.bounds
AM = {"restaurant", "fast_food", "cafe", "bar", "pub", "ice_cream", "biergarten", "food_court"}
PREF = ("disused:amenity", "was:amenity", "abandoned:amenity", "removed:amenity", "demolished:amenity")
fp = osmium.FileProcessor(pbf).with_locations()
els = []
for o in fp:
    if not (o.is_node() or o.is_way()):
        continue
    hit = [(k, o.tags[k]) for k in PREF if k in o.tags and o.tags[k] in AM]
    if not hit and not ("disused:shop" in o.tags and False):
        continue
    if o.is_node():
        if not o.location.valid(): continue
        lon, lat = o.location.lon, o.location.lat
    else:
        pts = [(n.lon, n.lat) for n in o.nodes if n.location.valid()]
        if not pts: continue
        lon = sum(p[0] for p in pts) / len(pts); lat = sum(p[1] for p in pts) / len(pts)
    if not (minx <= lon <= maxx and miny <= lat <= maxy) or not pm.contains(shapely.Point(lon, lat)):
        continue
    els.append({"type": "node" if o.is_node() else "way", "id": o.id, "lon": lon, "lat": lat, "timestamp": o.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"), "uid": o.uid,
                "chiave": hit[0][0], "valore": hit[0][1], "name": o.tags.get("name") or o.tags.get("disused:name") or o.tags.get("old_name"), "amenity_attuale": o.tags.get("amenity"), "shop_attuale": o.tags.get("shop"), "tags_n": len(o.tags)})
json.dump(els, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print(len(els), "POI chiusi")
