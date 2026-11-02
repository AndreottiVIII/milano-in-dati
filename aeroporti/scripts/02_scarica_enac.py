"""Scarica da enac.gov.it alcuni rapporti annuali 'Dati di traffico' e 'Annuario statistico' (PDF) per controllare i dati Eurostat.
Pagine dei rapporti: https://www.enac.gov.it/aeroporti/statistiche/dati-di-traffico-sul-trasporto-aereo/documento-annuale-dati-di-traffico/
uso: python -I -X utf8 02_scarica_enac.py <cartella aeroporti assoluta>
Pausa 5 s, User-Agent onesto, nessuna registrazione. Salva in raw/enac/ e aggiorna raw/download_log.csv."""
import sys, os, time, datetime, urllib.request
base = sys.argv[1]
raw = os.path.join(base, "raw", "enac")
os.makedirs(raw, exist_ok=True)
UA = {"User-Agent": "milano-in-dati research (aeroporti fase 1)"}
PDF = {
    2025: "https://www.enac.gov.it/app/uploads/2026/05/Dati-di-traffico-2025-v.0.7.pdf",
    2024: "https://www.enac.gov.it/app/uploads/2025/07/Dati-di-traffico-2024-v.0.7_cover_c.pdf",
    2019: "https://www.enac.gov.it/app/uploads/2024/04/Traffico_LLC_2019.pdf",
    2010: "https://www.enac.gov.it/app/uploads/2024/04/Dati_di_traffico-2010.pdf",
    2007: "https://www.enac.gov.it/app/uploads/2024/04/Dati_traffico_2007.pdf",
    2003: "https://www.enac.gov.it/app/uploads/2024/04/Annuario2003.pdf",
    2002: "https://www.enac.gov.it/app/uploads/2024/04/Annuario2002.pdf",
    2001: "https://www.enac.gov.it/app/uploads/2024/04/Annuario2001.pdf",
    2000: "https://www.enac.gov.it/app/uploads/2024/04/Annuario2000.pdf",
}
log = open(os.path.join(base, "raw", "download_log.csv"), "a", encoding="utf-8")
for anno, url in PDF.items():
    fn = os.path.join(raw, f"Dati-di-traffico-{anno}.pdf")
    if os.path.exists(fn):
        continue
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as f:
        data = f.read()
    open(fn, "wb").write(data)
    log.write(f"{datetime.date.today()};{url};{fn};{len(data)};ENAC, nessuna licenza dichiarata sulla pagina\n")
    log.flush()
    print(anno, len(data))
    time.sleep(5)
