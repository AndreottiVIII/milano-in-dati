"""Scarica i CSV dei dataset di nomi trovati su dati.lombardia.it (Socrata). Uso: python -I -X utf8 03_scarica_lombardia.py <cartella nomi-bambini>"""
import sys, os, time, urllib.request, datetime, hashlib, json
base = sys.argv[1]
out = os.path.join(base, 'raw', 'lombardia'); os.makedirs(out, exist_ok=True)
H = {'User-Agent': 'milano-in-dati/1.0 (ricerca open data; polite)'}
D = {'bergamo_nomi_residenti_s29g-dr7j': 's29g-dr7j', 'bergamo_nomi_neonati_7nxs-kdhf': '7nxs-kdhf',
     'cremona_graduatoria_rnp5-bkha': 'rnp5-bkha', 'brescia_eta_2018_4w2s-n4fk': '4w2s-n4fk',
     'rozzano_maschili_aqb5-z3e6': 'aqb5-z3e6', 'rozzano_femminili_ht8t-tug7': 'ht8t-tug7'}
log = []
for name, vid in D.items():
    for kind, url in (('csv', f'https://www.dati.lombardia.it/api/views/{vid}/rows.csv?accessType=DOWNLOAD'),
                      ('meta', f'https://www.dati.lombardia.it/api/views/{vid}.json')):
        fn = os.path.join(out, f'{name}.{"csv" if kind=="csv" else "meta.json"}')
        if os.path.exists(fn): continue
        data = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=120).read()
        open(fn, 'wb').write(data)
        log.append((datetime.date.today().isoformat(), url, fn, len(data), hashlib.sha256(data).hexdigest()[:12]))
        print(log[-1]); time.sleep(2)
with open(os.path.join(base, 'raw', 'download_log.csv'), 'a', encoding='utf8') as f:
    for r in log: f.write(','.join(map(str, r)) + '\n')
