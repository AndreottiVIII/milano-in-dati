"""Estrae il testo dei PDF pagina per pagina in <out_dir>/<nome>.txt (marcatore ===PAGINA n===). Uso: python -I -X utf8 03_pdf_text.py <pdf_dir> <out_dir>"""
import sys, os
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
import pymupdf
for f in sorted(os.listdir(src)):
    if not f.lower().endswith(".pdf"): continue
    doc = pymupdf.open(os.path.join(src, f))
    with open(os.path.join(out, f[:-4] + ".txt"), "w", encoding="utf-8") as o:
        for i, p in enumerate(doc, 1):
            o.write(f"\n===PAGINA {i}===\n" + p.get_text())
    print(f, len(doc))
