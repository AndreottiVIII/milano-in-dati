"""Popolazione residente al 1 gennaio (ISTAT, demo.istat.it) per Milano, Roma, Torino, Napoli, Bologna,
Lombardia, Italia. 2002-2019: ricostruzione intercensuaria (riga 'Totale' del blocco 'Tutte le cittadinanze', totale);
2020-2026: POSAS (somma delle eta' di 'Totale' = ultima colonna). Scrive pulito/popolazione_1gen.csv.
Uso: python -I -X utf8 popolazione.py <percorso assoluto redditi>"""
import sys, os, zipfile, csv, io, re
base = sys.argv[1]; D = os.path.join(base, "raw", "istat_pop"); OUT = os.path.join(base, "pulito")
CITTA = {"Milano": "015146", "Roma": "058091", "Torino": "001272", "Napoli": "063049", "Bologna": "037006"}
LOMB = {"012", "013", "014", "015", "016", "017", "018", "019", "020", "097", "098", "108"}
out = []
z = zipfile.ZipFile(os.path.join(D, "ricostruzione_2002_2019_comuni.zip"))
names = z.namelist()
for c, code in CITTA.items():
    n = [x for x in names if f"Comune_{code}-" in x]; assert len(n) == 1, (c, n)
    L = z.read(n[0]).decode("utf8").splitlines()
    anni = [int(a) for a in L[4].split(";")[1:]]
    tot = next(l for l in L if l.startswith("Totale")).split(";")[1:]
    for a, v in zip(anni, tot):
        out.append([c, a, int(v), f"ricostruzione_2002_2019_comuni.zip / {n[0]} / riga Totale (tutte le cittadinanze)"])
zr = zipfile.ZipFile(os.path.join(D, "ricostruzione_2002_2019_Regioni.zip"))
L = zr.read(zr.namelist()[0]).decode("utf8").splitlines()
idx = [i for i, l in enumerate(L) if l.startswith('"Tutte le cittadinanze - Regione: Lombardia')]; assert len(idx) == 1
i = idx[0]; anni = [int(a) for a in L[i + 1].split(";")[1:]]
tot = next(l for l in L[i:] if l.startswith("Totale")).split(";")[1:]
for a, v in zip(anni, tot): out.append(["Lombardia", a, int(v), "ricostruzione_2002_2019_Regioni.zip / blocco Lombardia, Tutte le cittadinanze, riga Totale"])
zi = zipfile.ZipFile(os.path.join(D, "ricostruzione_2002_2019_Italia-Ripartizioni.zip"))
L = zi.read(zi.namelist()[0]).decode("utf8").splitlines()
anni = [int(a) for a in L[4].split(";")[1:]]
tot = next(l for l in L if l.startswith("Totale")).split(";")[1:]
for a, v in zip(anni, tot): out.append(["Italia", a, int(v), "ricostruzione_2002_2019_Italia-Ripartizioni.zip / blocco Italia, Tutte le cittadinanze, riga Totale"])

for y in range(2020, 2027):
    zf = zipfile.ZipFile(os.path.join(D, f"POSAS_{y}_it_Comuni.zip"))
    s = zf.read(zf.namelist()[0]).decode("utf8")
    r = csv.reader(io.StringIO(s), delimiter=";"); next(r); hdr = next(r)
    ti = len(hdr) - 1
    assert hdr[ti].strip().lower() == "totale", hdr[ti]
    tot = {}; ital = 0; lomb = 0
    for row in r:
        if len(row) < ti + 1 or not row[0].strip(): continue
        code = row[0].strip().zfill(6); eta = row[2].strip()
        if eta == "999": continue
        v = int(row[ti])
        tot[code] = tot.get(code, 0) + v; ital += v
        if code[:3] in LOMB: lomb += v
    src = f"POSAS_{y}_it_Comuni.zip / colonna Totale, somma delle eta'"
    for c, code in CITTA.items(): out.append([c, y, tot[code], src])
    out.append(["Lombardia", y, lomb, src + " (province 012-020, 097, 098, 108)"]); out.append(["Italia", y, ital, src])
with open(os.path.join(OUT, "popolazione_1gen.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["unita", "anno_1_gennaio", "popolazione", "fonte"]); w.writerows(sorted(out, key=lambda r: (r[0], r[1])))
print(len(out), "righe")
