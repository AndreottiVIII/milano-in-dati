"""Costanti e funzioni comuni dei programmi in strumenti/ (anteprime_link, seo, statico, controllo).

Se il sito cambia indirizzo (dominio proprio), si cambia solo BASE qui sotto e si rilancia
strumenti/dopo_pubblicazione.py.
"""
import html, json, pathlib, re

BASE = 'https://andreottiviii.github.io/milano-in-dati/'
LOCALE = 'http://localhost:8796/'
USER_AGENT = 'milano-in-dati/1.0'
R = pathlib.Path(__file__).resolve().parent.parent
DOCS = R / 'docs'
STRUMENTI = R / 'strumenti'
ESCLUSE = {'anteprima'}

AUTORE = {
    '@type': 'Person',
    'name': 'Davide Caniatti',
    'url': 'https://davidecaniatti.com',
    'sameAs': ['https://davidecaniatti.com', 'https://davidecaniatti96.substack.com'],
}

# Descrizioni scritte a mano per le pagine dove la frase d'apertura la riempie il JavaScript
# o e' troppo corta per fare da descrizione.
DESCRIZIONI_FISSE = {
    '': 'Milano raccontata con i dati aperti: oltre cento pagine con grafici, mappe e fonti '
        'su casa, persone, clima, soldi, muoversi e voto, dal 1763 a oggi.',
    'il-sito': 'Quante pagine, grafici, numeri e fonti ci sono in Milano in dati, da dove '
               'vengono i dati e chi ha costruito il sito, Davide Caniatti.',
}

LIMITI_DESC = (120, 160)
PAROLINE = set('a ad al allo alla ai agli alle e ed o ma di del dello della dei degli delle da dal dallo dalla dai dagli dalle in nel nello nella nei negli nelle su sul sulla per tra fra con il lo la i gli le un uno una l d che chi se non più'.split())


def pagine(con_home=True):
    """Le pagine del sito: '' (home) e i nomi delle cartelle di docs/ con index.html, senza anteprima/."""
    out = sorted(d.name for d in DOCS.iterdir()
                 if d.is_dir() and d.name not in ESCLUSE and not d.name.startswith('_')
                 and (d / 'index.html').is_file())
    return [''] + out if con_home else out


def file_pagina(p):
    return DOCS / p / 'index.html' if p else DOCS / 'index.html'


def url_pagina(p):
    return BASE + (p + '/' if p else '')


def leggi(path):
    return pathlib.Path(path).read_text(encoding='utf-8')


def scrivi(path, testo):
    """Scrive solo se il testo e' cambiato (non tocca la data del file inutilmente)."""
    path = pathlib.Path(path)
    if path.exists() and path.read_text(encoding='utf-8') == testo:
        return False
    path.write_text(testo, encoding='utf-8', newline='')
    return True


def sostituisci_blocco(s, nome, blocco, dopo=None):
    """Mette 'blocco' (gia' racchiuso fra <!--nome--> e <!--/nome-->) nel testo s: lo sostituisce se c'e',
    altrimenti lo inserisce dopo il primo dei marcatori in 'dopo' (espressioni regolari) che trova."""
    rx = re.compile(r'<!--%s-->.*?<!--/%s-->' % (nome, nome), re.S)
    if rx.search(s):
        return rx.sub(lambda m: blocco, s, count=1)
    for d in (dopo or []):
        m = re.search(d, s, re.S | re.I)
        if m:
            return s[:m.end()] + blocco + s[m.end():]
    raise ValueError('nessun punto dove inserire il blocco ' + nome)


def senza_blocchi(s, nomi=('seo', 'condividi', 'statico')):
    for n in nomi:
        s = re.sub(r'<!--%s-->.*?<!--/%s-->' % (n, n), '', s, flags=re.S)
    return s


def pulisci(s):
    return re.sub(r'\s+', ' ', (s or '').replace('\xa0', ' ')).strip()


def taglia(t, minimo, massimo):
    """Tronca t a parola intera entro 'massimo' caratteri; se possibile finisce a fine frase."""
    t = pulisci(t)
    if len(t) <= massimo:
        return t
    pezzo = t[:massimo + 1]
    # fine frase fra minimo e massimo
    fine = max(pezzo.rfind('. '), pezzo.rfind('? '), pezzo.rfind('! '))
    if fine + 1 >= minimo:
        return pezzo[:fine + 1]
    pezzo = t[:massimo - 1]
    pezzo = pezzo.rsplit(' ', 1)[0].rstrip(' ,;:–-—(«')
    # mai finire su una parolina (articolo, preposizione...)
    while ' ' in pezzo and pezzo.rsplit(' ', 1)[1].lower().strip(',;:') in PAROLINE:
        pezzo = pezzo.rsplit(' ', 1)[0].rstrip(' ,;:–-—(«')
    return pezzo + '…'


def descrizione(p, testo_html=None):
    """La description di una pagina: quella gia' scritta nella pagina fuori dai blocchi, quella fissa,
    oppure la riga d'apertura sotto l'h1 portata a 120-160 caratteri. Stessa per seo.py e anteprime_link.py."""
    from bs4 import BeautifulSoup
    s = testo_html if testo_html is not None else leggi(file_pagina(p))
    s = senza_blocchi(s)
    m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', s, re.I)
    if m:
        return pulisci(html.unescape(m.group(1)))
    if p in DESCRIZIONI_FISSE:
        return DESCRIZIONI_FISSE[p]
    soup = BeautifulSoup(s, 'lxml')
    h1 = soup.find('h1')
    cand = []
    lead = soup.select_one('.lead')
    if lead:
        cand.append(lead)
    if h1:
        for e in h1.find_all_next('p'):
            if e is lead or e.find_parent(['nav', 'footer', 'details', 'script']):
                continue
            if set(e.get('class') or []) & {'src', 'note', 'sub'}:
                continue
            cand.append(e)
            if len(cand) > 4:
                break
    # ultima risorsa, se la frase d'apertura e' corta: le didascalie dei primi grafici
    cand += soup.select('.fig > .sub')[:3]
    testo = ''
    for e in cand:
        t = pulisci(e.get_text(' '))
        if not t:
            continue
        testo = (testo + ' ' + t).strip() if testo else t
        if len(testo) >= LIMITI_DESC[0]:
            break
    testo = re.sub(r'\s+([.,;:!?])', r'\1', testo)
    return taglia(testo, *LIMITI_DESC) if testo else (pulisci(h1.get_text(' ')) if h1 else 'Milano in dati')
