"""Dal file ISTAT scaricato da 02_ estrae la provincia di Milano (ITC45), tutte le cittadinanze:
nati ogni 1.000 donne, per eta' (15-49 e 50+) e anno 2000-2025. Scrive docs/nascite/data/fecondita_per_eta_provincia_milano.csv.
Uso: python -I -X utf8 03_fecondita_eta_provincia.py <cartella nascite> <cartella docs/nascite/data>"""
import sys, os, csv
N, OUT = sys.argv[1], sys.argv[2]
src = os.path.join(N, "raw", "istat", "istat_FECONDITA1_7_fecondita_per_eta_province.csv")
rows = []
for r in csv.DictReader(open(src, encoding="utf-8")):
    if r["REF_AREA"] != "ITC45" or r["CITIZENSHIP"] != "TOTAL" or r["DATA_TYPE"] != "ASFR":
        continue
    a = r["MOTHER_AGE"]
    if a == "Y_GE50": eta = 50
    elif a.startswith("Y") and a[1:].isdigit() and int(a[1:]) >= 15: eta = int(a[1:])
    else: continue
    rows.append((int(r["TIME_PERIOD"]), eta, r["OBS_VALUE"]))
rows.sort()
with open(os.path.join(OUT, "fecondita_per_eta_provincia_milano.csv"), "w", encoding="utf-8", newline="") as f:
    f.write("anno,eta_madre,nati_ogni_1000_donne\n")
    for a, e, v in rows: f.write(f"{a},{e},{v}\n")
print(len(rows), "righe")
