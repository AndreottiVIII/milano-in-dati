"""Scarica da dati.lombardia.it (Socrata) i dati 2026 dei sensori vicini a Brera, UNA richiesta alla volta,
con pause lunghe e backoff su 429/503. Salta i file gia presenti.
uso: python -I scarica_2026.py CARTELLA_OUT
Coppie: dataset 647i-nhxk (dal 2026-03-30) per 5909 5911 5920 2001; w9wd-u6jh e d4kj-kbpj per 2001 (Lambrate)."""
import sys, os, time, requests
out = sys.argv[1]
jobs = [('647i-nhxk', s) for s in ('5909', '5911', '5920', '2001')] + [('w9wd-u6jh', '2001'), ('d4kj-kbpj', '2001')]
H = {'User-Agent': 'milano-in-dati (ricerca, un sensore alla volta)'}
t0 = time.time(); LIMITE = 40 * 60
for ds, s in jobs:
    dst = os.path.join(out, f'sens_{s}_{ds}.csv')
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        print('gia', dst, flush=True); continue
    url = f'https://www.dati.lombardia.it/resource/{ds}.csv'
    off, page, first, n = 0, 50000, True, 0
    tmp = dst + '.part'
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        while True:
            wait = 60
            while True:
                try:
                    r = requests.get(url, params={'$where': f"idsensore='{s}'", '$order': 'data', '$limit': page, '$offset': off}, headers=H, timeout=180)
                    if r.status_code in (429, 503, 502, 504):
                        raise RuntimeError('HTTP %d %s' % (r.status_code, r.text[:80]))
                    r.raise_for_status(); break
                except Exception as e:
                    print('attesa', wait, 's:', e, flush=True)
                    if time.time() - t0 > LIMITE:
                        print('BLOCCATO oltre il limite, mi fermo', flush=True); sys.exit(2)
                    time.sleep(wait); wait = min(wait * 2, 300)
            lines = r.text.splitlines()
            if len(lines) <= 1: break
            f.write('\n'.join(lines if first else lines[1:]) + '\n'); first = False
            n += len(lines) - 1; off += page; print(ds, s, 'righe', n, flush=True)
            if len(lines) - 1 < page: break
            time.sleep(60)
    os.replace(tmp, dst)
    print('FINE', ds, s, n, flush=True)
    time.sleep(60)
