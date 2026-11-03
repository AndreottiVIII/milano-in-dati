# Seconda prova: Ferragosto 2019 e tre grandi partite a San Siro con serate di confronto.
# Uso: python prova_ferragosto_sansiro.py <cartella_raw> <cartella_out>
import csv, os, sys, urllib.request
import datetime as dt
from zoneinfo import ZoneInfo

import numpy as np
from obspy import read
from scipy.signal import butter, sosfiltfilt

UA = {'User-Agent': 'milano-in-dati/1.0'}
BASE = 'https://webservices.ingv.it/fdsnws/dataselect/1/query?net=IV&sta=MILN&cha=HHZ&start=%s&end=%s'
ROMA = ZoneInfo('Europe/Rome')
FERRAGOSTO = [dt.date(2019, 8, 11) + dt.timedelta(days=i) for i in range(9)]
PARTITE = ['2023-05-10', '2023-05-16', '2025-05-06']
CONFRONTO = ['2023-05-03', '2023-05-17', '2023-05-09', '2023-05-23', '2025-04-29', '2025-05-13']
FASCE = {'folla': (1.5, 4.0), 'citta': (2.0, 20.0), 'controllo': (0.1, 1.0)}


def scala(g):
    return 1953930000.0 if g >= dt.date(2025, 3, 18) else 1474290000.0


def scarica(cart, g):
    os.makedirs(cart, exist_ok=True)
    p = os.path.join(cart, 'MILN_HHZ_%s.mseed' % g)
    if not os.path.exists(p):
        u = BASE % (g.isoformat() + 'T00:00:00', (g + dt.timedelta(days=1)).isoformat() + 'T00:00:00')
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=300) as r:
            b = r.read()
        with open(p + '.tmp', 'wb') as f:
            f.write(b)
        os.replace(p + '.tmp', p)
    return p


def minuti(p, g):
    fuori = []
    for tr in read(p):
        fs = tr.stats.sampling_rate
        if len(tr.data) < fs * 60:
            continue
        x = (tr.data.astype(float) - tr.data.mean()) / scala(g) * 1e9
        y = {k: sosfiltfilt(butter(4, b, 'bandpass', fs=fs, output='sos'), x) for k, b in FASCE.items()}
        n = int(fs * 60)
        for i in range(0, len(x) - n + 1, n):
            t = (tr.stats.starttime + i / fs).datetime.replace(tzinfo=dt.timezone.utc).astimezone(ROMA)
            fuori.append((t, *[round(float(np.sqrt(np.mean(y[k][i:i + n] ** 2))), 1) for k in FASCE]))
    return fuori


def main(raw, out):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'minuti_ferragosto.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['minuto', 'folla', 'citta', 'controllo'])
        for g in FERRAGOSTO:
            for r in minuti(scarica(os.path.join(raw, 'ferragosto'), g), g):
                w.writerow([r[0].isoformat(), *r[1:]])
            print('ferragosto', g, flush=True)
    with open(os.path.join(out, 'minuti_partite.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['tipo', 'giorno', 'minuto', 'folla', 'citta', 'controllo'])
        for tipo, elenco in (('partita', PARTITE), ('confronto', CONFRONTO)):
            for s in elenco:
                g = dt.date.fromisoformat(s)
                for r in minuti(scarica(os.path.join(raw, 'sansiro'), g), g):
                    w.writerow([tipo, s, r[0].isoformat(), *r[1:]])
                print(tipo, s, flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
