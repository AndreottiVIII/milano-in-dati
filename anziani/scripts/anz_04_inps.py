"""INPS, Osservatorio sui lavoratori domestici (dati annuali 2016-2025).
Interroga la banca dati interattiva pubblica come fa la pagina stessa (stessa richiesta del pulsante
"Dati annuali"), da dentro la pagina aperta in un browser. Ok di Davide del 15/11/2026.
Uso: python -I -X utf8 anziani/scripts/anz_04_inps.py  -> anziani/raw/inps/q_<nome>.json"""
import json, sys
from playwright.sync_api import sync_playwright
O = 'C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/anziani/raw/inps/'
def sel(rows, filters=None):
    return {"id_osservatorio": "350", "nome_osservatorio": "Dati annuali", "language": "", "totalRow": True, "totalColumn": True,
            "subtotalRow": True, "subtotalColumn": True,
            "selections": {"rows": [{"id": r, "label": r, "order": i + 1, "aggregate": True, "expand": "", "hide": False} for i, r in enumerate(rows)],
                           "cols": [{"id": "Anno-", "label": "Anno-", "aggregate": False, "order": 1, "expand": "", "hide": False}],
                           "measures": [{"id": "numeroSUM", "label": "numeroSUM", "order": 0, "statistic": "SUM"}],
                           "filters": filters or []}}
Q = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge'); pg = b.new_context(user_agent='milano-in-dati/1.0').new_page()
    pg.goto('https://servizi2.inps.it/servizi/osservatoristatistici/12', timeout=60000); pg.wait_for_timeout(4000)
    for nome, rows in Q.items():
        body = sel(rows)
        r = pg.evaluate("""async b => { const r = await fetch('/servizi/osservatoristatistici/api/getDatiOsservatorio/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(b)}); return [r.status, await r.text()] }""", body)
        open(O + 'q_' + nome + '.json', 'w', encoding='utf-8').write(r[1]); print(nome, r[0], len(r[1]))
        pg.wait_for_timeout(1500)
    b.close()
