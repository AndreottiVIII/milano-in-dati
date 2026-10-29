"""Scarica da dati.lombardia.it (Socrata) altre stazioni ARPA di Milano e dintorni per controllare Brera 2008-2016.
Solo le letture allo scoccare dell'ora (minuto 00): servono solo quelle (serie a passo orario costante, come BRERA_H),
e cosi' si scarica sei volte meno. UNA richiesta alla volta, pause di 30 s, backoff su 429/5xx. Salta i file gia' presenti.
uso: python -I scarica_omog.py CARTELLA_OUT
Sensori: 8162 Feltre (solo 2011+, il 6eu4 c'e' gia' in raw/arpa_altre), 4058 Cinisello Parco Nord, 5903 Corsico,
5917 Rodano, 5910 Lacchiarella, 5895 Agrate Brianza (chiusa 2018)."""
import sys, os, time, requests
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
DS = ('6eu4-4tja', 'd4kj-kbpj', 'w9wd-u6jh')
jobs = [('d4kj-kbpj', '8162'), ('w9wd-u6jh', '8162')]
for s in ('4058', '5903', '5917', '5910', '5895'):
    jobs += [(ds, s) for ds in DS]
H = {'User-Agent': 'milano-in-dati (ricerca, un sensore alla volta)'}
t0 = time.time(); LIMITE = 90 * 60
for ds, s in jobs:
    dst = os.path.join(out, f'sens_{s}_{ds}.csv')
    if os.path.exists(dst):
        print('gia', dst, flush=True); continue
    url = f'https://www.dati.lombardia.it/resource/{ds}.csv'
    off, page, first, n = 0, 50000, True, 0
    tmp = dst + '.part'
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        while True:
            wait = 60
            while True:
                try:
                    r = requests.get(url, params={'$where': f"idsensore='{s}' AND date_extract_mm(data)=0", '$order': 'data',
                                                  '$limit': page, '$offset': off}, headers=H, timeout=180)
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
            time.sleep(30)
    os.replace(tmp, dst)
    print('FINE', ds, s, n, flush=True)
    time.sleep(30)
print('TUTTO FATTO', flush=True)
