"""Scarica da Eurostat (API di diffusione SDMX 2.1, senza registrazione) le tabelle intere in TSV compresso.
Uso, dalla cartella del progetto:  python -I -X utf8 economia/scripts/01_scarica.py"""
import os, urllib.request
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'raw')
os.makedirs(R, exist_ok=True)
URL = 'https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/%s?format=TSV&compressed=true'
for t in ('nama_10r_3gdp', 'nama_10r_3popgdp', 'nama_10r_3empers', 'nama_10r_3gva', 'met_10r_3gdp'):
    dest = os.path.join(R, t + '.tsv.gz')
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print('già presente', t); continue
    req = urllib.request.Request(URL % t, headers={'User-Agent': 'milano-in-dati (dati aperti)'})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, 'wb') as f:
        f.write(r.read())
    print('scaricata', t, os.path.getsize(dest))
