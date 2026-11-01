"""Estrae dalle Carte della Mobilita ATM (PDF, testo gia' estratto da 03_pdf_text.py) la tabella 'ATM in numeri':
passeggeri trasportati (rete ATM Milano, metro + superficie), corse metro al giorno, linee/lunghezza/stazioni metro. Con pagina PDF.
Uso: python -I -X utf8 08_carta_atm.py <pdf_txt_dir> <out_csv>"""
import sys, re, csv, os, glob
d, out = sys.argv[1], sys.argv[2]
def fix_staz(v):
    # il testo estratto attacca il numero della nota a pie di pagina (es. 119 + nota 18 -> 11918)
    return v[:3] if v and int(v) > 200 else v
rows = []
for f in sorted(glob.glob(os.path.join(d, "ATM_Carta_Mobilita_*.txt"))):
    anno_carta = int(re.search(r"(\d{4})\.txt", f).group(1))
    t = open(f, encoding="utf-8").read()
    pages = re.split(r"===PAGINA (\d+)===", t)
    for i in range(1, len(pages), 2):
        pg, txt = int(pages[i]), pages[i+1]
        m = re.search(r"Passeggeri trasportati\s*\n\s*([\d.]{9,})", txt)
        if not m: continue
        da = re.search(r"Dati al 31\.12\.(\d{4})", txt)
        flat = re.sub(r"\s+", " ", txt)
        def g(p):
            mm = re.search(p, flat); return mm.group(1) if mm else ""
        rows.append([int(da.group(1)) if da else anno_carta-1, m.group(1).replace(".", ""), 
                     g(r"in metropolitana \(media annuale\) ([\d.]+)").replace(".", ""),
                     g(r"RETE METROPOLITANA Numero linee ([\d]+)"), g(r"RETE METROPOLITANA Numero linee \d+ Lunghezza rete \(km\) ([\d,]+)"),
                     fix_staz(g(r"Numero stazioni ([\d]+)")), os.path.basename(f).replace(".txt", ".pdf"), pg])
        break
w = csv.writer(open(out, "w", newline="", encoding="utf-8"))
w.writerow(["anno_dati", "passeggeri_rete_atm_metro_e_superficie", "corse_giorno_metro_lun_ven_inv_media", "linee_metro", "lunghezza_metro_km", "stazioni_metro", "file", "pagina_pdf"])
w.writerows(sorted(rows)); 
for r in sorted(rows): print(r)
