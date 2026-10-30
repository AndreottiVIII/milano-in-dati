"""Fase 4 (servizi extra): scarica i dati extra. Uso: python -I f4_scarica.py <ABS strand>   (riprendibile: salta i file presenti)
Comune CKAN (aree gioco, aree cani, centri balneari/piscine, posti letto ospedali, Milano Musei Card), Regione Lombardia Socrata
(georeferenziazione strutture di ricovero, 6n7g-5p5e) e una query Overpass (teatri, musei, ospedali, parchi gioco, aree cani, piscine)."""
import requests, sys, os, time, json
S = sys.argv[1]
H = {'User-Agent': 'milano-in-dati/1.0 (ricerca open data; davide.caniatti)'}
API = 'https://dati.comune.milano.it/api/3/action/package_show'
DS = [('aree_gioco', 'ds724_infogeo_aree_gioco_localizzazione', ['CSV', 'GeoJSON']),
      ('aree_cani', 'ds52_infogeo_aree_cani_localizzazione', ['CSV', 'GeoJSON']),
      ('centri_balneari', 'ds32-infogeo-centri-balneari-localizzazione', ['CSV', 'GeoJSON']),
      ('ospedali_posti_letto', 'ds683-sanita-posti-letto-delle-strutture-ospedaliere-e-case-di-cura-2010-avanti', ['CSV', 'GeoJSON']),
      ('musei_card', 'ds2727-cultura-milano-musei-card', ['CSV', 'GeoJSON'])]
def get(url, **kw):
    for t in range(5):
        try:
            r = requests.get(url, headers=H, timeout=180, **kw)
            if r.status_code == 200: return r
            print('  HTTP', r.status_code, url[:90], flush=True)
        except Exception as e: print('  err', str(e)[:100], flush=True)
        time.sleep(10 * (t + 1))
for cart, pid, fmts in DS:
    d = S + '/raw/extra_comune/' + cart; os.makedirs(d, exist_ok=True)
    r = get(API, params={'id': pid}); p = r.json()['result']
    json.dump(p, open(d + '/_metadati.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for res in p['resources']:
        if res['format'] in fmts:
            fn = d + '/' + res['url'].split('/')[-1]
            if os.path.exists(fn): continue
            rr = get(res['url'])
            if rr: open(fn, 'wb').write(rr.content); print(cart, res['format'], len(rr.content), flush=True)
            time.sleep(2)
# Regione Lombardia (Socrata): georeferenziazione strutture di ricovero
d = S + '/raw/extra_regione'; os.makedirs(d, exist_ok=True)
fn = d + '/6n7g-5p5e_georeferenziazione_strutture.csv'
if not os.path.exists(fn):
    rr = get('https://www.dati.lombardia.it/resource/6n7g-5p5e.csv', params={'$limit': 5000})
    if rr: open(fn, 'wb').write(rr.content); print('regione', len(rr.content))
for u in ['https://www.dati.lombardia.it/api/views/6n7g-5p5e.json']:
    fn = d + '/6n7g-5p5e_metadati.json'
    if not os.path.exists(fn):
        rr = get(u)
        if rr: open(fn, 'wb').write(rr.content)
# Overpass
bb = '45.36,9.00,45.56,9.32'
q = f"""[out:json][timeout:300];
(
nwr["amenity"~"^(theatre|hospital|clinic|doctors|community_centre)$"]["amenity"!="doctors"]["amenity"!="community_centre"]({bb});
nwr["healthcare"~"^(hospital|centre)$"]["amenity"!~"."]({bb});
nwr["tourism"="museum"]({bb});
nwr["leisure"~"^(playground|dog_park|swimming_pool|sports_centre|water_park)$"]({bb});
nwr["emergency"="yes"]["amenity"~"hospital|clinic"]({bb});
nwr["shop"="supermarket"]({bb});
);
out center tags;"""
fn = S + '/raw/osm_extra/overpass_extra_milano.json'
if not os.path.exists(fn):
    for url in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']:
        done = False
        for t in range(3):
            try:
                r = requests.post(url, data={'data': q}, headers=H, timeout=400); print(url, r.status_code, len(r.content), flush=True)
                if r.status_code == 200: open(fn, 'wb').write(r.content); done = True; break
            except Exception as e: print('err', str(e)[:100], flush=True)
            time.sleep(30 * (t + 1))
        if done: break
# Librerie (aggiunte dopo): shop=books (anche usate)
fn = S + '/raw/osm_extra/overpass_librerie_milano.json'
if not os.path.exists(fn):
    q2 = f'[out:json][timeout:300];\n(\nnwr["shop"="books"]({bb});\nnwr["shop"="stationery"]["books"]({bb});\n);\nout center tags;'
    for url in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']:
        done = False
        for t in range(3):
            try:
                r = requests.post(url, data={'data': q2}, headers=H, timeout=400); print(url, r.status_code, len(r.content), flush=True)
                if r.status_code == 200: open(fn, 'wb').write(r.content); done = True; break
            except Exception as e: print('err', str(e)[:100], flush=True)
            time.sleep(30 * (t + 1))
        if done: break
