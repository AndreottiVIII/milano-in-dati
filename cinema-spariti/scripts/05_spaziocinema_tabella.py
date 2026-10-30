import sys, csv, pymupdf
src, dst = sys.argv[1], sys.argv[2]
d = pymupdf.open(src)
rows = []
for i, p in enumerate(d):
    for t in p.find_tables().tables:
        for r in t.extract():
            r = [(c or "").replace("\n", " ").strip() for c in r]
            if r[0].lower().startswith("sala cinemat") or r[0].startswith("SALE CINEMAT") or not any(r): continue
            rows.append([i + 1] + r)
with open(dst, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["pagina", "sala", "periodo", "indirizzo"]); w.writerows(rows)
print(len(rows))
