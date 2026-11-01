"""Inventario dei file in raw/ (nome, dimensione, SHA-256 per i file sotto 400 MB). Uso: python -I -X utf8 08_inventario_raw.py <fondi-quartieri>"""
import os, sys, csv, hashlib
F = sys.argv[1]
rows = []
for r, _, fs in os.walk(os.path.join(F, "raw")):
    for f in sorted(fs):
        p = os.path.join(r, f)
        n = os.path.getsize(p)
        h = ""
        if n < 400e6:
            m = hashlib.sha256()
            with open(p, "rb") as fh:
                for b in iter(lambda: fh.read(1 << 20), b""):
                    m.update(b)
            h = m.hexdigest()
        rows.append((os.path.relpath(p, F).replace(os.sep, "/"), n, h))
with open(os.path.join(F, "pulito", "inventario_file_raw.csv"), "w", newline="", encoding="utf-8") as o:
    w = csv.writer(o, delimiter=";"); w.writerow(["file", "byte", "sha256"]); w.writerows(rows)
print(len(rows), "file")
