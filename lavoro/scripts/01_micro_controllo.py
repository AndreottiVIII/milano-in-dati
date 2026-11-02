"""Lavoro, passo 1: controllo a livello di comune con i record individuali del Comune (1991, 2001).
Uso: python -I -X utf8 01_micro_controllo.py <milano-in-dati> 
Legge in streaming gli zip del Comune (censimenti/raw/comune_ckan) e tabula condizione professionale x sesso x fascia di eta'.
Serve per due cose: (a) quantificare quanti occupati hanno piu' di 64 anni e quanti 14enni ci sono tra gli studenti del 1991
(le tabelle per sezione non lo dicono); (b) controllare che i totali coincidano con quelli per sezione dell'ISTAT.
Output: lavoro/out/micro_condizione_1991_2001.csv
"""
import sys, zipfile
import pandas as pd

root = sys.argv[1]
C = root + "/censimenti/raw/comune_ckan/"
cfg = {
    1991: dict(zip=C + "ds1636-censimento-1991-popolazione-residente/00_ds1636-censimento-1991-residenti.zip", tr=[2, 4]),
    2001: dict(zip=C + "ds1518-censimento-2001-popolazione-residente/00_ds1518-censimento-2001-popolazione-residente.zip", tr=[1, 2]),
}
rows = []
for y, c in cfg.items():
    z = zipfile.ZipFile(c["zip"]); fn = z.namelist()[0]
    parts = []
    for ch in pd.read_csv(z.open(fn), sep=";", usecols=["TR", "Sesso", "Eta", "CondProf"], chunksize=300000, low_memory=False):
        ch = ch[ch.TR.isin(c["tr"])].copy()
        ch["Eta"] = pd.to_numeric(ch.Eta, errors="coerce")
        ch["fascia"] = pd.cut(ch.Eta, [-1, 13, 14, 64, 200], labels=["0-13", "14", "15-64", "65+"])
        parts.append(ch.groupby(["Sesso", "fascia", "CondProf"], observed=True, dropna=False).size().rename("n").reset_index())
    d = pd.concat(parts).groupby(["Sesso", "fascia", "CondProf"], observed=True, dropna=False).n.sum().reset_index()
    d.insert(0, "anno", y)
    rows.append(d)
    print(y, "residenti nei record:", int(d.n.sum()))
out = pd.concat(rows)
out.to_csv(root + "/lavoro/out/micro_condizione_1991_2001.csv", index=False)
print(out.groupby(["anno", "CondProf"]).n.sum().unstack(0))
