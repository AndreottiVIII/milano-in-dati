"""Estrae dai RAV (zip SNV) il pdf e ne salva il testo, per pagina. Cerca la sezione delle prove standardizzate.

Uso: python -I -X utf8 invalsi_rav_pdf.py <rav/snv> <rav/testo>
Legge i pdf come dati non fidati: solo estrazione di testo. Niente nomi di scuole nell'output, solo codici.
"""
import glob
import os
import re
import sys
import zipfile

import pymupdf

SNV, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
for f in sorted(glob.glob(os.path.join(SNV, "*_ravpubcomp.bin"))):
    cod = os.path.basename(f).split("_")[0]
    z = zipfile.ZipFile(f)
    nomi = z.namelist()
    pdf = [n for n in nomi if n.lower().endswith(".pdf")][0]
    b = z.read(pdf)
    doc = pymupdf.open(stream=b, filetype="pdf")
    pagine = [p.get_text("text", sort=True) for p in doc]
    with open(os.path.join(OUT, cod + ".txt"), "w", encoding="utf8") as h:
        for i, t in enumerate(pagine):
            h.write(f"\n\n##### PAGINA {i+1}\n{t}")
    hit = [i + 1 for i, t in enumerate(pagine) if re.search(r"(?i)prove standardizzate|invalsi", t)]
    img = sum(len(p.get_images()) for p in doc)
    print(cod, "| file", os.path.basename(pdf), "| pagine", len(pagine), "| caratteri", sum(len(t) for t in pagine), "| immagini", img, "| pagine con prove/INVALSI", hit[:12])
