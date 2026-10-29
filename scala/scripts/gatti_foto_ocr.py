"""SCHELETRO (non ancora usato su foto vere): foto delle pagine di Gatti, vol. 2, 'Cronologia completa degli spettacoli'
-> OCR -> tabella con le STESSE colonne del resto del progetto.

Uso:  python -I gatti_foto_ocr.py <cartella_foto> <cartella_output>
Passi:
 1. pretratta ogni foto (grigi, contrasto, raddrizza) -> output/prep/
 2. OCR con riquadri delle parole: Tesseract (--psm 6, lingua ita) se e' nel PATH, altrimenti il motore di Windows (winocr.ps1)
 3. raggruppa le parole in righe (y) e riconosce l'inizio di una riga-spettacolo: data (es. '7 dic.') + titolo
 4. scrive output/gatti_grezzo.csv (una riga per spettacolo, testo originale in 'testo_riga') + output/gatti_da_rivedere.csv (righe dubbie)
Il formato esatto delle righe di Gatti va deciso guardando 3-4 foto vere: le funzioni parse_* sono da adattare allora.
"""
import sys, os, re, csv, json, shutil, subprocess
from PIL import Image, ImageOps

COLONNE = ["fonte", "pagina_o_foto", "data_iso", "stagione", "luogo", "tipo", "titolo", "compositore", "direttore",
           "interpreti", "regia_coreografia", "note", "testo_riga", "affidabilita_ocr"]
MESI = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12}
HERE = os.path.dirname(os.path.abspath(__file__))

def prepara(src, dst):
    im = ImageOps.exif_transpose(Image.open(src)).convert("L")
    im = ImageOps.autocontrast(im, cutoff=1)
    if max(im.size) < 2400:                      # foto troppo piccole: ingrandisci
        k = 2400 / max(im.size); im = im.resize((int(im.width*k), int(im.height*k)))
    im.save(dst)
    return dst

def ocr_tesseract(img):
    out = subprocess.run(["tesseract", img, "-", "-l", "ita", "--psm", "6", "tsv"], capture_output=True, text=True, encoding="utf8").stdout
    words = []
    for r in csv.DictReader(out.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r.get("text", "").strip() and float(r["conf"]) >= 0:
            words.append((int(r["left"]), int(r["top"]), int(r["width"]), int(r["height"]), r["text"], float(r["conf"])))
    return words

def ocr_windows(img):
    out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(HERE, "winocr.ps1"), "-Img", os.path.abspath(img)],
                         capture_output=True, text=True, encoding="utf8").stdout
    words = []
    for ln in json.loads(out or "[]"):
        for w in ln["words"]:
            words.append((w["x"], w["y"], w["w"], w["h"], w["t"], -1.0))   # il motore Windows non da' la confidenza
    return words

def righe(words, tol=0.6):
    """raggruppa le parole in righe visive usando l'altezza media come tolleranza"""
    words = sorted(words, key=lambda w: (w[1] + w[3]/2, w[0]))
    rows, cur, cy = [], [], None
    for w in words:
        yc = w[1] + w[3]/2
        if cy is None or abs(yc - cy) <= tol * w[3]:
            cur.append(w); cy = yc if cy is None else (cy + yc)/2
        else:
            rows.append(sorted(cur)); cur = [w]; cy = yc
    if cur: rows.append(sorted(cur))
    return rows

RE_DATA = re.compile(r"^\s*(\d{1,2})\s*(?:°|o)?\s*(gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)[a-z]*\.?", re.I)

def parse_riga(testo):
    """DA ADATTARE sulle foto vere. Ora: riconosce solo 'giorno mese' all'inizio e prende il resto come titolo/testo."""
    m = RE_DATA.match(testo)
    return {"giorno": int(m.group(1)), "mese": MESI[m.group(2).lower()[:3]], "resto": testo[m.end():].strip()} if m else None

def main(cartella_foto, out):
    os.makedirs(os.path.join(out, "prep"), exist_ok=True)
    usa_tess = shutil.which("tesseract") is not None
    ocr = ocr_tesseract if usa_tess else ocr_windows
    print("motore OCR:", "tesseract" if usa_tess else "Windows (it-IT)")
    grezzo, dubbie = [], []
    for nome in sorted(os.listdir(cartella_foto)):
        if not nome.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic")): continue
        prep = prepara(os.path.join(cartella_foto, nome), os.path.join(out, "prep", os.path.splitext(nome)[0] + ".png"))
        for r in righe(ocr(prep)):
            testo = " ".join(w[4] for w in r)
            conf = sum(w[5] for w in r)/len(r) if r[0][5] >= 0 else ""
            p = parse_riga(testo)
            rec = dict.fromkeys(COLONNE, ""); rec.update(fonte="Gatti 1964 vol.2", pagina_o_foto=nome, testo_riga=testo, affidabilita_ocr=conf)
            if p: rec.update(note=f"giorno={p['giorno']} mese={p['mese']}", titolo=p["resto"])   # data_iso/stagione si completano quando si conosce l'anno della pagina
            (grezzo if p else dubbie).append(rec)
    for nome, dati in (("gatti_grezzo.csv", grezzo), ("gatti_da_rivedere.csv", dubbie)):
        with open(os.path.join(out, nome), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, COLONNE); w.writeheader(); w.writerows(dati)
    print(len(grezzo), "righe con data;", len(dubbie), "da rivedere")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
