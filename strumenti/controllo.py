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
  - testo doppio: un blocco .statico ancora visibile quando la pagina ha il JavaScript acceso;
  - pittogrammi a unità: frasi come «ogni quadretto», «ogni pallino = 250», «un omino vale 3.000»,
    «= 1 su 100», «una figurina» (regola di Davide: mai un simbolo che vale N);
  - forme radiali: nei grafici (svg larghi almeno 200 px) archi di cerchio di raggio 25 o più, cioè torte,
    ciambelle, orologi, anelli. Gli archi piccoli (icone, angoli arrotondati) e i piccoli disegni non contano.
    Se una pagina usa un arco grande per altro, si segna l'svg o un suo contenitore con data-arco-ok.
    Contano anche i poligoni radar (vertici su un cerchio), le righe disposte in cerchio (anelli di barre,
    lancette, raggi) e d3.arc / d3.pie / d3.radialLine nel codice della pagina.
    Gli svg in schede nascoste contano con la larghezza dichiarata. Unica eccezione esplicita: #ch-anello nella pagina proverbi.
Stampa un elenco breve (una riga per tipo di problema, con le prime pagine); con --tutto stampa ogni caso.

Uso: python -I -X utf8 strumenti/controllo.py [--tutto] [pagina ...]   (senza nomi: tutte)
Esce con codice 1 se trova qualcosa.
"""
import asyncio, json, pathlib, re, sys
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
  // pittogrammi a unità (testo visibile e descrizioni dei grafici)
  const NOMI = 'quadrett\\w*|pallin\\w*|omin\\w*|casett\\w*|monet\\w*|figurin\\w*|mattoncin\\w*|gocc\\w*|lampadin\\w*|biciclett\\w*|auto|simbol\\w*|puntin\\w*|bottigli\\w*|icon\\w*|cerchiett\\w*|tesser\\w*';
  const PIT = [
    // «ogni quadretto» da solo conta, ma non nei calendari a quadretti (un quadretto = un giorno, un mese...) né in «in ogni quadretto c'è il numero»
    ['ogni quadretto', /(?<!\bin )\bogni quadrett[oi](?![^.;]{0,25}\b(?:giorno|mese|anno|settimana|decennio|stazione|riga|colonna|quartiere|zona|comune)\b)/i],
    ['ogni simbolo = N', new RegExp('\\bogni\\s+(?:' + NOMI + ')(?:\\s+[a-zà-ù]+){0,2}\\s*(?:=|vale|valgono|è|sono|rappresenta)\\s*(?:circa\\s+)?(?:(?:un[oa]?\\s+)?\\d[\\d.]*(?![\\d])|[^.;]{0,25}\\bsu 100\\b)', 'i')],
    ['un simbolo = N', new RegExp('\\bun[oa]?\\s+(?:' + NOMI + ')\\s*(?:=|vale|sono)\\s*(?:circa\\s+)?\\d', 'i')],
    ['= 1 su 100', /(?:=|\bè|\bsono|\bvale)\s*(?:1|un[oa]?\s+\w+) su 100\b/i],
    ['una figurina', /\buna figurina\b/i],
    ['100 simboli', /\b(?:i|le|a|di|su|delle|dei) 100 (?:omin|casett|monet|quadrett|pallin|figurin|mattoncin)\w*/i]];
  R.pitt = [];
  const testi = [];
  const w2 = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (w2.nextNode()) {
    const n = w2.currentNode, el = n.parentElement;
    if (!el || el.closest('script,style,noscript,title')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || !el.getClientRects().length) continue;
    testi.push(n.nodeValue.replace(/\s+/g, ' ').trim());
  }
  document.querySelectorAll('[aria-label],[title]').forEach(e => {
    if (e.closest('script,style')) return;
    testi.push((e.getAttribute('aria-label') || '') + ' ' + (e.getAttribute('title') || ''));
  });
  const visti2 = new Set();
  for (const t of testi) {
    for (const [k, rx] of PIT) {
      const m = t.match(rx);
      if (m && !visti2.has(k + m[0])) { visti2.add(k + m[0]); R.pitt.push(k + ': «' + t.slice(Math.max(0, m.index - 20), m.index + 70) + '»'); }
    }
  }
  // forme radiali: archi grandi nei grafici
  R.arco = [];
  for (const p of document.querySelectorAll('svg path')) {
    const d = p.getAttribute('d') || '';
    if (!/[Aa]/.test(d)) continue;
    const sv = p.closest('svg');
    if (!sv || sv.closest('[data-arco-ok],.leaflet-container')) continue;
    // Eccezione voluta da Davide: l'«anello dell'anno» della pagina proverbi resta radiale. Solo quel grafico.
    if (location.pathname.indexOf('proverbi') >= 0 && sv.closest('#ch-anello')) continue;
    // larghezza reale; se l'svg è in una scheda nascosta (larghezza 0) si usa quella dichiarata (viewBox o width)
    let lar = sv.getBoundingClientRect().width;
    if (!lar) { const vb = (sv.getAttribute('viewBox') || '').split(/[ ,]+/); lar = parseFloat(vb[2]) || parseFloat(sv.getAttribute('width')) || 0; }
    if (lar < 200) continue;
    let grande = 0;
    for (const m of d.matchAll(/[Aa]\s*(-?[\d.]+)[ ,]+(-?[\d.]+)/g)) grande = Math.max(grande, Math.abs(parseFloat(m[1])), Math.abs(parseFloat(m[2])));
    if (grande >= 25) {
      const box = sv.parentElement;
      R.arco.push((box && box.id ? '#' + box.id : 'svg') + ' raggio ' + Math.round(grande));
      if (R.arco.length > 3) break;
    }
  }
  // forme radiali fatte di linee e poligoni (radar, anelli di barre, orologi a lancette): punti che stanno su un cerchio
  // e lo coprono quasi tutto. Righe in fila, assi e griglie rettangolari non hanno questa forma.
  const suCerchio = (pts) => {
    const uniq = [], vistiP = new Set();
    for (const q of pts) { const k = Math.round(q[0]) + ',' + Math.round(q[1]); if (!vistiP.has(k)) { vistiP.add(k); uniq.push(q); } }
    if (uniq.length < 6) return 0;
    const mx = uniq.reduce((a, q) => a + q[0], 0) / uniq.length, my = uniq.reduce((a, q) => a + q[1], 0) / uniq.length;
    const rs = uniq.map(q => Math.hypot(q[0] - mx, q[1] - my)), rm = rs.reduce((a, b) => a + b, 0) / rs.length;
    if (rm < 25) return 0;
    const sd = Math.sqrt(rs.reduce((a, r) => a + (r - rm) * (r - rm), 0) / rs.length);
    if (sd / rm > 0.12) return 0;
    const an = uniq.map(q => Math.atan2(q[1] - my, q[0] - mx)).sort((a, b) => a - b);
    let gap = an[0] + 2 * Math.PI - an[an.length - 1];
    for (let i = 1; i < an.length; i++) gap = Math.max(gap, an[i] - an[i - 1]);
    return gap < Math.PI * 0.55 ? Math.round(rm) : 0;
  };
  for (const sv of document.querySelectorAll('svg')) {
    if (sv.closest('[data-arco-ok],.leaflet-container')) continue;
    if (location.pathname.indexOf('proverbi') >= 0 && sv.closest('#ch-anello')) continue;
    let lar = sv.getBoundingClientRect().width;
    if (!lar) { const vb = (sv.getAttribute('viewBox') || '').split(/[ ,]+/); lar = parseFloat(vb[2]) || parseFloat(sv.getAttribute('width')) || 0; }
    if (lar < 200) continue;
    const nome = () => { const box = sv.parentElement; return box && box.id ? '#' + box.id : 'svg'; };
    const num = (e, a) => parseFloat(e.getAttribute(a));
    const L1 = [], L2 = [];
    for (const l of sv.querySelectorAll('line')) {
      const a = [num(l, 'x1'), num(l, 'y1')], b = [num(l, 'x2'), num(l, 'y2')];
      if (a.concat(b).some(isNaN) || Math.hypot(a[0] - b[0], a[1] - b[1]) < 3) continue;
      L1.push(a); L2.push(b);
    }
    let r = suCerchio(L1) || suCerchio(L2);
    if (r) { R.arco.push(nome() + ' righe disposte in cerchio (raggio ' + r + ')'); continue; }
    for (const pg of sv.querySelectorAll('polygon,polyline')) {
      const pts = (pg.getAttribute('points') || '').trim().split(/[\s]+/).map(s => s.split(',').map(parseFloat)).filter(q => q.length === 2 && !isNaN(q[0]) && !isNaN(q[1]));
      r = suCerchio(pts);
      if (r) { R.arco.push(nome() + ' poligono radar (raggio ' + r + ')'); break; }
    }
  }
  // d3.arc / d3.pie / d3.radialLine nel codice della pagina
  for (const sc of document.querySelectorAll('script:not([src])')) {
    const m = (sc.textContent || '').match(/\bd3\s*\.\s*(arc|pie|lineRadial|areaRadial|radialLine|radialArea)\s*\(/);
    if (m) R.arco.push('script con d3.' + m[1]);
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
    for x in r.get('pitt', []):
        out.append(('pittogramma a unità', x))
    for x in sorted(set(r.get('arco', []))):
        out.append(('forma radiale (arco, poligono radar, righe in cerchio, d3.arc/pie)', x))
    if r.get('statico'):
        out.append(('testo doppio (.statico visibile)', str(r['statico'])))
    return out


async def lavora(pagine):
    async with async_playwright() as pw:
        b = await pw.chromium.launch(channel='msedge')
        sem = asyncio.Semaphore(3)  # con più pagine insieme il server locale rifiuta qualche richiesta
        ris = await asyncio.gather(*[una(b, p, w, sem) for p in pagine for w in (375, 1000)])
        await b.close()
    return ris


def controllo_testa(scelte):
    """Controllo statico della testa: un solo canonical e un solo og:url, uguali tra loro e uguali a BASE + pagina;
    nessun indirizzo assoluto del sito scritto a mano fuori dai blocchi <!--seo--> e <!--condividi-->."""
    out = []
    dominio = sito.BASE.split('/')[2]
    for p in scelte:
        f = sito.file_pagina(p)
        if not f.is_file():
            continue
        s = sito.leggi(f)
        testa = s.split('</head>')[0]
        can = re.findall(r'<link\s+rel="canonical"\s+href="([^"]*)"', testa)
        ogu = re.findall(r'<meta\s+property="og:url"\s+content="([^"]*)"', testa)
        atteso = sito.url_pagina(p)
        if can != [atteso]:
            out.append(('canonical sbagliato o doppio', p, '%s (atteso %s)' % (can, atteso)))
        if ogu != [atteso]:
            out.append(('og:url sbagliato o doppio', p, '%s (atteso %s)' % (ogu, atteso)))
        fuori = sito.senza_blocchi(s)
        for d in (dominio, 'andreottiviii.github.io'):
            if d in fuori:
                out.append(('indirizzo assoluto scritto a mano', p, d))
                break
    return out


def main():
    args = sys.argv[1:]
    tutto = '--tutto' in args
    scelte = [a.strip('/') for a in args if not a.startswith('--')] or sito.pagine()
    ris = asyncio.run(lavora(scelte))
    per_tipo = {}
    for tipo, p, d in controllo_testa(scelte):
        per_tipo.setdefault(tipo, []).append('%s @0: %s' % (p or 'home', d))
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
