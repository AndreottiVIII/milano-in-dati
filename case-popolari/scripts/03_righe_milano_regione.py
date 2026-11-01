"""Estrae da ogni Rapporto annuale al Consiglio regionale (PDF) le righe 'Milano Citta' (tabelle per ambito), con la pagina.
Uso: python -I -X utf8 03_righe_milano_regione.py <cartella_pdf_1> [<cartella_2> ...]   (percorsi assoluti)
Stampa: file | pagina | testo della riga (parole ordinate per x). Le intestazioni delle tabelle vanno lette a mano (vedi NOTE)."""
import sys, glob, os, re
import warnings; warnings.filterwarnings("ignore")
import pymupdf
for d in sys.argv[1:]:
    for f in sorted(glob.glob(os.path.join(d, "*.pdf"))):
        doc = pymupdf.open(f)
        for pno, page in enumerate(doc, 1):
            words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
            for i, w in enumerate(words):
                if w[4].startswith("Milano") and i + 1 < len(words) and words[i+1][4].startswith("Citt"):
                    yc = (w[1] + w[3]) / 2
                    row = sorted([x for x in words if abs((x[1]+x[3])/2 - yc) < 4], key=lambda x: x[0])
                    print(os.path.basename(f), "| p.", pno, "|", " ".join(x[4] for x in row))
