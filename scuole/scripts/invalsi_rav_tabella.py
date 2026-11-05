"""Legge i riquadri 2.2.a.1 salvati e ne fa una riga per istituto, grado e materia. Solo codici, niente nomi.

Uso: python -I -X utf8 invalsi_rav_tabella.py <rav/ind> <rav/scelta.csv> <csv di uscita>
"""
import csv
import os
import re
import sys

import pandas as pd

IND, SC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
num = lambda s: float(s.replace(",", ".")) if re.fullmatch(r"-?\d+(?:[.,]\d+)?", s) else None
righe = []
for r in csv.DictReader(open(SC, encoding="utf8"), delimiter=";"):
    cod = r["istituto"]
    p = os.path.join(IND, cod + "_2.2.a.1.html")
    if not os.path.exists(p):
        continue
    t = open(p, "rb").read().decode("utf8", "replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    celle = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", t, flags=re.S)]
    anni = sorted(set(re.findall(r"a\.s\. (\d{4}/\d{4})", t)))
    et = {}
    i = 0
    while i < len(celle):
        c = celle[i]
        m = re.match(r"(Scuola .* - classi \w+)$", c)
        if m and i + 1 < len(celle) and celle[i + 1] in ("Italiano", "Matematica"):
            grado, mat = m.group(1), celle[i + 1]
            j = i + 2
            while j < len(celle) and "Punteggio nazionale" not in celle[j]:
                j += 1
            rif = [num(x) for x in celle[j + 1:j + 4]]
            k = j + 4
            righe_ist = []
            while k < len(celle) and not (celle[k] == grado and celle[k + 1] in ("Italiano", "Matematica", "Inglese Listening", "Inglese Reading")):
                if celle[k] == grado:
                    righe_ist.append(celle[k + 1:k + 5])
                k += 1
            v = righe_ist[0] if righe_ist else [None] * 4
            diff = num(v[2]) if "quinte" in grado or "terze" in grado else None
            righe.append(dict(istituto=cod, quota_primaria=round(float(r["quota"]), 1), anni="+".join(anni), grado=grado, materia=mat,
                              punteggio=num(v[0] or ""), partecipazione=num(v[1] or ""), diff_escs=diff,
                              lombardia=rif[0], nord_ovest=rif[1], italia=rif[2], righe_nella_tabella=len(righe_ist)))
        i += 1
d = pd.DataFrame(righe)
d.to_csv(OUT, index=False, sep=";", encoding="utf-8-sig")
pd.set_option("display.width", 200, "display.max_rows", 200)
q = d[d.grado.str.contains("quinte|terze")]
print(q.to_string(index=False))
print("\nistituti con punteggi:", d[d.punteggio.notna()].istituto.nunique(), "| con Diff ESCS:", q[q.diff_escs.notna()].istituto.nunique())
for g in ("primaria - classi quinte", "primo grado - classi terze"):
    for m in ("Italiano", "Matematica"):
        x = q[q.grado.str.contains(g) & (q.materia == m)].dropna(subset=["punteggio"])
        if len(x) > 3:
            y = x.dropna(subset=["diff_escs"])
            print(g, m, "n", len(x), "Spearman quota-punteggio", round(x.quota_primaria.corr(x.punteggio, method="spearman"), 2),
                  "| n", len(y), "quota-diff ESCS", round(y.quota_primaria.corr(y.diff_escs, method="spearman"), 2))
