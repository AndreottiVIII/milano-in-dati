"""Gatti vol.1: dai due indici (opere, nomi) e dal testo OCR ricava, per ogni voce dell'indice delle opere e per ogni pagina citata,
la stagione (dedotta dai titoli di sezione e dalle date sulla pagina) e, se nominati nella stessa frase, direttore / regista / interpreti.
Solo FATTI (titolo, autore, pagina, stagione, nomi): nessuna prosa viene copiata nel file di uscita. I contesti per il controllo a mano
vanno in pulito/_gatti_contesti_locali.csv (SOLO LOCALE, non ripubblicabile).
Uso: python -I -X utf8 scripts/gatti_citazioni.py raw/gatti_testo/gatti_pagine.json pulito
"""
import sys, json, re, csv, os, unicodedata, bisect, collections

pag = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
OFF = 12           # pagina PDF = pagina stampata + 12 (narrazione)
ROMOFF = 492       # appendice 1958-63: pagina romana n = PDF 492+n
NARR = range(15, 492)   # pagine PDF 1-based della narrazione
APP = range(495, 504)

MESI = {"gennaio":1,"febbraio":2,"marzo":3,"aprile":4,"maggio":5,"giugno":6,"luglio":7,"agosto":8,"settembre":9,"ottobre":10,"novembre":11,"dicembre":12}

def strip_acc(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
def norm(s):
    s = strip_acc(s.lower().replace("’", "'").replace("`", "'"))
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# ------------------------------------------------------------------ flusso di testo con ancore
stream = []           # pezzi di testo
page_start = []       # (offset, etichetta_pagina_stampata, pdf)
anchors = []          # (offset, kind, season_start_year, label)
rej = []
pos = 0
HEAD = re.compile(r"^(?:La |Le |Nella |Per la )?(?:prima |seconda |terza |ultima )?stagion[ei]\b[^.\n]{0,45}?(\d{4})\s*[-–—]\s*(\d{2,4})", re.I)
def clean_page(t):
    lines = [l.rstrip() for l in t.split("\n")]
    # via numeri di pagina isolati in testa/coda
    while lines and re.fullmatch(r"\s*[\dIl|]{1,3}\.?\s*|\s*[IVXilv]{1,5}\s*", lines[-1] or " "): lines.pop()
    while lines and re.fullmatch(r"\s*[\dIl|]{1,3}\.?\s*", lines[0] or " "): lines.pop(0)
    return lines
text_parts = []
heads = []
for idx in list(NARR) + list(APP):
    pdf = idx
    lab = str(pdf - OFF) if pdf <= 491 else None
    if pdf in APP:
        n = pdf - ROMOFF
        lab = "r%d" % n
    page_start.append((pos, lab, pdf))
    lines = clean_page(pag[pdf - 1])
    buf = ""
    for l in lines:
        s = l.strip()
        if not s: continue
        m = HEAD.match(s)
        if m and len(s) < 90:
            y1 = int(m.group(1)); y2 = m.group(2)
            heads.append((pos + len(buf), y1, y2, s))
        if buf.endswith("-") and s[:1].islower():
            buf = buf[:-1] + s
        else:
            buf += (" " if buf else "") + s
    # ricalcolo offset dei heads in base al buf: semplificazione - posizione = inizio pagina + lunghezza buf al momento
    text_parts.append(buf + " ")
    pos += len(buf) + 1
TEXT = "".join(text_parts)
page_offsets = [p[0] for p in page_start]

def page_of(off):
    i = bisect.bisect_right(page_offsets, off) - 1
    return page_start[max(i, 0)]

def season_label(y1, y2=None):
    if y2 is None: return str(y1)
    y2 = str(y2)
    if len(y2) == 4: y2 = y2[2:]
    # correzione OCR: seconda cifra incoerente
    exp = "%02d" % ((y1 + 1) % 100)
    if y2 != exp: y2 = exp
    return "%d-%s" % (y1, y2)

# heading anchors
for (off, y1, y2, s) in heads:
    if 1778 <= y1 <= 1963:
        anchors.append([off, "testata", y1, season_label(y1, y2)])

# date anchors con anno
DATE = re.compile(r"\b(\d{1,2}|1°|primo)?\s*(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(?:del(?:l')?\s+)?(1[789]\d\d)\b", re.I)
for m in DATE.finditer(TEXT):
    mo = MESI[m.group(2).lower()]; y = int(m.group(3))
    if y < 1778 or y > 1963: continue
    if y >= 1905:
        s = y if mo >= 9 else y - 1
        lab = season_label(s, s + 1)
    else:
        s = y; lab = str(y)
    anchors.append([m.start(), "data", s, lab])
anchors.sort(key=lambda a: a[0])

# filtro di coerenza (rimanda a ricordi/flashback): stato = ultima ancora accettata
# Dopo un titolo di sezione ("La stagione 1950-51.") le date che puntano a un'altra stagione sono scartate per 25000 caratteri
# (circa 7 pagine); due date consecutive che puntano alla stessa stagione successiva fanno ripartire lo stato.
acc = []; state = None; recent_rej = []; head = None   # head = (offset, anno)
for a in anchors:
    if a[1] == "testata":
        acc.append(a); state = a[2]; head = (a[0], a[2]); recent_rej = []; continue
    if head is not None and a[0] - head[0] <= 25000:
        if a[2] == head[1]:
            acc.append(a); recent_rej = []
        elif a[2] > head[1]:
            recent_rej.append(a); acc.append(a) if a[2] <= head[1] + 1 else None   # una data in avanti di una stagione si accetta subito (stagioni senza titolo di sezione)
            if len(recent_rej) >= 2 and recent_rej[-1][2] == recent_rej[-2][2] and recent_rej[-1][0] - recent_rej[-2][0] < 4000:
                for r in recent_rej[-2:]: acc.append(r)
                head = (recent_rej[-1][0], recent_rej[-1][2]); state = head[1]; recent_rej = []
        continue
    if state is None:
        acc.append(a); state = a[2]; continue
    if abs(a[2] - state) <= 1:
        acc.append(a); state = a[2]; recent_rej = []
    else:
        recent_rej.append(a)
        if len(recent_rej) >= 3 and max(r[2] for r in recent_rej[-3:]) - min(r[2] for r in recent_rej[-3:]) <= 1:
            for r in recent_rej[-3:]: acc.append(r)
            state = recent_rej[-1][2]; recent_rej = []
acc.sort(key=lambda a: a[0])
acc_off = [a[0] for a in acc]
print("ancore:", len(anchors), "accettate:", len(acc), "testate:", sum(1 for a in acc if a[1] == "testata"))

def season_at(off):
    i = bisect.bisect_right(acc_off, off) - 1
    prev = acc[i] if i >= 0 else None
    nxt = acc[i + 1] if i + 1 < len(acc) else None
    return prev, nxt

# ------------------------------------------------------------------ indici
def read_csv(fn):
    return list(csv.DictReader(open(os.path.join(out, fn), encoding="utf-8")))
opere = read_csv("_gatti_opere.csv"); nomi = read_csv("_gatti_nomi.csv")

def pagenum_to_stream_label(p):
    return p  # 'rN' oppure int come stringa

# mappa etichetta pagina -> (inizio, fine) nel testo
page_range = {}
for i, (off, lab, pdf) in enumerate(page_start):
    end = page_start[i + 1][0] if i + 1 < len(page_start) else len(TEXT)
    page_range[lab] = (off, end)

# nomi: cognome -> [(nome_completo, set(pagine))]
GP = {"de","del","della","dal","di","da","van","von","le","la","lo","dei","degli","mc","santa","san","ten","sant","d"}
persone = collections.defaultdict(list)
for r in nomi:
    full = re.sub(r"\s*\([^)]*\)", "", r["nome"]).split(",")[0].strip()
    full = re.sub(r"\s+(cant|dir|sopr|ten|bar)\.?$", "", full)
    if not full or ":" in full or re.search(r"[0-9]", full) or not re.fullmatch(r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’.\- ]+", full): continue
    pgs = set()
    for x in (r["pagine"] or "").split(";"):
        if x: pgs.add(x)
    toks = full.split()
    if not toks: continue
    keys = {toks[0]}
    if toks[0].lower() in GP and len(toks) > 2: keys.add(toks[0] + " " + toks[1])
    for k in keys:
        persone[k].append((full, pgs))

CONDUCT_CUE = re.compile(r"(diretto da|diretta da|diretti da|dirette da|direttore|direttori|direzione di|direzione del|bacchetta|concertat\w+|dirige|dirigono|diresse|dirigeva|sul podio|maestro)\s*(?:d'orchestra|e direttore)?\s*(?:è|e|sono|:)?\s*(?:il |lo |l')?(?:maestro |M\. )?$", re.I)
REGIA_CUE = re.compile(r"(regista|regia|direzione scenica|messa in scena|allestimento scenico|allestimento)\s*(?:di|del|dello|è|:)?\s*(?:il |lo |l')?(?:signor |sig\. )?$", re.I)
SCENE_CUE = re.compile(r"(scene|bozzetti|figurini|costumi|scenografo|scenografie|scenari|pittore|coreografo|coreografia|ballerina|prima ballerina|maestro del coro|coro istruito da|coro|disegni|apparato|apparati)\s*(?:di|del|dello|ed?|:)?\s*(?:il |lo |l')?(?:signor |sig\. )?$", re.I)
SINGER_CUE = re.compile(r"(cantanti|cantano|canta|interpreti|protagonist\w+|compagni|soprano|tenore|baritono|basso|mezzosoprano|contralto|esecutori|con loro|con lei|con lui|\bcon)\b[^.;]{0,160}$", re.I)
PERF_CUE = re.compile(r"(si rappresenta|rappresentazion|va in scena|si da\b|si dà|si ripete|si replica|prima rappresentazione|si inaugura|si apre|esito|direttore|cantanti|cantano|interpreti|protagonist|inaugura|la sera|in cartellone|programma|maestro concertatore|diretta da|diretto da|bacchetta|si eseguono|esegu)", re.I)
LITERARY_AUTHORS = {"w shakespeare","shakespeare","v hugo","hugo","c goldoni","goldoni","c gozzi","gozzi","p metastasio","metastasio","g d annunzio","d annunzio","l tolstoi","tolstoi","t s eliot","eliot","o wilde","wilde","f schiller","schiller","j w goethe","goethe","j ancelot","ancelot","b constant","n gogol","gogol","molière","moliere","g b meiners"}
SYMPH = re.compile(r"^(?:la |il |l')?(sinfonia|concerto|requiem|messa|stabat|salmo|suite|variazioni|sonata|quartetto|inno|te deum|magnificat|ouverture|preludio|poema|canti|cantata|oratorio|passione)\b", re.I)
BALLET_AUT = {"s vigano","s vigand","vigano","r pick mangiagalli","j weaver","a savinio"}

WRITER_SURNAMES = {"shakespeare","hugo","goldoni","gozzi","metastasio","annunzio","tolstoi","eliot","wilde","schiller","goethe","gothe","ancelot","constant","gogol","moliere","hauptmann","ibsen","dostoevskij","manzoni","dante","boccaccio","pellico","byron","scott","sardou","pirandello","cocteau","claudel","maeterlinck","sofocle","euripide","eschilo","aristofane","andersen","grimm","perrault","gorki","cechov","strindberg","wedekind","shaw","benelli","bracco","giacosa","fogazzaro","verga","bertolazzi","gallina"}
def genere_guess(title, autore):
    a = norm(autore).replace("'", "")
    last = a.split(" ")[-1] if a else ""
    if last in WRITER_SURNAMES: return "testo letterario"
    if a in LITERARY_AUTHORS or any(a.endswith(x) for x in LITERARY_AUTHORS): return "testo letterario"
    if SYMPH.match(title.strip()): return "concerto"
    if a in BALLET_AUT or "vigan" in a: return "balletto"
    return "opera o balletto"

# ------------------------------------------------------------------ ricerca dei titoli nella pagina
ART_RE = r"(?:il |lo |la |l'|le |gli |i |un |una |un')?"
def core(title):
    t = norm(title)
    t = re.sub(r"^(?:il|lo|la|l|le|gli|i|un|una|un) ", "", t)
    t = re.sub(r"^l' ?", "", t)
    return t
NTEXT_CACHE = {}
def norm_with_map(text):
    """normalizza mantenendo mappa offset normalizzato -> offset originale"""
    res = []; mp = []
    prev_space = True
    for i, ch in enumerate(text):
        c = ch.lower()
        c = strip_acc(c)
        if c == "’" or c == "`": c = "'"
        if not (c.isalnum() or c == "'"):
            c = " "
        if c == " ":
            if prev_space: continue
            prev_space = True
        else:
            prev_space = False
        res.append(c); mp.append(i)
    return "".join(res), mp

WORD = re.compile(r"[a-z0-9']+")
pages_words = {}
for lab, (a_, b_) in page_range.items():
    nt, mp = norm_with_map(TEXT[a_:b_])
    ws = [(m.group(0), a_ + mp[m.start()], a_ + mp[m.end() - 1] + 1) for m in WORD.finditer(nt)]
    pages_words[lab] = ws

def ed1(a, b):
    if a == b: return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1 or min(la, lb) < 5: return False
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) <= 1
    if la > lb: a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]: i += 1
    return a[i:] == b[i + 1:]

def wmatch(w, t):
    return w == t or (len(t) >= 6 and ed1(w, t))

def find_title(lab, title):
    toks = core(title).split()
    toks = [t for t in toks if t]
    if not toks or len(core(title)) < 4: return []
    ws = pages_words[lab]
    keys = [(i, t) for i, t in enumerate(toks) if len(t) >= 4] or list(enumerate(toks))
    if toks[0] in ("sinfonia", "concerto", "sonata", "quartetto", "suite", "sinfonie") and len(toks) > 1:
        keys = list(enumerate(toks))
    i0, k0 = keys[0]
    res = []
    for i, (w, o1, o2) in enumerate(ws):
        if not wmatch(w, k0): continue
        lo = max(0, i - i0 - 1); hi = min(len(ws), i - i0 + len(toks) + 3)
        seg = [x[0] for x in ws[lo:hi]]
        if all(any(wmatch(x, t) for x in seg) for (_, t) in keys[1:]):
            res.append((ws[max(0, i - i0)][1], ws[min(len(ws) - 1, i - i0 + len(toks) - 1)][2]))
    return res

# n-gram dei titoli (per riconoscere altri titoli in una finestra)
cores_set = set(c for c, t in [(core(r["titolo"]), r["titolo"]) for r in opere] if len(c) >= 5)
first_map = collections.defaultdict(list)
for c in cores_set:
    first_map[c.split()[0]].append(c.split())
def titles_in(a_, b_, skip_core=None):
    """span (inizio, fine, core) dei titoli d'indice presenti in TEXT[a_:b_]"""
    nt, mp = norm_with_map(TEXT[a_:b_])
    ws = [(m.group(0), m.start(), m.end()) for m in WORD.finditer(nt)]
    res = []
    i = 0
    while i < len(ws):
        w = ws[i][0]
        best = None
        for cand in first_map.get(w, ()):
            n = len(cand)
            if [x[0] for x in ws[i:i + n]] == cand:
                if best is None or n > len(best): best = cand
        if best:
            c = " ".join(best)
            if c != skip_core:
                res.append((a_ + mp[ws[i][1]], a_ + mp[ws[i + len(best) - 1][2] - 1] + 1, c))
            i += len(best)
        else:
            i += 1
    return res

# ------------------------------------------------------------------ finestra frase e personaggi
def sentence_bounds(off):
    a = TEXT.rfind(". ", max(0, off - 400), off)
    a = a + 2 if a >= 0 else max(0, off - 120)
    b = TEXT.find(". ", off)
    b = b + 1 if b >= 0 and b - off < 600 else min(len(TEXT), off + 400)
    return a, b

PERS_CAND = re.compile(r"(?<![A-Za-zÀ-ÿ'’])((?:De |Del |Della |Dal |Di |Da |Van |Von |Le |La )?[A-ZÀ-Ý][a-zà-ÿ'’]+(?:-[A-Z][a-zà-ÿ]+)?)")

def nome_cognome(full, key):
    """'Guarnieri Antonio' -> 'Antonio Guarnieri' (la chiave e' il cognome)"""
    q = full.endswith("?"); f = full.rstrip("?")
    if f.startswith(key + " "):
        rest = f[len(key) + 1:].strip()
        f = (rest + " " + key).strip()
    return f + ("?" if q else "")

CUEWORDS = {"Direttore","Direttori","Regista","Regia","Maestro","Cantano","Cantanti","Interpreti","Protagonista","Protagonisti","Con","Dirige","Diretta","Diretto"}
def persons_in(a, b, page_labels):
    res = []
    seg = TEXT[a:b]
    for m in PERS_CAND.finditer(seg):
        key = m.group(1)
        cands = persone.get(key)
        if not cands: continue
        # nome di battesimo seguito dal cognome ("Franco Capuana")?
        mm = re.match(r"\s+((?:De |Del |Della |Dal |Di |Da |Van |Von )?[A-ZÀ-Ý][a-zà-ÿ'’]+)", seg[m.end():m.end() + 30])
        if mm:
            k2 = mm.group(1)
            if any(key in c[0].split()[1:] for c in persone.get(k2, [])): continue
        ok = [c for c in cands if any(p in c[1] for p in page_labels)]
        if not ok: continue
        names = sorted(set(c[0] for c in ok))
        full = names[0] if len(names) == 1 else names[0] + "?"
        pre = TEXT[max(0, a + m.start() - 90): a + m.start()]
        for _ in range(3):
            mp = re.search(r"([A-ZÀ-Ý][\w'’.]*|von|van|de)\s+$", pre)
            if mp and mp.group(1) not in CUEWORDS: pre = pre[:mp.start()]
            else: break
        res.append((a + m.start(), key, nome_cognome(full, key), pre))
    return res

def classify(pre, nxt):
    if CONDUCT_CUE.search(pre): return "dir"
    if re.match(r"\s*(dirige|diresse|dirigeva|concerta|dirigono)\b", nxt): return "dir"
    if REGIA_CUE.search(pre): return "reg"
    if SCENE_CUE.search(pre): return "altro"
    return "int"

def uniq(l):
    o = []
    for x in l:
        if x not in o: o.append(x)
    return o

SINGER_OK = re.compile(r"(cantano|canta|cantanti|cantante|interpret\w+|protagonist\w+|affidat\w+|compagn\w+|soprano|tenore|baritono|basso|mezzosoprano|contralto|artist\w+|voci|ballerin\w+|danzator\w+|solist\w+|con|e|alla|al|la|il|lo|dalla|dal|,|:)\s*(?:(?:la|il|lo|l')\s*)?$", re.I)
CUE_NAME = re.compile(r"(?:diretta da|diretto da|diretti da|dirette da|direttore|direttori|concertatore e direttore|concertata da)\s+(?:il |lo |l')?(?:maestro )?((?:(?:von|de|di|Von|De|Di)\s+)?[A-Z][\w'’-]+)")
CASTWORDS = re.compile(r"(Cantano|Cantanti|Interpreti|Direttore|Direttori|Maestro|Regista|Regia|Protagonist|Con loro|Lodevoli|Dirige|Diretta|Diretto|Esecutori)")
def extract_cast(span, titolo, autore, plabels):
    off1, off2 = span
    a, b = sentence_bounds(off1)
    cs = core(titolo)
    others = titles_in(off2, b, skip_core=cs)
    end = b
    j = bisect.bisect_right(acc_off, off2)
    while j < len(acc) and acc[j][1] != "testata": j += 1
    if j < len(acc): end = min(end, acc[j][0]); b = min(b, acc[j][0])
    semi = TEXT.find(";", off2, b)
    if semi >= 0: end = min(end, semi)
    if others: end = min(end, others[0][0])
    before = [t for t in titles_in(a, off1, skip_core=cs)]
    flags = []
    pers = persons_in(off2, end, plabels)
    mode = "frase"
    if others and end < b: mode = "elenco"
    strong = re.search(r"(si rappresenta|va in scena|si da|si dà|si inaugura|si apre|prima rappresentazione|si ripete|si replica|rappresentazione)", TEXT[a:b], re.I)
    if not pers and not others and not before and strong:
        pos_ = b
        for _ in range(2):
            nb = TEXT.find(". ", pos_ + 1)
            nb = nb + 1 if nb >= 0 and nb - pos_ < 500 else min(len(TEXT), pos_ + 300)
            nxt = TEXT[pos_:nb]
            if titles_in(pos_, nb, skip_core=cs): break
            if CASTWORDS.search(nxt):
                pers = persons_in(pos_, nb, plabels); mode = "frase_seguente"
                if pers: break
            pos_ = nb
    dirs, regs, ints = [], [], []
    aut_sur = norm(autore.split(" ")[-1]) if autore else ""
    for (p, key, full, pre) in pers:
        if aut_sur and norm(key) == aut_sur: continue
        nxt = TEXT[p + len(key): p + len(key) + 40]
        role = classify(pre, nxt)
        if role == "int" and re.search(r"(\bdi|\bdel|\bdello|\bdella|\bda|musiche di|musica di|poesia di|libretto di|opera di|maestro|compositore)\s+$", pre[-40:], re.I): continue
        if role == "dir": dirs.append(full)
        elif role == "reg": regs.append(full)
        elif role == "int" and SINGER_OK.search(pre[-110:]): ints.append(full)
    # "De Sabata dirige l'Otello": direttore PRIMA del titolo
    base0 = max(0, off1 - 70)
    m0 = re.search(r"([A-Z][\w'’]+(?: [A-Z][\w'’]+)?)\s+(?:dirige|diresse|dirigeva|concerta|concertò)\b[^.;]{0,25}$", TEXT[base0:off1])
    if m0:
        for (p, key, full, pre) in persons_in(base0 + m0.start(1), base0 + m0.end(1), plabels):
            if full not in dirs: dirs.append(full)
    if before and not others and pers: flags.append("altri_titoli_prima_nella_frase")
    ints = [x for x in ints if x not in dirs and x not in regs]
    # direttore indicato nel testo ma non riconosciuto con l'indice dei nomi: i nomi della finestra non sono sicuri
    wtxt = TEXT[off2:end]
    rec = set(k for (_, k, _, _) in pers)
    for mc in CUE_NAME.finditer(wtxt):
        sur_ = mc.group(1).split()[-1]
        if sur_ not in rec:
            flags.append("nome_non_riconosciuto"); break
    sicuro = ((not before and not others and mode == "frase") or (mode == "elenco" and bool(dirs))) and "nome_non_riconosciuto" not in flags
    if not sicuro: flags.append("nomi_incerti")
    return uniq(dirs), uniq(regs), uniq(ints), mode, flags

# ------------------------------------------------------------------ giro sulle voci d'indice
def pagelabel_list(p):
    return [x for x in (p or "").split(";") if x]

def adjacent(lab):
    if lab.startswith("r"): return []
    n = int(lab)
    return [str(x) for x in (n - 1, n + 1) if str(x) in page_range]

rows = []; ctx_rows = []
n_pair = 0; n_found = 0; n_adj = 0
seen_keys = set()
for r in opere:
    titolo = r["titolo"]; autore = r["autore"]
    pgs = pagelabel_list(r["pagine"])
    if not pgs: continue
    gen = genere_guess(titolo, autore)
    for pg in pgs:
        lab = pg
        if lab not in page_range: continue
        k = (titolo, autore, lab)
        if k in seen_keys: continue
        seen_keys.add(k)
        n_pair += 1
        spans = find_title(lab, titolo); where = lab; adj_note = ""
        if spans: n_found += 1
        else:
            for al in adjacent(lab):
                spans = find_title(al, titolo)
                if spans:
                    where = al; adj_note = "titolo trovato nella pagina %s (l'indice dice %s)" % (al, lab); n_adj += 1; break
        if not spans:
            a_, b_ = page_range[lab]
            prev, nxt = season_at((a_ + b_) // 2)
            if prev is None: continue
            rows.append({"titolo": titolo, "autore": autore, "pagina": lab, "stagione": prev[3], "anno": prev[2],
                         "direttore": "", "regista": "", "interpreti": "", "genere": gen, "trovato_nel_testo": "no",
                         "segnale_spettacolo": "", "tipo_ancora": prev[1], "conf": "bassa", "collegamento_nomi": "", "note": "titolo non localizzato nel testo OCR; stagione dedotta dalla pagina"})
            continue
        seen_seasons = {}
        for (o1, o2) in spans:
            prev, nxt = season_at(o1)
            if prev is None: continue
            s_ = prev[3]; dist = o1 - prev[0]
            a_, b_ = sentence_bounds(o1)
            cue = bool(PERF_CUE.search(TEXT[max(0, a_ - 40): b_ + 60]))
            seen_seasons.setdefault(s_, []).append(((o1, o2), prev, dist, cue))
        for s_, lst in seen_seasons.items():
            lst.sort(key=lambda x: (not x[3], x[2]))
            (o1, o2), prev, dist, cue = lst[0]
            dirs, regs, ints, flags, modes = [], [], [], [], []
            for (sp, pv2, d2, c2) in lst[:3]:
                if not c2 and len(lst) > 1: continue
                d, rg, it, mode, fl = extract_cast(sp, titolo, autore, [where, lab])
                for x in d:
                    if x not in dirs: dirs.append(x)
                for x in rg:
                    if x not in regs: regs.append(x)
                for x in it:
                    if x not in ints: ints.append(x)
                if d or rg or it: modes.append(mode)
                flags += fl
            ok_anchor = (prev[1] == "data" and dist <= 1500) or (prev[1] == "testata" and dist <= 6000)
            score = 1 + (1 if cue else 0) + (1 if ok_anchor else 0)
            conf = "alta" if score == 3 else ("media" if score == 2 else "bassa")
            if gen == "testo letterario": conf = "bassa"
            elif adj_note and conf == "alta": conf = "media"
            note = []
            if adj_note: note.append(adj_note)
            if "altri_titoli_prima_nella_frase" in flags: note.append("altri titoli prima nella frase: nomi da verificare")
            if (dirs or regs or ints) and "nomi_incerti" in flags: note.append("collegamento nomi-titolo incerto")
            if not cue: note.append("senza segnale di rappresentazione")
            rows.append({"titolo": titolo, "autore": autore, "pagina": lab, "stagione": s_, "anno": prev[2],
                         "direttore": "; ".join(dirs), "regista": "; ".join(regs), "interpreti": "; ".join(ints), "genere": gen,
                         "trovato_nel_testo": "si", "segnale_spettacolo": "si" if cue else "no", "tipo_ancora": prev[1] + ("" if ok_anchor else "_lontana"),
                         "conf": conf, "collegamento_nomi": ",".join(sorted(set(modes))), "note": " | ".join(note)})
            ctx_rows.append({"titolo": titolo, "pagina": lab, "stagione": s_, "contesto_locale": TEXT[max(0, o1 - 150): min(len(TEXT), o2 + 450)]})

print("coppie (voce,pagina):", n_pair, "titolo trovato nella pagina:", n_found, "= %.1f%%" % (100 * n_found / max(n_pair, 1)), "; in pagina adiacente:", n_adj)

def pk(p):
    return (1000 + int(p[1:])) if p.startswith("r") else int(p)
rows.sort(key=lambda r: (r["anno"], r["stagione"], r["titolo"], pk(r["pagina"])))
cols = ["titolo", "autore", "pagina", "stagione", "anno", "direttore", "regista", "interpreti", "genere", "trovato_nel_testo", "segnale_spettacolo", "tipo_ancora", "confidenza", "collegamento_nomi", "note", "fonte", "affidabilita", "ripubblicabile", "riferimento"]
with open(os.path.join(out, "gatti_vol1_citazioni.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, cols); w.writeheader()
    for r in rows:
        r2 = dict(r); r2["confidenza"] = r2.pop("conf")
        r2["fonte"] = "gatti_vol1"; r2["affidabilita"] = "bassa" if r["conf"] == "bassa" else "media"
        r2["ripubblicabile"] = "no"
        pnum = ("p. " + r["pagina"]) if not r["pagina"].startswith("r") else "appendice p. " + r["pagina"][1:]
        r2["riferimento"] = "C. Gatti, Il Teatro alla Scala nella storia e nell'arte, vol. I, Ricordi 1964, " + pnum
        w.writerow(r2)
with open(os.path.join(out, "_gatti_contesti_locali.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, ["titolo", "pagina", "stagione", "contesto_locale"]); w.writeheader(); w.writerows(ctx_rows)
c = collections.Counter(r["conf"] for r in rows)
print("righe:", len(rows), dict(c))
