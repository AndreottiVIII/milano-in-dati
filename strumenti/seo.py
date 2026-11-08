"""SEO di Milano in dati: tutto quello che serve a Google nella <head>, la mappa del sito, il manifest e la 404.

Per ogni pagina di docs/ (mai docs/anteprima/) scrive nella <head> un blocco fra <!--seo--> e <!--/seo-->
(si puo' rilanciare quante volte si vuole: il blocco viene sostituito). Dentro:
- meta description, solo se la pagina non ne ha gia' una scritta a mano fuori dai blocchi
  (altrimenti la prende dalla riga d'apertura sotto l'h1, 120-160 caratteri: vedi sito.descrizione());
- link canonical con l'indirizzo assoluto;
- theme-color e link al site.webmanifest;
- JSON-LD: in home WebSite e Person; nelle pagine di dati un Dataset (nome, descrizione, url, autore, lingua,
  Milano, fonti, licenze dalle fonti, anni coperti da il-sito/data/conti.json, data di modifica).
Scrive anche:
- docs/sitemap.xml: tutte le pagine tranne anteprima/; lastmod cambia solo quando cambia il testo della pagina
  (impronta salvata in strumenti/date_pagine.json);
- docs/site.webmanifest (icone favicon-192.png e favicon-512.png);
- docs/404.html (usa percorsi assoluti: GitHub Pages la serve da qualsiasi indirizzo).
robots.txt non serve: su un sito "di progetto" Google legge solo quello alla radice del dominio.

Meglio rilanciarlo DOPO statico.py (l'impronta del testo comprende il blocco statico).
Uso: python -I -X utf8 strumenti/seo.py [pagina ...]   (senza nomi: tutte)
"""
import datetime, hashlib, html, json, re, sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup

import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sito
from sito import BASE, DOCS, STRUMENTI

DATE = STRUMENTI / 'date_pagine.json'
COLORE_TEMA = '#E30613'
NON_DATI = {'elenco', 'fonti', 'il-sito', 'dati-importanti'}  # WebPage invece di Dataset

# licenze con indirizzo (le altre indicate si scrivono a parole; quelle "non aperte" non sono licenze)
URL_LICENZE = {
    'CC BY 4.0': 'https://creativecommons.org/licenses/by/4.0/',
    'CC BY 3.0': 'https://creativecommons.org/licenses/by/3.0/',
    'CC BY-SA 4.0': 'https://creativecommons.org/licenses/by-sa/4.0/',
    'CC0 1.0': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'ODbL': 'https://opendatacommons.org/licenses/odbl/1-0/',
    'IODL 2.0': 'https://www.dati.gov.it/content/italian-open-data-license-v20',
    'NLOD 2.0': 'https://data.norge.no/nlod/en/2.0',
}
NON_LICENZE = ('non indicata', 'uso con citazione', 'tutti i diritti riservati', 'autorizzazione dichiarata')

e = lambda s: html.escape(s, quote=True)


def carica_dati():
    f = json.load(open(DOCS / 'fonti' / 'data' / 'fonti.json', encoding='utf-8'))
    per_pagina = {}
    for x in f['fonti']:
        per_pagina.setdefault(x['pagina'], []).append(x)
    conti = json.load(open(DOCS / 'il-sito' / 'data' / 'conti.json', encoding='utf-8'))
    anni = {x['path'].strip('/'): (x.get('anno_da'), x.get('anno_a')) for x in conti['elenco']}
    return per_pagina, anni


def licenze(fonti_pagina):
    out = []
    tutte = {(x.get('licenza') or '').strip() for x in fonti_pagina}
    for x in fonti_pagina:
        l = (x.get('licenza') or '').strip()
        if not l or l.lower().startswith(NON_LICENZE):
            continue
        if l in ('CC BY', 'CC BY-SA') and any(t.startswith(l + ' ') for t in tutte):
            continue  # "CC BY" senza versione, quando la stessa pagina ha anche "CC BY 4.0"
        v = URL_LICENZE.get(l, l)
        if v not in out:
            out.append(v)
    return out[0] if len(out) == 1 else (out or None)


def fonti_link(fonti_pagina):
    out = []
    for x in fonti_pagina:
        for l in list(x.get('link') or []) + list(x.get('siti') or []):
            if isinstance(l, str) and l.startswith('http') and l not in out:
                out.append(l)
    return out[:30]


def json_ld(g):
    return '<script type="application/ld+json">%s</script>' % \
        json.dumps(g, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def grafo(p, nome, desc, modificata, per_pagina, anni):
    url = sito.url_pagina(p)
    if not p:
        return {'@context': 'https://schema.org', '@graph': [
            {'@type': 'WebSite', '@id': BASE + '#sito', 'url': BASE, 'name': 'Milano in dati',
             'description': desc, 'inLanguage': 'it-IT', 'author': {'@id': BASE + '#autore'}},
            dict(sito.AUTORE, **{'@id': BASE + '#autore'}),
        ]}
    fp = per_pagina.get(p, [])
    base_su = fonti_link(fp)
    if p in NON_DATI or p not in anni:  # elenco, fonti, il-sito...: pagine che parlano del sito, non archivi di dati
        return {'@context': 'https://schema.org', '@type': 'WebPage', 'name': nome, 'description': desc,
                'url': url, 'inLanguage': 'it-IT', 'dateModified': modificata,
                'isPartOf': {'@type': 'WebSite', 'name': 'Milano in dati', 'url': BASE},
                'author': sito.AUTORE}
    d = {'@context': 'https://schema.org', '@type': 'Dataset', 'name': nome, 'description': desc,
         'url': url, 'creator': sito.AUTORE, 'inLanguage': 'it-IT',
         'spatialCoverage': {'@type': 'Place', 'name': 'Milano'},
         'isPartOf': {'@type': 'WebSite', 'name': 'Milano in dati', 'url': BASE}}
    if base_su:
        d['isBasedOn'] = base_su
    lic = licenze(fp)
    if lic:
        d['license'] = lic
    da, a = anni.get(p, (None, None))
    if da:
        d['temporalCoverage'] = str(da) if (not a or a == da) else '%s/%s' % (da, a)
    d['dateModified'] = modificata
    return d


def testo_pagina(s):
    """Il testo della pagina (titolo, descrizione, corpo senza script), per l'impronta."""
    soup = BeautifulSoup(s, 'lxml')
    t = soup.title.get_text() if soup.title else ''
    d = soup.find('meta', attrs={'name': 'description'})
    for x in soup(['script', 'style', 'noscript', 'template']):
        x.decompose()
    corpo = soup.body.get_text(' ', strip=True) if soup.body else ''
    return sito.pulisci(t + ' | ' + (d.get('content', '') if d else '') + ' | ' + corpo)


def blocco(p, s, modificata, per_pagina, anni):
    desc = sito.descrizione(p, s)
    ha_desc = re.search(r'<meta\s+name="description"', sito.senza_blocchi(s), re.I) is not None
    h1 = BeautifulSoup(sito.senza_blocchi(s), 'lxml').find('h1')
    nome = sito.pulisci(h1.get_text(' ')) if h1 else 'Milano in dati'
    righe = []
    if not ha_desc:
        righe.append('<meta name="description" content="%s">' % e(desc))
    righe += [
        '<link rel="canonical" href="%s">' % e(sito.url_pagina(p)),
        '<meta name="theme-color" content="%s">' % COLORE_TEMA,
        '<link rel="manifest" href="%ssite.webmanifest">' % BASE,
        json_ld(grafo(p, nome, desc, modificata, per_pagina, anni)),
    ]
    return '<!--seo-->' + ''.join(righe) + '<!--/seo-->'


def manifest():
    return json.dumps({
        'name': 'Milano in dati', 'short_name': 'Milano in dati', 'lang': 'it',
        'description': 'Milano raccontata con i dati aperti.',
        'start_url': BASE, 'scope': BASE, 'display': 'browser',
        'background_color': '#ffffff', 'theme_color': COLORE_TEMA,
        'icons': [
            {'src': BASE + 'favicon-192.png', 'sizes': '192x192', 'type': 'image/png'},
            {'src': BASE + 'favicon-512.png', 'sizes': '512x512', 'type': 'image/png'},
        ]}, ensure_ascii=False, indent=2) + '\n'


def pagina_404():
    radice = urlparse(BASE).path or '/'
    temi = json.load(open(DOCS / 'temi.json', encoding='utf-8'))
    liste = []
    for t in temi['temi']:
        voci = [x for x in temi['pagine'] if x['tema'] == t['id']]
        if not voci:
            continue
        liste.append('<h2>%s</h2><ul>%s</ul>' % (e(t['nome']), ''.join(
            '<li><a href="%s%s">%s</a></li>' % (radice, x['path'], e(x['label'])) for x in voci)))
    return ('<!doctype html>\n<html lang="it"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Pagina non trovata · Milano in dati</title>'
            '<meta name="robots" content="noindex">'
            '<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">'
            '<link rel="icon" href="{r}favicon.ico" sizes="48x48">'
            '<link rel="apple-touch-icon" href="{r}apple-touch-icon.png">'
            '<style>body{{margin:0;font:16px/1.5 "Helvetica Neue",Helvetica,Arial,sans-serif;color:#000;background:#fff}}'
            'nav{{display:flex;flex-wrap:wrap;gap:6px 18px;padding:12px 16px;border-bottom:3px solid {c};font-weight:700}}'
            'nav a{{color:#000}}main{{max-width:760px;margin:0 auto;padding:16px}}'
            'h1{{font-size:clamp(30px,7vw,48px);line-height:1.05;margin:24px 0 8px}}'
            'h2{{font-size:16px;margin:22px 0 4px;color:#555;text-transform:uppercase;letter-spacing:.06em}}'
            'ul{{margin:0;padding-left:20px}}a{{color:#0072BC}}</style></head><body>'
            '<nav><a href="{r}">Milano in dati</a><a href="{r}elenco/">Tutte le pagine</a>'
            '<a href="{r}quartiere/">Il tuo quartiere</a><a href="{r}fonti/">Fonti e metodo</a></nav>'
            '<main><h1>Pagina non trovata</h1>'
            '<p>L’indirizzo che hai aperto non esiste. Torna alla <a href="{r}">pagina iniziale</a> '
            'oppure guarda l’<a href="{r}elenco/">elenco di tutte le pagine</a>.</p>'
            '{liste}</main></body></html>\n').format(r=radice, c=COLORE_TEMA, liste=''.join(liste))


def main():
    scelte = [a.strip('/') for a in sys.argv[1:]] or sito.pagine()
    oggi = datetime.date.today().isoformat()
    registro = json.load(open(DATE, encoding='utf-8')) if DATE.exists() else {}
    per_pagina, anni = carica_dati()
    nuovo = {}
    cambiate = 0
    for p in sito.pagine():
        f = sito.file_pagina(p)
        s = sito.leggi(f)                      # si legge subito prima di scrivere
        # la data di modifica serve dentro il blocco: se il testo e' cambiato vale oggi
        vecchio = registro.get('/' + p)
        mod = vecchio[1] if vecchio else oggi
        if p in scelte:
            b = blocco(p, s, mod, per_pagina, anni)
            nuova = sito.sostituisci_blocco(s, 'seo', b, dopo=[r'<!--/condividi-->', r'</title>', r'<meta charset[^>]*>'])
        else:
            nuova = s
        h = hashlib.sha1(testo_pagina(nuova).encode('utf-8')).hexdigest()[:10]
        if vecchio and vecchio[0] == h:
            data = vecchio[1]
        else:
            data = oggi
        if data != mod and p in scelte:
            # il testo e' cambiato: rifare il blocco con la data nuova (dateModified)
            nuova = sito.sostituisci_blocco(nuova, 'seo', blocco(p, nuova, data, per_pagina, anni))
            h = hashlib.sha1(testo_pagina(nuova).encode('utf-8')).hexdigest()[:10]
        nuovo[p] = [h, data]
        if p in scelte:
            # rilettura subito prima di scrivere: se un altro agente ha toccato la pagina nel frattempo, si rifa'
            if sito.leggi(f) != s:
                s = sito.leggi(f)
                nuova = sito.sostituisci_blocco(s, 'seo', blocco(p, s, data, per_pagina, anni),
                                                dopo=[r'<!--/condividi-->', r'</title>', r'<meta charset[^>]*>'])
            if sito.scrivi(f, nuova):
                cambiate += 1
    registro_nuovo = {'/' + p: v for p, v in nuovo.items()}
    sito.scrivi(DATE, json.dumps(registro_nuovo, ensure_ascii=False, sort_keys=True, indent=0))
    voci = ['  <url><loc>%s</loc><lastmod>%s</lastmod></url>' % (e(sito.url_pagina(p)), nuovo[p][1]) for p in sito.pagine()]
    sito.scrivi(DOCS / 'sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(voci) + '\n</urlset>\n')
    sito.scrivi(DOCS / 'site.webmanifest', manifest())
    sito.scrivi(DOCS / '404.html', pagina_404())
    print('seo: %d pagine scritte (%d cambiate), sitemap con %d indirizzi' % (len(scelte), cambiate, len(voci)))


if __name__ == '__main__':
    main()
