"""Scarica i documenti pubblici (PDF) usati come contesto. Uso: python -I -X utf8 02_scarica_documenti.py <cartella_case_vuote>
File non fidati: restano in raw/, mai eseguiti. Pausa di 3 s tra i download, User-Agent dichiarato."""
import sys, os, time, urllib.request, datetime
root = sys.argv[1]
items = [
 ("istat_abitazioni/Today-Abitazioni_01_08-2024.pdf", "https://www.istat.it/wp-content/uploads/2024/08/Today-Abitazioni_01_08-2024.pdf"),
 ("istat_abitazioni/Abitazioni-occupate-Anni-2021-2023.pdf", "https://www.istat.it/wp-content/uploads/2026/02/Abitazioni-occupate-Anni-2021-2023.pdf"),
 ("agenzia_entrate/RI2024_Residenziale_20240521.pdf", "https://www.agenziaentrate.gov.it/portale/documents/20143/263076/RI2024_Residenziale_20240521.pdf/2ac96c07-26a6-6eeb-de79-c7d6428054f3"),
 ("mef_immobili/immobili_2023.pdf", "https://www1.finanze.gov.it/finanze/immobili/public/contenuti/immobili_2023.pdf"),
 ("mef_immobili/immobili_2019.pdf", "https://www1.finanze.gov.it/finanze/immobili/public/contenuti/immobili_2019.pdf"),
 ("mef_immobili/immobili_2026.pdf", "https://www1.finanze.gov.it/finanze/immobili/public/contenuti/immobili_2026.pdf"),
 ("agenzia_entrate/Utilizzo_delle_abitazioni_in_Italia.pdf", "https://www.agenziaentrate.gov.it/portale/documents/20143/5768425/2+L_utilizzo+delle+abitazioni+in+Italia.pdf/ab5ff83c-dc5d-8420-fe34-8afb34110f9f"),
 ("polimi/ComSt_260429_dashboard_Milano_def.pdf", "https://www.polimi.it/fileadmin/user_upload/comunicati_stampa/ComSt_260429_dashboard_Milano_def.pdf"),
]
log = []
for rel, url in items:
    p = os.path.join(root, "raw", rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p): print("gia' presente", rel); continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati research"})
        b = urllib.request.urlopen(req, timeout=120).read()
        open(p, "wb").write(b); print("ok", rel, len(b))
        log.append(f"{datetime.date.today()};{rel};{url};{len(b)}")
    except Exception as e:
        print("ERRORE", rel, e)
    time.sleep(3)
open(os.path.join(root, "raw", "download_log.csv"), "a", encoding="utf-8").write("\n".join(log) + ("\n" if log else ""))
