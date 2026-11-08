"""Controlla che il numero in home di ogni pagina (docs/temi.json, campo "numero")
compaia davvero nel testo visibile della pagina.
Uso (server locale acceso su http://localhost:8796, radice docs/):
    python -I -X utf8 strumenti/controlla_numeri_home.py [porta]
Stampa solo le pagine dove il valore non si trova. Nessun risultato = tutto torna.
Serve Playwright con Microsoft Edge."""
import json, os, re, sys
from playwright.sync_api import sync_playwright

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = sys.argv[1] if len(sys.argv) > 1 else '8796'


def norma(s):
    s = s.replace('−', '-').replace('–', '-').replace('‒', '-')
    s = s.replace('’', "'").replace(' ', ' ').replace(' ', ' ')
    return re.sub(r'\s+', '', s).lower()


def main():
    t = json.load(open(os.path.join(R, 'docs', 'temi.json'), encoding='utf-8'))
    errori = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge')
        pg = b.new_page()
        for p in t['pagine']:
            n = p.get('numero')
            if not n:
                continue
            try:
                pg.goto('http://localhost:%s/%s' % (PORTA, p['path']), wait_until='networkidle', timeout=30000)
                pg.evaluate("document.querySelectorAll('details').forEach(function(d){d.open=true})")
                pg.wait_for_timeout(300)
                testo = norma(pg.inner_text('body'))
            except Exception as e:
                errori.append((p['path'], n['valore'], 'pagina non aperta: %s' % e))
                continue
            if norma(n['valore']) not in testo:
                errori.append((p['path'], n['valore'], n['testo']))
        b.close()
    for path, v, tx in errori:
        print('%s  valore «%s» non trovato  (%s)' % (path, v, tx))
    print('%d pagine da sistemare' % len(errori))


if __name__ == '__main__':
    main()
