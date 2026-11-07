"""Nati vivi da madri residenti per anno e genere (2003-2024), somma di tutti i quartieri e dei nati senza quartiere.
Uso: python -I -X utf8 04_nati_per_genere.py <cartella nascite> <cartella docs/nascite/data>"""
import sys, os, pandas as pd
N, OUT = sys.argv[1], sys.argv[2]
R = os.path.join(N, "raw", "comune")
a = pd.read_csv(os.path.join(R, "ds141-popolazione-nascite-quartiere.csv"), sep=";"); a.columns = ["anno", "q", "g", "cm", "cp", "n"]
b = pd.read_csv(os.path.join(R, "ds1943_popolazione-nascite-residenti-quartiere.csv"), sep=";"); b.columns = ["anno", "q", "g", "cm", "cp", "n"]
d = pd.concat([a[a.anno <= 2020], b[b.anno >= 2021]])
t = d.groupby(["anno", "g"]).n.sum().unstack().fillna(0).astype(int)
t["totale"] = t.sum(axis=1)
t = t.rename(columns={"Maschi": "maschi", "Femmine": "femmine"})[["maschi", "femmine", "totale"]]
t.to_csv(os.path.join(OUT, "nati_per_genere_citta.csv"))
print(t.tail(3), t.shape)
