"""Pagine /it/stagione/ del sito pubblico della Scala (2023-24 ... 2026-27) -> pulito/_scala_sito.csv
Una riga per spettacolo: stagione, prima data, titolo, autore (opera/balletto), direttore, regia, interpreti, categoria, sala, indirizzo.
Dati (c) Teatro alla Scala, raccolta autorizzata dalla Scala. Uso: python -I -X utf8 scripts/parse_scala_stagioni.py raw/scala_stagioni pulito/_scala_sito.csv"""
import sys, os, re, csv, html, glob

MESI = {"gennaio":1,"febbraio":2,"marzo":3,"aprile":4,"maggio":5,"giugno":6,"luglio":7,"agosto":8,"settembre":9,"ottobre":10,"novembre":11,"dicembre":12}
CAT = {"opera": "opera", "balletto": "balletto", "concerti": "concerto", "grandi-spettacoli-per-piccoli": "spettacolo per ragazzi",
       "grandi-spettacoli-per-piccoli-e-famiglie": "spettacolo per ragazzi", "tournee": "tournee", "eventi-fuori-sede": "evento fuori sede"}
src, out = sys.argv[1], sys.argv[2]
rows = []
def clean(s): return re.sub(r"\s+", " ", html.unescape(s).replace("\xa0", " ")).strip()
def date_iso(s):
    m = re.search(r"(\d{1,2})\s+(?:[a-z]+\s+)?([a-z]+)\s+(20\d\d)", s.lower())
    if not m: 
        m2 = re.search(r"(\d{1,2})\s+([a-z]+)\s+(20\d\d)", s.lower())
        if not m2: return ""
        m = m2
    mo = MESI.get(m.group(2))
    return "%s-%02d-%02d" % (m.group(3), mo, int(m.group(1))) if mo else ""
def first_date(lines):
    for l in lines:
        m = re.match(r"^Dal\s+(\d{1,2})(?:\s+([a-z]+))?\s+al\s+(\d{1,2})\s+([a-z]+)\s+(20\d\d)", l.lower())
        if m:
            mo = MESI.get(m.group(2) or m.group(4)); yr = int(m.group(5))
            if m.group(2) and MESI.get(m.group(2)) and MESI[m.group(2)] > MESI.get(m.group(4), 0) and False: yr -= 1
            return "%d-%02d-%02d" % (yr, mo, int(m.group(1)))
        m = re.match(r"^(?:Dal\s+)?(?:lun|mar|mer|gio|ven|sab|dom)[a-zì]*\s+(\d{1,2})\s+([a-z]+)\s+(20\d\d)", l.lower())
        if m and MESI.get(m.group(2)): return "%s-%02d-%02d" % (m.group(3), MESI[m.group(2)], int(m.group(1)))
        m = re.match(r"^(?:Il\s+|Dal\s+)?(\d{1,2})\s+([a-z]+)\s+(20\d\d)", l.lower())
        if m and MESI.get(m.group(2)): return "%s-%02d-%02d" % (m.group(3), MESI[m.group(2)], int(m.group(1)))
    return ""
for fp in sorted(glob.glob(os.path.join(src, "*.html"))):
    fn = os.path.basename(fp)
    parts = fn[:-5].split("__")
    season = parts[0]; cat = parts[1]
    raw0 = open(fp, encoding="utf-8").read()
    raw = re.sub(r"(?s)<(script|style|noscript).*?</\1>", "", raw0)
    txt = re.sub(r"<[^>]+>", "\n", raw)
    lines = [clean(l) for l in txt.split("\n")]
    lines = [l for l in lines if l and not l.startswith('">') and not l.startswith("Credits")]
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", raw0, flags=re.S)
    title = clean(re.sub(r"<[^>]+>", "", h1[0])) if h1 else ""
    ti = [i for i, l in enumerate(lines) if l == title and i > 15]
    if not title or not ti:
        rows.append({"stagione": season.replace("-20", "-"), "data": "", "titolo": title, "autore": "", "direttore": "", "regista": "", "interpreti": "", "genere": CAT.get(parts[1], parts[1]), "sala": "", "riga_fonte": fn, "nota": "struttura non riconosciuta"})
        continue
    start = ti[0]
    sub = lines[start - 1] if start > 0 and cat == "concerti" else ""
    j = start + 1
    aut = ""
    if cat in ("opera", "balletto") and j < len(lines) and not re.match(r"^(Dal|Il|Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato|Domenica|\d)", lines[j]):
        aut = lines[j]; j += 1
    head = lines[j:j + 25]
    data = first_date(head)
    if not data:
        # "Tutte le date" o prima data nel testo
        try:
            k = lines.index("Tutte le date"); data = first_date(lines[k + 1:k + 4])
        except ValueError:
            data = ""
    def after(label, n=1):
        for i, l in enumerate(lines):
            if l.lower() == label.lower() and i + 1 < len(lines): return lines[i + 1]
        return ""
    direttore = after("Direttore"); regia = after("Regia")
    # cast: coppie ruolo / interpreti dopo "Cast" fino a "Tutte le date" o "In breve"
    interpreti = []
    if "Cast" in lines:
        k = lines.index("Cast") + 1
        # salta etichette se "Cast" compare prima (menu): prendi l'ultima occorrenza prima di "Tutte le date"
        ks = [i for i, l in enumerate(lines) if l == "Cast"]
        k = ks[-1] + 1 if ks else k
        blk = []
        while k < len(lines) and lines[k] not in ("Tutte le date", "In breve", "Vedi tutti", "Libretto"):
            blk.append(lines[k]); k += 1
        # coppie (ruolo, interprete)
        for a in range(1, len(blk), 2):
            names = re.split(r"\s+/\s+", re.sub(r"\([^)]*\)", "", blk[a]))
            for nm in names:
                nm = nm.strip(" ,;")
                if nm and nm not in interpreti and len(nm) < 60: interpreti.append(nm)
    sala = "Teatro alla Scala"
    headtxt = " ".join(lines[start:start + 20]).lower()
    if "arcimboldi" in headtxt: sala = "Teatro degli Arcimboldi"
    elif "ridotto" in headtxt or cat == "concerti" and "ridotto" in fn: sala = "Ridotto dei Palchi Toscanini"
    elif "piccolo teatro" in headtxt: sala = "Piccolo Teatro"
    gen = CAT.get(cat, cat)
    if sub and cat == "concerti": gen = "concerto (" + sub.lower() + ")"
    rows.append({"stagione": season.replace("-20", "-"), "data": data, "titolo": title, "autore": aut, "direttore": direttore, "regista": regia,
                 "interpreti": ";".join(interpreti), "genere": gen, "sala": sala,
                 "riga_fonte": "https://www.teatroallascala.org/it/stagione/" + season + "/" + cat + "/" + "/".join(parts[2:]).replace("/", "/") .replace(".html", "") + ".html", "nota": ""})
cols = ["stagione", "data", "titolo", "autore", "direttore", "regista", "interpreti", "genere", "sala", "riga_fonte", "nota"]
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
print(len(rows), "pagine;", sum(1 for r in rows if r["nota"]), "non riconosciute;", sum(1 for r in rows if r["data"]), "con data;", sum(1 for r in rows if r["direttore"]), "con direttore;", sum(1 for r in rows if r["interpreti"]), "con interpreti")
