"""Costruisce invalsi_istituti.csv dai json di raw/invalsi_rav e lo incrocia con la quota di cittadinanza non italiana per istituto (MIM 2024/25).

Uso: python -I -X utf8 invalsi_rav_incrocio.py <cartella scuole>
Solo codici, nessun nome di scuola. Solo istituti statali di Milano (F205), anno scolastico 2024/25 per l'incrocio.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

BASE = sys.argv[1]
RAW = os.path.join(BASE, "raw", "invalsi_rav")
rows, meta = [], []
for p in sorted(glob.glob(os.path.join(RAW, "*.json"))):
    d = json.load(open(p, encoding="utf8"))
    meta.append(dict(istituto=d["istituto"], anni="+".join(d["anni"]), n_righe=len(d["righe"]), data_raccolta=d["data_raccolta"]))
    for r in d["righe"]:
        rows.append(dict(istituto=d["istituto"], anni="+".join(d["anni"]), grado=r["grado"], materia=r["materia"],
                         punteggio=r.get("punteggio"), partecipazione=r.get("partecipazione"), diff_escs=r.get("diff_escs"),
                         copertura_background=r.get("copertura_background"), lombardia=r["lombardia"], nord_ovest=r["nord_ovest"], italia=r["italia"],
                         data_raccolta=d["data_raccolta"]))
inv = pd.DataFrame(rows)
meta = pd.DataFrame(meta)
inv["scarto_lombardia"] = inv.punteggio - inv.lombardia
inv.to_csv(os.path.join(BASE, "pulito", "invalsi_istituti.csv"), index=False, sep=";", encoding="utf-8-sig")
print("istituti raccolti (file):", len(meta), "| con almeno un punteggio:", inv[inv.punteggio.notna()].istituto.nunique())
print(meta.anni.value_counts().to_string())

# quota stranieri per istituto e ordine, 2024/25
g = pd.read_csv(os.path.join(BASE, "raw", "miur", "SCUANAGRAFESTAT20252620250901.csv"), dtype=str, keep_default_na=False)
g = g[g.CODICECOMUNESCUOLA == "F205"]
m = g[["CODICESCUOLA", "CODICEISTITUTORIFERIMENTO"]].rename(columns={"CODICESCUOLA": "codice_mecc", "CODICEISTITUTORIFERIMENTO": "istituto"})
a = pd.read_csv(os.path.join(BASE, "pulito", "miur_scuole_anno.csv"), sep=";", dtype={"codice_mecc": str})
a = a[(a.anno_inizio == 2024) & (a.tipo == "statale") & a.ordine.isin(["primaria", "sec1", "sec2"])]
a = a.merge(m, on="codice_mecc", how="left")
print("plessi statali 2024/25 senza istituto di riferimento (anagrafe 2025/26):", a.istituto.isna().sum(), "su", len(a))
a = a.dropna(subset=["istituto"])
q = a.groupby(["istituto", "ordine"]).agg(iscritti=("iscritti", "sum"), nonita=("cittadinanza_non_italiana", "sum"), plessi=("codice_mecc", "nunique")).reset_index()
q["quota"] = q.nonita / q.iscritti * 100
Q = q.pivot(index="istituto", columns="ordine", values=["quota", "iscritti"])
Q.columns = [f"{x}_{y}" for x, y in Q.columns]
Q = Q.reset_index()
Q.to_csv(os.path.join(BASE, "pulito", "invalsi_istituti_quota_stranieri.csv"), index=False, sep=";", encoding="utf-8-sig")

ordine = {"Scuola primaria - classi seconde": "primaria", "Scuola primaria - classi quinte": "primaria",
          "Scuola secondaria di primo grado - classi terze": "sec1"}
print("\nabbinamento (istituti con punteggio nel grado e quota nello stesso ordine):")
x = inv[(inv.anni == "2024/2025") & inv.punteggio.notna()].copy()
x["ord"] = x.grado.map(ordine)
for gr, o in ordine.items():
    s = x[(x.grado == gr)].istituto.nunique()
    print(" ", gr, "| istituti con punteggio 2024/25:", s)
print("istituti con punteggio 2024/25 ma 2025/26 esclusi:", inv[(inv.anni != "2024/2025") & inv.punteggio.notna()].istituto.nunique())
print("istituti nella raccolta senza nessuna quota stranieri (primaria o sec1):",
      len(set(meta.istituto) - set(Q.istituto[Q.quota_primaria.notna() | Q.quota_sec1.notna()])))

rng = np.random.default_rng(1)


def slope(xv, yv):
    return np.polyfit(xv, yv, 1)[0] * 10


def spearman(xv, yv):
    return pd.Series(xv).corr(pd.Series(yv), method="spearman")


out = []
print("\nIncrocio (quota cittadinanza non italiana dell'ordine, 2024/25; pendenza = punti per +10 pp di quota):")
for gr, o in ordine.items():
    for mat in ("Italiano", "Matematica"):
        z = x[(x.grado == gr) & (x.materia == mat)].merge(Q[["istituto", f"quota_{o}", f"iscritti_{o}"]], on="istituto")
        z = z.rename(columns={f"quota_{o}": "quota", f"iscritti_{o}": "iscritti"}).dropna(subset=["quota"])
        for var, lab in (("scarto_lombardia", "punteggio - media Lombardia"), ("diff_escs", "differenza da scuole con ESCS simile")):
            w = z.dropna(subset=[var])
            n = len(w)
            if n < 8:
                continue
            xv, yv = w.quota.values, w[var].values
            b = slope(xv, yv)
            bs = []
            for _ in range(2000):
                i = rng.integers(0, n, n)
                if np.ptp(xv[i]) > 0:
                    bs.append(slope(xv[i], yv[i]))
            lo, hi = np.percentile(bs, [2.5, 97.5])
            out.append(dict(grado=gr, materia=mat, variabile=lab, n_istituti=n, spearman=round(spearman(xv, yv), 2),
                            pendenza_per_10pp=round(b, 2), ic95_lo=round(lo, 2), ic95_hi=round(hi, 2),
                            quota_min=round(xv.min(), 1), quota_max=round(xv.max(), 1)))
res = pd.DataFrame(out)
pd.set_option("display.width", 250, "display.max_columns", 30)
print(res.to_string(index=False))
res.to_csv(os.path.join(BASE, "pulito", "invalsi_istituti_incrocio.csv"), index=False, sep=";", encoding="utf-8-sig")
