"""Cerca nel portale CKAN del Comune di Milano i dataset sui nomi. Uso: python -I -X utf8 01_cerca_ckan.py <cartella nomi-bambini>"""
import sys, json, time, os, urllib.request, urllib.parse, re
base = sys.argv[1]
H = {'User-Agent': 'milano-in-dati/1.0 (ricerca open data; polite)'}
def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60))
seen = {}
qs = ['nomi','nome','nati','neonati','nascite','nomi bambini','nomi più diffusi','prenome','cognomi','cognome','nomi residenti','popolazione residente nome','battesimo','nomi proprio','newborn','names','anagrafe nomi','residenti cittadinanza','stranieri']
for q in qs:
    for start in (0, 100, 200):
        j = get('https://dati.comune.milano.it/api/3/action/package_search?' + urllib.parse.urlencode({'q': q, 'rows': 100, 'start': start}))['result']
        for p in j['results']:
            seen[p['name']] = p
        if len(j['results']) < 100: break
        time.sleep(1)
    time.sleep(1)
print(len(seen))
json.dump(seen, open(os.path.join(base, 'raw', 'ckan', 'search_all.json'), 'w'), ensure_ascii=False)
pat = re.compile(r'\bnom[ie]\b|prenom|nati\b|neonat|nascit|cognom', re.I)
for n, p in sorted(seen.items()):
    t = p['title'] + ' ' + (p.get('notes') or '')
    if pat.search(t):
        print(n, '|', p['title'], '|', p.get('license_id'), '|', p['metadata_modified'][:10], '|', len(p['resources']))
