"""Scarica il catalogo completo (metadati) del portale CKAN di Milano. Uso: python -I -X utf8 02_catalogo_completo.py <cartella nomi-bambini>"""
import sys, json, time, os, urllib.request
base = sys.argv[1]
H = {'User-Agent': 'milano-in-dati/1.0 (ricerca open data; polite)'}
allp = []
start = 0
while True:
    u = f'https://dati.comune.milano.it/api/3/action/package_search?rows=100&start={start}&sort=name+asc'
    j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=90))['result']
    allp += j['results']
    start += 100
    if start >= j['count'] or not j['results']: break
    time.sleep(1)
print(len(allp), 'pacchetti, count', j['count'])
json.dump(allp, open(os.path.join(base, 'raw', 'ckan', 'catalogo_completo.json'), 'w', encoding='utf8'), ensure_ascii=False)
