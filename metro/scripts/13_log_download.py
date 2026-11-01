"""Registro dei file scaricati in raw/ (nome, URL di origine, dimensione, sha256, data). Gli URL sono quelli usati dagli script 02, 05 e dai download manuali (curl)
di PDF e pagine web, elencati qui. Uso: python -I -X utf8 13_log_download.py <metro_dir>"""
import sys, os, csv, hashlib, datetime
M = sys.argv[1]
ATM = "https://www.atm.it/it/IlGruppo/ChiSiamo/Documents/"
SRC = {
 "pdf/Report-della-Mobilita-2024_cleancities.pdf": "https://italy.cleancitiescampaign.org/wp-content/uploads/2025/11/Report-della-Mobilita-2024.pdf (copia ospitata da Clean Cities Campaign; autore AMAT)",
 "pdf/ATM_RFA2025.pdf": "https://risultati.atm.it/2025/sites/default/files/documents/GruppoAtm-RFA2025.pdf",
 "pdf/ATM_RFA2024.pdf": "https://risultati.atm.it/2024/sites/default/files/documents/ATM-2024-RELAZIONE-FINANZIARIA-ANNUALE-INTEGRATA.pdf",
 "pdf/ATM_2025_profilo.pdf": "https://risultati.atm.it/2025/sites/default/files/documents/ATM-1-Profilo_0.pdf",
 "pdf/ATM_2024_profilo.pdf": "https://risultati.atm.it/2024/sites/default/files/documents/ATM2024-1-Profilo_0.pdf",
 "pdf/ATM_2023_gestione_operativa.pdf": "https://risultati.atm.it/2023/files/5_ATM-Gestioneoperativa.pdf",
 "pdf/ATM_bilancio2021.pdf": "https://risultati.atm.it/2021/files/12_BILANCIO_minisito_def.pdf",
 "pdf/ATM_bilancio2020.pdf": "https://risultati.atm.it/2020/files/BILANCIO_GRUPPO_ATM_2020.pdf",
 "pdf/ATM_bilancio_finanziario_interno.pdf": "https://www.atm.it/it/IlGruppo/Financial_information/Documents/ATM_bilancio_finanziario_interno_web_.pdf (e' il bilancio 2018)",
 "web_probe/wiki_metropolitana_di_milano.wikitext": "https://it.wikipedia.org/w/index.php?title=Metropolitana_di_Milano&action=raw",
 "web_probe/wiki_stazioni.wikitext": "https://it.wikipedia.org/w/index.php?title=Stazioni_della_metropolitana_di_Milano&action=raw",
 "web_probe/amat_report_mobilita.html": "https://www.amat-mi.it/it/progetti/report-mobilita/",
 "web_probe/amat_notizia168.html": "https://www.amat-mi.it/it/notizie/168/",
 "web_probe/atm_carta_mobilita.html": "https://www.atm.it/it/IlGruppo/ChiSiamo/Pagine/CartaMobilita.aspx",
 "lombardia_trenord/m2u2-frtq.csv": "https://www.dati.lombardia.it/resource/m2u2-frtq.json (API Socrata, tutte le righe)",
 "lombardia_trenord/ut63-s688.csv": "https://www.dati.lombardia.it/resource/ut63-s688.json (API Socrata, tutte le righe)",
}
for y in range(2016, 2027):
    SRC[f"pdf/ATM_Carta_Mobilita_{y}.pdf"] = ATM + {2021: "../Governance/Documents/Carta%20della%20Mobilit%C3%A0%202021.pdf"}.get(y, f"Carta%20della%20Mobilit%C3%A0%20ATM%20{y}.pdf")
today = datetime.date.today().isoformat()
rows = []
for rel, url in SRC.items():
    p = os.path.join(M, "raw", rel)
    if not os.path.exists(p): rows.append([rel, url, "", "", today, "MANCANTE"]); continue
    b = open(p, "rb").read()
    rows.append([rel, url, len(b), hashlib.sha256(b).hexdigest()[:16], today, "ok"])
# dataset del Comune: registro scritto da 02_download_comune.py
w = csv.writer(open(os.path.join(M, "raw", "download_log.csv"), "w", newline="", encoding="utf-8"))
w.writerow(["file_in_raw", "origine", "byte", "sha256_16", "data_download", "esito"])
w.writerows(rows)
print(len(rows), "righe; vedi anche raw/download_log_comune.csv per i dataset dati.comune.milano.it")
