"""Stampa fogli e prime righe di un xls. Uso: esplora_xls.py <file> [righe]"""
import sys, xlrd
wb = xlrd.open_workbook(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
print(len(wb.sheets()), "fogli")
for s in wb.sheets():
    print("---", repr(s.name), s.nrows, s.ncols)
    for i in range(min(n, s.nrows)):
        v = [c for c in s.row_values(i) if c != ""]
        if v: print(i, [str(x)[:40] for x in v][:12])
