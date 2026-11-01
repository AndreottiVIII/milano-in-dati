"""Inventario dei file in raw/ (percorso, byte, sha256 corto). Uso: python -I -X utf8 inventario.py <antenne_dir>
Scrive pulito/inventario_file.csv"""
import sys, os, hashlib, csv
A = sys.argv[1]
rows = []
for dp, dn, fn in os.walk(os.path.join(A, "raw")):
    for f in sorted(fn):
        p = os.path.join(dp, f)
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        rows.append([os.path.relpath(p, A).replace(os.sep, "/"), os.path.getsize(p), h])
with open(os.path.join(A, "pulito", "inventario_file.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["file", "byte", "sha256_16"])
    w.writerows(rows)
print(len(rows), "file")
