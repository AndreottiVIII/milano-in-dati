"""Apre la pagina pubblica 'Indicatori' del RAV (SNV) e il riquadro 2.2.a.1 'Punteggio nelle prove', come fa la pagina.

Uso: python -I -X utf8 invalsi_rav_indicatori.py <cartella output> <codice1> [codice2 ...]
Solo GET pubblici, User-Agent dichiarato, un cookie di sessione tecnico, 3 secondi tra le richieste.
"""
import hashlib
import http.cookiejar
import os
import sys
import time
import urllib.request

UA = "milano-in-dati/1.0"
OUT = sys.argv[1]
BASE = "https://snv.pubblica.istruzione.it/SistemaNazionaleValutazione"
DESC = [("2.2.a", "2.2.a.1"), ("2.2.a", "2.2.a.2")]

for cod in sys.argv[2:]:
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", UA)]
    time.sleep(3)
    with op.open(f"{BASE}/scuolaInChiaro.do?dispatch=indicatori&scuolainserita={cod}", timeout=120) as r:
        b = r.read()
        print(cod, "pagina", r.status, len(b))
    for ci, cd in DESC:
        time.sleep(3)
        with op.open(f"{BASE}/mvc/descrittoriNonQs/loadDsc/{ci}/{cd}/", timeout=120) as r:
            b = r.read()
            print(" ", cd, r.status, r.headers.get("Content-Type"), len(b), hashlib.sha256(b).hexdigest()[:12])
            with open(os.path.join(OUT, f"{cod}_{cd}.html"), "wb") as f:
                f.write(b)
