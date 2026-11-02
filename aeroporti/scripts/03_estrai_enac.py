"""Estrae dai PDF ENAC (raw/enac/) i numeri dei tre aeroporti di Milano.

1) Annuario statistico 2003: pagine con la serie 1994-2003 di Linate, Malpensa e Bergamo-Orio al Serio
   (movimenti, passeggeri, cargo; traffico commerciale arrivi + partenze) -> pulito/enac_serie_1994_2003.csv
2) Tavola APT 1 dei rapporti 2007, 2010, 2024, 2025 (un anno per volta) -> pulito/enac_controllo.csv
   (servono come controllo dei dati Eurostat)
Ogni riga ha il numero di pagina del PDF.

uso: python -I -X utf8 03_estrai_enac.py <cartella aeroporti assoluta>
"""
import csv
import os
import re
import sys
import pymupdf

base = sys.argv[1]
raw = os.path.join(base, "raw", "enac")
out = os.path.join(base, "pulito")
os.makedirs(out, exist_ok=True)
NUM = re.compile(r"^-?\d{1,3}(?:\.\d{3})*(?:,\d+)?%?$|^-?\d+(?:,\d+)?%?$")


def it(x):
    """numero all'italiana -> float (punto = migliaia, virgola = decimali)"""
    return float(x.replace("%", "").replace(".", "").replace(",", "."))


# ---------------- 1) annuario 2003
# pagine dell'Annuario 2003 con la serie storica per aeroporto (1994-2003). Per Linate e Malpensa il nome e' nel testo;
# la pagina 156 non ha il nome nel testo ed e' quella di Bergamo (ordine alfabetico: Bari 155, Bergamo 156, Bologna 157):
# lo controlliamo con i valori 2001 e 2002 della Tavola APT 1 dei rapporti 2001 e 2002 (1.046.454 e 1.287.059 passeggeri)
PAGINE = {150: "Italia", 152: "Malpensa", 153: "Linate", 156: "Bergamo"}
d = pymupdf.open(os.path.join(raw, "Dati-di-traffico-2003.pdf"))
rows = []
for pag, ap in PAGINE.items():
    L = [l.strip() for l in d[pag - 1].get_text().split("\n")]
    k = 0
    while k < len(L):
        if re.fullmatch(r"(19|20)\d\d", L[k]):
            vals = L[k + 1:k + 7]
            if len(vals) == 6 and all(NUM.match(v) or v == "-" for v in vals) and it(vals[0]) >= 5000:
                rows.append((ap, int(L[k]), int(it(vals[0])), int(it(vals[2])), int(it(vals[4])), pag))
                k += 7
                continue
        k += 1
berg = {r[1]: r[3] for r in rows if r[0] == "Bergamo"}
assert berg.get(2001) == 1046454 and berg.get(2002) == 1287059, berg
ita = {r[1]: r[3] for r in rows if r[0] == "Italia"}
assert abs(ita.get(2001, 0) - 90210038) < 1000, ita  # totale della Tavola APT 1 del rapporto 2001 (90.210.038; piccola revisione di 270)
rows.sort()
with open(os.path.join(out, "enac_serie_1994_2003.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";", lineterminator="\n")
    w.writerow(["aeroporto", "anno", "movimenti", "passeggeri", "cargo_tonnellate", "pagina_pdf_annuario_2003"])
    w.writerows(rows)
print("serie 1994-2003:", len(rows), "righe")

# ---------------- 2) tavola APT 1 (controllo)
# ordine delle colonne: 2007, 2010 = movimenti, passeggeri, transiti, cargo ; 2024, 2025 = passeggeri, transiti, cargo, movimenti
CFG = {2007: (9, "mpTc"), 2010: (13, "mpTc"), 2024: (76, "pTcm"), 2025: (74, "pTcm")}
KEY = {"MILANO LINATE": "Linate", "MILANO MALPENSA": "Malpensa", "BERGAMO ORIO AL SERIO": "Bergamo", "BERGAMO": "Bergamo", "TOTALE": "Italia"}
res = []
for anno, (pag, ordine) in CFG.items():
    doc = pymupdf.open(os.path.join(raw, f"Dati-di-traffico-{anno}.pdf"))
    L = [l.strip() for l in doc[pag - 1].get_text().split("\n")]
    L = [l for l in L if l != ""]
    for k, l in enumerate(L):
        name = re.sub(r"^\d+\s+", "", l).upper()
        if name in KEY:
            toks = [t for t in L[k + 1:k + 14] if NUM.match(t)]
            vals = [it(t) for t in toks[0:8:2]]  # numero, %, numero, %, ... -> prendo le posizioni 0,2,4,6
            r = dict(zip(ordine, vals))
            res.append((KEY[name], anno, int(r["m"]), int(r["p"]), int(r["T"]), r["c"], pag))
            if KEY[name] == "Italia":
                pass
rows2 = []
seen = set()
for r in res:
    key = (r[0], r[1])
    if key in seen:
        continue
    seen.add(key)
    rows2.append(r)
with open(os.path.join(out, "enac_controllo.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";", lineterminator="\n")
    w.writerow(["aeroporto", "anno", "movimenti_commerciali", "passeggeri", "transiti_diretti", "cargo_tonnellate", "pagina_pdf"])
    w.writerows(rows2)
for r in sorted(rows2, key=lambda x: (x[1], x[0])):
    print(r)
