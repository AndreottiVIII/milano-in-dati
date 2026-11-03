"""SIOPE - movimenti cumulati mensili di ENTRATA dei comuni, dal catalogo BDAP open data (CC-BY).
Ogni file e' per regione e anno (circa 200 MB). Lo leggo in streaming e tengo solo le righe delle sette grandi citta':
il file intero non viene salvato.

Uso: python -I -X utf8 scarica_siope.py <cartella raw/siope> <elenco.csv: regione;anno;id>
"""
import sys, os, csv, io, time, datetime, urllib.request, urllib.error, hashlib

UA = {'User-Agent': 'milano-in-dati/1.0'}
BASE = 'https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/{}.csv'
CITTA = ['COMUNE DI MILANO', 'ROMA CAPITALE', 'COMUNE DI ROMA', 'COMUNE DI TORINO', 'COMUNE DI NAPOLI', 'COMUNE DI BOLOGNA',
         'COMUNE DI FIRENZE', 'COMUNE DI GENOVA']


def stream(regione, anno, rid, out):
    fn = os.path.join(out, f'siope_entrate_{regione}_{anno}.csv')
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        print('gia presente', fn, flush=True)
        return
    u = BASE.format(rid)
    t0 = time.time()
    h = hashlib.sha256()
    n = 0
    keep = 0
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180)
    tmp = fn + '.part'
    with open(tmp, 'w', encoding='utf-8', newline='') as o:
        buf = b''
        header = None
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
            buf += chunk
            lines = buf.split(b'\n')
            buf = lines.pop()
            for ln in lines:
                n += 1
                s = ln.decode('cp1252', errors='replace')
                if header is None:
                    header = s
                    o.write(s + '\n')
                    continue
                # colonna 7 = Descrizione Ente BDAP
                if any(('"' + c + '"') in s[:200] for c in CITTA):
                    o.write(s + '\n')
                    keep += 1
    if n < 1000:
        # il server a volte risponde con poche righe invece del file: si riprova
        raise RuntimeError('risposta troppo corta: %d righe' % n)
    os.replace(tmp, fn)
    print(regione, anno, 'righe', n, 'tenute', keep, 'sec', int(time.time() - t0), 'sha256', h.hexdigest()[:12], flush=True)
    with open(os.path.join(out, 'download_log.csv'), 'a', encoding='utf-8') as lf:
        lf.write(';'.join([regione, str(anno), u, datetime.datetime.now().isoformat(timespec='seconds'), str(n), str(keep),
                           h.hexdigest()]) + '\n')


def main(out, lista):
    os.makedirs(out, exist_ok=True)
    for row in csv.reader(open(lista, encoding='utf-8'), delimiter=';'):
        if not row or row[0].startswith('#'):
            continue
        reg, anno, rid = row[0], row[1], row[2]
        for tent in range(6):
            try:
                stream(reg, anno, rid, out)
                break
            except Exception as e:
                print('errore', reg, anno, e, flush=True)
                time.sleep(20)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
