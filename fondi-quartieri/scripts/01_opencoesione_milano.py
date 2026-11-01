"""Estrae da OpenCoesione (progetti_esteso_LOM.zip, tutti i cicli 2007-2027) le righe del Comune di Milano.
Uso: python -I -X utf8 01_opencoesione_milano.py <zip_LOM> <out_csv>
Tiene le righe in cui COD_COMUNE contiene 015146 (ISTAT Milano) o DEN_COMUNE contiene 'Milano' (progetti multi-comune compresi).
Scrive tutte le colonne (separatore ';', come nell'origine). Stampa conteggi."""
import sys, zipfile, io, csv
zp, out = sys.argv[1], sys.argv[2]
csv.field_size_limit(10**9)
z = zipfile.ZipFile(zp)
nome = z.namelist()[0]
t = io.TextIOWrapper(z.open(nome), encoding="utf-8-sig", newline="")
r = csv.reader(t, delimiter=";")
h = next(r)
ic, idn = h.index("COD_COMUNE"), h.index("DEN_COMUNE")
n = k = 0
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(h)
    for row in r:
        n += 1
        if len(row) <= idn:
            continue
        if "015146" in row[ic] or "milano" in row[idn].lower():
            w.writerow(row); k += 1
print(nome, "righe totali", n, "righe Milano", k)
