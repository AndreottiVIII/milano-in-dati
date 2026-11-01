"""Elenca i file dei microdati Banca d'Italia (indagine turismo internazionale) scorrendo le pagine dell'elenco.
uso: python -I -X utf8 04_bdi_elenco.py <cartella raw/bancaditalia assoluta>
Pausa 3 s tra pagine; salva elenco_microdati.txt con i link a stra_*_principali / fp / secondarie e i pivot stranieri."""
import sys, re, time, os, urllib.request
out = sys.argv[1]
B = "https://www.bancaditalia.it/statistiche/tematiche/rapporti-estero/turismo-internazionale/distribuzione-microdati/file-dati/index.html?page="
UA = {"User-Agent": "milano-in-dati research (turisti fase 1)"}
links = set()
for p in range(1, 36):
    h = urllib.request.urlopen(urllib.request.Request(B + str(p), headers=UA), timeout=60).read().decode("utf-8", "replace")
    for m in re.findall(r"documenti/[^'\"\s<>]*stra[^'\"\s<>]*", h, re.I):
        links.add(m)
    time.sleep(3)
open(os.path.join(out, "elenco_microdati_stranieri.txt"), "w").write("\n".join(sorted(links)))
print(len(links))
for l in sorted(links): print(l)
