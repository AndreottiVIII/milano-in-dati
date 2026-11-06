"""Cerca nel catalogo CKAN del Comune di Milano i dataset su fogne, depurazione, Seveso.
Uso: python -I -X utf8 01_cerca_comune.py <cartella_raw>
Scrive <raw>/comune/ricerca_<parola>.json e stampa titoli unici.
"""
import json, sys, time, pathlib, urllib.parse
import requests

H = {'User-Agent': 'milano-in-dati/1.0'}
API = 'https://dati.comune.milano.it/api/3/action/package_search'
PAROLE = ['fognatura', 'fognaria', 'fogne', 'depuratore', 'depurazione', 'reflue', 'Seveso',
          'esondazione', 'allagamenti', 'allagamento', 'Lambro', 'Vettabbia', 'vasca', 'laminazione',
          'idrometro', 'scarichi', 'tariffa idrica', 'servizio idrico', 'MM', 'acqua', 'Nosedo',
          'San Rocco', 'rogge', 'navigli', 'corsi d\'acqua', 'reticolo idrico', 'pioggia', 'Olona']

out = pathlib.Path(sys.argv[1]) / 'comune'
out.mkdir(parents=True, exist_ok=True)
visti = {}
for p in PAROLE:
    f = out / ('ricerca_' + p.replace(' ', '_').replace("'", '') + '.json')
    if not f.exists():
        r = requests.get(API, params={'q': p, 'rows': 200}, headers=H, timeout=60)
        r.raise_for_status()
        f.write_text(r.text, encoding='utf-8')
        time.sleep(3.5)
    d = json.loads(f.read_text(encoding='utf-8'))['result']
    print(f'{p}: {d["count"]}')
    for x in d['results']:
        if x['name'] not in visti:
            visti[x['name']] = (x['title'], p, x.get('license_id'), x.get('metadata_modified', '')[:10])
for k, v in sorted(visti.items(), key=lambda kv: kv[1][1]):
    print(k, '|', v[0], '|', v[1], '|', v[2], '|', v[3])
