"""Riserva lo spazio dei riquadri e dei grafici disegnati con JavaScript, per non far saltare la pagina.

Ogni pagina disegna numeri e grafici dopo aver scaricato i file di dati: al primo disegno i contenitori
sono vuoti e, quando si riempiono, tutto il resto scende (Cumulative Layout Shift). Per ogni pagina e
per due larghezze (375x760 telefono, 1280x800 computer) il programma:
- apre la pagina dal server locale (http://localhost:8796, deve essere acceso) trattenendo i dati
  (/data/, .json .csv .geojson .topojson .txt, tile.openstreetmap.org; le librerie cdnjs/unpkg/jsdelivr passano,
  perche' a volte sono script che bloccano la pagina);
- misura l'altezza dei contenitori con id senza figli (stato "prima");
- rilascia i dati, aspetta la fine del caricamento e misura di nuovo (stato "dopo");
- tiene i contenitori cresciuti di almeno 24 px che a fine caricamento hanno almeno un figlio
  (quelli che restano vuoti crescono per testo e si scartano);
- scrive nella <head> un blocco <!--riserva--><style>...</style><!--/riserva--> con min-height
  per i soli contenitori ancora vuoti (:not(:has(*))): la riserva sparisce da sola quando si riempiono.
Il blocco si puo' rilanciare quante volte si vuole: viene sostituito (o tolto se non servono riserve).

Uso: python -I -X utf8 strumenti/riserva_spazio.py [pagina ...]   (senza nomi: tutte le pagine della sitemap;
     '' o '/' = home; i nomi sono come 'anziani' o 'anziani/')
"""
import pathlib, re, sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sito
from sito import DOCS, LOCALE

SOGLIA = 24
TRATTIENI = re.compile(r'(/data/|\.(json|csv|geojson|topojson|txt)(\?|$)|tile\.openstreetmap\.org)', re.I)
# le librerie (cdnjs, unpkg, jsdelivr) NON si trattengono: a volte sono script che bloccano la pagina e DOMContentLoaded non scatterebbe

RX_RISERVA = re.compile(r'<!--riserva-->.*?<!--/riserva-->', re.S)

MISURA_JS = r"""() => {
  // tutta la pagina, non solo dentro <main>: in home il contenitore vuoto e' proprio <main id="temi">
  const radice = document.body;
  const out = {};
  for (const el of radice.querySelectorAll('[id]')) {
    if (el.children.length !== 0) continue;
    if (/^(INPUT|SELECT|OPTION|BUTTON|A|SPAN|svg|SCRIPT|STYLE)$/i.test(el.tagName) || el.closest('svg')) continue;
    if (el.closest('#mid-menu, #mid-ck, #mid-cita, .tip, [role=tooltip], [class*=tooltip]')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.position === 'fixed' || cs.position === 'absolute') continue;
    out[el.id] = el.getBoundingClientRect().height;
  }
  return out;
}"""

FINALE_JS = r"""(ids) => {
  const o = {};
  for (const id of ids) {
    const el = document.getElementById(id);
    o[id] = el ? [el.getBoundingClientRect().height, el.children.length] : [0, 0];
  }
  return o;
}"""


# riserva massima: oltre questa altezza il contenitore e' comunque fuori dallo schermo al primo disegno,
# e se i dati non arrivassero la pagina resterebbe lunghissima e vuota
TETTO = 1500

MENU_JS = """(() => { const m = document.getElementById('mid-menu'); if (!m) return 0;
  const cs = getComputedStyle(m); if (cs.position === 'fixed' || cs.position === 'absolute') return 0;
  return Math.round(m.getBoundingClientRect().height + parseFloat(cs.marginTop || 0) + parseFloat(cs.marginBottom || 0)); })()"""


def misura(browser, p, w, h):
    """Restituisce {id: altezza_dopo - altezza_prima} per i candidati a questa larghezza."""
    ctx = browser.new_context(viewport={'width': w, 'height': h})
    pg = ctx.new_page()
    trattenute = []
    stato = {'libero': False}

    def gestore(route):
        req = route.request
        if req.resource_type == 'document' and req.frame.parent_frame is None:
            # la pagina si misura SENZA il blocco riserva gia' scritto (altrimenti il risultato cambierebbe a ogni giro)
            r = route.fetch()
            corpo = RX_RISERVA.sub('', r.text())
            route.fulfill(response=r, body=corpo)
        elif TRATTIENI.search(req.url):
            # finche' non e' il momento le richieste restano ferme; dopo passano subito
            if stato['libero']:
                route.continue_()
            else:
                trattenute.append(route)
        else:
            route.continue_()
    pg.route('**/*', gestore)
    try:
        pg.goto(LOCALE + (p + '/' if p else ''), wait_until='domcontentloaded')
        pg.wait_for_timeout(400)
        prima = pg.evaluate(MISURA_JS)
        stato['libero'] = True
        for r in trattenute:
            try:
                r.continue_()
            except Exception as ex:
                print('   (richiesta non rilasciata: %s)' % str(ex)[:80])
        try:
            pg.wait_for_load_state('networkidle', timeout=20000)
        except Exception:
            pass
        pg.wait_for_timeout(1000)
        # aspetta che i contenitori smettano di riempirsi (il disegno puo' arrivare in ritardo)
        dopo, ultimo = None, -1
        for _ in range(16):
            dopo = pg.evaluate(FINALE_JS, list(prima))
            pieni = sum(1 for v in dopo.values() if v[1] > 0)
            if pieni == ultimo:
                break
            ultimo = pieni
            pg.wait_for_timeout(700)
        # altezza della barra del menu (la inserisce menu.js: se arriva dopo il primo disegno, sposta tutta la pagina)
        menu = pg.evaluate(MENU_JS)
    finally:
        ctx.close()
    ris = {}
    for i, a in prima.items():
        d, figli = dopo[i]
        if figli == 0:
            continue  # resta vuoto: cresce per testo, non si riserva
        if int(d - a) >= SOGLIA:
            ris[i] = min(int(d), TETTO)
    return ris, menu


def selettore(i):
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', i):
        return '#' + i
    return '[id="%s"]' % i.replace(chr(92), chr(92) * 2).replace('"', chr(92) + '"')


def blocco(tel, pc, menu_tel=0, menu_pc=0):
    # Sempre presente, anche senza riserve:
    # - classe "js" su <html> appena parte la pagina, cosi' il testo .statico (per chi non ha JavaScript)
    #   non compare per un attimo prima che menu.js lo tolga (era la causa dei salti in home e il-tuo-giorno);
    # - spazio per la barra del menu finche' menu.js non l'ha inserita.
    css = '.js .statico{display:none}'
    if menu_tel:
        css += '@media (max-width:599px){.js body:not(:has(#mid-menu))::before{content:"";display:block;height:%dpx}}' % menu_tel
    if menu_pc:
        css += '@media (min-width:600px){.js body:not(:has(#mid-menu))::before{content:"";display:block;height:%dpx}}' % menu_pc
    if tel:
        css += '@media (max-width:599px){' + ''.join('%s:not(:has(*)){min-height:%dpx}' % (selettore(i), v) for i, v in tel.items()) + '}'
    if pc:
        css += '@media (min-width:600px){' + ''.join('%s:not(:has(*)){min-height:%dpx}' % (selettore(i), v) for i, v in pc.items()) + '}'
    return ('<!--riserva--><script>document.documentElement.classList.add("js")</script>'
            '<style>' + css + '</style><!--/riserva-->')


def leggi_grezzo(f):
    # senza tradurre i fine riga
    with open(f, encoding='utf-8', newline='') as fh:
        return fh.read()


def scrivi_pagina(p, b):
    f = sito.file_pagina(p)
    s = leggi_grezzo(f)
    s = sito.senza_blocchi(s, ('riserva',))
    if b:
        i = s.lower().rfind('</head>')
        if i < 0:
            raise ValueError('manca </head>')
        s = s[:i] + b + s[i:]
    if leggi_grezzo(f) != s:
        with open(f, 'w', encoding='utf-8', newline='') as fh:
            fh.write(s)


def main():
    nomi = [a for a in sys.argv[1:] if not a.startswith('--')]
    if nomi:
        elenco = [n.strip('/') for n in nomi]
    else:
        elenco = sito.pagine()
    with sync_playwright() as pw:
        br = pw.chromium.launch(channel='msedge')
        for p in elenco:
            try:
                tel, mt = misura(br, p, 375, 760)
                pc, mp = misura(br, p, 1280, 800)
                scrivi_pagina(p, blocco(tel, pc, mt, mp))
                print('%-34s telefono %d  computer %d' % (p or '(home)', len(tel), len(pc)), flush=True)
            except Exception as ex:
                print('%-34s ERRORE: %s' % (p or '(home)', ex), flush=True)
        br.close()


if __name__ == '__main__':
    main()
