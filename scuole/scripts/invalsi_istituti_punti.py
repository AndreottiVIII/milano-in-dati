"""Scrive docs/scuole/data/invalsi_istituti_punti.json: dati del grafico a due assi degli istituti statali di Milano.

Uso: python -I -X utf8 invalsi_punti_anonimi.py <cartella scuole> <cartella docs>
Legge dal pulito (invalsi_istituti.csv, invalsi_istituti_quota_stranieri.csv) e dall'anagrafe MIM in raw/miur (solo per nome e codice
dell'istituto di riferimento). Solo righe di istituto: mai plessi, sezioni o classi. Valori alla precisione della fonte (un decimale).
Ogni vista contiene gli istituti con quel punteggio; il confronto con scuole di contesto simile (e) puo' mancare per qualche istituto.
Rette e intervalli sono calcolati sui valori della fonte (minimi quadrati; intervallo da 4.000 estrazioni a caso degli istituti).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

BASE, DOCS = sys.argv[1], sys.argv[2]
TOTALE_ISTITUTI = 135  # istituti statali di riferimento di Milano citta' (anagrafe MIM 2025/26), vedi _idee/invalsi_stranieri.md sez. 8
inv = pd.read_csv(os.path.join(BASE, "pulito", "invalsi_istituti.csv"), sep=";", dtype={"istituto": str})
Q = pd.read_csv(os.path.join(BASE, "pulito", "invalsi_istituti_quota_stranieri.csv"), sep=";", dtype={"istituto": str})
an = pd.read_csv(os.path.join(BASE, "raw", "miur", "SCUANAGRAFESTAT20252620250901.csv"), dtype=str, keep_default_na=False)
an = an[an.CODICECOMUNESCUOLA == "F205"]
NOMI = dict(an.groupby("CODICEISTITUTORIFERIMENTO").DENOMINAZIONEISTITUTORIFERIMENTO.first())
inv = inv[(inv.anni == "2024/2025") & inv.punteggio.notna()]
VISTE = [("p5ita", "Scuola primaria - classi quinte", "Italiano", "primaria"),
         ("m3ita", "Scuola secondaria di primo grado - classi terze", "Italiano", "sec1"),
         ("m3mat", "Scuola secondaria di primo grado - classi terze", "Matematica", "sec1")]
rng = np.random.default_rng(20261105)


def fit(x, y):
    b, a = np.polyfit(x, y, 1)
    bs = []
    for _ in range(4000):
        i = rng.integers(0, len(x), len(x))
        if np.ptp(x[i]) > 0:
            bs.append(np.polyfit(x[i], y[i], 1)[0] * 10)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return dict(pend=round(b * 10, 2), lo=round(float(lo), 2), hi=round(float(hi), 2), a=round(float(a), 2))


out = {"anno": "2024/25", "totale_istituti": TOTALE_ISTITUTI, "viste": {}}
for k, gr, mat, o in VISTE:
    z = inv[(inv.grado == gr) & (inv.materia == mat)].merge(Q[["istituto", f"quota_{o}"]], on="istituto").dropna(subset=[f"quota_{o}"])
    z = z.dropna(subset=["scarto_lombardia"]).sort_values("istituto")
    v = {}
    righe = []
    for _, r in z.iterrows():
        righe.append(dict(c=r.istituto, n=NOMI[r.istituto], q=round(float(r[f"quota_{o}"]), 1), s=round(float(r.scarto_lombardia), 1),
                          e=None if pd.isna(r.diff_escs) else round(float(r.diff_escs), 1)))
    for nome, col in (("scarto", "s"), ("escs", "e")):
        w = [r for r in righe if r[col] is not None]
        x = np.array([r["q"] for r in w]); y = np.array([r[col] for r in w])
        d = dict(n=len(w), fuori=TOTALE_ISTITUTI - len(w))
        d.update(fit(x, y))
        v[nome] = d
        print(k, nome, d["n"], d["pend"], d["lo"], d["hi"])
    v["istituti"] = righe
    out["viste"][k] = v
p = os.path.join(DOCS, "scuole", "data", "invalsi_istituti_punti.json")
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("scritto", p, os.path.getsize(p), "byte")
