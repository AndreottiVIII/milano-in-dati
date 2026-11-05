"""ISTAT DELITTI_PERS_CONDAN_1985_2008: tavole annuali 2000-2008, per provincia -> pulito/istat_2000_2008_omicidi_territori.csv
Uso: python -I -X utf8 02_estrai_2000_2008.py <cartella omicidi>"""
import sys, os, csv, xlrd
B = sys.argv[1]
d = os.path.join(B, "raw/istat_delitti_1985_2008/estratto/DELITTI_PERS_CONDAN_1985_2008/DELITTI DENUNCIATI DA FFPP A AUTOR GIUDIZ 2000_2008")
out = []
for anno in range(2000, 2009):
    wb = xlrd.open_workbook(os.path.join(d, f"DELITTI DENUNCIATI DA FFPP A AUTOR GIUDIZ {anno}.xls"))
    s = None
    for sh in wb.sheets():
        heads = " ".join(str(c) for i in range(0, 4) for c in sh.row_values(i))
        if "Omicidi volontari" in heads or "Omicidi dolosi" in heads:
            s = sh; break
    h1 = [str(c).strip() for c in s.row_values(1)]; h2 = [str(c).strip() for c in s.row_values(2)]
    print(anno, s.name, [(j, x[:28]) for j, x in enumerate(h1) if x][:9], [(j, x[:22]) for j, x in enumerate(h2) if x][:9], str(s.row_values(0)[0])[:110])
    ic = next(j for j, x in enumerate(h1) if "Omicidi" in x and ("volontari" in x or "dolosi" in x))
    it = next((j for j, x in enumerate(h1) if "Tentati" in x), None)
    im = ic + 1
    for i in range(3, s.nrows):
        r = s.row_values(i); nome = str(r[0]).strip()
        if not nome or len(nome) > 40 or not (isinstance(r[ic], float) or str(r[ic]).strip() == "-"): continue
        num = lambda v: int(v) if isinstance(v, float) else 0
        out.append({"anno": anno, "territorio": nome, "om_consumati": num(r[ic]), "om_mafia": num(r[im]), "tentati": (num(r[it]) if it is not None else "")})
with open(os.path.join(B, "pulito/istat_2000_2008_omicidi_territori.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
for a in range(2000, 2009):
    print(a, {d["territorio"]: (d["om_consumati"], d["tentati"]) for d in out if d["anno"] == a and d["territorio"] in ("Milano","Monza e della Brianza","Lodi","ITALIA","Italia","Roma","Lombardia","LOMBARDIA")})
