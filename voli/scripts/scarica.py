"""Scarica i dati grezzi per la pagina «Dove si vola da Milano» in voli/grezzi/.
Uso: python -I -X utf8 voli/scripts/scarica.py
- Eurostat avia_par_it (rotte tra aeroporti): annuale e mensile, passeggeri trasportati (PAS_CRD). CC BY 4.0.
- OurAirports (coordinate degli aeroporti): pubblico dominio.
- Natural Earth 1:50m (confini degli stati): pubblico dominio.
User-Agent «milano-in-dati/1.0», nessuna registrazione. I file grezzi non vanno nel repository."""
import os, sys, time, urllib.request
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'grezzi'); os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'milano-in-dati/1.0'}
B = ('https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/avia_par_it'
     '?format=JSON&lang=EN&unit=PAS&tra_meas=PAS_CRD')
def prendi(url, nome):
    p = os.path.join(OUT, nome)
    if os.path.exists(p) and os.path.getsize(p) > 1000:
        print('già presente', nome); return
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r: d = r.read()
    open(p, 'wb').write(d); print('scaricato', nome, len(d)); time.sleep(1)
prendi(B + '&freq=A', 'eurostat_A.json')
for y in range(2002, 2025):
    prendi('%s&freq=M&sinceTimePeriod=%d-01&untilTimePeriod=%d-12' % (B, y, y), 'eurostat_M%d.json' % y)
prendi('https://davidmegginson.github.io/ourairports-data/airports.csv', 'airports.csv')
prendi('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson', 'ne50.geojson')
