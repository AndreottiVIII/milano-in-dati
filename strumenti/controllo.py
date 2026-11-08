"""Controllo del sito prima di pubblicare. Apre le pagine con Playwright (Edge) dal server locale
(http://localhost:8796, deve essere acceso) a 375 e a 1000 px e cerca:
  - errori JavaScript;
  - richieste fallite (rete o risposte 4xx/5xx);
  - scorrimento laterale;
  - testi sotto 12 px;
  - ancore rotte (link a #qualcosa che non esiste);
  - parole vietate: "trappol", "IA ", "intelligenza artificiale", "OCR", "Opzione A/B/C", "bozza",
    "Claude" (salvo Claude Sautet);
  - nomi di file (.csv .json .geojson .xlsx .zip .py) nel testo visibile, fuori dai <details> intitolati File o Come e' fatto;
  - testo doppio: un blocco .statico ancora visibile quando la pagina ha il JavaScript acceso.
Stampa un elenco breve (una riga per tipo di problema, con le prime pagine); con --tutto stampa ogni caso.

Uso: python -I -X utf8 strumenti/controllo.py [--tutto] [pagina ...]   (senza nomi: tutte)
Esce con codice 1 se trova qualcosa.
"""
import asyncio, json, pathlib, sys
from playwright.async_api import async_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sito

JS = r"""
async () => {
  document.querySelectorAll('details').forEach(d => d.open = true);
  const de = document.documentElement;
  const H = Math.max(de.scrollHeight, document.body ? document.body.scrollHeight : 0);
  for (let y = 0; y < H; y += Math.max(400, innerHeight * 0.8)) { scrollTo(0, y); await new Promise(r => setTimeout(r, 50)); }
  scrollTo(0, H); await new Promise(r => setTimeout(r, 500)); scrollTo(0, 0); await new Promise(r => setTimeout(r, 200));
  const R = {};
  // scorrimento laterale
  R.scrollW = de.scrollWidth; R.clientW = de.clientWidth;
  R.wide = [];
  if (de.scrollWidth > de.clientWidth + 1) {
    for (const el of document.body.querySelectorAll('*')) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.right > de.clientWidth + 1 && getComputedStyle(el).position !== 'fixed') {
        let p = el.parentElement, dentro = false;
        while (p && p !== document.body) { if (/(auto|scroll|hidden)/.test(getComputedStyle(p).overflowX)) { dentro = true; break; } p = p.parentElement; }
        if (dentro) continue;
        R.wide.push(el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + ' right=' + Math.round(r.right));
        if (R.wide.length > 4) break;
      }
    }
  }
  // testi piccoli, parole vietate, nomi di file
  const RX = [['trappol', /trappol/i], ['IA', /\bIA\b/], ['intelligenza artificiale', /intelligenza artificiale/i],
              ['OCR', /\bOCR\b/], ['Opzione', /\bOpzione [ABC]\b/], ['bozza', /\bbozz[ae]\b/i],
              ['Claude', /\bClaude\b(?! Sautet)/i]];
  const FILE = /[\w\-]+\.(csv|json|geojson|xlsx|zip|py)\b/i;
  R.small = []; R.nSmall = 0; R.parole = []; R.file = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const visti = new Set();
  while (w.nextNode()) {
    const n = w.currentNode, s = n.nodeValue.trim();
    if (!s) continue;
    const el = n.parentElement;
    if (!el || el.closest('script,style,noscript,title')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const rects = el.getClientRects();
    if (!rects.length) continue;
    for (const [k, rx] of RX) {
      const m = s.match(rx);
      if (m) R.parole.push(k + ': «' + s.slice(Math.max(0, m.index - 30), m.index + 40).replace(/\s+/g, ' ') + '»');
    }
    let mf = null;
    for (const m of s.matchAll(new RegExp(FILE.source, 'gi'))) { if (s[m.index - 1] !== '/') { mf = m; break; } }  // dentro un indirizzo web non conta
    if (mf) {
      const det = el.closest('details');
      const tit = det && det.querySelector('summary') ? det.querySelector('summary').innerText.trim() : '';
      if (!/^(File|Come è fatto)/i.test(tit)) R.file.push(mf[0] + ' «' + s.slice(0, 50).replace(/\s+/g, ' ') + '»');
    }
    if (!visti.has(el)) {
      visti.add(el);
      if (parseFloat(cs.opacity) === 0) continue;
      let fs = parseFloat(cs.fontSize);
      if (el instanceof SVGElement) {
        const t = el.closest('text') || el, m = t.getScreenCTM && t.getScreenCTM();
        if (m) fs = fs * Math.sqrt(m.a * m.a + m.b * m.b);
      }
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      if (fs < 11.95) { R.nSmall++; if (R.small.length < 3) R.small.push(fs.toFixed(1) + 'px «' + s.slice(0, 35) + '»'); }
    }
  }
  // ancore rotte
  R.ancore = [];
  for (const a of document.querySelectorAll('a[href^="#"]')) {
    const id = decodeURIComponent(a.getAttribute('href').slice(1));
    if (id && !document.getElementById(id) && !document.getElementsByName(id).length) R.ancore.push('#' + id);
  }
  // testo doppio: blocco statico ancora in pagina e visibile
  R.statico = [...document.querySelectorAll('.statico')].filter(x => x.getClientRects().length).length;
  return R;
}
"""


async def una(browser, p, larghezza, sem):
    async with sem:
        ctx = await browser.new_context(viewport={'width': larghezza, 'height': 800}, user_agent=sito.USER_AGENT)
        pg = await ctx.new_page()
        errori, fallite = [], []
        pg.on('pageerror', lambda x: errori.append(str(x)[:160]))
        pg.on('console', lambda m: errori.append('console: ' + m.text[:160]) if m.type == 'error' else None)
        pg.on('requestfailed', lambda r: fallite.append('%s (%s)' % (r.url[-70:], (r.failure or '')[:30]))
              if 'ERR_ABORTED' not in (r.failure or '') else None)  # richieste interrotte dalla pagina stessa: non sono errori
        pg.on('response', lambda r: fallite.append('%d %s' % (r.status, r.url[-70:])) if r.status >= 400 else None)
        rec = {'p': p, 'w': larghezza}
        try:
            await pg.goto(sito.LOCALE + (p + '/' if p else ''), wait_until='load', timeout=60000)
            try:
                await pg.wait_for_load_state('networkidle', timeout=15000)
            except Exception:
                pass
            await pg.wait_for_timeout(600)
            rec.update(await pg.evaluate(JS))
        except Exception as x:
            errori.append('pagina non caricata: ' + str(x)[:120])
        rec['errori'], rec['fallite'] = errori, fallite
        await ctx.close()
        return rec


def problemi(r):
    out = []
    for x in r['errori']:
        out.append(('errore JS', x))
    for x in r['fallite']:
        out.append(('richiesta fallita', x))
    if r.get('scrollW', 0) > r.get('clientW', 0) + 1:
        out.append(('scorrimento laterale', '%s > %s %s' % (r['scrollW'], r['clientW'], ' '.join(r.get('wide', [])[:2]))))
    if r.get('nSmall'):
        out.append(('testo sotto 12 px', '%d testi, es. %s' % (r['nSmall'], '; '.join(r['small']))))
    for x in r.get('ancore', []):
        out.append(('ancora rotta', x))
    for x in r.get('parole', []):
        out.append(('parola vietata', x))
    for x in r.get('file', []):
        out.append(('nome di file', x))
    if r.get('statico'):
        out.append(('testo doppio (.statico visibile)', str(r['statico'])))
    return out


async def lavora(pagine):
    async with async_playwright() as pw:
        b = await pw.chromium.launch(channel='msedge')
        sem = asyncio.Semaphore(6)
        ris = await asyncio.gather(*[una(b, p, w, sem) for p in pagine for w in (375, 1000)])
        await b.close()
    return ris


def main():
    args = sys.argv[1:]
    tutto = '--tutto' in args
    scelte = [a.strip('/') for a in args if not a.startswith('--')] or sito.pagine()
    ris = asyncio.run(lavora(scelte))
    per_tipo = {}
    for r in ris:
        for tipo, d in problemi(r):
            per_tipo.setdefault(tipo, []).append('%s @%d: %s' % (r['p'] or 'home', r['w'], d))
    if not per_tipo:
        print('controllo: %d pagine a 375 e 1000 px, nessun problema' % len(scelte))
        return 0
    print('controllo: %d pagine a 375 e 1000 px' % len(scelte))
    for tipo, righe in sorted(per_tipo.items()):
        pagine_t = sorted({x.split(' @')[0] for x in righe})
        print('- %s: %d casi in %d pagine' % (tipo, len(righe), len(pagine_t)))
        for x in (righe if tutto else righe[:3]):
            print('    ' + x[:200])
    return 1


if __name__ == '__main__':
    sys.exit(main())
