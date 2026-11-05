"""Scarica i file grezzi di violenza-donne/raw (rieseguibile: salta i file gia' presenti).

Uso:  python -I -X utf8 scarica.py <cartella violenza-donne assoluta> [--forza]

- User-Agent dichiarato (nessuna imitazione di un browser), pausa di 20 s tra due richieste ISTAT.
- Scrive pulito/inventario_fonti.csv con data (data di modifica del file = scaricamento) e sha256.
"""
import sys, os, time, hashlib, csv, datetime, urllib.request

UA = "milano-in-dati-research/1.0 (milano-in-dati)"
SDMX = "https://esploradati.istat.it/SDMXWS/rest/data/IT1,{flow},1.0/"
CSVACC = "application/vnd.sdmx.data+csv;version=1.0.0"
IST = "https://www.istat.it/wp-content/uploads/2026/09/"
FILES = [
    ("raw/istat/Tavole_ITA_REV-19ottobre2026.xlsx", IST + "Tavole_ITA_REV-19ottobre2026.xlsx", "*/*",
     "ISTAT, Il numero verde 1522: chi chiama, perche' e cosa racconta - anno 2025 (tavole trimestrali 2023-2025 e giornaliere dal 2018; fonte primaria DPO-PCM; revisione del 19/10/2026)", "ISTAT (condizioni d'uso istat.it: CC BY 4.0)"),
    ("raw/istat/Nota-metodologica.pdf", IST + "Nota-metodologica.pdf", "*/*", "ISTAT, 1522 anno 2025: nota metodologica", "ISTAT"),
    ("raw/istat/Glossario.pdf", IST + "Glossario.pdf", "*/*", "ISTAT, 1522 anno 2025: glossario", "ISTAT"),
    ("raw/istat/Indice-delle-tavole-statistiche.pdf", IST + "Indice-delle-tavole-statistiche.pdf", "*/*", "ISTAT, 1522 anno 2025: indice delle tavole", "ISTAT"),
    ("raw/istat/cav.csv", SDMX.format(flow="78_1260"), CSVACC,
     "ISTAT esploradati, Centri antiviolenza (78_1260, struttura DCCV_CAV1)", "CC BY 4.0 (ISTAT)"),
    ("raw/istat/1522_utenti_regione.csv", SDMX.format(flow="78_1205_DF_DCCV_1522UTENTI4_3"), CSVACC,
     "ISTAT esploradati, Utenti del 1522: tipologia utenti, sesso, nazionalita', regione, chiamate valide (78_1205_DF_DCCV_1522UTENTI4_3)", "CC BY 4.0 (ISTAT)"),
    ("raw/istat/1522_vittime_regione.csv", SDMX.format(flow="78_1121_DF_DCCV_1522_VITTIME_1"), CSVACC,
     "ISTAT esploradati, Vittime che si rivolgono al 1522: sesso, classi di eta', regione (78_1121_DF_DCCV_1522_VITTIME_1)", "CC BY 4.0 (ISTAT)"),
    ("raw/istat/pop_1.csv",
     "https://esploradati.istat.it/SDMXWS/rest/data/IT1,22_289_DF_DCIS_POPRES1_1,1.0/A.IT+ITC4+ITC4C+ITC45...TOTAL.?startPeriod=2013", CSVACC,
     "ISTAT esploradati, Popolazione residente al 1 gennaio, Italia/Lombardia/Milano provincia (22_289_DF_DCIS_POPRES1_1)", "CC BY 4.0 (ISTAT)"),
    ("raw/istat_omicidi/Report_Le-vittime-di-omicidio_Anno-2024.pdf", "https://www.istat.it/wp-content/uploads/2025/11/Report_Le-vittime-di-omicidio_Anno-2024.pdf", "*/*",
     "ISTAT, Report Le vittime di omicidio - anno 2024 (25/11/2025)", "ISTAT (CC BY 4.0 secondo le condizioni d'uso di istat.it)"),
    ("raw/lombardia/dphu-pcij.csv", "https://www.dati.lombardia.it/api/views/dphu-pcij/rows.csv?accessType=DOWNLOAD", "text/csv",
     "Regione Lombardia, Elenco dei centri antiviolenza iscritti all'albo regionale (aggiornato 14/04/2026)", "CC0 1.0 (Regione Lombardia)"),
    ("raw/lombardia/jvq8-53gf.csv", "https://www.dati.lombardia.it/api/views/jvq8-53gf/rows.csv?accessType=DOWNLOAD", "text/csv",
     "Regione Lombardia, Centri antiviolenza convenzionati (aggiornato 30/09/2026)", "CC0 1.0 (Regione Lombardia)"),
    ("raw/lombardia/8eux-iam2.csv", "https://www.dati.lombardia.it/api/views/8eux-iam2/rows.csv?accessType=DOWNLOAD", "text/csv",
     "Regione Lombardia, Elenco delle case rifugio iscritte all'albo regionale (aggiornato 14/04/2026)", "CC0 1.0 (Regione Lombardia)"),
]

def main():
    base = sys.argv[1]
    forza = "--forza" in sys.argv
    inv = []
    first_istat = True
    for rel, url, acc, desc, lic in FILES:
        p = os.path.join(base, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if forza or not os.path.exists(p):
            if "istat.it" in url and not first_istat:
                time.sleep(20)
            if "istat.it" in url:
                first_istat = False
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": acc})
            with urllib.request.urlopen(req, timeout=300) as r, open(p, "wb") as f:
                f.write(r.read())
            print("scaricato", rel)
        else:
            print("gia' presente", rel)
        data = open(p, "rb").read()
        d = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")
        inv.append([rel, url, desc, lic, d, hashlib.sha256(data).hexdigest(), len(data)])
    os.makedirs(os.path.join(base, "pulito"), exist_ok=True)
    with open(os.path.join(base, "pulito", "inventario_fonti.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "url", "descrizione", "licenza", "data_scaricamento", "sha256", "byte"])
        w.writerows(inv)

if __name__ == "__main__":
    main()
