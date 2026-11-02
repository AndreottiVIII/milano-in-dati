"""Scrive raw/fonti.csv: per ogni file scaricato, fonte, URL, byte, sha256, data di scarico (data di modifica del file).
Uso: python -I -X utf8 fonti.py <poverta-educativa_dir>"""
import sys, os, hashlib, csv, datetime
PE = sys.argv[1]; RAW = os.path.join(PE, "raw")
B_IST = "https://esploradati.istat.it/SDMXWS/rest/data/"
URL = {
 "istat/tavole_nidi_2023.xlsx": ("ISTAT", "https://www.istat.it/wp-content/uploads/2026/02/tavole_nidi_2023.xlsx", "Tavole del comunicato 'Offerta di nidi e servizi integrativi, a.e. 2023/2024' (solo regioni: non usate per i comuni)"),
 "istat/REPORT_nidi_2023_24.pdf": ("ISTAT", "https://www.istat.it/wp-content/uploads/2026/02/REPORT_OFFERTA-DI-NIDI-E-SERVIZI-INTEGRATIVI-PER-LA-PRIMA-INFANZIA.pdf", "Report del comunicato (consultato)"),
 "istat/REPORT_servizi_infanzia_2022_23.pdf": ("ISTAT", "https://www.istat.it/wp-content/uploads/2024/10/Report-Completo_I-servizi-educativi-per-linfanzia-in-Italia_16_10_24-1.pdf", "Report 2022/23 (consultato, nessun dato comunale)"),
 "istat/sdmx_SERVSOCEDU1_6.csv": ("ISTAT IstatData", B_IST + "IT1,47_850_DF_DCIS_SERVSOCEDU1_6,1.0/A.015146+058091+001272+063049+037006+048017..........?startPeriod=2010", "Servizi sul territorio, comuni: posti autorizzati, servizi, posti per 100 bambini 0-2; 6 città, 2013-2024"),
 "istat/sdmx_SERVSOCEDU1_3.csv": ("ISTAT IstatData", B_IST + "IT1,47_850_DF_DCIS_SERVSOCEDU1_3,1.0/A.015146+058091+001272+063049+037006+048017..........?startPeriod=2010", "Servizi offerti dai comuni: utenti, spesa; 6 città, 2013-2024"),
 "istat/sdmx_SERVSOCEDU1_6_14capoluoghi_IT.csv": ("ISTAT IstatData", B_IST + "IT1,47_850_DF_DCIS_SERVSOCEDU1_6,1.0/A.<14 capoluoghi>+IT+ITC4.P_100CH_Y0_2+AUTP.ALL.ALL.9?startPeriod=2013", "Posti per 100 bambini 0-2 e posti autorizzati, 14 città metropolitane (capoluoghi), Italia, Lombardia"),
 "istat/sdmx_FRISC4_6citta.csv": ("ISTAT IstatData", B_IST + "IT1,DF_DCSS_LCAS_FRISC_4,1.0/A.<6 città>........", "Censimento permanente, frequenza nido: tutte le celle vuote (flag J): NON usato"),
 "istat/dataflow.xml": ("ISTAT IstatData", "https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1?detail=allstubs", "tentativo di elenco (non arrivato)"),
}
rows = []
for dp, dn, fs in os.walk(RAW):
    for f in sorted(fs):
        p = os.path.join(dp, f); rel = os.path.relpath(p, RAW).replace("\\", "/")
        if rel == "fonti.csv" or f == "download.out": continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if rel in URL: fonte, url, nota = URL[rel]
        elif rel.startswith("miur/ALUTEMPOSCUOLA"): fonte, url, nota = "MIM", "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/" + f, "Studenti per tempo scuola (DS0090 statale / DS0100 paritaria), nazionale"
        elif rel.startswith("miur/EDI"): fonte, url, nota = "MIM", "https://dati.istruzione.it/opendata/opendata/catalogo/elements1/" + f, "Edilizia scolastica statale, a.s. 2024/25"
        elif rel.startswith("invalsi/") and f.endswith(".csv"):
            fonte = "INVALSI Servizio statistico"; nota = "Open data"
            url = "https://serviziostatistico.invalsi.it/download/" + ("1024/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/" if "dispersione" in f else "1037/sistemi-locali-del-lavoro-sll-gestione-scolastica-capoluogo-di-provincia-dal-2015/") + "<id>/" + f
        elif rel.startswith("invalsi/"): fonte, url, nota = "INVALSI Servizio statistico", "https://serviziostatistico.invalsi.it/ (pagine di catalogo)", "pagina HTML consultata"
        elif rel.startswith("comune/"): fonte, url, nota = "Comune di Milano CKAN", "https://dati.comune.milano.it/api/3/action/package_search", "ricerca per parole chiave"
        else: fonte, url, nota = "", "", ""
        rows.append([rel, fonte, url, os.path.getsize(p), h, datetime.date.fromtimestamp(os.path.getmtime(p)).isoformat(), nota])
with open(os.path.join(RAW, "fonti.csv"), "w", newline="", encoding="utf8") as g:
    w = csv.writer(g, delimiter=";"); w.writerow(["file", "fonte", "url", "byte", "sha256", "data_scarico", "nota"]); w.writerows(rows)
print(len(rows), "file")
