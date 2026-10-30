"""Scarica tutte le risorse dei dataset acqua dal CKAN del Comune di Milano.
Uso: python -I 01_scarica.py <cartella_strand>
Riprendibile: salta i file gia' presenti con la dimensione giusta."""
import sys, os, json, time, requests
base = sys.argv[1]
raw = os.path.join(base, 'raw')
H = {'User-Agent': 'milano-in-dati/1.0 (ricerca open data; contatto davide.caniatti@gmail.com)'}
API = 'https://dati.comune.milano.it/api/3/action/'

def get(url, **kw):
    for i in range(5):
        try:
            r = requests.get(url, headers=H, timeout=120, **kw)
            if r.status_code == 429:
                time.sleep(30 * (i + 1)); continue
            r.raise_for_status(); return r
        except Exception as e:
            print('retry', url, e); time.sleep(5 * (i + 1))
    raise SystemExit('fallito ' + url)

names = set()
for q in ["analisi dell'acqua", "acqua immessa erogata perdite", "analisi dell'acqua trimestre"]:
    r = get(API + 'package_search', params={'q': q, 'rows': 100}).json()
    for p in r['result']['results']:
        t = p['title'].lower()
        if "analisi dell'acqua" in t or 'perdite idriche' in t:
            names.add(p['name'])
    time.sleep(1)
print(len(names), 'dataset')
inv = []
for n in sorted(names):
    p = get(API + 'package_show', params={'id': n}).json()['result']
    time.sleep(1)
    d = os.path.join(raw, n)
    os.makedirs(d, exist_ok=True)
    json.dump(p, open(os.path.join(d, '_package.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for res in p['resources']:
        fn = os.path.basename(res['url'].split('?')[0])
        path = os.path.join(d, fn)
        ok = os.path.exists(path) and os.path.getsize(path) > 0
        if not ok:
            r = get(res['url'])
            open(path, 'wb').write(r.content)
            time.sleep(1)
        inv.append({'dataset': n, 'title': p['title'], 'license': p.get('license_id'),
                    'modified': p.get('metadata_modified'), 'file': os.path.relpath(path, base).replace(os.sep, '/'),
                    'format': res['format'], 'size_declared': res.get('size'), 'size_real': os.path.getsize(path),
                    'url': res['url']})
        print(n, fn, os.path.getsize(path))
json.dump(inv, open(os.path.join(base, 'raw', '_inventario.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
