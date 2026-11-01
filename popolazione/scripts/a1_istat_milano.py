"""a1: estrae Milano (codice comune 015146) dai file ISTAT scaricati: RBD 2001-2018 (ricostruzione del bilancio), D7B 2019-2024 (bilancio mensile, da censimenti/raw/istat_demo),
P2 2025 (bilancio 2019-2025). Uso: python -I -X utf8 a1_istat_milano.py <popolazione assoluto> <milano-in-dati assoluto>
Scrive pulito/istat_bilancio_milano_2001_2018.csv e pulito/istat_bilancio_milano_2019_2024_mensile.csv (+ annuale)."""
import sys, os, zipfile, io, glob
import pandas as pd
P, M = sys.argv[1], sys.argv[2]
out = os.path.join(P, "pulito")
rows = []
for y in range(2001, 2019):
    z = zipfile.ZipFile(os.path.join(P, "raw", "istat_demo", f"RBD-Dataset-{y}.csv.zip"))
    df = pd.read_csv(z.open(z.namelist()[0]), sep=";", dtype=str, encoding="utf-8")
    df = df[df["Codice comune"] == "015146"]
    rows.append(df)
rbd = pd.concat(rows)
for c in ["Popolazione inizio periodo", "Nati", "Morti", "Iscritti dall'interno", "Cancellati per l'interno", "Iscritti dall'estero", "Cancellati per l'estero", "Acquisizioni di cittadinanza italiana", "Popolazione fine periodo"]:
    rbd[c] = pd.to_numeric(rbd[c], errors="coerce")
print(rbd.groupby(["Cittadinanza", "Sesso"]).size().head(12))
rbd.to_csv(os.path.join(out, "istat_bilancio_milano_2001_2018.csv"), index=False)
# D7B mensile 2019-2024 da censimenti
rows = []
for y in range(2019, 2025):
    z = zipfile.ZipFile(os.path.join(M, "censimenti", "raw", "istat_demo", f"D7B{y}.csv.zip"))
    df = pd.read_csv(z.open(z.namelist()[0]), sep=";", dtype=str)
    rows.append(df[df["Codice comune"] == "015146"])
d7 = pd.concat(rows)
num = ["Popolazione inizio periodo", "Nati vivi", "Morti", "Immigrati da altro comune", "Emigrati per altro comune", "Immigrati dall'estero", "Emigrati per l'estero", "Popolazione fine periodo", "Unità in più/meno dovute a variazioni territoriali"]
for c in num:
    d7[c] = pd.to_numeric(d7[c])
d7.to_csv(os.path.join(out, "istat_bilancio_milano_2019_2024_mensile.csv"), index=False)
t = d7[d7.Sesso == "Totale"].groupby("Anno")[["Nati vivi", "Morti", "Immigrati da altro comune", "Emigrati per altro comune", "Immigrati dall'estero", "Emigrati per l'estero"]].sum()
t.to_csv(os.path.join(out, "istat_bilancio_milano_2019_2024_annuale.csv"))
print(t)
# P2 2025
z = zipfile.ZipFile(os.path.join(P, "raw", "istat_demo", "P2_2025_it_015_Milano.zip"))
print(z.namelist())
for n in z.namelist():
    z.extract(n, os.path.join(P, "raw", "istat_demo", "P2_2025_unzip"))
