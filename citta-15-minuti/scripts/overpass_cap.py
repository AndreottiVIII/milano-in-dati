"""Overpass: confini CAP (boundary=postal_code) dentro il rettangolo di Milano, come geometria. Uso: python -I overpass_cap.py <out.json>"""
import requests,sys,time
q="""[out:json][timeout:300];
rel["boundary"="postal_code"](45.36,9.00,45.56,9.32);
out geom;"""
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
