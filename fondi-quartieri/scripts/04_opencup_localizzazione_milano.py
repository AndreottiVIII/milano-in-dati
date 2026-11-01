"""OpenCUP: elenco dei CUP localizzati nel Comune di Milano (codice ISTAT 015146).
Uso: python -I -X utf8 04_opencup_localizzazione_milano.py <OpendataLocalizzazione.zip> <out_csv>
Un CUP puo' avere piu' localizzazioni (piu' comuni): si tengono tutte le righe con COD comune 015146 e si segna se il CUP e' multi-comune
(conteggio righe totali per CUP non calcolato qui: il file e' ordinato per CUP? no, quindi si scrive solo la riga Milano)."""
import sys, zipfile, io, csv
zp, out = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(zp)
t = io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8-sig", newline="")
r = csv.reader(t, delimiter=";")
h = next(r)
ic = h.index("CODICE_COMUNE")
n = k = 0
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(h)
    for row in r:
        n += 1
        if row[ic] == "015146":
            w.writerow(row); k += 1
print("righe", n, "Milano", k)
