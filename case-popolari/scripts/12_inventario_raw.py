"""Elenca i file in raw/ (percorso relativo, byte, sha256, data di modifica sul disco = data di scaricamento) in pulito/inventario_file_raw.csv.
Uso: python -I -X utf8 12_inventario_raw.py <case-popolari>   (percorso assoluto)"""
import sys, os, hashlib, csv, datetime
base = sys.argv[1]
raw = os.path.join(base, "raw")
rows = []
for d, _, fs in os.walk(raw):
    for f in sorted(fs):
        p = os.path.join(d, f)
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        rows.append(dict(file=os.path.relpath(p, raw).replace("\\", "/"), byte=os.path.getsize(p), sha256=h,
                         data=datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")))
with open(os.path.join(base, "pulito", "inventario_file_raw.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file", "byte", "sha256", "data"]); w.writeheader(); w.writerows(rows)
print(len(rows), "file,", round(sum(r["byte"] for r in rows) / 1e6, 1), "MB")
