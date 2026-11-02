"""Scarica in raw/ i file usati dal filone "Rifiuti" (ISPRA Catasto rifiuti e CKAN del Comune di Milano).

Uso (percorsi assoluti):
    python -I -X utf8 download.py <cartella raw>

- un solo file per volta, pausa di 3 secondi, User-Agent che dice chi siamo (nessuna imitazione di un browser);
- se il sito risponde con una pagina HTML al posto del CSV (accade a volte: pagina con uno script di verifica)
  il programma NON la esegue e NON tenta di superarla: salva la risposta con estensione .html, segnala e passa
  oltre. Una nuova esecuzione piu' tardi (dopo una pausa) di solito basta;
- i file gia' presenti non vengono riscaricati.
I file scaricati sono dati non fidati: si leggono soltanto come testo (build.py), non si eseguono mai.
"""
import json
import os
import sys
import time
import urllib.request

UA = 'ClaudeTower-research (davide.caniatti@gmail.com)'
ISPRA = 'https://www.catasto-rifiuti.isprambiente.it/'
PAUSA = 3


def prendi(url, dest):
    if os.path.exists(dest):
        return 'gia presente'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        corpo = r.read()
    if corpo[:200].lstrip().lower().startswith((b'<html', b'<!doctype')):
        with open(dest + '.html', 'wb') as f:
            f.write(corpo)
        return 'RISPOSTA HTML (non CSV): salvata come .html, non eseguita; riprovare piu tardi'
    with open(dest, 'wb') as f:
        f.write(corpo)
    time.sleep(PAUSA)
    return 'ok %d byte' % len(corpo)


def main(raw):
    os.makedirs(os.path.join(raw, 'ispra_comuni'), exist_ok=True)
    os.makedirs(os.path.join(raw, 'ispra_costi'), exist_ok=True)
    os.makedirs(os.path.join(raw, 'comune_milano'), exist_ok=True)
    for y in range(2010, 2025):
        d = os.path.join(raw, 'ispra_comuni', 'rifiuti_comuni_%d.csv' % y)
        print('rifiuti', y, prendi(ISPRA + 'get/getDettaglioComunale.csv.php?&aa=%d' % y, d))
    for y in range(2011, 2025):
        d = os.path.join(raw, 'ispra_costi', 'costi_procapite_%d.csv' % y)
        print('costi', y, prendi(ISPRA + 'costi/getCostiComunaleproc.csv.php?costicomuneproc&aa=%d&regid=1&regid2=Italia&reg1=Italia&p=1' % y, d))
    # Comune di Milano (CKAN): solo per controllo dei numeri di Milano
    api = 'https://dati.comune.milano.it/api/3/action/package_show?id='
    for nome in ('ds857-rifiuti-serie-storica-2014-avanti-dettaglio', 'ds858-rifiuti-serie-storica-2010-avanti-sintesi',
                 'ds859-costi-di-gestione-pro-capite-dei-rifiuti', 'ds860-costo-di-gestione-dei-rifiuti-per-chilogrammo',
                 'ds572_raccolta-differenziata-2010-avanti', 'ds524_rifiuti-raccolti-a-milano-e-nei-comuni-limitrofi-2000-2016'):
        req = urllib.request.Request(api + nome, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            pk = json.loads(r.read().decode('utf-8'))['result']
        time.sleep(PAUSA)
        for x in pk['resources']:
            if x['format'].upper() == 'CSV':
                print(nome.split('-')[0].split('_')[0], prendi(x['url'], os.path.join(raw, 'comune_milano', nome.split('-')[0].split('_')[0] + '.csv')))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
