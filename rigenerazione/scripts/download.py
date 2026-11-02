"""Scarica i livelli CC BY 4.0 del PGT Milano 2030 (Geoportale del Comune) in raw/pgt/.
Uso: python -I -X utf8 download.py <rigenerazione_dir>
Server pubblico ArcGIS (gisportal.comune.milano.it), nessun login. Un file GeoJSON (WGS84) per livello + log.
Non scarica il servizio "Mappa dei progetti di Rigenerazione urbana" (Atlante): licenza "Copyright Comune di Milano. Solo consultazione autorizzata"."""
import sys, os, json, urllib.request, urllib.parse, datetime, hashlib, time
R = sys.argv[1]
OUT = os.path.join(R, "raw", "pgt"); os.makedirs(OUT, exist_ok=True)
S = "https://gisportal.comune.milano.it/federated/rest/services/PGT/"
LAYERS = [  # (servizio, id livello, nome file)
    ("Milano_2030_PGT_Vigente_Tavola_R02", 10, "r02_provvedimenti_in_itinere"),
    ("Milano_2030_PGT_Vigente_Tavola_R02", 12, "r02_piani_attuativi_obbligatori"),
    ("Milano_2030_PGT_Vigente_Tavola_R02", 21, "r02_ers"),
    ("Milano_2030_PGT_Vigente_Tavola_R02", 6, "r02_grandi_funzioni_urbane"),
    ("Milano_2030_PGT_Vigente_Tavola_R02", 2, "r02_rigenerazione_ambientale"),
    ("Milano_2030_PGT_Vigente_Tavola_R02", 4, "r02_nodi_interscambio"),
    ("Milano_2030_PGT_Vigente_Tavola_R10", 3, "r10_rigenerazione"),
]
def get(u):
    for k in range(4):
        try: return urllib.request.urlopen(u, timeout=60).read()
        except Exception as e:
            print("retry", k, e); time.sleep(3)
    raise SystemExit("fallito " + u)
log = open(os.path.join(OUT, "download_log.csv"), "a", encoding="utf-8")
for srv, lid, name in LAYERS:
    base = f"{S}{srv}/MapServer/{lid}"
    meta = json.loads(get(base + "?f=json"))
    json.dump(meta, open(os.path.join(OUT, name + "_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = json.loads(get(base + "/query?where=1%3D1&returnCountOnly=true&f=json"))["count"]
    feats = []; off = 0
    while off < n:
        q = urllib.parse.urlencode({"where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson", "resultOffset": off, "resultRecordCount": 500, "orderByFields": "objectid"})
        d = json.loads(get(base + "/query?" + q)); feats += d["features"]; off += 500
        if not d["features"]: break
    assert len(feats) == n, (name, len(feats), n)
    dst = os.path.join(OUT, name + ".geojson")
    json.dump({"type": "FeatureCollection", "features": feats}, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
    h = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
    log.write(f"{datetime.date.today()};{srv};{lid};{name};{n};{os.path.getsize(dst)};{h};CC-BY 4.0 (descrizione del servizio)\n"); log.flush()
    print(name, n, os.path.getsize(dst))
