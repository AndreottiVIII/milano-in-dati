import sys, time, requests
out = sys.argv[1]
q = """[out:json][timeout:300];
rel["boundary"="administrative"]["admin_level"="8"]["wikidata"="Q490"];
map_to_area->.a;
(
  way(area.a)["highway"]["name"];
  way(area.a)["place"="square"]["name"];
  relation(area.a)["place"="square"]["name"];
  way(area.a)["highway"="pedestrian"]["name"];
  relation(area.a)["highway"="pedestrian"]["name"];
);
out tags center;
"""
UA = {"User-Agent": "milano-in-dati/0.1 (davide.caniatti@gmail.com; research on street names)"}
for url in ["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]:
    for att in range(3):
        try:
            r = requests.post(url, data={"data": q}, headers=UA, timeout=400)
            print(url, r.status_code, len(r.content))
            if r.status_code == 200:
                open(out, "wb").write(r.content); sys.exit(0)
        except Exception as e:
            print("err", e)
        time.sleep(20)
sys.exit(1)
