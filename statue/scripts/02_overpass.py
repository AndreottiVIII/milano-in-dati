"""OSM (ODbL): memoriali, monumenti, opere d'arte pubbliche nel Comune di Milano. Uso: python -I -X utf8 02_overpass.py <out.json>"""
import sys, time, requests
out = sys.argv[1]
q = """[out:json][timeout:300];
rel["boundary"="administrative"]["admin_level"="8"]["wikidata"="Q490"];
map_to_area->.a;
(
  nwr(area.a)["historic"~"^(memorial|monument)$"];
  nwr(area.a)["memorial"];
  nwr(area.a)["tourism"="artwork"];
  nwr(area.a)["historic"="wayside_cross"];
);
out tags center;
"""
UA = {"User-Agent": "milano-in-dati/0.3 (davide.caniatti@gmail.com; research on statues and monuments)"}
for url in ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    for att in range(4):
        try:
            r = requests.post(url, data={"data": q}, headers=UA, timeout=400)
            print(url, r.status_code, len(r.content))
            if r.status_code == 200 and b'"elements"' in r.content[:2000] + r.content[-2000:] or (r.status_code == 200 and len(r.content) > 1000):
                open(out, "wb").write(r.content); sys.exit(0)
        except Exception as e:
            print("err", e)
        time.sleep(30)
sys.exit(1)
