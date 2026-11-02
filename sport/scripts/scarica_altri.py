"""Sport: ricerca catalogo Regione Lombardia (Socrata) e query Overpass OSM. Uso: python -I -X utf8 scarica_altri.py <ABS sport>  (riprendibile)"""
import requests, sys, os, time, json
S = sys.argv[1]
H = {'User-Agent': 'milano-in-dati/1.0 (ricerca open data; davide.caniatti)'}
os.makedirs(S + '/raw/regione', exist_ok=True); os.makedirs(S + '/raw/osm', exist_ok=True)
fn = S + '/raw/regione/catalogo_ricerca.json'
if not os.path.exists(fn):
    out = {}
    for q in ['impianti sportivi', 'impianto sportivo', 'sport', 'piscine', 'palestre', 'censimento impianti', 'CONI', 'sport e salute']:
        r = requests.get('https://api.us.socrata.com/api/catalog/v1', params={'domains': 'www.dati.lombardia.it', 'q': q, 'limit': 50}, headers=H, timeout=120)
        out[q] = [(x['resource']['id'], x['resource']['name'], x['resource'].get('updatedAt'), (x['resource'].get('description') or '')[:200]) for x in r.json().get('results', [])] if r.status_code == 200 else r.status_code
        print(q, len(out[q]) if isinstance(out[q], list) else out[q], flush=True)
    json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
bb = '45.36,9.00,45.56,9.32'
Q = f"""[out:json][timeout:300];
(
nwr["leisure"~"^(sports_centre|pitch|swimming_pool|fitness_centre|stadium|track|sports_hall|ice_rink|golf_course|horse_riding|dance)$"]({bb});
nwr["sport"]["leisure"!~"."]["amenity"!~"."]({bb});
nwr["building"="sports_hall"]({bb});
nwr["amenity"="gym"]({bb});
);
out center tags;"""
fn = S + '/raw/osm/overpass_sport_milano.json'
if not os.path.exists(fn):
    for url in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']:
        done = False
        for t in range(3):
            try:
                r = requests.post(url, data={'data': Q}, headers=H, timeout=400); print(url, r.status_code, len(r.content), flush=True)
                if r.status_code == 200:
                    open(fn, 'wb').write(r.content); done = True
                    print(time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()), file=open(S + '/raw/osm/overpass_sport_data.txt', 'w')); break
            except Exception as e: print('err', str(e)[:100], flush=True)
            time.sleep(30 * (t + 1))
        if done: break
