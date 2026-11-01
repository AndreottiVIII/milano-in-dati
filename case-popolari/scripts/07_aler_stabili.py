"""Estrae da ALER Milano (amministrazione trasparente, 'canoni incassati') l'elenco dei fabbricati con il canone fatturato per anno
(2013, 2015, 2016; PDF con colonne LOCALITA', INDIRIZZO, CANONE FATTURATO) e scrive pulito/aler_stabili_canone_<anno>.csv.
Sono dati per EDIFICIO (indirizzo + civico), non per inquilino ne' per singolo alloggio.
Uso: python -I -X utf8 07_aler_stabili.py <cartella canoni> <cartella pulito>   (percorsi assoluti)"""
import sys, os, re, csv, warnings
warnings.filterwarnings("ignore")
import pymupdf

src, out = sys.argv[1], sys.argv[2]
AMT = re.compile(r"^-?\d{1,3}(\.\d{3})*,\d{2}$")
STREET = {"VIA", "VIALE", "PIAZZA", "PIAZZALE", "CORSO", "LARGO", "VICOLO", "VICOLETTO", "STRADA", "VIALETTO", "ALZAIA", "BASTIONI", "CAVALCAVIA",
          "GALLERIA", "RIPA", "PASSAGGIO", "SALITA", "SENTIERO", "TRAVERSA", "CASCINA", "C.NA", "FRAZIONE", "LOCALITA'", "LUNGOLAMBRO", "RACCORDO",
          "STRADONE", "VIA-", "CIRCONVALLAZIONE", "PIAZZETTA", "SS", "S.S.", "SP", "S.P."}
for anno in (2013, 2015, 2016):
    doc = pymupdf.open(os.path.join(src, f"prospetto_{anno}.pdf"))
    rows = []
    pend = None
    for pno, page in enumerate(doc, 1):
        ws = page.get_text("words")
        lines = {}
        for w in ws:
            lines.setdefault(round((w[1] + w[3]) / 2 / 3), []).append(w)
        for k in sorted(lines):
            L = sorted(lines[k], key=lambda w: w[0])
            toks = [w[4] for w in L]
            if toks[0] in ("LOCALITA'", "INDIRIZZO") or toks[0].startswith("Il") or toks[0] in ("canone", "Pertanto", "stata", "2016.", "monte"):
                continue
            amt = toks[-1] if AMT.match(toks[-1]) and L[-1][0] > 380 else None
            body = toks[:-1] if amt else toks
            # separa localita' e indirizzo con la prima parola di tipo via
            idx = next((i for i, t in enumerate(body) if t in STREET), None)
            if idx is None:
                loc, addr = (" ".join(body), "")
            else:
                loc, addr = " ".join(body[:idx]), " ".join(body[idx:])
            rows.append(dict(anno=anno, pagina=pno, localita=loc, indirizzo=addr, canone_fatturato=(amt or "").replace(".", "").replace(",", ".") if amt else "", y=round(L[0][1])))
    # riempie localita'/indirizzo/canone sulle righe spezzate (celle a capo): unisce con la riga precedente se mancano pezzi
    clean = []
    for r in rows:
        if clean and not r["localita"] and r["indirizzo"] and not clean[-1]["indirizzo"]:
            clean[-1]["indirizzo"] = r["indirizzo"]
            if r["canone_fatturato"] and not clean[-1]["canone_fatturato"]:
                clean[-1]["canone_fatturato"] = r["canone_fatturato"]
            continue
        clean.append(r)
    fn = os.path.join(out, f"aler_stabili_canone_{anno}.csv")
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["anno", "pagina", "localita", "indirizzo", "canone_fatturato"])
        w.writeheader()
        for r in clean:
            w.writerow({k: r[k] for k in w.fieldnames})
    mi = [r for r in clean if r["localita"].startswith("MILANO")]
    tot = sum(float(r["canone_fatturato"]) for r in mi if r["canone_fatturato"])
    print(anno, "righe", len(clean), "Milano", len(mi), "con importo", sum(1 for r in mi if r["canone_fatturato"]), "somma canone Milano", round(tot))
