"""Inventario delle fonti scaricate: file, byte, righe, licenza (dai metadati CKAN), data di scarico.
uso: python -I -X utf8 10_inventario.py <cartella turisti assoluta>"""
import sys, os, json, csv, glob, datetime
base = sys.argv[1]
rows = []
def nrighe(p):
    try:
        with open(p, "rb") as f: return sum(1 for _ in f) - 1
    except Exception: return ""
for f in sorted(glob.glob(os.path.join(base, "raw", "comune_milano", "*.csv"))):
    k = os.path.basename(f)[:-4]
    mp = f[:-4] + ".meta.json"
    lic = mod = pub = titolo = ""
    if os.path.exists(mp):
        j = json.load(open(mp, encoding="utf-8"))["result"]
        lic = j.get("license_id", ""); mod = j.get("metadata_modified", "")[:10]; pub = j.get("publisher_name", ""); titolo = j.get("title", "")
    rows.append(["Comune di Milano (CKAN dati.comune.milano.it)", k, titolo, os.path.relpath(f, base), os.path.getsize(f), nrighe(f), lic, mod, pub,
                 "copiato da affitti-brevi/raw (scaricato 2026-11-01)" if k == "ds213" else "scaricato 2026-11-01"])
for f in sorted(glob.glob(os.path.join(base, "raw", "lombardia", "*.csv"))):
    k = os.path.basename(f).split("_")[0]
    rows.append(["Regione Lombardia (dati.lombardia.it, Socrata)", k, "", os.path.relpath(f, base), os.path.getsize(f), nrighe(f), "non specificata dal portale", "", "Polis Lombardia - ISTAT",
                 "copiato da affitti-brevi/raw (scaricato 2026-11-01)" if k in ("vyxt-7jdx", "mzxz-sz25") else "scaricato 2026-11-01"])
for f in sorted(glob.glob(os.path.join(base, "raw", "bancaditalia", "microdati_stranieri", "*.zip"))):
    rows.append(["Banca d'Italia, Indagine sul turismo internazionale (microdati stranieri, variabili principali)", os.path.basename(f)[:4], "", os.path.relpath(f, base), os.path.getsize(f), "",
                 "uso libero con citazione della fonte (testo della pagina 'Utilizzo dei dati'); nessuna sigla di licenza", "", "Banca d'Italia", "scaricato 2026-11-01"])
for f in ["Turismo_TS_1997-2025.xlsx", "Metadati_csv.zip", "Formato_variabili_2025.zip", "pivot_stranieri/PIVOT_STRANIERI_2020.zip"]:
    p = os.path.join(base, "raw", "bancaditalia", f)
    if os.path.exists(p): rows.append(["Banca d'Italia", f, "", os.path.relpath(p, base), os.path.getsize(p), "", "come sopra", "", "Banca d'Italia", "scaricato 2026-11-01"])
with open(os.path.join(base, "pulito", "inventario_fonti.csv"), "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo); w.writerow(["fonte", "id", "titolo", "file", "byte", "righe", "licenza", "scheda_modificata", "editore", "scarico"]); w.writerows(rows)
print(len(rows), "file")
