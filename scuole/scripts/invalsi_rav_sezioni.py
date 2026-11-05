"""Stampa dai testi dei RAV la sezione 'Risultati nelle prove standardizzate' e tutte le frasi con numeri vicino a INVALSI.

Uso: python -I -X utf8 invalsi_rav_sezioni.py <rav/testo> <rav/scelta.csv>
"""
import csv
import os
import re
import sys

TXT, SC = sys.argv[1], sys.argv[2]
for r in csv.DictReader(open(SC, encoding="utf8"), delimiter=";"):
    cod = r["istituto"]
    t = open(os.path.join(TXT, cod + ".txt"), encoding="utf8").read()
    pag = re.split(r"##### PAGINA \d+\n", t)
    print("=" * 90)
    print(cod, "quota primaria", round(float(r["quota"]), 1))
    corpo = []
    for p in pag:
        testa = p[:400]
        if re.search(r"Risultati nelle prove standardizzate", testa) and "INDICE" not in testa:
            corpo.append(p)
    s = re.sub(r"[ \t]+", " ", "\n".join(corpo))
    s = re.sub(r"\n\s*\n+", "\n", s)
    i = s.find("Motivazione dell'autovalutazione")
    print("--- pagine di sezione:", len(corpo), "| caratteri:", len(s))
    print(s[i:i + 2200] if i >= 0 else s[:1500])
    tutto = re.sub(r"\s+", " ", t)
    print("--- frasi con numeri e INVALSI in tutto il documento")
    frasi = re.split(r"(?<=[.;:])\s+", tutto)
    k = 0
    for f in frasi:
        if re.search(r"(?i)invalsi|prove standardizzate|effetto scuola|cheating|punteggi", f) and re.search(r"\d", f) and not re.search(r"Triennio di riferimento", f[:60]):
            print("  *", f[:420])
            k += 1
            if k >= 14:
                break
    print("--- parole: ESCS", len(re.findall(r"ESCS", t)), "| WLE", len(re.findall(r"WLE", t)), "| 'punteggio'", len(re.findall(r"(?i)punteggi", t)), "| tabelle di indicatori (2.2.a.)", len(re.findall(r"2\.2\.[a-z]", t)))
