"""Cambiasi 1881: pulizia di pulito/_cambiasi_opere.csv (riga grezza OCR) -> pulito/_cambiasi_pulito.csv
 - riporta avanti anno e stagione ("id."), normalizza stagione e mese, separa il segno * (opera scritta per la Scala) e le note (1) (2)
 - corregge i nomi dei maestri con i nomi piu' frequenti (difflib) e con i compositori di Wikipedia
 - scarta le righe che non sono opere (note a piedipagina, righe di rumore)
Uso: python -I -X utf8 scripts/pulisci_cambiasi.py pulito/_cambiasi_opere.csv pulito/_wp_stagioni.csv pulito/_cambiasi_pulito.csv"""
import csv, re, sys, collections, difflib, unicodedata

src, wp, out = sys.argv[1:4]
R = list(csv.DictReader(open(src, encoding="utf-8")))
MESI = ["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"]
STAG = {"carne": "Carnevale", "quare": "Quaresima", "prima": "Primavera", "estat": "Estate", "autun": "Autunno", "avven": "Avvento"}

def strip_acc(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
def alpha(s): return re.sub(r"[^A-Za-z]", "", s)
def mese_norm(s):
    s0 = alpha(strip_acc(s)).lower()
    if len(s0) < 3: return ""
    best = difflib.get_close_matches(s0, MESI, n=1, cutoff=0.6)
    return best[0] if best else ""
def stag_norm(s):
    s0 = alpha(strip_acc(s)).lower()
    if not s0: return ""
    if s0.startswith("id"): return "id"
    for k, v in STAG.items():
        if s0.startswith(k[:3]): return v
    return ""

# nomi di compositori noti (Wikipedia) per correggere
known = collections.Counter()
for x in csv.DictReader(open(wp, encoding="utf-8")):
    c = x["compositore"].strip()
    if c: known[c.split()[-1]] += 5
freq = collections.Counter()
def clean_maestro(m):
    m = re.sub(r"[^\w\s.'’\-]", " ", m).strip(" .-_")
    m = re.sub(r"\s+", " ", m)
    return m
for x in R:
    m = clean_maestro(x["maestro_raw"])
    if m: freq[m.split()[-1]] += 1
good = {k for k, v in (freq + known).items() if v >= 3}

def fix_name(m):
    if not m: return m
    toks = m.split()
    last = toks[-1]
    if last in good or len(last) < 4: return m
    cand = difflib.get_close_matches(last, list(good), n=1, cutoff=0.82)
    if cand:
        toks[-1] = cand[0]
    return " ".join(toks)

rows = []; year = None; stag = ""; last_month = 0; prev_ord = None
rej = collections.Counter()
for x in R:
    t = x["titolo_raw"].strip()
    conf = float(x["conf"] or 0)
    if conf < 20 or len(t) < 3 or len(t) > 85:
        rej["conf/lunghezza"] += 1; continue
    lett = len(re.findall(r"[A-Za-zÀ-ÿ]", t))
    if lett / max(len(t), 1) < 0.7:
        rej["rumore"] += 1; continue
    if x["pagina_hocr"] == "102" and not x["maestro_raw"]:
        rej["note fondo"] += 1; continue
    if re.search(r"\b(si diedero|concerti|Introito|inondazioni|beneficio)\b", t + " " + x["esecutori_raw"]):
        rej["nota (concerti)"] += 1; continue
    TR = str.maketrans("SGOIlB", "860118")
    ar = x["anno_raw"].translate(TR)
    ym = re.search(r"(1[78]\d\d)", ar)
    anchored = False
    if ym:
        y = int(ym.group(1))
        if year is None or year <= y <= year + 3: year = y; anchored = True
        elif sum(a != b for a, b in zip(str(y), str(year + 1))) <= 1: year = year + 1; anchored = True
    elif year is not None and re.search(r"[1I][78S][0-9A-Z]{2}", x["anno_raw"]):
        ar2 = re.search(r"[1I][78S][0-9A-Z]{2}", x["anno_raw"]).group(0).translate(TR)
        if sum(a != b for a, b in zip(ar2, str(year + 1))) <= 1: year = year + 1; anchored = True
    s = stag_norm(x["stagione_raw"])
    ORD = {"Carnevale": 0, "Quaresima": 1, "Primavera": 2, "Estate": 3, "Autunno": 4, "Avvento": 5}
    if s and s != "id":
        if (not anchored) and year is not None and prev_ord is not None and ORD[s] < prev_ord: year += 1   # nuovo anno teatrale senza anno leggibile
        prev_ord = ORD[s]
        stag = s
    if anchored and s and s != "id": prev_ord = ORD[s]
    elif not s and x["stagione_raw"].strip() and "chiuso" in x["stagione_raw"].lower():
        rej["teatro chiuso"] += 1; continue
    mese = mese_norm(x["mese_raw"])
    gm = re.match(r"\s*(\d{1,2})", re.sub(r"^\(?\d\)\s*", "", x["giorno_raw"]))
    giorno = int(gm.group(1)) if gm and 1 <= int(gm.group(1)) <= 31 else None
    # titolo: via asterisco/note
    star = "*" in t or "^" in t or "•" in t
    t2 = re.sub(r"[\^*•■]", "", t)
    t2 = re.sub(r"\s*\(\d\)\s*", " ", t2)
    t2 = re.sub(r"\s*[-–~]\s*(?:f[aeoi]|\^\w*|£|[a-z]?£|\(\?\))\s*$", "", t2)
    t2 = re.sub(r"\s*\(\?\)\s*", " ", t2)
    t2 = re.sub(r"[\"“”«»]", "", t2)
    t2 = re.sub(r"\s+", " ", t2).strip(" .,;:-_")
    if len(t2) < 3: rej["titolo vuoto"] += 1; continue
    maestro = fix_name(clean_maestro(x["maestro_raw"]))
    esec = re.sub(r"-\s+", "", x["esecutori_raw"])
    esec = re.sub(r"[^\w\s,.'’\-()]", "", esec)
    esec = [e.strip(" .") for e in esec.split(",") if len(e.strip(" .")) > 2]
    genere_raw = alpha(strip_acc(x["genere_raw"])).lower()
    gen = {"serio": "opera seria", "buffo": "opera buffa", "semis": "opera semiseria", "semiserio": "opera semiseria"}.get(genere_raw[:6], "opera seria" if genere_raw.startswith("ser") else ("opera buffa" if genere_raw.startswith("buf") else "opera"))
    data = ""
    if year and mese:
        m_i = MESI.index(mese) + 1
        yy = year - 1 if (stag == "Carnevale" and m_i >= 11) else year
        if giorno: data = "%04d-%02d-%02d" % (yy, m_i, giorno)
    esito = alpha(strip_acc(x["esito_raw"])).lower()
    rows.append({
        "pagina_hocr": x["pagina_hocr"], "anno": year or "", "stagione": ((stag + " " + str(year)) if stag and year else ""), "stagione_nome": stag,
        "data": data, "titolo": t2, "autore": maestro, "poeta": re.sub(r"[^\w\s.'’\-]", "", x["poeta_raw"]).strip(),
        "genere": gen, "interpreti": ";".join(esec), "prima_per_la_scala": "si" if star else "", "esito": esito[:12], "conf_ocr": x["conf"],
        "riga_fonte": "Cambiasi 1881, hOCR p.%s y=%s" % (x["pagina_hocr"], x["y"]),
    })
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(R), "righe grezze ->", len(rows), "pulite; scartate:", dict(rej))
yc = collections.Counter(r["anno"] for r in rows)
print("anni coperti:", len(yc), "min", min(yc), "max", max(yc))
