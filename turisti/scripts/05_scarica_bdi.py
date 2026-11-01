"""Scarica i microdati principali dei viaggiatori stranieri (Banca d'Italia, CSV zip) 1997-2025 + metadati + manuale.
uso: python -I -X utf8 05_scarica_bdi.py <cartella raw/bancaditalia assoluta>
Salta i file gia' presenti. Pausa 3 s. Nessun account. Fonte da citare: Banca d'Italia, Indagine sul turismo internazionale dell'Italia."""
import sys, os, time, urllib.request, datetime
out = sys.argv[1]
root = "https://www.bancaditalia.it/statistiche/tematiche/rapporti-estero/turismo-internazionale/distribuzione-microdati/"
elenco = [l.strip() for l in open(os.path.join(out, "elenco_microdati_stranieri.txt")) if "/csv/" in l and "principali" in l.lower()]
elenco = [l for l in elenco if "Residenza-dei-viaggiatori" not in l or True]
UA = {"User-Agent": "milano-in-dati research (turisti fase 1)"}
dst = os.path.join(out, "microdati_stranieri"); os.makedirs(dst, exist_ok=True)
log = open(os.path.join(out, "download_log.csv"), "a", encoding="utf-8")
extra = [root + "metadati/Metadati_csv.zip",
         root + "documentazione/formato-variabili/Formato_variabili_2025.zip"]
todo = [root + "file-dati/" + l.split("file-dati/")[-1] if "file-dati/" in l else root + "file-dati/" + l for l in elenco]
# i link sono relativi a .../file-dati/ ; normalizzo
todo = []
for l in elenco:
    l = l.lstrip("/")
    todo.append("https://www.bancaditalia.it/" + l if l.startswith("statistiche") else root + "file-dati/" + l)
for u in todo + extra:
    name = u.split("/")[-1]
    if "/csv/" in u and "documenti/" in u:
        name = u.split("/documenti/")[-1].replace("/csv/", "_")
    p = os.path.join(dst if "file-dati" in u else out, name)
    if os.path.exists(p): continue
    try:
        b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read()
    except Exception as e:
        print("ERRORE", u, e); log.write(f"{datetime.datetime.now():%F %R};{u};ERRORE {e}\n"); time.sleep(3); continue
    open(p, "wb").write(b); log.write(f"{datetime.datetime.now():%F %R};{u};{os.path.relpath(p, out)};{len(b)}\n"); log.flush()
    print(name, len(b)); time.sleep(3)
