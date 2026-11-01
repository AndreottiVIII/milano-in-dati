"""Per ogni Rapporto regionale, trova le pagine con le tabelle degli avvisi SAP (alloggi in avviso, domande, assegnazioni)
e stampa le righe di 'Milano Citta' e le due righe successive (secondo/terzo avviso, con cella ambito vuota).
Uso: python -I -X utf8 04_avvisi_milano.py <cartella_pdf> [...]"""
import sys, glob, os, warnings
warnings.filterwarnings("ignore")
import pymupdf
for d in sys.argv[1:]:
    for f in sorted(glob.glob(os.path.join(d, "*.pdf"))):
        doc = pymupdf.open(f)
        for pno, page in enumerate(doc, 1):
            txt = page.get_text("text")
            if "Milano Citt" not in txt: continue
            try:
                tabs = page.find_tables().tables
            except Exception as e:
                continue
            for t in tabs:
                rows = t.extract()
                hdr = " ".join(str(c) for r in rows[:3] for c in r if c).replace("\n", " ")
                if "ASSEGNAZIONI" not in hdr.upper() and "Alloggi" not in hdr: continue
                for i, r in enumerate(rows):
                    if any(c and "Milano Citt" in c for c in r):
                        print("##", os.path.basename(f), "p.", pno, "| hdr:", hdr[:160])
                        for rr in rows[i:i+3]:
                            print("   ", [(c or "").replace("\n", " ") for c in rr])
