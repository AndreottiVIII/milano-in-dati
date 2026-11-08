"""Scarica da Wikimedia Commons le immagini libere di film e libri ambientati a Milano.

Uso (dalla cartella film-e-libri):
    python -I -X utf8 scripts/30_immagini_commons.py

Per ogni file della SELEZIONE:
  1. chiede a Commons (API, prop=imageinfo, iiprop=url|extmetadata) autore, licenza e miniatura larga 400 px;
  2. accetta solo licenze libere: pubblico dominio, CC0, CC BY, CC BY-SA (altrimenti salta);
  3. scarica la miniatura in ../docs/milano-raccontata/data/img/ con un nome nuovo;
  4. scrive ../docs/milano-raccontata/data/immagini.json (opera, anno, autore, licenza, pagina del file).

Regole: User-Agent 'milano-in-dati/1.0' (niente email), una richiesta alla volta, con pausa.
"""
import json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

UA = {'User-Agent': 'milano-in-dati/1.0'}
API = 'https://commons.wikimedia.org/w/api.php'
QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(QUI, '..', '..', 'docs', 'milano-raccontata', 'data'))
IMG = os.path.join(OUT, 'img')
PAUSA = 6

# (tipo, titolo dell'opera, anno, file su Commons, nome nuovo)
SELEZIONE = [
    ('film', 'Miracolo a Milano', 1951, 'File:Miracolo a Milano 03.png', 'film-miracolo-a-milano'),
    ('film', 'Rocco e i suoi fratelli', 1960, 'File:Photo Alain Delon in a scene from Rocco e i suoi fratelli, a 1960 film directed by Luchino Visconti 1960 - Touring Club Italiano 04 1716.jpg', 'film-rocco-e-i-suoi-fratelli'),
    ('film', 'La notte', 1961, 'File:SalvatoreQuasimodoappareinuncameoneLaNotte.png', 'film-la-notte'),
    ('film', 'Il posto', 1961, 'File:Photo Sandro Panseri in a scene from Il posto, a 1961 film directed by Ermanno Olmi. 1961 - Touring Club Italiano 04 1577.jpg', 'film-il-posto'),
    ('film', 'La vita agra', 1964, 'File:La vita agra 01.jpg', 'film-la-vita-agra'),
    ('film', 'Milano calibro 9', 1972, 'File:Gastone Moschin and Ettore Geri, Milano Calibro 9.jpg', 'film-milano-calibro-9'),
    ('libro', 'I promessi sposi (copertina della seconda edizione)', 1840, 'File:I promessi sposi - 2nd edition cover.jpg', 'libro-promessi-sposi-copertina'),
    ('libro', 'I promessi sposi (illustrazione di Francesco Gonin)', 1840, 'File:I promessi sposi - Renzo.jpg', 'libro-promessi-sposi-renzo'),
    ('libro', 'Il Giorno di Giuseppe Parini (frontespizio dell\'edizione 1799)', 1799, 'File:Il "Giorno" e le "Odi" di Giuseppe Parini.jpg', 'libro-parini-il-giorno'),
]

# Autore da mostrare sotto l'immagine (a mano, dalle informazioni della pagina del file su Commons)
AUTORI = {
    'film-miracolo-a-milano': 'fotogramma del film, regia di Vittorio De Sica',
    'film-rocco-e-i-suoi-fratelli': 'Archivio Storico del Touring Club Italiano, fotografo sconosciuto',
    'film-la-notte': 'fotogramma del film, regia di Michelangelo Antonioni',
    'film-il-posto': 'Archivio Storico del Touring Club Italiano, fotografo sconosciuto',
    'film-la-vita-agra': 'fotogramma del film, regia di Carlo Lizzani',
    'film-milano-calibro-9': 'fotogramma del film, regia di Fernando Di Leo (caricato da Wristrel)',
    'libro-promessi-sposi-copertina': 'Francesco Gonin',
    'libro-promessi-sposi-renzo': 'Francesco Gonin',
    'libro-parini-il-giorno': 'edizione del 1799, opera di Giuseppe Parini',
}

LIBERE = [r'^public domain', r'^cc0', r'^cc by \d', r'^cc by-sa \d', r'^cc-by-\d', r'^cc-by-sa-\d']


def chiama(url, binario=False):
    for k in range(6):
        time.sleep(PAUSA + 20 * k)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                dati = r.read()
                return dati if binario else json.loads(dati)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            print('429, aspetto', file=sys.stderr)
    raise SystemExit('troppi 429')


def pulisci(h):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h or '')).strip()


def main():
    os.makedirs(IMG, exist_ok=True)
    risultati = []
    for tipo, opera, anno, titolo, nome in SELEZIONE:
        q = {'action': 'query', 'format': 'json', 'titles': titolo, 'prop': 'imageinfo|templates',
             'iiprop': 'url|extmetadata|size|mime', 'iiurlwidth': 400, 'tllimit': 50}
        d = chiama(API + '?' + urllib.parse.urlencode(q))
        pg = list(d['query']['pages'].values())[0]
        if 'imageinfo' not in pg:
            print('NON TROVATO', titolo); continue
        ii = pg['imageinfo'][0]
        em = ii.get('extmetadata', {})
        val = lambda k: pulisci(em.get(k, {}).get('value', ''))
        lic = val('LicenseShortName')
        if not any(re.search(p, lic.lower()) for p in LIBERE):
            print('LICENZA NON LIBERA, salto:', titolo, lic); continue
        if val('Restrictions') and 'personality' not in val('Restrictions').lower():
            print('RESTRIZIONI', titolo, val('Restrictions'))
        thumb = ii['thumburl']
        ext = os.path.splitext(urllib.parse.urlparse(thumb).path)[1].lower() or '.jpg'
        if ext == '.jpeg':
            ext = '.jpg'
        fn = nome + ext
        with open(os.path.join(IMG, fn), 'wb') as f:
            f.write(chiama(thumb, binario=True))
        autore = AUTORI.get(nome) or val('Artist') or val('Credit')
        risultati.append({
            'tipo': tipo, 'opera': opera, 'anno': anno, 'file': 'data/img/' + fn,
            'autore': autore, 'licenza': lic, 'licenza_url': val('LicenseUrl'),
            'pagina': 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(titolo.replace(' ', '_'), safe=':_(),'),
            'titolo_commons': titolo.replace('File:', ''),
            'modelli': [t['title'].replace('Template:', '') for t in pg.get('templates', [])][:12],
        })
        print('OK', fn, '|', lic, '|', autore[:60])
    with open(os.path.join(OUT, 'immagini.json'), 'w', encoding='utf-8') as f:
        json.dump(risultati, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
