"""OpenCUP (registro dei CUP, CC-BY, aggiornato al 1/10/2026): progetti localizzati a Milano nel settore "abitativo".
Uso: python -I -X utf8 06_opencup_milano_abitativo.py <OpendataProgetti.zip> <loc_milano.csv> <out_csv>
Tiene i CUP che (a) risultano localizzati nel Comune di Milano (loc_milano.csv, script 04) e (b) hanno SOTTOSETTORE_INTERVENTO = ABITATIVE
oppure titolare/descrizione con ALER, MM S.P.A. + ERP/alloggi/edilizia residenziale. Esclude gli incentivi a imprese (NATURA 07).
Nota: un CUP puo' avere piu' comuni; qui si tiene se Milano e' uno dei comuni (colonna n_comuni = quante localizzazioni nel file Localizzazione non e' calcolata)."""
import sys, zipfile, io, csv, re
zp, locp, out = sys.argv[1:4]
csv.field_size_limit(10**9)
milano = set()
with open(locp, encoding="utf-8", newline="") as f:
    r = csv.reader(f, delimiter=";"); h = next(r); ic = h.index("CUP")
    for row in r:
        milano.add(row[ic])
print("CUP localizzati a Milano:", len(milano))
z = zipfile.ZipFile(zp)
KW = re.compile(r"\bERP\b|EDILIZIA RESIDENZIALE|EDILIZIA PUBBLICA|ALLOGGI|ALLOGGIO|CASE POPOLARI|ABITAZIONI", re.I)
ENTI = re.compile(r"\bALER\b|AZIENDA LOMBARDA EDILIZIA|\bMM S\.?P\.?A|METROPOLITANA MILANESE", re.I)
n = k = 0
with open(out, "w", encoding="utf-8", newline="") as fo:
    w = None
    for name in z.namelist():
        t = io.TextIOWrapper(z.open(name), encoding="utf-8-sig", newline="")
        r = csv.reader(t, delimiter=";")
        h = next(r)
        if w is None:
            w = csv.writer(fo, delimiter=";"); w.writerow(h)
        i = {c: h.index(c) for c in ("CUP", "SOTTOSETTORE_INTERVENTO", "COD_NATURA_DIPE", "CODICE_NATURA_INTERVENTO", "SOGGETTO_TITOLARE", "DESCRIZIONE_SINTETICA_CUP", "DESCRIZIONE_INTERVENTO")}
        for row in r:
            n += 1
            if row[i["CUP"]] not in milano:
                continue
            if row[i["CODICE_NATURA_INTERVENTO"]] == "07":
                continue
            ab = row[i["SOTTOSETTORE_INTERVENTO"]] == "ABITATIVE"
            tx = row[i["DESCRIZIONE_SINTETICA_CUP"]] + " " + row[i["DESCRIZIONE_INTERVENTO"]]
            en = ENTI.search(row[i["SOGGETTO_TITOLARE"]]) is not None
            if ab or (en and KW.search(tx)):
                w.writerow(row); k += 1
        print(name, n, k, flush=True)
print("righe totali", n, "tenute", k)
