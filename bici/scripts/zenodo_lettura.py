"""Legge i CSV di Zenodo (BikeMI 2011-2014) e li porta a una tabella ordinata. Usato da analisi.py.
Formato riga: AAMMGGOOMM:nome:bici:stalli_liberi  (il nome puo' contenere ':' -> si taglia dalla destra).
"""
import re, numpy as np, pandas as pd

def leggi(path):
    d, n, b, f = [], [], [], []
    scartate = 0
    with open(path, encoding="utf8", errors="replace") as fh:
        next(fh)
        for line in fh:
            line = line.rstrip("\n")
            if len(line) < 14 or line[10] != ":":
                scartate += 1; continue
            parts = line[11:].rsplit(":", 2)
            if len(parts) != 3:
                scartate += 1; continue
            try:
                bb = int(parts[1]); ff = int(parts[2])
            except ValueError:
                scartate += 1; continue
            d.append(line[:10]); n.append(parts[0]); b.append(bb); f.append(ff)
    t = pd.DataFrame({"d": d, "nome": n, "b": b, "f": f})
    t["t"] = pd.to_datetime(t.d, format="%y%m%d%H%M", errors="coerce")
    scartate += int(t.t.isna().sum())
    t = t.dropna(subset=["t"]).drop(columns="d")
    return t, scartate

def chiave(nome):
    s = nome.strip()
    s = re.sub(r"\s+0$", "", s)               # suffisso " 0" presente in molte righe 2012-2013
    m = re.match(r"^(\d{1,3})\b", s)
    num = m.group(1).zfill(3) if m else None
    norm = re.sub(r"\s+", " ", s.lower())
    return num, norm
