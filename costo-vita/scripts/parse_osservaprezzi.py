"""Legge le pagine HTML dell'Osservatorio Prezzi e Tariffe (MIMIT) scaricate in raw/mimit_osservaprezzi/ e scrive
pulito/prezzi_medi_milano_mimit.csv. Controlla che anno, mese e provincia selezionati nella pagina siano quelli richiesti.
Uso: python -I -X utf8 parse_osservaprezzi.py <costo-vita assoluto>"""
import sys, os, re, glob, csv, html
C = sys.argv[1]
rows = []; bad = []
for fn in sorted(glob.glob(os.path.join(C, "raw", "mimit_osservaprezzi", "*.html"))):
    b = os.path.basename(fn)[:-5]; anno, mese, tipo = b.split("_", 2)
    t = open(fn, encoding="utf-8", errors="replace").read()
    sel = re.findall(r"selected='selected'\s+value=\"([^\"]*)\"", t)
    if sel[:4] != [anno, str(int(mese)), "Milano", tipo]:
        bad.append((b, sel[:4])); continue
    for m in re.finditer(r'<td data-label="Descrizione Prodotto">(.*?)</td>.*?Minima">(.*?)</td>.*?Massima">(.*?)</td>.*?Media">(.*?)</td>', t, re.S):
        d, a, bmax, med = [re.sub(r"\s+", " ", html.unescape(x)).strip() for x in m.groups()]
        mm = re.match(r"(.*) \(([\d.,]+) ?([A-Za-z0-9]+)\)$", d)
        nome, qta, um = (mm.group(1), mm.group(2), mm.group(3)) if mm else (d, "", "")
        rows.append([int(anno), int(mese), tipo, nome, qta, um, float(a), float(bmax), float(med)])
rows.sort()
with open(os.path.join(C, "pulito", "prezzi_medi_milano_mimit.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["anno", "mese", "tipologia", "prodotto", "quantita", "unita", "prezzo_min_eur", "prezzo_max_eur", "prezzo_medio_eur"]); w.writerows(rows)
print(len(rows), "righe;", len(set((r[0], r[1]) for r in rows)), "mesi;", "pagine con selezione diversa dalla richiesta:", bad[:5], len(bad))
