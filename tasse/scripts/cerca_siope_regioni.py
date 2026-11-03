"""Cerca nel catalogo BDAP (CKAN) i dataset SIOPE entrate per regione e anno. Scrive un CSV regione;anno;id."""
import sys, json, urllib.request, urllib.parse, time, re
UA = {'User-Agent': 'milano-in-dati/1.0'}
B = 'https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/action/'
out = sys.argv[1]
res = {}
for reg in ['Lazio', 'Piemonte', 'Campania', 'Emilia-Romagna', 'Toscana', 'Liguria']:
    for tent in range(4):
        try:
            u = B + 'package_search?' + urllib.parse.urlencode({'q': reg, 'rows': 100})
            j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=100))
            for p in j['result']['results']:
                m = re.match(r'(\d{4}) - (.+?) - SIOPE Movimenti cumulati mensili di Entrata', p['title'])
                if m and m.group(2) == reg:
                    res[(reg, m.group(1))] = p['id']
            print(reg, len(j['result']['results']), flush=True)
            break
        except Exception as e:
            print('err', reg, e, flush=True); time.sleep(10)
    time.sleep(2)
open(out, 'w', encoding='utf-8').write('\n'.join(f'{k[0]};{k[1]};{v}' for k, v in sorted(res.items())) + '\n')
for k in sorted(res): print(k)
