import json, os, sys, time, requests
H = {'User-Agent': 'milano-in-dati/1.0'}
ids = json.load(open(sys.argv[1]))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
for anno, i in sorted(ids.items()):
    dest = os.path.join(out, f'incidenti_microdati_lombardia_{anno}_MILANO.json')
    if os.path.exists(dest):
        continue
    rows = []
    off = 0
    while True:
        for t in range(4):
            try:
                r = requests.get(f'https://www.dati.lombardia.it/resource/{i}.json', params={'$where': "upper(denominazione_comune)='MILANO'", '$limit': 50000, '$offset': off, '$order': ':id'}, headers=H, timeout=120)
                r.raise_for_status(); break
            except Exception as e:
                print('retry', anno, e); time.sleep(5 * (t + 1))
        b = r.json()
        rows += b
        if len(b) < 50000: break
        off += 50000
    json.dump(rows, open(dest, 'w'), ensure_ascii=False)
    print(anno, i, len(rows), flush=True)
    time.sleep(1)
