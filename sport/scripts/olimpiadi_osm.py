"""Sport: coordinate delle sedi olimpiche 2026 dell'area di Milano, da OSM (Overpass, per nome). Uso: python -I -X utf8 olimpiadi_osm.py <out.json>"""
import requests, sys, time, json
H = {'User-Agent': 'milano-in-dati/1.0'}
Q = """[out:json][timeout:120];
(
nwr["name"~"Giuseppe Meazza|San Siro",i]["leisure"="stadium"](45.3,8.9,45.6,9.4);
nwr["name"~"PalaItalia|Santa Giulia|Arena Milano",i]["leisure"~"stadium|sports_centre|pitch"](45.3,8.9,45.6,9.4);
nwr["name"~"Forum|Unipol|Mediolanum",i]["leisure"~"sports_centre|stadium"](45.3,8.9,45.6,9.4);
nwr["name"~"Olimpic|Olympic",i]["building"](45.4,9.1,45.5,9.3);
nwr["name"~"Ice Hockey Arena|Speed Skating|Milano Ice Park|Fiera Milano",i]["leisure"~"ice_rink|sports_centre|stadium"](45.3,8.9,45.6,9.4);
nwr["leisure"="ice_rink"](45.3,8.9,45.6,9.4);
);
out center tags;"""
for url in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']:
    r = requests.post(url, data={'data': Q}, headers=H, timeout=200); print(url, r.status_code, len(r.content))
    if r.status_code == 200:
        open(sys.argv[1], 'wb').write(r.content); break
    time.sleep(20)
# villaggio olimpico di Porta Romana (per nome)
Q2 = '[out:json][timeout:60];nwr["name"~"Olimpic|Olympic|Scalo Romana|Scalo di Porta Romana|Villaggio",i](45.42,9.18,45.46,9.23);out center tags;'
r = requests.post('https://overpass-api.de/api/interpreter', data={'data': Q2}, headers=H, timeout=100); print(r.status_code, len(r.content))
if r.status_code == 200: open(sys.argv[1].replace('.json', '_villaggio.json'), 'wb').write(r.content)
