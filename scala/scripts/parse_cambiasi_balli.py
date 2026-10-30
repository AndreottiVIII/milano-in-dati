"""Cambiasi 1881: 'SERIE DEI BALLI' (libro p.83-110, testo OCR ABBYY di Internet Archive) -> pulito/_cambiasi_balli.csv
La serie dei balli NON e' una tabella ma un testo a stagioni:  "1779. CARNEVALE — Porzia, di Candiani — La festa campestre — ..., tutti di Regina.  P. B. <prime ballerine>; <primi ballerini>."
Ogni ballo = una riga: anno, stagione, titolo, coreografo ("di X" / "tutti di X"), compositore ("m. di Y", "m. dello stesso"), data (se tra parentesi), esito (ottimo/buono/...), prime ballerine/ballerini della stagione.
Uso (dalla cartella scala/):  python -I -X utf8 scripts/parse_cambiasi_balli.py raw/cambiasi/teatroallascala100camb/teatroallascala100camb_djvu.txt pulito/_cambiasi_balli.csv
Anche: pulito/_cambiasi_balli_log.txt (anni letti con il numero di balli, anomalie)."""
import re, sys, csv, os, collections
sys.stdout.reconfigure(encoding="utf-8")

src, out = sys.argv[1], sys.argv[2]
T = open(src, encoding="utf-8").read()
T = re.sub(r"[ \t]+", " ", T)
i0 = T.find("Palio e Mirra") - 60
i1 = T.find("MAESTRI CONCERTATORI", i0)
S = T[i0:i1]

# ---------------------------------------------------------------- pulizia: intestazioni di pagina, numeri di pagina, a-capo con trattino
page_at = []          # (posizione nel testo piatto, pagina stampata)
lines = [l.strip() for l in S.split("\n")]
flat = ""
cur_page = 83
cleaned = []
for k, l in enumerate(lines):
    if not l:
        continue
    if re.fullmatch(r"(?:[A-Z]\s?)?B\s?A\s?L\s?L\s?[I1l]\s?\.?", l) or re.fullmatch(r"(?:B ?A ?L ?L ?[I1l]\s*)?\d{2,3}(?:\s*B ?A ?L ?L ?[I1l])?", l):
        m = re.search(r"\d{2,3}", l)
        if m and 80 <= int(m.group()) <= 112:
            cur_page = int(m.group())
            cleaned.append(("\x01PAG%d\x01" % cur_page, True))
        continue
    cleaned.append((l, False))
for l, isp in cleaned:
    if isp:
        flat += " " + l + " "
    elif flat.endswith("¬ ") or flat.endswith("¬"):
        flat = flat.rstrip("¬ ") + l
    elif re.search(r"\w-$", flat) and False:
        flat = flat[:-1] + l
    else:
        flat += " " + l
flat = re.sub(r"¬\s*", "", flat)
flat = re.sub(r"(?<=[a-z])-\s+(?=[a-z])", "", flat)      # "am- bidue", "calzo- laja"
flat = re.sub(r"\s+", " ", flat)

# ---------------------------------------------------------------- marcatori di stagione
import difflib
NOMI_STAG = ["CARNEVALE", "QUARESIMA", "PRIMAVERA", "AUTUNNO", "AUTUNNINO", "AVVENTO", "ESTATE"]
RANK = {"CARNEVALE": 0, "QUARESIMA": 1, "PRIMAVERA": 2, "ESTATE": 3, "AUTUNNO": 4, "AUTUNNINO": 5, "AVVENTO": 6}
YR = r"(?<![\w(])[1I][78SG5Ib][0-9OSIlGgB(\)]{2}"
RX = re.compile(r"(?:(?P<y>" + YR + r")\.?\s+)?(?P<s>(?<![A-Za-z])(?:C ?A[A-Z ]{5,9}|[A-Z]{5,10})(?:\s*(?:,|E|ED|ET|-|—)\s*[A-Z]{5,10})?)(?![A-Za-z])")

def fuzzy_name(w):
    w = w.replace(" ", "")
    if w in ("CARNEI", ): return None
    if w in ("INVERNALE", "INVERNAL"): return "CARNEVALE"
    if w.startswith("CAPNEA") or w.startswith("CAENEV") or w.startswith("CARNEI"): return "CARNEVALE"
    m = difflib.get_close_matches(w, NOMI_STAG, n=1, cutoff=0.72)
    return m[0] if m else None

def norm_seas(s):
    s0 = s.upper()
    parts = [p.strip() for p in re.split(r"\s*(?:,|\bED\b|\bET\b|\bE\b|-|—)\s*", s0) if p.strip()]
    names = []
    for p in parts:
        k = fuzzy_name(p)
        if k: names.append(k.capitalize())
    return names

marks = []
for m in RX.finditer(flat):
    s = m.group("s")
    names = norm_seas(s)
    if not names:
        continue
    # il primo termine deve essere davvero un nome di stagione (non una parola qualsiasi): gia' garantito da fuzzy_name
    # le parole minuscole/maiuscole del corpo (es. "ECC", "DEI") non passano il fuzzy
    marks.append(dict(pos=m.start(), end=m.end(), ytok=m.group("y"), names=names, rank=RANK[names[0].upper()]))

# due marcatori attaccati ("CARNEVALE E" + "QUARESIMA") = una stagione composta
merged = []
for m in marks:
    if merged:
        gap = flat[merged[-1]["end"]:m["pos"]]
        if re.fullmatch(r"\s*(?:E|ED|ET|,|-|—|\s)*", gap) and not m["ytok"]:
            merged[-1]["names"] = merged[-1]["names"] + [n for n in m["names"] if n not in merged[-1]["names"]]
            merged[-1]["end"] = m["end"]
            continue
    merged.append(m)
marks = merged

# pagine: posizione -> pagina
pages = [(m.start(), int(m.group(1))) for m in re.finditer(r"\x01PAG(\d+)\x01", flat)]
def page_of(pos):
    p = 83
    for a, b in pages:
        if a <= pos: p = b
        else: break
    return p
flat_nop = re.sub(r"\x01PAG\d+\x01", " ", flat)
# ricalcolo posizioni senza i marcatori di pagina (tengo la mappa pagina per marcatore)
# (piu' semplice: lascio i marcatori nel testo e li tolgo dal corpo di ogni voce)

# ---------------------------------------------------------------- anni
def tok_year(t):
    if not t: return None
    t2 = t.replace("O", "0").replace("S", "8").replace("I", "1").replace("l", "1").replace("G", "6").replace("g", "9").replace("B", "8").replace("b", "6").replace("(", "6").replace(")", "")
    t2 = re.sub(r"\D", "", t2)
    return int(t2) if len(t2) == 4 else None

SUBST = {"O": "0", "S": "835", "I": "1", "l": "1", "G": "60", "g": "9", "B": "8", "b": "6", "(": "6", "5": "58", "1": "174", "8": "836", "3": "38", "6": "658", "0": "0"}
def match_score(tok, cand):
    t = re.sub(r"[^0-9A-Za-z(]", "", tok)
    if len(t) != 4: return -1
    sc = 0
    for ch, d in zip(t, str(cand)):
        if ch == d: sc += 2
        elif d in SUBST.get(ch, ""): sc += 1
        else: sc -= 1
    return sc

year = None
prev_rank = 99
log = []
for k, m in enumerate(marks):
    if year is None:
        year = 1778; new_year = False
    elif m["ytok"]:
        best = max(range(year + 1, year + 5), key=lambda c: (match_score(m["ytok"], c), -c))
        sc = match_score(m["ytok"], best)
        if sc < 5: log.append("anno incerto: letto %r, scelgo %d (punteggio %d, pos %d)" % (m["ytok"], best, sc, m["pos"]))
        if best != year + 1: log.append("anno saltato: %d -> %d (letto %r)" % (year, best, m["ytok"]))
        year = best
    elif m["rank"] <= prev_rank:
        year += 1; log.append("anno senza numero letto: %s %d (stagione ricomincia)" % (m["names"], year))
    m["year"] = year
    prev_rank = m["rank"] if len(m["names"]) == 1 else RANK[m["names"][-1].upper()]

# ---------------------------------------------------------------- corpo di ogni voce
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
MESI3 = {m[:3]: i + 1 for i, m in enumerate(MESI)}; MESI3["die"] = 12; MESI3["dic"] = 12
ESITI = r"ottimo|buonissimo|buono|mediocre|cattivo|pessimo|discreto|ottimamente|fiasco"
RX_PB = re.compile(r"\b[PI1l]\s?\.\s*(?:[BbRlì15]|IL|lì|IÌ|J5|13|8|IÌ)\s?\.?\s")

def split_body(body):
    """-> (testo dei balli, testo dei ballerini)"""
    body = re.sub(r"\x01PAG\d+\x01", " ", body)
    m = RX_PB.search(body)
    if m:
        return body[:m.start()].strip(), body[m.end():].strip()
    # senza P. B.: il testo dei balli finisce al primo punto che chiude la frase
    pos = 0
    for mm in re.finditer(r"\.\s+(?=[A-ZÈ«\d])", body):
        before = body[:mm.start()]
        w = re.search(r"(\S+)$", before).group(1) if before else ""
        if re.fullmatch(r"[A-Z]|m|in|ni|ui|ecc|ed|sig|G|P|S|T|N", w): continue
        return body[:mm.start() + 1].strip(), ""
    return body.strip(), ""

def clean_name(n):
    n = re.sub(r"\s+", " ", n).strip(" ,.;—-")
    n = re.sub(r"\s*\([^)]*\)?$", "", n).strip(" ,.;—-")
    return n

RX_MUS = re.compile(r",?\s*(?:m|in|ni|ui|rn|111|il|nn|ili|iii|iu|ii)\.\s*(?:(?:di|del|dello)\s*,?\s+)?(?P<c>dello stesso|varii[^,(]*|diversi[^,(]*|[A-ZÈ][^—]*?)(?=,\s*(?:di|eli|dì)\s|\s*\(|\s*$)")
MESI_ALT = "gennai|febbra|marzo|april|maggi|giugn|lugli|agost|settem|ottob|novem|dicem|die|dic|genn|febb|apr|mag|giu|lug|ago|set|ott|nov"
def fix_digits(s):
    s = re.sub(r"\b2G\b", "26", s)
    s = re.sub(r"\b2S\b", "28", s)
    s = re.sub(r"\b(?:Il|IL|1l|Ii|li)(?=\s+(?:" + MESI_ALT + r"))", "11", s, flags=re.I)
    s = re.sub(r"\b[1I]\s1(?=\s+(?:" + MESI_ALT + r"))", "11", s)
    s = re.sub(r"\bdie\.", "dicembre", s)
    return s

def parse_segment(seg):
    """-> dict(titolo, coreografo, compositore, tutti, data_raw, esito, note, ballabile)"""
    s = fix_digits(seg.strip().strip(".;, "))
    s = re.sub(r"\bP, ", "P. ", s)
    s = s.replace(",'", ",")
    s = re.sub(r"\\\d?\s+((?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\b)", r"(\1", s)   # "(7 ottobre" letto "\1 ottobre": il giorno si perde, resta il mese
    s = re.sub(r",\s*ultimato da [^,(]*", "", s)
    s = re.sub(r",\s*(?:balletto|ballo)\s*$", "", s)
    s = re.sub(r"\blutti\b", "tutti", s); s = re.sub(r"\bam-?\s?bidue\b", "ambedue", s); s = re.sub(r"\bdj\b", "di", s)
    s = re.sub(r"\b3f", "M", s); s = re.sub(r"\b3I", "M", s); s = re.sub(r"\b31(?=[a-z])", "M", s)
    s = re.sub(r"\bdi(?=S[a-z])", "di ", s)
    s = re.sub(r"\bm\.\s*di(?=[A-Z])", "m. di ", s)
    s = re.sub(r",\s*balletto di\b", ", di", s)
    s = re.sub(r"\s+c\. s\b\.?", " (come sopra)", s)
    d = dict(titolo="", coreografo="", compositore="", tutti=False, data_raw="", esito="", note="", ballabile=False)
    paren = []
    def grab(m):
        paren.append(m.group(1)); return " "
    s = re.sub(r"\(([^()]*?)(?:\)|['’]\s*$)", grab, s)       # "(...)" o "(...'" (OCR)
    # parentesi aperta persa dall'OCR: "..., m. di Busi 26 dicembre 1871, cattivo)"
    if ")" in s and "(" not in s:
        m = re.search(r"(?<=[\s,])((?:\d{1,2})\s*(?:" + MESI_ALT + r")\w*\b[^)]*|ri-?\s*produ\w*[^)]*|riprodott\w*[^)]*)\)\s*$", s)
        if m:
            paren.append(m.group(1)); s = s[:m.start()]
        s = s.replace(")", " ")
    if "(" in s:                                     # parentesi mai chiusa (OCR: "cattivol", "mediocre i")
        k_ = s.rfind("(")
        paren.append(s[k_ + 1:]); s = s[:k_]
    mt_ = re.search(r"[\s,]+((?:\d{1,2}\s*)?(?:" + MESI_ALT + r")\w*\s*,\s*(?:" + ESITI + r"))\s*$", s)   # "... Taglioni giugno, buonissimo"
    if mt_:
        paren.append(mt_.group(1)); s = s[:mt_.start()]
    mt_ = re.search(r",\s*(" + ESITI + r")\s*$", s)
    if mt_:
        paren.append(mt_.group(1)); s = s[:mt_.start()]
    s = s.strip().strip(".;, ")
    mr_ = re.search(r",?\s*(riprodott[oa] da [A-Z][\w.\s]*?)$", s)
    if mr_:
        paren.append(mr_.group(1)); s = s[:mr_.start()]
    note = []
    for p in paren:
        p = re.sub(r"ri-\s*produ", "produ", p.strip())
        if re.fullmatch(r"\d", p): continue          # rimando a nota (1)
        me = re.search(r"\b(" + ESITI + r")[l1i']?\b", p, re.I)
        if me: d["esito"] = me.group(1).lower()
        md = re.search(r"(\d{1,2})\s*([a-zA-Zì]{3,10})\.?(?:\s+(\d{4}))?", p)
        if md and md.group(2)[:3].lower() in MESI3:
            d["data_raw"] = (md.group(1) + " " + md.group(2) + (" " + md.group(3) if md.group(3) else "")).strip()
        elif not me:
            mm = re.search(r"\b(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\b", p, re.I)
            if mm: d["data_raw"] = mm.group(1).lower()
        rest = re.sub(r"\b(" + ESITI + r")[l1i']?\b", "", p, flags=re.I)
        rest = re.sub(r"\d{1,2}\s*[a-zì]{3,10}\.?(?:\s+\d{4})?", "", rest, flags=re.I)
        rest = re.sub(r"\s+", " ", rest).strip(" ,.;")
        if rest: note.append(rest)
    if re.match(r"^(Ballabil[ei]|Divertimento danzante|Intermezzo danzante)\b", s, re.I):
        d["ballabile"] = True
    # "composto da X" (ballabili)
    mc = re.search(r",?\s*\bcompost[oi] (?:da|dallo stesso)\s+(.+?)(?=,\s*(?:m|in|ni|ui)\.|$)", s)
    if mc:
        d["coreografo"] = clean_name(mc.group(1)); s = (s[:mc.start()] + " " + s[mc.end():]).strip(" ,")
    # compositore "m. di X"
    mm = RX_MUS.search(s)
    if mm:
        d["compositore"] = clean_name(mm.group("c")) if not mm.group("c").startswith("dello") else "<stesso>"
        s = (s[:mm.start()] + " " + s[mm.end():]).strip(" ,")
    # coreografo: "tutti di X" oppure ", di X"
    mt = re.search(r",?\s*\b(?:tutti|tutte|ambedue|ambo|entrambi)\s+(?:di|eli|dì)\s+(.+)$", s)
    if mt:
        d["tutti"] = True; d["coreografo"] = clean_name(mt.group(1)); s = s[:mt.start()]
    elif not d["coreografo"]:
        mc = re.search(r",\s*(?:di|eli|dì)\s+([A-ZÈ][^,]*?)$", s)
        if mc:
            d["coreografo"] = clean_name(mc.group(1)); s = s[:mc.start()]
    if re.match(r"(varii|diversi)\b", d["compositore"], re.I): d["compositore"] = "vari autori"
    s = re.sub(r",\s*(?:di|eli)\s+[A-ZÈ][\w. ]*?\s*,\s*(?:m|ni|in)\.\s*$", "", s)
    d["titolo"] = re.sub(r"\s+", " ", s).strip(" ,.;—-'")
    d["note"] = "; ".join(n for n in note if n)
    return d

def parse_ballerini(txt):
    t = re.sub(r"\s+", " ", txt)
    t = re.split(r"\s*[—-]\s*(?:[MmJ]|3[1IUl!]|1I|AL)\.?\s|\s+[—-]\s+Allievi|Allieva emerita|Allieve|Scuola di Ballo|\bNB\.|\.\s+(?:il |Il |Questo|Come |Ballabil)|\n", t)[0]
    t = re.sub(r"\([^)]*\)", "", t)
    t = t.strip(" .;,")
    return t

def to_date(year, season_first, raw):
    if not raw: return ""
    m = re.match(r"(\d{1,2}|[1I]l?)\s*([a-zA-Zì]+)\.?\s*(\d{4})?$", raw)
    if m:
        g = m.group(1)
        g = 1 if g in ("I", "Il", "Il") else int(g)
        mo = MESI3.get(m.group(2)[:3].lower())
        if not mo or not (1 <= g <= 31): return ""
        y = int(m.group(3)) if m.group(3) else (year - 1 if (season_first == "Carnevale" and mo == 12) else year)
        return "%04d-%02d-%02d" % (y, mo, g)
    return ""

rows = []
anom = []
for k, m in enumerate(marks):
    end = marks[k + 1]["pos"] if k + 1 < len(marks) else len(flat)
    body = flat[m["end"]:end]
    # il corpo comincia dopo il marcatore; taglio la parte "Scuola di Ballo" ecc. (la gestisce split_body: dopo P. B.)
    pagina = page_of(m["pos"])
    # bozza di titolo/tag: se il marcatore e' seguito da "—"
    body = re.sub(r"^\s*[—–\-]+\s*", "", body)
    balli_txt, bal_txt = split_body(body)
    stagione_nome = " e ".join(m["names"])
    first = m["names"][0]
    # voci "Compositore, X" / "Compositori, X e Y" (solo musicisti, nessun ballo nominato)
    if re.match(r"^Compositor[ei]\b", balli_txt):
        anom.append("solo compositori (nessun titolo): %s %d: %s" % (stagione_nome, m["year"], balli_txt[:80]))
        continue
    parsed = []
    for part in re.split(r"(?<=\.)\s+(?=Ballabil|Divertimento danzante|Intermezzo danzante)", balli_txt):
        segs0 = [s for s in re.split(r"\s*[—–]\s*|\s+-\s+(?:-\s+)?|(?<=\))\s+(?=[A-ZÈ][a-zà-ù])", part) if s.strip()]
        segs = []
        for sg in segs0:
            mbn = re.match(r"^(.*?\b\d{1,2}\s+\w+,\s+a beneficio[^,]*?,\s+si diede il ballo\s+)(.+)$", sg)
            if mbn:                                  # "27 settembre, a beneficio del Pio Istituto Teatrale, si diede il ballo La rosiera, di Casati, ..."
                segs.append(mbn.group(2) + " (" + mbn.group(1).split(",")[0] + ", a beneficio del Pio Istituto Teatrale)"); continue
            cut = re.search(r",\s*(?:di|eli)\s+((?:[A-Z]\.\s*)?[A-Z][a-zà-ù]+)\s+(?=[A-Z][a-z]+\s+[a-z]|[A-Z][a-z]+\s+[A-Z]|[IL][a-z’' ]+\s)", sg)
            if cut and re.search(r",\s*(?:di|eli)\s+[A-Z]", sg[cut.end():]):
                segs.append(sg[:cut.end()].strip()); segs.append(sg[cut.end():].strip())
            else:
                segs.append(sg)
        ps = [parse_segment(s) for s in segs]
        # "tutti di X" si applica a tutti i balli precedenti del gruppo senza coreografo esplicito
        group = []
        for p in ps:
            group.append(p)
            if p["tutti"]:
                for q in group:
                    if not q["coreografo"]:
                        q["coreografo"] = p["coreografo"]
                group = []
        parsed += ps
    # compositore '<stesso>' = coreografo
    for p in parsed:
        if p["compositore"] == "<stesso>":
            p["compositore"] = p["coreografo"]
    ball = parse_ballerini(bal_txt)
    for p in parsed:
        if not p["titolo"] or len(p["titolo"]) < 3:
            continue
        data = to_date(m["year"], first, p["data_raw"])
        rows.append(dict(anno=m["year"], stagione="%s %d" % (stagione_nome, m["year"]), stagione_nome=stagione_nome, data=data,
                         titolo=p["titolo"], coreografo=p["coreografo"], compositore=p["compositore"], esito=p["esito"], note=p["note"],
                         ballabile="si" if p["ballabile"] else "", primi_ballerini=ball, pagina_libro=pagina, anno_letto=m["ytok"] or "",
                         riga_fonte="Cambiasi 1881, Serie dei balli, p.%d (%s %d)" % (pagina, stagione_nome, m["year"])))

# correzioni a mano su righe dove l'OCR rompe la frase (controllate sul testo; elencate nel log)
MANUALE = [
    (lambda r: r["anno"] == 1800 and r["titolo"].startswith("Zulima"), dict(titolo="Zulima", compositore="Pontelibero detto Ajutantini")),
    (lambda r: r["anno"] == 1844 and r["titolo"].startswith("I tre gobbi di Damasco"), dict(titolo="I tre gobbi di Damasco", coreografo="Paradisi")),
    (lambda r: r["anno"] == 1846 and r["titolo"].startswith("Un sogno di una notte"), dict(titolo="Un sogno di una notte d’estate", note="danza mima aerea eseguita dalla famiglia americana di Riccardo Risley")),
    (lambda r: r["anno"] == 1851 and "si diede il ballo" in r["titolo"], dict(titolo="La rosiera", coreografo="Casati", data="1851-09-27", note="a beneficio del Pio Istituto Teatrale (gia' dato nella stagione)")),
    (lambda r: r["anno"] == 1816 and r["titolo"].startswith("La scuola da ballo annessa"), None),
    (lambda r: r["anno"] == 1823 and r["titolo"].startswith("Kenilworth"), dict(titolo="Kenilworth", coreografo="Gioja", compositore="vari autori")),
    (lambda r: r["anno"] == 1837 and r["titolo"].startswith("I promessi sposi"), dict(titolo="I promessi sposi", coreografo="S. Taglioni")),
    (lambda r: r["anno"] == 1822 and r["titolo"].startswith("Alfredo il grande"), dict(titolo="Alfredo il grande", compositore="conte di Gallenberg")),
    (lambda r: r["anno"] == 1781 and r["titolo"].startswith("Solimano"), dict(titolo="Solimano")),
]
corr = []
rows2 = []
for r in rows:
    drop = False
    for f, fix in MANUALE:
        if f(r):
            if fix is None: drop = True
            else: r.update(fix)
            corr.append("%s %s: %s" % (r["anno"], r["titolo"][:40], "scartata" if fix is None else "corretta a mano"))
    if not drop: rows2.append(r)
rows = rows2

cols = ["anno", "stagione", "stagione_nome", "data", "titolo", "coreografo", "compositore", "esito", "note", "ballabile", "primi_ballerini", "pagina_libro", "anno_letto", "riga_fonte"]
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
per_anno = collections.Counter(r["anno"] for r in rows)
logp = os.path.join(os.path.dirname(out), "_cambiasi_balli_log.txt")
with open(logp, "w", encoding="utf-8") as f:
    f.write("righe: %d; marcatori di stagione: %d; anni con balli: %d (%d-%d)\n" % (len(rows), len(marks), len(per_anno), min(per_anno), max(per_anno)))
    f.write("anni 1778-1881 senza balli: %s\n" % [y for y in range(1778, 1882) if y not in per_anno])
    f.write("balli per anno: %s\n" % dict(sorted(per_anno.items())))
    f.write("\n".join(log + anom + ["correzione manuale: " + c for c in corr]) + "\n")
print("righe", len(rows), "marcatori", len(marks), "anni", len(per_anno), min(per_anno), max(per_anno))
print("anni senza balli:", [y for y in range(1778, 1882) if y not in per_anno])
print("\n".join(log[:40])); print("\n".join(anom[:20]))
