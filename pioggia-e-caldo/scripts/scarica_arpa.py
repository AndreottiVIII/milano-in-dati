"""Scarica da dati.lombardia.it (Socrata, ARPA Lombardia, CC0) le righe dei sensori scelti.
Una richiesta ogni N sensori e per dataset (filtro idsensore IN (...)), risposta in streaming e divisa in un file per sensore.
(Il portale limita le richieste senza token: una richiesta ogni ~30 s dopo qualche raffica; per questo si raggruppano i sensori.)
Riprendibile: salta i file gia' completi; scrive in .part e rinomina a fine scarico.
uso: python -I -X utf8 scarica_arpa.py <sensori_selezionati.csv> <cartella_raw/arpa> [T|P|TP] [N_per_richiesta]
Nessun account, nessun token."""
import csv, os, sys, time, requests
sens_csv, outdir = sys.argv[1], sys.argv[2]
kinds = sys.argv[3] if len(sys.argv) > 3 else 'TP'
NB = int(sys.argv[4]) if len(sys.argv) > 4 else 8
DS = {'T': [('6eu4-4tja','fino2010'),('d4kj-kbpj','2011-2020'),('w9wd-u6jh','dal2021'),('647i-nhxk','mese_in_corso')],
      'P': [('e7r2-7m84','fino2010'),('2kar-pnuk','2011-2020'),('pstb-pga6','dal2021'),('647i-nhxk','mese_in_corso')]}
sel = [r for r in csv.DictReader(open(sens_csv, encoding='utf-8'))]
log = open(os.path.join(outdir, 'download_log.csv'), 'a', encoding='utf-8')
HEAD = '"idsensore","data","valore","stato"\n'
def fetch(ds, ids):
    """scarica e divide per sensore; ritorna {id: (righe, byte)}"""
    q = ','.join(f"'{i}'" for i in ids)
    for t in range(12):
        try:
            r = requests.get(f'https://www.dati.lombardia.it/resource/{ds}.csv',
                             params={'$where': f'idsensore in ({q})', '$order': 'idsensore,data', '$limit': 50000000}, timeout=900, stream=True)
            if r.status_code != 200:
                print('HTTP', r.status_code, r.text[:80], 'attesa', 30*(t+1), flush=True); time.sleep(30*(t+1)); continue
            head = [None]
            files = {}; cnt = {i: 0 for i in ids}; byt = {i: 0 for i in ids}
            for line in r.iter_lines(decode_unicode=False):
                if line.startswith(b'"idsensore"'): head[0] = line + b'
'; continue
                i = line.split(b',', 1)[0].strip(b'"').decode()
                if i not in cnt: continue
                if i not in files: files[i] = open(os.path.join(outdir, ds, f'{kind}_{i}.csv.part'), 'wb'); files[i].write(head[0] or HEAD.encode())
                files[i].write(line + b'\n'); cnt[i] += 1; byt[i] += len(line) + 1
            for f in files.values(): f.close()
            return cnt, byt
        except Exception as e:
            print('errore', repr(e)[:150], flush=True); time.sleep(30)
            for fn in os.listdir(os.path.join(outdir, ds)):
                if fn.endswith('.part'): os.remove(os.path.join(outdir, ds, fn))
    raise SystemExit('troppi errori')
for kind in kinds:
    names = {r['idsensore']: r['nomestazione'] for r in sel if r['tipologia'] == ('Temperatura' if kind == 'T' else 'Precipitazione')}
    ids_all = list(names)
    for ds, lab in DS[kind]:
        os.makedirs(os.path.join(outdir, ds), exist_ok=True)
        todo = [i for i in ids_all if not os.path.exists(os.path.join(outdir, ds, f'{kind}_{i}.csv'))]
        for b in range(0, len(todo), NB):
            ids = todo[b:b+NB]
            cnt, byt = fetch(ds, ids)
            for i in ids:  # anche i sensori senza righe ricevono un file con la sola intestazione
                fn = os.path.join(outdir, ds, f'{kind}_{i}.csv')
                if os.path.exists(fn + '.part'): os.replace(fn + '.part', fn)
                else: open(fn, 'w').write(HEAD)
                log.write(f"{time.strftime('%Y-%m-%d')},{ds},{lab},{i},{names[i].replace(',',' ')},{cnt[i]},{byt[i]}\n")
            log.flush(); print(time.strftime('%H:%M:%S'), ds, kind, ids, [cnt[i] for i in ids], flush=True)
            time.sleep(2)
print('FINE')
