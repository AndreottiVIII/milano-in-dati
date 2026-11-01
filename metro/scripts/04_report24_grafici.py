"""Legge dal PDF vettoriale del Report della Mobilita 2024 (AMAT, 3a edizione) tre grafici, leggendo la posizione dei marcatori:
 A) pdf pag. 48 (stampata 94): passeggeri rete TPL, 2016-2024 (asse 350-850 mln)
 B) pdf pag. 48: passeggeri rete metropolitana per linea, 2016-2024 (asse 0-160 mln). Le serie NON sono cumulative: la somma 2024 e' 340 mln (testo: 'oltre 341')
 C) pdf pag. 81 (stampata 160-161): passeggeri ingresso/uscita Linate M4 per mese, dic 2022-dic 2024 (asse 0-400 migliaia)
Precisione di lettura circa +-0,5 mln (A: +-2 mln; C: +-3 mila). Uso: python -I -X utf8 04_report24_grafici.py <pdf> <out_dir>"""
import sys, csv, os, pymupdf
pdf, out = sys.argv[1], sys.argv[2]
doc = pymupdf.open(pdf)
def calib(page, label_vals, xmax, ymin, ymax):
    """usa le etichette numeriche dell'asse: posizione verticale del centro -> valore (regressione lineare sui punti)"""
    pts = []
    for w in page.get_text("words"):
        if w[0] < xmax and ymin < w[1] < ymax and w[4].replace(".", "").isdigit() and int(w[4].replace(".", "")) in label_vals:
            pts.append(((w[1]+w[3])/2, int(w[4].replace(".", ""))))
    n = len(pts); sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
    sxx = sum(p[0]**2 for p in pts); sxy = sum(p[0]*p[1] for p in pts)
    a = (n*sxy - sx*sy)/(n*sxx - sx**2); b = (sy - a*sx)/n
    return lambda y: a*y + b
# ---- pagina 48
p = doc[47]; dr = p.get_drawings()
fA = calib(p, {350,400,450,500,550,600,650,700,750,800,850}, 120, 190, 380)
fB = calib(p, {0,20,40,60,80,100,120,140,160}, 120, 540, 800)
# A: marcatori rotondi piccoli 4.7 pt nella zona sup. sx
A = sorted([(round(x["rect"].x0+2.35, 1), round(fA((x["rect"].y0+x["rect"].y1)/2), 1)) for x in dr
            if abs(x["rect"].width-4.7) < 0.2 and 190 < x["rect"].y0 < 380 and x["rect"].x0 < 450 and x.get("fill")])
anni = list(range(2016, 2025))
rowsA = [(anni[i], v) for i, (x, v) in enumerate(A)]
cols = {(0.859,0.29,0.29): "M1", (0.361,0.588,0.341): "M2", (0.878,0.627,0.0): "M3", (0.769,0.6,0.769): "M5", (0.161,0.231,0.6): "M4"}
B = []
for x in dr:
    r = x["rect"]; f = x.get("fill")
    if f and abs(r.width-7.1) < 0.3 and 500 < r.y0 < 800:
        k = tuple(round(c, 3) for c in f)
        if k in cols: B.append((cols[k], round((r.x0+r.x1)/2, 1), round(fB((r.y0+r.y1)/2), 1)))
rowsB = []
for l in ("M1", "M2", "M3", "M4", "M5"):
    xs = sorted([b for b in B if b[0] == l], key=lambda b: b[1])
    # x dei 9 anni sulla griglia M1
    gx = sorted([b[1] for b in B if b[0] == "M1"])
    for b in xs: rowsB.append((l, anni[gx.index(b[1])], b[2]))
# ---- pagina 81 (C)
p = doc[80]; dr = p.get_drawings()
fC = calib(p, {0,50,100,150,200,250,300,350,400}, 770, 130, 380)
C = sorted([(round(x["rect"].x0+x["rect"].width/2, 1), round(fC((x["rect"].y0+x["rect"].y1)/2), 1)) for x in dr
            if 3 < x["rect"].width < 6 and abs(x["rect"].width-x["rect"].height) < 0.5 and x["rect"].x0 > 770 and 130 < x["rect"].y0 < 380 and x.get("fill")])
mesi = ["dic","gen","feb","mar","apr","mag","giu","lug","ago","set","ott","nov"]
rowsC = []
for i, (x, v) in enumerate(C):
    y = 2022 + (i+11)//12; m = (i+11) % 12 + 1
    rowsC.append((f"{y}-{m:02d}", v))
os.makedirs(out, exist_ok=True)
for name, hdr, rows in (("report24_tpl_totale_anno.csv", ["anno","passeggeri_mln_letto_da_grafico"], rowsA),
                        ("report24_metro_linea_anno.csv", ["linea","anno","passeggeri_mln_letto_da_grafico"], rowsB),
                        ("report24_m4_linate_mese.csv", ["mese","passeggeri_migliaia_letto_da_grafico"], rowsC)):
    w = csv.writer(open(os.path.join(out, name), "w", newline="", encoding="utf-8")); w.writerow(hdr); w.writerows(rows)
    print(name, len(rows))
print("A", rowsA); print("somma metro per anno", {a: round(sum(v for l, y, v in rowsB if y == a), 1) for a in anni}); print("C", len(C), rowsC[:4], rowsC[-3:])
