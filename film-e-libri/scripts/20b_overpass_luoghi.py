"""Scarica da Overpass (una sola richiesta, cache) i luoghi con nome dentro il Comune di Milano:
teatri, stazioni, musei, chiese, ospedali, universita, stadi, monumenti, parchi, quartieri...
Il file OSM della striscia 7 contiene solo le strade, quindi qui si usa l'API Overpass.
Uso: python -I 20b_overpass_luoghi.py <cartella_strand>"""
import sys, os, json, time, requests
base = sys.argv[1]
out = os.path.join(base, "raw", "osm"); os.makedirs(out, exist_ok=True)
fn = os.path.join(out, "overpass_luoghi_milano.json")
if os.path.exists(fn): print("gia presente"); sys.exit()
Q = """[out:json][timeout:180];
area["name"="Milano"]["boundary"="administrative"]["admin_level"="8"]->.a;
(
 nwr(area.a)["name"]["railway"~"^(station|halt)$"];
 nwr(area.a)["name"]["amenity"~"^(theatre|cinema|university|college|hospital|courthouse|prison|townhall|library|arts_centre|place_of_worship|marketplace)$"];
 nwr(area.a)["name"]["tourism"~"^(museum|attraction|gallery|hotel)$"];
 nwr(area.a)["name"]["leisure"~"^(stadium|park|garden)$"];
 nwr(area.a)["name"]["historic"];
 nwr(area.a)["name"]["man_made"="tower"];
 nwr(area.a)["name"]["building"~"^(cathedral|church|chapel|castle|palace|train_station|stadium|theatre|hospital|university)$"];
 nwr(area.a)["name"]["place"~"^(suburb|quarter|neighbourhood)$"];
 nwr(area.a)["name"]["wikidata"]["building"];
);
out center tags;"""
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
for ep in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
    for t in range(3):
        try:
            r = requests.post(ep, data={"data": Q}, headers=UA, timeout=240)
            if r.status_code in (429, 502, 503, 504): print(ep, r.status_code); time.sleep(40*(t+1)); continue
            r.raise_for_status()
            open(fn, "w", encoding="utf8").write(r.text)
            print("ok", len(r.json()["elements"]), "elementi"); sys.exit()
        except requests.RequestException as e:
            print(ep, e); time.sleep(30)
print("FALLITA")
