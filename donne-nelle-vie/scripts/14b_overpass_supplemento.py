"""Fase 2, passo 4 (supplemento): poche strade di donne non hanno 'way' tra i tipi scaricati (sono solo 'service' o 'footway' in OSM, o hanno un nome OSM diverso).
Una sola richiesta piccola per nome (qualsiasi tipo di highway). Uso: python -I 14b_overpass_supplemento.py out.json regex_nomi"""
import sys, time, requests
out, rx = sys.argv[1:3]
q = f"""[out:json][timeout:120];
area["boundary"="administrative"]["admin_level"="8"]["wikidata"="Q490"]->.a;
way(area.a)["highway"]["name"~"{rx}",i];
out geom;
"""
UA = {"User-Agent": "milano-in-dati/0.2 (davide.caniatti@gmail.com; research on street names)"}
for url in ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]:
    for att in range(3):
        try:
            r = requests.post(url, data={"data": q}, headers=UA, timeout=200)
            print(url, r.status_code, len(r.content), flush=True)
            if r.status_code == 200 and r.content[:1] == b'{':
                open(out, "wb").write(r.content); sys.exit(0)
        except Exception as e:
            print("err", e, flush=True)
        time.sleep(30)
sys.exit(1)
