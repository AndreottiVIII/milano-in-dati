"""Anteprime dei link (quando si condivide una pagina su WhatsApp, social, ecc.).

Per ogni pagina di docs/:
- legge dal sito in locale (http://localhost:8796, il server deve essere acceso) il titolo e il primo
  numero grande della pagina, con la sua frase; se non c'e', usa il numero di temi.json;
- disegna un'immagine 1200x630 nello stile scelto da Davide (opzione A: bianca, striscia dei colori
  del metro', numero nel riquadro del colore del tema, favicon e "Milano in dati" in basso);
- la salva come docs/<pagina>/condividi.png (la home: docs/condividi.png);
- scrive nella pagina i meta Open Graph e Twitter tra <!--condividi--> e <!--/condividi-->
  (si puo' rilanciare quante volte si vuole: il blocco viene sostituito).

Uso: python -I -X utf8 strumenti/anteprime_link.py [pagina ...]   (senza nomi: tutte)
Il modello grafico e' bozze-grafici/anteprime-link/modello.html. Se il sito cambia indirizzo, cambiare BASE.
"""
import html, json, os, pathlib, re, sys
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

BASE = 'https://andreottiviii.github.io/milano-in-dati/'
LOCALE = 'http://localhost:8796/'
R = pathlib.Path(__file__).resolve().parent.parent
DOCS = R / 'docs'
MODELLO = (R / 'bozze-grafici' / 'anteprime-link' / 'modello.html').as_uri()
ESCLUSE = {'anteprima'}

temi = json.load(open(DOCS / 'temi.json', encoding='utf-8'))
COL = {t['id']: (t['colore'], t['testo']) for t in temi['temi']}
TEMA = {p['path'].strip('/'): p for p in temi['pagine']}


def pagine():
    out = [''] + sorted(d.name for d in DOCS.iterdir()
                        if d.is_dir() and d.name not in ESCLUSE and not d.name.startswith('_') and (d / 'index.html').is_file())
    return out


def pulisci(s):
    return re.sub(r'\s+', ' ', (s or '').replace('↓ il grafico', '').replace('↓ la mappa', '')).strip()


def dati_pagina(pg, p):
    pg.goto(LOCALE + (p + '/' if p else '') + '?v=condividi', wait_until='load')
    pg.wait_for_timeout(1800)
    info = pg.evaluate("""() => {
      const h1 = document.querySelector('h1');
      const box = document.querySelector('#hl, .hl');
      let n = '', t = '';
      if (box && box.children.length) {
        const c = box.children[0];
        const ne = c.querySelector('.n, .num, b, strong');
        n = ne ? ne.innerText : '';
        const pe = c.querySelector('p');
        t = pe ? pe.innerText : c.innerText.replace(n, '');
      }
      const d = document.querySelector('meta[name="description"]');
      return {h1: h1 ? h1.innerText : document.title, n, t, desc: d ? d.content : ''};
    }""")
    return info


def numero_home():
    c = json.load(open(DOCS / 'il-sito' / 'data' / 'conti.json', encoding='utf-8'))
    mil = c['numeri'] / 1e6
    n = ('%.1f' % mil).replace('.', ',') + ' milioni'
    t = 'di numeri sulla città in %d grafici e %d pagine, da %d fonti. Dal %d a oggi.' % (
        c['grafici'], c['pagine'], c['fonti'], c['anno_da'])
    return n, t


def blocco(p, titolo, desc, alt, ha_desc):
    url = BASE + (p + '/' if p else '')
    img = url + 'condividi.png'
    e = lambda s: html.escape(s, quote=True)
    righe = []
    if not ha_desc:
        righe.append('<meta name="description" content="%s">' % e(desc))
    righe += [
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Milano in dati">',
        '<meta property="og:locale" content="it_IT">',
        '<meta property="og:title" content="%s">' % e(titolo),
        '<meta property="og:description" content="%s">' % e(desc),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:image" content="%s">' % img,
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="%s">' % e(alt),
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % e(titolo),
        '<meta name="twitter:description" content="%s">' % e(desc),
        '<meta name="twitter:image" content="%s">' % img,
    ]
    return '<!--condividi-->' + ''.join(righe) + '<!--/condividi-->'


def scrivi_meta(path, b):
    s = path.read_text(encoding='utf-8')
    if '<!--condividi-->' in s:
        s = re.sub(r'<!--condividi-->.*?<!--/condividi-->', lambda m: b, s, flags=re.S)
    else:
        m = re.search(r'<title>.*?</title>', s, re.S) or re.search(r'<meta charset[^>]*>', s, re.I)
        s = s[:m.end()] + b + s[m.end():]
    path.write_text(s, encoding='utf-8', newline='')


def main():
    scelte = [a.strip('/') for a in sys.argv[1:]] or pagine()
    fav = (DOCS / 'favicon.svg').read_text(encoding='utf-8')
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge')
        sito = b.new_context(viewport={'width': 1000, 'height': 900})
        img = b.new_context(viewport={'width': 1200, 'height': 630})
        img.add_init_script('window.FAV=' + json.dumps(fav))
        ps, pi = sito.new_page(), img.new_page()
        for p in scelte:
            f = DOCS / p / 'index.html' if p else DOCS / 'index.html'
            if not f.is_file():
                print('manca', p); continue
            info = dati_pagina(ps, p)
            tema = TEMA.get(p, {})
            colore, testo = COL.get(tema.get('tema'), ('#E30613', '#fff'))
            titolo = pulisci(info['h1'])
            if len(titolo) > 48 and tema.get('label'):
                titolo = tema['label']
            if not p:
                titolo = 'Milano in dati'
                n, t = numero_home()
            elif p == 'dati-importanti':
                titolo = 'Milano nei dati più importanti'
                n, t = '12 numeri', "per capire com'è cambiata la città: casa, persone, soldi, clima e voto."
            elif p == 'il-sito':
                n, t = numero_home()
            else:
                n, t = pulisci(info['n']), pulisci(info['t'])
                n = re.sub(r'(\d)([A-Za-zÀ-ÿ])', r'\1 \2', n)
                if (not n or len(n) > 14) and tema.get('numero'):
                    n, t = tema['numero']['valore'], tema['numero']['testo']
                if not n:
                    n, t = '', pulisci(tema.get('descrizione', '')) or 'I numeri di Milano, con le fonti.'
            if len(t) > 140:
                t = t[:137].rsplit(' ', 1)[0] + '…'
            pi.goto(MODELLO + '?' + urlencode(dict(v='A', t=titolo, n=n or '·', p=t, c=colore, tx=testo)))
            pi.wait_for_selector('body[data-ok]')
            if not n:
                pi.evaluate("document.querySelector('.box').style.display='none'")
            pi.wait_for_timeout(150)
            out = (DOCS / p / 'condividi.png') if p else (DOCS / 'condividi.png')
            pi.screenshot(path=str(out))
            desc = (info['desc'] or ((n + ' ' + t).strip() if n else t))[:160]
            titolo_og = titolo if not p else titolo + ' · Milano in dati'
            alt = (titolo + ': ' + (n + ' ' + t if n else t)).strip()
            scrivi_meta(f, blocco(p, titolo_og, desc, alt, bool(info['desc'])))
            print(p or 'home', '|', n, '|', t[:60])
        b.close()


if __name__ == '__main__':
    main()
