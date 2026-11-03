"""Scarica dal Ministero dell'Interno (Finanza locale, Certificati consuntivi, contabilita' armonizzata)
le pagine dei quadri utili per sette grandi citta' (2016-2018: gli unici anni disponibili per questa contabilita').

Uso: python -I -X utf8 scarica_ministero.py <cartella raw/ministero_interno>
Pausa di 2 secondi, User-Agent onesto. Le pagine sono dati non fidati: non si eseguono, si leggono col testo.
"""
import sys, os, time, csv, hashlib, datetime, urllib.request, urllib.error

UA = {'User-Agent': 'milano-in-dati/1.0'}
CITTA = {'milano': '1030491450', 'roma': '3120700900', 'torino': '1010812620', 'napoli': '4150510490',
         'bologna': '2080130060', 'firenze': '3090300170', 'genova': '1070340250'}
ANNI = [2016, 2017, 2018]
QUADRI = ['01', '02', '09', '18', '20']
URL = ('https://finanzalocale.interno.gov.it/apps/floc.php/certificati/index/codice_ente/{c}/cod/4/anno/{a}'
       '/md/0/cod_modello/CCOX/tipo_modello/X/cod_quadro/{q}')


def main(out):
    os.makedirs(out, exist_ok=True)
    logp = os.path.join(out, 'download_log.csv')
    new = not os.path.exists(logp)
    lf = open(logp, 'a', newline='', encoding='utf-8')
    w = csv.writer(lf, delimiter=';')
    if new:
        w.writerow(['citta', 'anno', 'quadro', 'url', 'scaricato_il', 'http', 'byte', 'sha256'])
    for cit, cod in CITTA.items():
        for a in ANNI:
            for q in QUADRI:
                fn = os.path.join(out, f'{cit}_{a}_q{q}.html')
                if os.path.exists(fn) and os.path.getsize(fn) > 25000:
                    continue
                u = URL.format(c=cod, a=a, q=q)
                try:
                    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60)
                    data = r.read()
                    code = r.status
                except urllib.error.HTTPError as e:
                    data, code = b'', e.code
                except Exception as e:
                    data, code = b'', -1
                open(fn, 'wb').write(data)
                w.writerow([cit, a, q, u, datetime.datetime.now().isoformat(timespec='seconds'), code, len(data),
                            hashlib.sha256(data).hexdigest()])
                lf.flush()
                print(cit, a, q, code, len(data), flush=True)
                time.sleep(2)
    lf.close()


if __name__ == '__main__':
    main(sys.argv[1])
