"""Legge i due indici di Gatti vol.1 (nomi: PDF 633-656; opere: PDF 657-671) da raw/gatti_testo/gatti_pagine.json.
Scrive pulito/_gatti_opere.csv (titolo, autore, pagine, grezzo) e pulito/_gatti_nomi.csv (nome, cognome, pagine, grezzo).
Uso: python -I -X utf8 scripts/gatti_indici.py raw/gatti_testo/gatti_pagine.json pulito"""
import sys, json, re, csv, os
pag = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]

ROM = {"i":1,"ii":2,"iii":3,"iv":4,"v":5,"vi":6,"vii":7,"viii":8,"ix":9,"x":10}
def pages_from_tail(tail):
    """tail = stringa dopo l'ultima virgola prima dei numeri. Ritorna lista di pagine (int; romane come 'r3')."""
    res = []
    t = tail.replace("’", "'")
    # correzioni OCR: 4.4 -> 44, 4.64 -> 464, lettere simili a cifre
    t = re.sub(r"(\d)\.(\d)", r"\1\2", t)
    toks = [x for x in re.split(r"[,;]\s*|\s+", t) if x]
    for tok in toks:
        tok = tok.strip(".:;>'-_~=)]")
        if not tok: continue
        low = tok.lower()
        if low in ROM or re.fullmatch(r"[vx]?[1il]{1,3}|vi{1,3}|vim|x1|v1|v11|v111|x", low):
            fix = low.replace("1","i").replace("m","ii")  # v1 -> vi ; vim -> viii (approssimato)
            if fix in ROM: res.append("r%d" % ROM[fix]); continue
        t2 = tok.replace("I","1").replace("l","1").replace("|","1").replace("!","1").replace("O","0").replace("o","0").replace("g","9").replace("S","5").replace("B","8")
        m = re.fullmatch(r"(\d{1,3})(?:-(\d{1,3}))?", t2)
        if not m: continue
        a = int(m.group(1)); b = m.group(2)
        if a < 1 or a > 480: continue
        if b:
            bb = int(b)
            if bb < a:  # 143-4 -> 143-144
                s = str(a); bb = int(s[:len(s)-len(b)] + b)
            if a < bb <= a + 30: res.extend(range(a, bb + 1)); continue
        res.append(a)
    # unici in ordine
    seen = []; [seen.append(x) for x in res if x not in seen]
    return seen

ALLOWED = set("0123456789IlOo|!gSB.,;:>'’-~=_ ivxm)]")
def split_tail(s):
    """separa 'testa' e 'coda numerica' di una voce d'indice (scansione lineare, niente regex lente)"""
    s = s.strip()
    n = len(s); i = n
    while i > 0 and s[i-1] in ALLOWED: i -= 1
    # i = inizio della coda massima; cerca la prima virgola in coda dopo cui c'e' almeno una cifra/romano
    for k in range(i, n):
        if s[k] == "," :
            rest = s[k+1:]
            if not rest.strip(): continue
            # il carattere prima della virgola non deve essere in coda numerica 'attaccata' a una parola
            if re.search(r"[0-9IlOo|!gSB]|[ivx]{1,4}", rest):
                # rest deve iniziare dopo uno spazio o numero
                return s[:k], rest.strip()
    # ripiego: coda con rumore OCR -> taglio alla prima virgola seguita da cifra
    mm = re.search(r",\s*\d", s)
    if mm: return s[:mm.start()], s[mm.start()+1:].strip()
    return s, ""

def entries(first, last, dash_re):
    txt = "\n".join(pag[i] for i in range(first - 1, last))
    txt = re.sub(r"(\w)-\s*\n\s*([a-zàèéìòù])", r"\1\2", txt)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    buf = ""; out_e = []
    complete = re.compile(r"\d[\d\s.:;>'’\-]*$")
    for l in lines:
        newstart = bool(re.match(r"[A-ZÀ-Ý«“\"(]", l) or dash_re.match(l))
        if buf and newstart and complete.search(buf) and not buf.rstrip().endswith(","):
            out_e.append(buf); buf = l
        else:
            buf = (buf + " " + l).strip()
    if buf: out_e.append(buf)
    return out_e

# ---------------- opere ----------------
dash = re.compile(r"^[—\-–~=_]+\s*(?:di|d')|^[—\-–~=_]{1,3}\s*[A-Za-z]|^[—\-–~=_]{1,3}")
raw = entries(657, 671, dash)
rows = []; head = ""; head_auth = ""
ART = r"(Il|La|Lo|L'|Le|Gli|I|Un|Una|Un'|L’|Un’)"
def norm_title(t):
    t = re.sub(r"\s*\(\d{1,2}\)", "", t).strip(" ,.;")
    m = re.match(r"^(.*?)\s*\(\s*%s\s*\)(.*)$" % ART, t)
    if m:
        art = m.group(2); rest = (m.group(1) + m.group(3)).strip()
        t = (art + (" " if not art.endswith(("'", "’")) else "") + rest).strip()
    return re.sub(r"\s+", " ", t)
def SPLIT_DI(x):
    m = re.match(r"^(.*?),\s*di\s*(?=[A-Z])(.*)$", x)
    if m: return m
    return re.match(r"^(.*?)\s+di\s+((?:[A-Z]{1,2}\.\s*)+[A-Z][\w'’-]+.*)$", x)
for e in raw:
    e0 = e
    if e.startswith("INDICE DELLE OPERE") or "DEI LIBRETTI, DEI BALLI" in e:
        e = re.sub(r"^INDICE DELLE OPERE LETTERARIE E MUSICALI?T?,?\s*DEI LIBRETTI, DEI BALLI, ECC\.?\s*", "", e)
    isdash = bool(re.match(r"^[—\-–~=_]", e))
    h, tail = split_tail(e)
    pgs = pages_from_tail(tail) if tail else []
    if re.search(r",\s*v\.\s", h) or re.match(r".*\bv\.\s", h) and not pgs:
        continue  # rimandi
    if isdash:
        body = re.sub(r"^[—\-–~=_\s]+", "", h)
        if re.match(r"^(?:di|da|d')\s*[A-Z]{1,2}[.,]", body) or re.match(r"^di\s*[A-Z][a-zé]+\s*$", body) or re.match(r"^d[il]\s*[A-Z][.,]", body):
            title = head; auth = re.sub(r"^(?:di|da)\s*", "", body)
        else:
            m = SPLIT_DI(body)
            if m: suf = m.group(1); auth = m.group(2)
            else: suf = body; auth = ""
            title = norm_title(head_raw.split(" ")[0] + " " + suf) if suf else head
            # sub-entry con nuovo qualificatore: es. "Regina" + "di Golconda (La)"
    else:
        m = SPLIT_DI(h)
        if m: title = norm_title(m.group(1)); auth = m.group(2)
        else: title = norm_title(h); auth = ""
        head = title; head_raw = re.sub(r"\s*\(.*?\)\s*", " ", m.group(1) if m else h).strip()
    am = re.search(r",\s*\d", auth)
    if am:
        pgs = pages_from_tail(auth[am.start()+1:] + ", " + tail); auth = auth[:am.start()]
    rows.append({"titolo": title, "autore": auth.strip(" ,."), "pagine": ";".join(map(str, pgs)), "grezzo": e0[:200]})
with open(os.path.join(out, "_gatti_opere.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["titolo", "autore", "pagine", "grezzo"]); w.writeheader(); w.writerows(rows)
print("opere:", len(rows), "con pagine:", sum(1 for r in rows if r["pagine"]))

# ---------------- nomi ----------------
dash2 = re.compile(r"^[—\-–~=_]+")
raw = entries(633, 656, dash2)
nrows = []; surname = ""
for e in raw:
    e0 = e
    if "INDICE DEI NOMI" in e: e = e.replace("INDICE DEI NOMI", "").strip()
    h, tail = split_tail(e)
    pgs = pages_from_tail(tail) if tail else []
    if not h: continue
    if dash2.match(h):
        given = dash2.sub("", h).strip(" ,.")
        nm = (surname + " " + given).strip()
        sur = surname
    else:
        nm = h.strip(" ,."); sur = nm.split(" ")[0]; surname = sur
    nrows.append({"nome": nm, "cognome": sur, "pagine": ";".join(map(str, pgs)), "grezzo": e0[:160]})
with open(os.path.join(out, "_gatti_nomi.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["nome", "cognome", "pagine", "grezzo"]); w.writeheader(); w.writerows(nrows)
print("nomi:", len(nrows), "con pagine:", sum(1 for r in nrows if r["pagine"]))

# ---------------- indici dell'appendice 1958-63 (pagine romane III-XI = PDF 495-503) ----------------
def roman_ocr(tok):
    t = tok.strip(".:;,)(' ").lower()
    if not t or not re.fullmatch(r"[ivxlmtru1]{1,6}", t): return None
    t = t.replace("m", "ii").replace("u", "ii").replace("l", "i").replace("t", "i").replace("r", "i").replace("1", "i")
    val = {"i": 1, "v": 5, "x": 10}
    n = 0
    for k, ch in enumerate(t):
        v = val[ch]
        n += -v if (k + 1 < len(t) and val[t[k + 1]] > v) else v
    return n if 1 <= n <= 11 else None

def roman_tail(tail):
    res = []
    for tok in re.split(r"[,;\s]+", tail):
        n = roman_ocr(tok)
        if n and ("r%d" % n) not in res: res.append("r%d" % n)
    return res

def entries_app(first, last, dash_re):
    return entries(first, last, dash_re)
# la regola 'complete' di entries() richiede una cifra finale: qui la coda e' romana -> versione dedicata
def entries_roman(first, last, dash_re):
    txt = "\n".join(pag[i] for i in range(first - 1, last))
    txt = re.sub(r"(\w)-\s*\n\s*([a-zàèéìòù])", r"\1\2", txt)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    buf = ""; res = []
    endrom = re.compile(r",\s*[ivxlmtru1IVXLM]{1,6}[.]?\s*$|[ivxlmtru1IVXLM]{1,6}\.\s*$")
    for l in lines:
        newstart = bool(re.match(r"[A-ZÀ-Ý«“\"(]", l) or dash_re.match(l))
        if buf and newstart and endrom.search(buf) and not buf.rstrip().endswith(","):
            res.append(buf); buf = l
        else:
            buf = (buf + " " + l).strip()
    if buf: res.append(buf)
    return res

app_o = entries_roman(507, 509, dash)
app_rows = []; head2 = ""; head_raw2 = ""
for e in app_o:
    e0 = e
    e = re.sub(r"^INDICE DELLE OPERE LETTERARIE\s*E MUSICALIT?,?\s*\.?\s*DEI LIBRETTI,\s*DEI BALLI,\s*ECC\.?\s*", "", e)
    isdash = bool(re.match(r"^[—\-–~=_]", e))
    m = re.match(r"^(.*?)[,.]?\s+([ivxlmtru1IVXLM]{1,6})\.?\s*$", e)
    if not m: continue
    h = m.group(1); n = roman_ocr(m.group(2))
    # coda con piu' pagine: "..., di X, v, vi"
    mm = re.match(r"^(.*?),\s*((?:[ivxlmtru1IVXLM]{1,6}[.,]?\s*)+)$", e)
    if mm: h = mm.group(1); pgs = roman_tail(mm.group(2))
    else: pgs = ["r%d" % n] if n else []
    if not pgs: continue
    mt = SPLIT_DI(h)
    if isdash:
        body = re.sub(r"^[—\-–~=_\s]+", "", h)
        if re.match(r"^(?:di|da)\s*[A-Z]{1,2}[.,]", body):
            title = head2; auth = re.sub(r"^(?:di|da)\s*", "", body)
        else:
            m2 = SPLIT_DI(body)
            suf, auth = (m2.group(1), m2.group(2)) if m2 else (body, "")
            title = norm_title(head_raw2.split(" ")[0] + " " + suf)
    else:
        if mt: title = norm_title(mt.group(1)); auth = mt.group(2)
        else: title = norm_title(h); auth = ""
        head2 = title; head_raw2 = re.sub(r"\s*\(.*?\)\s*", " ", mt.group(1) if mt else h).strip()
    app_rows.append({"titolo": title, "autore": auth.strip(" ,."), "pagine": ";".join(pgs), "grezzo": "APPENDICE: " + e0[:180]})
with open(os.path.join(out, "_gatti_opere.csv"), "a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["titolo", "autore", "pagine", "grezzo"]); w.writerows(app_rows)
print("opere appendice 1958-63:", len(app_rows))

app_n = entries_roman(505, 506, dash2)
nrows2 = []; surname = ""
for e in app_n:
    e0 = e
    e = e.replace("INDICE DEI NOMI", "").strip()
    mm = re.match(r"^(.*?),\s*((?:[ivxlmtru1IVXLM]{1,6}[.,]?\s*)+)$", e)
    if not mm: continue
    h = mm.group(1); pgs = roman_tail(mm.group(2))
    if not pgs: continue
    if dash2.match(h):
        given = dash2.sub("", h).strip(" ,."); nm = (surname + " " + given).strip(); sur = surname
    else:
        nm = h.strip(" ,."); sur = nm.split(" ")[0]; surname = sur
    nrows2.append({"nome": nm, "cognome": sur, "pagine": ";".join(pgs), "grezzo": "APPENDICE: " + e0[:140]})
with open(os.path.join(out, "_gatti_nomi.csv"), "a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["nome", "cognome", "pagine", "grezzo"]); w.writerows(nrows2)
print("nomi appendice 1958-63:", len(nrows2))
