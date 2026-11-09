"""Testo statico per Google: scrive nell'HTML quello che oggi compare solo dopo il JavaScript.

Per ogni pagina di docs/ (mai docs/anteprima/):
- la apre con Playwright (Edge, 1000 px) dal server locale (http://localhost:8796, deve essere acceso),
  aspetta che sia disegnata e copia, nell'ordine in cui compaiono:
    * la frase d'apertura (solo se il JavaScript la cambia rispetto all'HTML);
    * i numeri in alto, ognuno con la sua frase (il contenitore .hl; in dati-importanti e milano-trema i loro);
    * i titoli dei grafici (gli h3 dentro ogni .fig), con il link all'ancora del grafico se esiste;
- li scrive in un blocco <!--statico--><div class="statico">...</div><!--/statico--> subito dopo la frase
  d'apertura (o dopo l'h1). E' HTML semplice: un elenco dei numeri, un elenco dei grafici.
- per la home il blocco e' l'elenco di tutte le pagine per tema, da docs/temi.json.
docs/menu.js, appena parte, toglie gli elementi .statico: chi ha JavaScript vede la pagina di sempre,
chi non lo ha (Google compreso, al primo passaggio) legge lo stesso testo. Il testo e' identico a quello
visibile, non e' un trucco.
Ogni volta il file viene riletto subito prima di scrivere (altri programmi possono averlo cambiato).

Uso: python -I -X utf8 strumenti/statico.py [pagina ...]   (senza nomi: tutte)
     python -I -X utf8 strumenti/statico.py --prova pagina ...   (stampa il blocco, non scrive)
"""
import html, json, re, sys, pathlib
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sito
from sito import DOCS, LOCALE

e = lambda s: html.escape(s, quote=False)
ea = lambda s: html.escape(s, quote=True)

ATTESA_JS = """() => {
  const vuoti = [...document.querySelectorAll('.fig')].filter(f => f.getClientRects().length).map(f => f.querySelector('h3,h4'))
    .filter(h => h && !h.innerText.trim());
  const hl = document.querySelector('.hl, #hl');
  return vuoti.length === 0 && (!hl || hl.children.length > 0);
}"""

ESTRAI_JS = r"""async () => {
  document.querySelectorAll('.statico').forEach(x => x.remove());
  document.querySelectorAll('details').forEach(d => d.open = true);
  const H = document.documentElement.scrollHeight;
  for (let y = 0; y < H; y += Math.max(400, innerHeight * 0.8)) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
  scrollTo(0, 0); await new Promise(r => setTimeout(r, 300));
  const pul = s => (s || '').replace(/ /g, ' ').replace(/↓ il grafico|↓ la mappa/g, '').replace(/\s+/g, ' ').trim();
  const dentroMenu = el => !!el.closest('#mid-menu,#mid-vicine,#mid-panel');
  const visibile = el => el.getClientRects().length > 0;
  // numero con la sua unita': "481" + "kg" -> "481 kg"
  function numero(el) {
    let out = '';
    el.childNodes.forEach(n => {
      const t = pul(n.textContent);
      if (!t) return;
      out += (out && /^[A-Za-zÀ-ÖØ-öø-ÿ€]/.test(t) ? ' ' : '') + t;
    });
    return out;
  }
  const R = {};
  const h1 = document.querySelector('h1');
  R.h1 = h1 ? pul(h1.innerText) : '';
  // frase d'apertura: .lead, oppure il primo paragrafo dopo l'h1
  let lead = document.querySelector('.lead');
  if (!lead && h1) {
    lead = [...document.querySelectorAll('p')].find(p => !dentroMenu(p) && (h1.compareDocumentPosition(p) & Node.DOCUMENT_POSITION_FOLLOWING));
  }
  R.lead = lead ? pul(lead.innerText) : '';
  // numeri in alto
  const nn = [];
  const hl = document.querySelector('.hl, #hl');
  if (hl) [...hl.children].forEach(c => {
    const ne = c.querySelector('.n, .num');
    const pe = c.querySelector('p');
    const a = c.tagName === 'A' ? c : c.querySelector('a');
    let n = ne ? numero(ne) : '', t = pe ? pul(pe.innerText) : '';
    if (!ne && !pe) { t = pul(c.innerText); }
    nn.push({href: a ? a.getAttribute('href') : '', n, t, label: ''});
  });
  document.querySelectorAll('.numeri .numero').forEach(c => {
    const b = c.querySelector('b'), s = c.querySelector('span');
    nn.push({href: '', n: b ? numero(b) : '', t: s ? pul(s.innerText) : '', label: ''});
  });
  document.querySelectorAll('section.sec').forEach(sec => {
    const top = sec.querySelector('.top'); if (!top) return;
    const n = top.querySelector('.n'), fr = top.querySelector('.fr'), sh = sec.querySelector('.sh');
    const no = sh && sh.querySelector('.no');
    nn.push({href: sec.id ? '#' + sec.id : '', n: n ? numero(n) : '', t: fr ? pul(fr.innerText) : '',
             label: sh ? pul(sh.innerText.replace(no ? no.innerText : '', '')) : ''});
  });
  R.numeri = nn.filter(x => x.n || x.t);
  // titoli dei grafici
  R.grafici = [];
  document.querySelectorAll('.fig').forEach(f => {
    if (dentroMenu(f)) return;
    const h = f.querySelector('h3,h4'); if (!h) return;
    const t = pul(h.innerText); if (!t) return;
    const id = h.id || f.id || '';
    R.grafici.push({t, id: id && document.getElementById(id) ? id : ''});
  });
  R.ancore = [...document.querySelectorAll('[id]')].map(x => x.id);
  return R;
}"""


def attendi(pg):
    pg.wait_for_load_state('load')
    try:
        pg.wait_for_load_state('networkidle', timeout=15000)
    except Exception:
        pass
    for _ in range(30):
        if pg.evaluate(ATTESA_JS):
            break
        pg.wait_for_timeout(300)
    pg.wait_for_timeout(500)


def blocco_home():
    T = json.load(open(DOCS / 'temi.json', encoding='utf-8'))
    out = []
    for t in T['temi']:
        if t.get('fuori_home'):
            continue  # riepiloghi e guide: nella home stanno solo nella barra in alto
        voci = [p for p in T['pagine'] if p['tema'] == t['id']]
        if not voci:
            continue
        li = []
        for p in voci:
            x = '<span>%s</span>' % e(p['label'])
            n = p.get('numero')
            if n:
                x += ' <strong>%s</strong> <span>%s</span>' % (e(n['valore']), e(n['testo']))
            if p.get('descrizione'):
                x += ' <span>%s</span>' % e(p['descrizione'])
            x = '<a href="%s">%s</a>' % (ea(p['path']), x)
            li.append('<li>%s</li>' % x)
        out.append('<h2>%s</h2><ul>%s</ul>' % (e(t['nome']), ''.join(li)))
    return '<!--statico--><div class="statico">%s</div><!--/statico-->' % ''.join(out)


def blocco_pagina(info, lead_statico):
    parti = []
    if info['lead'] and sito.pulisci(info['lead']) != sito.pulisci(lead_statico):
        parti.append('<p>%s</p>' % e(info['lead']))
    ancore = set(info['ancore'])
    if info['numeri']:
        li = []
        for x in info['numeri']:
            corpo = ''
            if x['label']:
                corpo += e(x['label']) + ': '
            if x['n']:
                corpo += '<strong>%s</strong> ' % e(x['n'])
            corpo += e(x['t'])
            corpo = corpo.strip()
            h = x['href']
            if h and h.startswith('#') and h[1:] in ancore:
                corpo = '<a href="%s">%s</a>' % (ea(h), corpo)
            li.append('<li>%s</li>' % corpo)
        parti.append('<ul>%s</ul>' % ''.join(li))
    if info['grafici']:
        li = []
        for g in info['grafici']:
            li.append('<li>%s</li>' % ('<a href="#%s">%s</a>' % (ea(g['id']), e(g['t'])) if g['id'] else e(g['t'])))
        parti.append('<ol>%s</ol>' % ''.join(li))
    if not parti:
        return None
    return '<!--statico--><div class="statico">%s</div><!--/statico-->' % ''.join(parti)


def lead_nel_file(s):
    """Il testo della frase d'apertura come sta nell'HTML (senza JavaScript)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(s, 'lxml')
    h1 = soup.find('h1')
    lead = soup.select_one('.lead')
    if not lead and h1:
        lead = h1.find_next('p')
    return lead.get_text(' ') if lead else ''


def punto_di_inserimento(s):
    """Posizione subito dopo la frase d'apertura (o dopo l'h1). s e' il file senza il vecchio blocco."""
    m = re.search(r'</h1>', s)
    if not m:
        raise ValueError('niente h1')
    fine_h1 = m.end()
    rx = re.compile(r'<p\b[^>]*>.*?</p>', re.S)
    lead = re.compile(r'<p\b[^>]*class="[^"]*\blead\b[^"]*"[^>]*>.*?</p>', re.S)
    p = lead.search(s, fine_h1)
    if not p:
        p = rx.search(s, fine_h1)
        if p and (p.start() - fine_h1 > 600 or '<h2' in s[fine_h1:p.start()]):
            p = None
    elif '<h2' in s[fine_h1:p.start()]:
        p = None
    return p.end() if p else fine_h1


def scrivi_blocco(p, blocco):
    """Rilegge il file, toglie il vecchio blocco, mette il nuovo. Restituisce True se ha scritto."""
    f = sito.file_pagina(p)
    s = sito.leggi(f)
    s0 = re.sub(r'<!--statico-->.*?<!--/statico-->', '', s, flags=re.S)
    if blocco is None:
        nuova = s0
    else:
        i = punto_di_inserimento(s0)
        nuova = s0[:i] + blocco + s0[i:]
    return sito.scrivi(f, nuova)


def main():
    args = sys.argv[1:]
    prova = '--prova' in args
    scelte = [a.strip('/') for a in args if not a.startswith('--')] or sito.pagine()
    cambiate = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge')
        ctx = b.new_context(viewport={'width': 1000, 'height': 900}, user_agent=sito.USER_AGENT)
        pg = ctx.new_page()
        for p in scelte:
            if not sito.file_pagina(p).is_file():
                print('manca', p)
                continue
            if not p:
                blocco = blocco_home()
                nn, ng = 'temi.json', 0
            else:
                pg.goto(LOCALE + p + '/?v=statico', wait_until='load')
                attendi(pg)
                info = pg.evaluate(ESTRAI_JS)
                s = re.sub(r'<!--statico-->.*?<!--/statico-->', '', sito.leggi(sito.file_pagina(p)), flags=re.S)
                blocco = blocco_pagina(info, lead_nel_file(s))
                nn, ng = len(info['numeri']), len(info['grafici'])
            if prova:
                print(p or 'home', '|', nn, 'numeri', ng, 'grafici')
                print(blocco)
                continue
            if scrivi_blocco(p, blocco):
                cambiate += 1
            print(p or 'home', '|', nn, 'numeri,', ng, 'grafici')
        b.close()
    print('statico: %d pagine, %d cambiate' % (len(scelte), cambiate))


if __name__ == '__main__':
    main()
