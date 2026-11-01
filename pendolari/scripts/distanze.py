"""Estrae dalle matrici ISTAT delle distanze (Lombardia, comuni al 1/1/2021) km e minuti stradali verso e da Milano.

Uso: python -I -X utf8 distanze.py <cartella pendolari, percorso assoluto>
Legge raw/istat_distanze/Lombardia.zip (un csv per provincia, righe origine-destinazione, ';', decimali con virgola).
Campi: KM_TOT km dell'itinerario scelto; TEP_TOT minuti effettivi (con traffico e barriere); TTP_TOT minuti ottimali
(senza traffico). Scrive pulito/distanze_milano.csv: pro_com, km_verso_milano, min_verso_milano, min_ottimo_verso_milano,
km_da_milano, min_da_milano. Solo comuni lombardi come origine (le altre regioni hanno file separati non scaricati).
"""
import sys, zipfile, io
from pathlib import Path
import pandas as pd

P = Path(sys.argv[1])
z = zipfile.ZipFile(P / 'raw/istat_distanze/Lombardia.zip')
MI = 15146
verso, da = [], []
for info in z.infolist():
    if not info.filename.startswith('R03_'):
        continue
    with z.open(info) as f:
        for ch in pd.read_csv(f, sep=';', encoding='latin1', decimal=',', chunksize=500000):
            ch.columns = [c.strip() for c in ch.columns]
            v = ch[ch['DEST_PROCOM'] == MI]
            if len(v):
                verso.append(v)
            d = ch[ch['OR_PROCOM'] == MI]
            if len(d):
                da.append(d)
    print(info.filename, sum(len(x) for x in verso), sum(len(x) for x in da))
v = pd.concat(verso).rename(columns={'OR_PROCOM': 'pro_com', 'KM_TOT': 'km_verso_milano', 'TEP_TOT': 'min_verso_milano', 'TTP_TOT': 'min_ottimo_verso_milano'})
v = v[['pro_com', 'km_verso_milano', 'min_verso_milano', 'min_ottimo_verso_milano']]
d = pd.concat(da).rename(columns={'DEST_PROCOM': 'pro_com', 'KM_TOT': 'km_da_milano', 'TEP_TOT': 'min_da_milano'})[['pro_com', 'km_da_milano', 'min_da_milano']]
out = v.merge(d, on='pro_com', how='outer')
out.to_csv(P / 'pulito/distanze_milano.csv', index=False)
print(len(out), out.describe().round(1).to_string())
