# Due controlli sulla prova:
# 1) il livello di dicembre 2023 e' molto piu' alto del 2019-2020: stagione, cantieri o strumento?
#    Si prende un mercoledi' per data scelta e si misura come in misura_prova.py.
# 2) Capodanno a passi di 10 minuti, perche' la mediana oraria nasconde un picco breve.
# Uso: python controlla_livello.py <cartella_raw> <file_uscita.csv>
import csv, os, sys, urllib.request
import datetime as dt
from zoneinfo import ZoneInfo

import numpy as np
from obspy import read
from scipy.signal import butter, sosfiltfilt

UA = {'User-Agent': 'milano-in-dati/1.0'}
BASE = 'https://webservices.ingv.it/fdsnws/dataselect/1/query?net=IV&sta=MILN&cha=HHZ&start=%s&end=%s'
ROMA = ZoneInfo('Europe/Rome')
DATE = ['2019-12-11', '2020-12-16', '2021-03-17', '2021-12-15', '2022-03-16', '2022-12-14', '2023-03-15', '2023-06-14', '2023-10-11', '2023-12-13', '2024-03-13', '2024-06-12', '2024-12-11', '2025-03-12', '2025-12-10', '2026-03-11', '2026-06-10', '2026-10-14']


def scala(g):
    return 1953930000.0 if g >= dt.date(2025, 3, 18) else 1474290000.0


def rms10(p, g):
    fuori = []
    for tr in read(p):
        fs = tr.stats.sampling_rate
        x = (tr.data.astype(float) - tr.data.mean()) / scala(g) * 1e9
        c = sosfiltfilt(butter(4, (2.0, 20.0), 'bandpass', fs=fs, output='sos'), x)
        k = sosfiltfilt(butter(4, (0.1, 1.0), 'bandpass', fs=fs, output='sos'), x)
        n = int(fs * 600)
        for i in range(0, len(x) - n + 1, n):
            t = (tr.stats.starttime + i / fs).datetime.replace(tzinfo=dt.timezone.utc).astimezone(ROMA)
            fuori.append((t, float(np.sqrt(np.mean(c[i:i + n] ** 2))), float(np.sqrt(np.mean(k[i:i + n] ** 2)))))
    return fuori


def main(raw, uscita):
    cart = os.path.join(raw, 'campione')
    os.makedirs(cart, exist_ok=True)
    with open(uscita, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['data', 'giorno_8_19_nm_s', 'notte_1_5_nm_s', 'controllo_nm_s'])
        for s in DATE:
            g = dt.date.fromisoformat(s)
            p = os.path.join(cart, 'MILN_HHZ_%s.mseed' % s)
            try:
                if not os.path.exists(p):
                    u = BASE % (s + 'T00:00:00', (g + dt.timedelta(days=1)).isoformat() + 'T00:00:00')
                    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=300) as r:
                        b = r.read()
                    with open(p, 'wb') as h:
                        h.write(b)
                v = rms10(p, g)
                gi = [a[1] for a in v if 8 <= a[0].hour < 19]
                no = [a[1] for a in v if 1 <= a[0].hour < 5]
                ri = [s, round(float(np.median(gi)), 1), round(float(np.median(no)), 1), round(float(np.median([a[2] for a in v])), 1)]
            except Exception as e:
                ri = [s, type(e).__name__, str(e)[:80], '']
            w.writerow(ri)
            print(ri, flush=True)
    print('--- Capodanno a 10 minuti')
    for nome in ('MILN_HHZ_2023-12-30.mseed', 'MILN_HHZ_2023-12-31.mseed'):
        g = dt.date.fromisoformat(nome[9:19])
        for t, c, k in rms10(os.path.join(raw, nome), g):
            if t.hour == 23 or (t.hour == 0 and t.minute < 60):
                print(t.strftime('%d/%m %H:%M'), round(c), round(k))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
