"""Fase 2, passo 4: una richiesta Overpass per l'area del Comune di Milano con la geometria (out geom) delle sole strade 'core'
(residential, tertiary, secondary, primary, unclassified, living_street, pedestrian, trunk) e delle piazze con nome.
Primo tentativo (tutte le highway con nome, via+map_to_area) respinto dal server con 502/504: qui area diretta e solo i tipi dell'universo.
Uso: python -I 14_overpass_geom.py out.json"""
import sys, time, requests
out = sys.argv[1]
q = """[out:json][timeout:600][maxsize:1073741824];
area["boundary"="administrative"]["admin_level"="8"]["wikidata"="Q490"]->.a;
(
  way(area.a)["highway"~"^(residential|tertiary|secondary|primary|unclassified|living_street|pedestrian|trunk)$"]["name"];
  way(area.a)["place"="square"]["name"];
  relation(area.a)["place"="square"]["name"];
  relation(area.a)["highway"="pedestrian"]["name"];
);
out geom qt;
"""
UA = {"User-Agent": "milano-in-dati/0.2 (davide.caniatti@gmail.com; research on street names)"}
for url in ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]:
    for att in range(2):
        try:
            r = requests.post(url, data={"data": q}, headers=UA, timeout=700)
            print(url, r.status_code, len(r.content), flush=True)
            if r.status_code == 200 and r.content[:1] == b'{':
                open(out, "wb").write(r.content); sys.exit(0)
        except Exception as e:
            print("err", e, flush=True)
        time.sleep(30)
sys.exit(1)
