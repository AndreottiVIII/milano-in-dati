"""Metadati (API metadata) degli elementi IA utili: accesso (aperto/prestito) e presenza del testo OCR. Riprendibile."""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia_cerca as ia
d1 = json.load(open(os.path.join(ia.ROOT, "raw", "ia_scala", "tutti.json"), encoding="utf8"))
d2 = json.load(open(os.path.join(ia.ROOT, "raw", "ia_scala", "tutti2.json"), encoding="utf8"))
tutti = dict(d1); tutti.update(d2)
def utile(x):
    t = (str(x.get("title")) + " " + str(x.get("creator"))).lower()
    if x.get("mediatype") != "texts": return False
    try: y = int(str(x.get("year", "0"))[:4])
    except Exception: y = 0
    if re.search(r"teatro alla scala|la scala|scala", t) and (y >= 1900 or re.search(r"rivista|annuario|cronolog|programma", t)): return True
    return bool(re.search(r"cambiasi|romani|marangoni|gatti", t))
sel = [x for x in tutti.values() if utile(x) and not re.search(r"da rappresentarsi|dramma|melodramma|opera in|cia-readingroom|phlebotomia", (str(x.get("title")) + x["identifier"]).lower())]
print("elementi da controllare:", len(sel), flush=True)
righe = []
for x in sel:
    ident = x["identifier"]
    try: m = ia.get("https://archive.org/metadata/" + ident, "meta_" + re.sub(r"[^\w.-]", "_", ident)[:100] + ".json")
    except Exception as e: print(ident, "ERR", e); continue
    files = m.get("files", [])
    nomi = [f["name"] for f in files]
    testo = [f for f in files if f["name"].endswith(("_djvu.txt", "_hocr_searchtext.txt.gz", ".txt"))]
    pdf = [f for f in files if f["name"].lower().endswith(".pdf")]
    md = m.get("metadata", {})
    righe.append(dict(identifier=ident, titolo=str(md.get("title"))[:100], autore=str(md.get("creator"))[:40], anno=md.get("date") or md.get("year"),
        accesso="prestito" if md.get("access-restricted-item") == "true" else "aperto", licenza=md.get("licenseurl", ""), collezioni=";".join(md.get("collection", [])) if isinstance(md.get("collection"), list) else md.get("collection"),
        testo_ocr="si" if testo else "no", testo_kb=round(sum(int(f.get("size", 0)) for f in testo) / 1024) if testo else 0, pdf_mb=round(sum(int(f.get("size", 0)) for f in pdf) / 1048576, 1),
        pagine=md.get("imagecount", ""), url="https://archive.org/details/" + ident))
import csv
with open(os.path.join(ia.ROOT, "raw", "ia_scala", "ia_elementi_scala.csv"), "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(righe[0].keys())); w.writeheader(); w.writerows(righe)
for r in righe: print(r["accesso"], r["testo_ocr"], r["testo_kb"], r["pdf_mb"], r["anno"], r["identifier"][:60], "|", r["titolo"][:60])
