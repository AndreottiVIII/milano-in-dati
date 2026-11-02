"""Scarica da statistica.cultura.gov.it (MiC, Ufficio Statistica) le tavole 'Visitatori e introiti 2024'
(xlsx) e il PDF di Regione Lombardia sui visitatori dei musei riconosciuti 2024. Pausa 5 s, User-Agent onesto.
uso: python -I -X utf8 04_scarica_mic.py <cartella musei assoluta>"""
import sys, os, time, urllib.request, datetime
base = sys.argv[1]
UA = {"User-Agent": "milano-in-dati research (musei fase 1)"}
voci = [("mic", "https://statistica.cultura.gov.it/wp-content/uploads/2025/05/MUSEI_TAVOLA%d_2024-1.xlsx" % n) for n in (1, 2, 3, 7, 8)]
voci.append(("regione_lombardia", "https://www.musei.regione.lombardia.it/wps/wcm/connect/7d32c541-8248-4574-ad17-ae99aa46cd4a/Rilevazione+visitatori+2024.pdf?MOD=AJPERES&CACHEID=ROOTWORKSPACE-7d32c541-8248-4574-ad17-ae99aa46cd4a-pYoWWk0"))
log = open(os.path.join(base, "raw", "download_log.csv"), "a", encoding="utf-8")
for sub, url in voci:
    fn = os.path.join(base, "raw", sub, url.split("?")[0].rsplit("/", 1)[1].replace("+", "_"))
    if os.path.exists(fn): continue
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as f: data = f.read()
    open(fn, "wb").write(data)
    log.write(f"{datetime.date.today()};{url};{fn};{len(data)};licenza non dichiarata nella pagina\n"); log.flush()
    print(fn, len(data)); time.sleep(5)
