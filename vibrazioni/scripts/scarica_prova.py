# Scarica i giorni di prova del sismografo INGV di Milano (IV.MILN, canale verticale HHZ).
# Uso: python scarica_prova.py <cartella_raw>
import datetime as dt, os, sys, time, urllib.error, urllib.request

UA = {'User-Agent': 'milano-in-dati/1.0'}
BASE = 'https://webservices.ingv.it/fdsnws/dataselect/1/query?net=IV&sta=MILN&cha=HHZ&start=%s&end=%s'
PERIODI = {
    'prima_2020': ('2020-02-17', 7),
    'lockdown_2020': ('2020-03-23', 7),
    'normale_2019': ('2019-03-25', 7),
    'capodanno_2023': ('2023-12-30', 3),
}


def giorni():
    for inizio, n in PERIODI.values():
        d = dt.date.fromisoformat(inizio)
        # un giorno in piu' prima e dopo: le ore locali scavalcano la mezzanotte UTC
        for i in range(-1, n + 1):
            yield d + dt.timedelta(days=i)


def main(raw):
    os.makedirs(raw, exist_ok=True)
    for g in sorted(set(giorni())):
        p = os.path.join(raw, 'MILN_HHZ_%s.mseed' % g)
        if os.path.exists(p):
            continue
        u = BASE % (g.isoformat() + 'T00:00:00', (g + dt.timedelta(days=1)).isoformat() + 'T00:00:00')
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=300) as r:
                b = r.read()
            with open(p + '.tmp', 'wb') as f:
                f.write(b)
            os.replace(p + '.tmp', p)
            print(g, len(b) // 1000000, 'MB', flush=True)
        except urllib.error.HTTPError as e:
            print(g, 'HTTP', e.code, flush=True)
        except Exception as e:
            print(g, type(e).__name__, str(e)[:120], flush=True)
        time.sleep(1)


if __name__ == '__main__':
    main(sys.argv[1])
