"""Funzioni comuni a tutti i programmi di incroci-esplorativi.
Solo lettura dei file del progetto; si scrive solo in incroci-esplorativi/out."""
import csv
import os
import re

import numpy as np
import pandas as pd

ROOT = r"C:\Users\davide\Desktop\ClaudeTower\milano-in-dati"
BASE = os.path.join(ROOT, "incroci-esplorativi")
OUT = os.path.join(BASE, "out")
os.makedirs(OUT, exist_ok=True)
SOGLIA_RESIDENTI = 3000
SEED = 20261102


def path(*a):
    return os.path.join(ROOT, *a)


def rd(rel, **kw):
    """Legge un CSV del progetto indovinando il separatore e la virgola decimale."""
    p = path(*rel.split("/"))
    with open(p, encoding="utf-8-sig", errors="replace") as h:
        head = h.readline()
    sep = ";" if head.count(";") > head.count(",") else ","
    d = pd.read_csv(p, sep=sep, encoding="utf-8-sig", low_memory=False, **kw)
    d.columns = [c.strip().lstrip("\ufeff") for c in d.columns]
    if sep == ";":
        for c in d.columns:
            if pd.api.types.is_string_dtype(d[c]) or d[c].dtype == object:
                s = d[c].fillna("").astype(str).str.strip()  # i vuoti restano vuoti: senza fillna contano come non numerici
                if s.str.fullmatch(r"-?\d+,\d+|-?\d+|nan|<NA>|").mean() > 0.9 and s.str.contains(",").any():
                    d[c] = pd.to_numeric(s.str.replace(",", "."), errors="coerce")
    return d


def bh(p):
    """q di Benjamini-Hochberg su un vettore di p (ignora i NaN)."""
    p = np.asarray(p, float)
    q = np.full(p.shape, np.nan)
    ok = ~np.isnan(p)
    x = p[ok]
    o = np.argsort(x)
    r = x[o] * len(x) / (np.arange(len(x)) + 1)
    r = np.minimum.accumulate(r[::-1])[::-1]
    t = np.empty(len(x))
    t[o] = np.minimum(r, 1)
    q[ok] = t
    return q


def rank(x):
    return pd.Series(x).rank().values


def residui(y, X):
    """Residui di y su X (con costante)."""
    X1 = np.column_stack([np.ones(len(y)), X])
    b, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return y - X1 @ b
