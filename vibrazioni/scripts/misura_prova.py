# Misura le vibrazioni orarie dai file del sismografo: fascia "citta'" (2-20 Hz) e fascia di controllo
# "mare e meteo" (0,1-1 Hz), che non dipende dalle attivita' umane.
# Uso: python misura_prova.py <cartella_raw> <file_uscita.csv>
import collections, csv, glob, os, sys
import datetime as dt
from zoneinfo import ZoneInfo

import numpy as np
from obspy import read
from scipy.signal import butter, sosfiltfilt

SCALA = 1474290000.0  # conteggi per m/s, valida dal 2012 al 17/3/2025 (metadati INGV)
ROMA = ZoneInfo('Europe/Rome')
FASCE = {'citta': (2.0, 20.0), 'controllo': (0.1, 1.0)}
FINESTRA = 600  # secondi


def main(raw, uscita):
    ore = collections.defaultdict(lambda: collections.defaultdict(list))
    for p in sorted(glob.glob(os.path.join(raw, '*.mseed'))):
        st = read(p)
        for tr in st:
            x = tr.data.astype(float)
            fs = tr.stats.sampling_rate
            if len(x) < fs * FINESTRA:
                continue
            x = (x - x.mean()) / SCALA * 1e9  # nanometri al secondo
            filtrati = {k: sosfiltfilt(butter(4, b, 'bandpass', fs=fs, output='sos'), x) for k, b in FASCE.items()}
            n = int(fs * FINESTRA)
            for i in range(0, len(x) - n + 1, n):
                t = (tr.stats.starttime + i / fs).datetime.replace(tzinfo=dt.timezone.utc).astimezone(ROMA)
                ora = t.replace(minute=0, second=0, microsecond=0)
                for k, y in filtrati.items():
                    ore[ora][k].append(float(np.sqrt(np.mean(y[i:i + n] ** 2))))
    with open(uscita, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ora_locale', 'citta_nm_s', 'controllo_nm_s', 'finestre'])
        for ora in sorted(ore):
            v = ore[ora]
            # mediana delle finestre da 10 minuti: un terremoto o un passaggio isolato non sposta l'ora
            w.writerow([ora.isoformat(), round(float(np.median(v['citta'])), 3), round(float(np.median(v['controllo'])), 3), len(v['citta'])])
    print('ore', len(ore))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
