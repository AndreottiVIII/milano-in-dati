"""Assembla gli HTML delle tre pagine (docs/arrivi-partenze, docs/comunita, docs/eta) dalle parti comuni e da html_p1/p2/p3.py.
Uso: python -I -X utf8 pagine_html.py <docs_dir>   (percorso assoluto). I dati li scrive pagina.py."""
import sys, os, importlib.util
here = os.path.dirname(os.path.abspath(__file__))
def load(n):
    sp = importlib.util.spec_from_file_location(n, os.path.join(here, n + ".py")); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
C = load("html_comune")
DOCS = sys.argv[1]
PAGES = [("html_p1", "arrivi-partenze"), ("html_p2", "comunita"), ("html_p3", "eta")]
NAMES = {"arrivi-partenze": "Chi arriva e chi lascia", "comunita": "Le comunità quartiere per quartiere", "eta": "Età e centenari"}
for mod, d in PAGES:
    if not os.path.exists(os.path.join(here, mod + ".py")): continue
    m = load(mod)
    nav = C.NAV
    for k, (_, dd) in enumerate(PAGES, 1):
        t = f'<a href="../{dd}/">{NAMES[dd]}</a>' if dd != d else f'<b>{NAMES[dd]}</b>'
        nav = nav.replace(f"@@N{k}@@", t)
    html = C.HEAD.replace("@@TITOLO@@", m.TITOLO).replace("@@CSS_EXTRA@@", m.CSS)
    body = m.BODY.replace("@@NAV@@", nav)
    js = "<script>\n(function(){\n'use strict';\n" + C.JS_COMUNE + m.JS + "\n})();\n</script>\n"
    html += body + "</main>\n" + C.FOOT_COMUNE + js + "</body></html>\n"
    os.makedirs(os.path.join(DOCS, d), exist_ok=True)
    open(os.path.join(DOCS, d, "index.html"), "w", encoding="utf-8").write(html)
    print(d, len(html))
