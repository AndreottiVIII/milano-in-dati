"""Persone senza dimora iscritte in anagrafe (sezioni fittizie 888888x; a Roma 88888xx, una per municipio) nelle 14 grandi citta'.
Uso: python -I -X utf8 citta.py <cartella Comuni_2021> <cartella Comuni_2023> <cartella di uscita>
Legge i file ISTAT per sezione (CC BY 4.0) e scrive citta_2021_2023.csv."""
import sys, glob, os, csv
import openpyxl
c21, c23, out = sys.argv[1:4]
def leggi(cartella):
    ris = {}
    for f in sorted(glob.glob(os.path.join(cartella, '*.xlsx'))):
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        it = ws.iter_rows(values_only=True)
        h = [str(x).strip() if x is not None else '' for x in next(it)]
        i_id = h.index('SEZ21_ID'); i_p = h.index('P1'); i_c = h.index('COMUNE')
        tot = 0; sd = 0; nsd = 0; nome = None
        for r in it:
            if r[i_id] is None: continue
            nome = r[i_c]
            v = r[i_p] or 0
            tot += v
            s = str(int(r[i_id]))
            if s[5:10] == '88888':
                sd += v; nsd += 1
        ris[nome] = (tot, sd, nsd)
    return ris
a = leggi(c21); b = leggi(c23)
with open(os.path.join(out, 'citta_2021_2023.csv'), 'w', encoding='utf-8', newline='') as fo:
    w = csv.writer(fo)
    w.writerow(['citta', 'abitanti_2021', 'senza_dimora_2021', 'sezioni_2021', 'abitanti_2023', 'senza_dimora_2023', 'sezioni_2023'])
    for n in sorted(a):
        t = b.get(n, (None, None, None))
        w.writerow([n, a[n][0], a[n][1], a[n][2], t[0], t[1], t[2]])
        print(n, a[n], t)
