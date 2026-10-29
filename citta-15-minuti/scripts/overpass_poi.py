"""Una sola query Overpass: servizi OSM nel rettangolo Milano + ~2 km (per bordo e per le poste).
Uso: python -I overpass_poi.py <out.json>"""
import requests,sys,time,json
bb='45.36,9.00,45.56,9.32'
q=f"""[out:json][timeout:300];
(
nwr["amenity"~"^(post_office|pharmacy|doctors|school|kindergarten|childcare|library|marketplace)$"]({bb});
nwr["shop"~"^(chemist|supermarket|convenience|greengrocer|bakery|butcher)$"]({bb});
nwr["leisure"~"^(park|garden|pitch|sports_centre|swimming_pool)$"]({bb});
nwr["amenity"="post_box"]["operator"~"Poste"]({bb});
);
out center tags;"""
H={'User-Agent':'milano-in-dati/1.0 (ricerca open data)'}
for url in ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']:
    for t in range(3):
        try:
            r=requests.post(url,data={'data':q},headers=H,timeout=400)
            print(url,r.status_code,len(r.content),flush=True)
            if r.status_code==200:
                open(sys.argv[1],'wb').write(r.content); sys.exit(0)
        except Exception as e: print('err',str(e)[:100],flush=True)
        time.sleep(30*(t+1))
sys.exit(1)
