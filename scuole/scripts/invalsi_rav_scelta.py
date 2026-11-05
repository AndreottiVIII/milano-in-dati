"""Sceglie 10 istituti statali milanesi con primaria, a quote di stranieri molto diverse (anno 2024/25, MIM).

Uso: python -I -X utf8 invalsi_rav_scelta.py <cartella scuole> <cartella output raw/rav>
Scrive scelta.csv (codice istituto, quota, sito). Solo per il test sui RAV: appunto interno.
"""
import csv
import os
import sys

import pandas as pd

BASE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
a = pd.read_csv(os.path.join(BASE, "pulito", "miur_scuole_anno.csv"), sep=";", dtype={"codice_mecc": str})
a = a[(a.anno_inizio == 2024) & (a.ordine == "primaria") & (a.tipo == "statale")]
g = pd.read_csv(os.path.join(BASE, "raw", "miur", "SCUANAGRAFESTAT20252620250901.csv"), dtype=str, keep_default_na=False)
g = g[g.CODICECOMUNESCUOLA == "F205"]
ist = g[["CODICESCUOLA", "CODICEISTITUTORIFERIMENTO"]].rename(columns={"CODICESCUOLA": "codice_mecc", "CODICEISTITUTORIFERIMENTO": "istituto"})
a = a.merge(ist, on="codice_mecc", how="left").dropna(subset=["istituto"])
s = a.groupby("istituto").agg(iscritti=("iscritti", "sum"), nonita=("cittadinanza_non_italiana", "sum"), plessi=("codice_mecc", "nunique")).reset_index()
s["quota"] = s.nonita / s.iscritti * 100
sito = g[g.CODICESCUOLA == g.CODICEISTITUTORIFERIMENTO][["CODICESCUOLA", "SITOWEBSCUOLA", "DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA"]].rename(columns={"CODICESCUOLA": "istituto", "SITOWEBSCUOLA": "sito", "DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA": "tipo"})
s = s.merge(sito, on="istituto", how="left")
s = s[s.sito.str.contains(r"\.", regex=True, na=False)].sort_values("quota").reset_index(drop=True)
print("istituti con sito:", len(s), "| quota min", round(s.quota.min(), 1), "max", round(s.quota.max(), 1), "mediana", round(s.quota.median(), 1))
pos = [round(i * (len(s) - 1) / 9) for i in range(10)]
sc = s.iloc[pos]
sc.to_csv(os.path.join(OUT, "scelta.csv"), index=False, sep=";", quoting=csv.QUOTE_MINIMAL)
print(sc[["istituto", "tipo", "plessi", "iscritti", "quota", "sito"]].round(1).to_string(index=False))
s.to_csv(os.path.join(OUT, "tutti.csv"), index=False, sep=";")
