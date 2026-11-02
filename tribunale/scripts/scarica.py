"""Scarica i file del Ministero della Giustizia (datiestatistiche.giustizia.it) usati dalla pagina "Il tribunale di Milano".

Uso (percorso assoluto, si puo' rilanciare):
  python -I -X utf8 scarica.py <tribunale_dir>

Solo file xlsx/pdf pubblici linkati dalle pagine del Ministero (robots.txt: Allow /). User-Agent dichiarato, nessuna imitazione di un browser,
nessun accesso a webstat.giustizia.it (blocca i programmi) ne' ai cruscotti. Scrive raw/ministero/ e raw/download_log.csv (data, url, byte, sha256).
"""
import sys, os, csv, hashlib, datetime, urllib.request, urllib.error
T = sys.argv[1]
OUT = os.path.join(T, "raw", "ministero")
os.makedirs(OUT, exist_ok=True)
B = "https://datiestatistiche.giustizia.it/cmsresources/cms/documents/"
UA = "milano-in-dati-research/1.0 (ricerca su open data, uso non commerciale)"
FILES = [
    # (nome file, pagina da cui e' linkato, cosa contiene)
    ("CivileFlussi20142025.xlsx", "https://datiestatistiche.giustizia.it/it/flussi_per_ufficio.page", "Civile: iscritti, definiti, pendenti per ufficio, 2014-2025"),
    ("PenaleFlussi20142025.xlsx", "https://datiestatistiche.giustizia.it/it/flussi_per_ufficio_penale.page", "Penale: flussi per ufficio, 2014-2025"),
    ("Monitoraggio_PNRR.xlsx", "https://datiestatistiche.giustizia.it/it/pnrr.page", "PNRR: disposition time e pendenza per sede, baseline 2019"),
    ("Durata_SICID_20142025.xlsx", "https://datiestatistiche.giustizia.it/it/durata_dei_procedimenti_civile.page", "Durata effettiva dei procedimenti civili (SICID), 2014-2025"),
    ("Durata_SIECIC_20142025.xlsx", "https://datiestatistiche.giustizia.it/it/durata_dei_procedimenti_civile.page", "Durata effettiva esecuzioni civili (SIECIC), 2014-2025"),
    ("Monitoraggio_mensile.xlsx", "https://datiestatistiche.giustizia.it/it/monitoraggio_mens_tribunali.page", "Flussi mensili civili dei tribunali dal 2019"),
    ("Nota_metodologica.pdf", "https://datiestatistiche.giustizia.it/it/pnrr.page", "Nota metodologica del monitoraggio PNRR"),
    ("Guida_alle_Statistiche_Civile.pdf", "https://datiestatistiche.giustizia.it/it/flussi_per_ufficio.page", "Guida alle statistiche civili"),
    ("251231MilanoMonitoraggioCIVILE.xlsx", "https://www.giustizia.it/giustizia/it/mg_1_14_1.page?contentId=SST244010", "Monitoraggio distrettuale Milano, civile (SICID), IV trimestre 2025"),
    ("251231MilanoMonitoraggioPENALE.xlsx", "https://www.giustizia.it/giustizia/it/mg_1_14_1.page?contentId=SST244010", "Monitoraggio distrettuale Milano, penale, IV trimestre 2025"),
    ("251231MilanoMonitoraggioSIECIC.xlsx", "https://www.giustizia.it/giustizia/it/mg_1_14_1.page?contentId=SST244010", "Monitoraggio distrettuale Milano, esecuzioni e concorsuali (SIECIC), IV trimestre 2025"),
    ("Allegato_MDG.AD31DEB.DIT.14092026.0031649.U_Isem2026_Continuous_Monitoring_PNRR_finale.pdf", "https://datiestatistiche.giustizia.it/it/pnrr.page", "Relazione sul monitoraggio statistico degli indicatori PNRR, I semestre 2026"),
]
log = os.path.join(T, "raw", "download_log.csv")
righe = []
for nome, pagina, desc in FILES:
    dest = os.path.join(OUT, nome)
    url = B + nome
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
            lm = r.headers.get("Last-Modified", "")
        open(dest, "wb").write(data)
        stato = "ok"
    except urllib.error.HTTPError as e:
        data, lm, stato = b"", "", f"HTTP {e.code}"
    righe.append([datetime.date.today().isoformat(), url, pagina, desc, len(data), hashlib.sha256(data).hexdigest() if data else "", lm, stato])
    print(stato, nome, len(data))
with open(log, "w", newline="", encoding="utf8") as f:
    w = csv.writer(f)
    if True:
        w.writerow(["data_scarico", "url", "pagina_di_origine", "contenuto", "byte", "sha256", "last_modified_server", "esito"])
    w.writerows(righe)
