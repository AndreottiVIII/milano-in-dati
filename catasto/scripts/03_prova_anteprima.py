"""Prova l'anteprima a 375 e 1000 px: errori, scorrimento laterale, testi piccoli, numeri cliccabili; scatta le schermate dei grafici.
Uso: python -I -X utf8 catasto/scripts/03_prova_anteprima.py"""
import os, sys, json
from playwright.sync_api import sync_playwright
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL = 'http://localhost:8796/anteprima/catasto/'
OUT = os.path.join(R, 'bozze-grafici', 'nuove-png'); os.makedirs(OUT, exist_ok=True)
FIG = ['t-scala', 't-nuvola', 't-abitante', 't-cambio', 't-linee', 't-prov']
with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    for w in (375, 1000):
        pg = b.new_page(viewport={'width': w, 'height': 800})
        errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until='networkidle'); pg.wait_for_timeout(800)
        info = pg.evaluate('''() => {
          const de = document.documentElement;
          const small = [];
          document.querySelectorAll('main *').forEach(el => {
            if (!el.childNodes.length) return;
            const direct = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
            if (!direct) return;
            const r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
            const fs = parseFloat(getComputedStyle(el).fontSize);
            const inSvg = !!el.closest('svg');
            const scale = inSvg ? (el.closest('svg').getBoundingClientRect().width / (el.closest('svg').viewBox.baseVal.width||1)) : 1;
            if (fs * scale < 12 - 0.01) small.push([el.tagName, (el.textContent||'').trim().slice(0,30), fs*scale]);
          });
          return {sw: de.scrollWidth, cw: de.clientWidth, small: small.slice(0,12), hl: document.querySelectorAll('.hl a').length};
        }''')
        print(w, 'errori:', errs, 'scroll', info['sw'], info['cw'], 'piccoli:', info['small'], 'numeri:', info['hl'])
        # numeri cliccabili
        for i in range(info['hl']):
            pg.evaluate('window.scrollTo(0,0)')
            h = pg.evaluate('(i)=>document.querySelectorAll(".hl a")[i].getAttribute("href")', i)
            pg.click('.hl a >> nth=%d' % i); pg.wait_for_timeout(900)
            top = pg.evaluate('(h)=>document.querySelector(h).getBoundingClientRect().top', h)
            print('  numero', i + 1, h, 'top', round(top))
        if w == 375:
            for k, fid in enumerate(FIG, 1):
                el = pg.locator('#%s' % fid).locator('xpath=ancestor::div[contains(@class,"fig")][1]')
                el.screenshot(path=os.path.join(OUT, 'catasto-%d.png' % k))
            pg.screenshot(path=os.path.join(OUT, 'catasto-0-alto.png'), full_page=False)
        else:
            pg.screenshot(path=os.path.join(OUT, 'catasto-1000.png'), full_page=True)
        pg.close()
    b.close()
