"""Consumi di elettricita per settore e provincia dal centro download di Terna (dati.terna.it), 2000-2024.
Somma le voci di ogni anno: fino al 2020 Terna le divide in molte righe. Scrive solo i totali di Milano, Monza e Italia.
Uso: python -I -X utf8 scarica_terna.py <radice del progetto>"""
import collections, csv, json, os, sys, time, urllib.request

R = sys.argv[1]
URL = 'https://dati.terna.it/api/sitecore/dati/downloadcenter/recordsv2'
UA = {'User-Agent': 'milano-in-dati/1.0', 'Content-Type': 'application/json'}


def pagina(anno, n):
    corpo = dict(filterDataset='ElectricalEnergy', filterYear=str(anno), filterMonth='1', orderByColumn='Consumo (GWh)',
                 orderByDir='desc', pageSize='1000', pageIndex=str(n), db='dati')
    q = urllib.request.Request(URL, data=json.dumps(corpo).encode(), headers=UA, method='POST')
    return json.load(urllib.request.urlopen(q, timeout=120))


somme = collections.defaultdict(float)
controlli = []
for anno in range(2000, 2025):
    letti, n = 0, 0
    while True:
        j = pagina(anno, n)
        for riga in j['Data']:
            assert riga[0] == anno, riga
            letti += 1
            prov = riga[2] if riga[2] in ('Milano', 'Monza e della Brianza') else 'altre'
            somme[anno, prov, riga[3]] += float(riga[4])
        if letti >= j['Count'] or not j['Data']:
            break
        n += 1
        time.sleep(0.5)
    assert letti == j['Count'], (anno, letti, j['Count'])
    controlli.append((anno, letti))
    print(anno, letti, flush=True)
    time.sleep(0.5)
d = os.path.join(R, 'consumi', 'raw', 'terna')
os.makedirs(d, exist_ok=True)
with open(os.path.join(d, 'settori_aggregati.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['anno', 'provincia', 'settore', 'gwh'])
    for (a, p, s), v in sorted(somme.items()):
        w.writerow([a, p, s, round(v, 3)])
print('scritto', len(somme))
