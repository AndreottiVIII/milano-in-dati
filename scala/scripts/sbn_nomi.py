"""Estrae i nomi CON RUOLO dalle schede complete SBN (raw/sbn/full) e arricchisce sbn/sbn_programmi.csv.

Ordine di lavoro (dalla cartella scala/):
    python -I -X utf8 scripts/sbn_parse.py        # ricrea sbn_programmi.csv dalle schede (con la correzione del numero d'ordine)
    python -I -X utf8 scripts/sbn_nomi.py         # questo programma: nomi con ruolo, interpreti, date

Fonti dei nomi (colonna `fonte` di sbn/sbn_persone.csv):
  nomi         campo strutturato "nomi" della scheda, ruolo preso dall'etichetta tra parentesi quadre ([Regista], [Direttore d'orchestra]...)
  nomi+titolo  nome senza etichetta nel campo "nomi" a cui la dichiarazione di responsabilita' del titolo/delle note da' un ruolo
  titolo       nome scritto nel titolo ("regia di ...", "interpreti principali ...") ma assente dal campo "nomi"
  note         come sopra, ma scritto nelle note della scheda
Nessuna rete: legge solo la cache. Scrive: sbn/sbn_persone.csv, sbn/sbn_nomi_log.csv (ogni cambio a sbn_programmi.csv),
sbn/sbn_nomi_copertura.csv (prima/dopo).
"""
import sys, os, re, csv, json, glob, unicodedata, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SBN = os.path.join(ROOT, "sbn")
FULL = os.path.join(ROOT, "raw", "sbn", "full")
MESI = "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre".split("|")
MESI_RE = "|".join(MESI)

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# ---------------------------------------------------------------- nomi
ENTE = re.compile(r"\b(teatro|teatr|accademia|orchestra|coro|edizioni|ente|fondazione|festival|opera house|op[eé]ra|ballet|bolshoi|filarmonica|piccolo|associazione|comune|regione|ministero|museo|biblioteca|amici|centro|istituto|societ[aà]|radio|rai|production|produzioni)\b", re.I)

def nome_pulito(raw):
    """'Cognome, Nome <date>' -> ('Nome Cognome', 'cognome_chiave'). 'Otter, Anne Sofie : von' -> 'Anne Sofie von Otter'."""
    n = re.sub(r"^\[[^\]]*\]\s*", "", raw or "")
    n = re.sub(r"<[^>]*>", "", n)
    n = n.replace("ʹ", "").strip()
    n = re.sub(r"\s+", " ", n)
    if "," in n:
        cogn, rest = n.split(",", 1)
        rest = rest.split(",")[0]                       # "Perrot, Jules, coreografo": scarta la qualifica dopo la 2a virgola
        part = ""
        m = re.match(r"^(.*?)\s*:\s*(.+)$", rest)
        if m: rest, part = m.group(1), m.group(2)
        nome = " ".join(x for x in (rest.strip(), part.strip(), cogn.strip()) if x)
        chiave = norm(cogn).split(" ")[-1] if norm(cogn) else ""
        ini = norm(rest)[:1]
    else:
        m = re.match(r"^(.*?)\s*:\s*(.+)$", n)           # "Saint-Georges : de"? raro senza virgola
        nome = n
        t = norm(n).split(" ")
        chiave = t[-1] if t else ""
        ini = t[0][:1] if len(t) > 1 else ""
    return nome.strip(" ."), chiave, ini

def chiave_libera(nome):
    t = norm(nome).split(" ")
    return (t[-1] if t else "", t[0][:1] if len(t) > 1 else "")

TAG = {  # etichetta -> (ruolo, dettaglio)
    "compositore": ("compositore", ""), "compositore della musica parafrasata": ("compositore", "musica parafrasata"),
    "librettista": ("librettista", ""), "paroliere, autore della poesia": ("librettista", "paroliere"),
    "autore del dialogo": ("librettista", "dialogo"), "sceneggiatore": ("librettista", "sceneggiatura"),
    "adattatore/rielaboratore": ("librettista", "adattatore"), "traduttore": ("traduttore", ""),
    "direttore d'orchestra": ("direttore", ""), "direttore di coro": ("maestro del coro", ""),
    "regista": ("regista", ""), "coreografo": ("coreografo", ""), "scenografo": ("scenografo", ""), "costumista": ("costumista", ""),
    "interprete": ("interprete", ""), "cantante": ("interprete", "cantante"), "strumentista": ("interprete", "strumentista"),
    "ballerino": ("interprete", "ballerino"), "personale di produzione": ("produzione", ""),
    "arrangiatore": ("arrangiatore", ""), "autore": ("autore (non specificato)", ""), "curatore": ("curatore", ""),
    "autore dell'introduzione": ("saggista", "introduzione"), "autore citato": ("autore citato", ""),
    "antecedente bibliografico": ("antecedente bibliografico", ""), "editore": ("editore", ""), "fotografo": ("fotografo", ""),
    "produttore": ("ente produttore", ""), "altro": ("altro", ""), "direttore editoriale": ("editoria", ""),
    "ideatore": ("ideatore", ""), "compilatore": ("curatore", "compilatore"), "consulente scientifico": ("saggista", "consulente"),
}
VOCI = {"S": "soprano", "T": "tenore", "B": "basso", "V-recit": "voce recitante", "M": "mezzosoprano", "C": "contralto", "A": "alto", "BAR": "baritono"}

def ruolo_da_tag(raw):
    m = re.match(r"^\[([^\]]*)\]", raw or "")
    if not m: return "", "", ""
    tag = m.group(1).strip()
    m2 = re.match(r"^\d+([A-Za-z-]+)=(.+)$", tag)       # [590S=Soprano]
    if m2: return "interprete", m2.group(2).lower(), tag
    if re.fullmatch(r"\d+", tag): return "ruolo_non_dichiarato", "codice " + tag, tag
    r = TAG.get(tag.lower())
    return (r[0], r[1], tag) if r else ("altro", tag, tag)

# ---------------------------------------------------------------- testo: dichiarazioni di responsabilita'
KW = {
    "direttore": r"concertatore e direttore(?: d'orchestra)?|maestro concertatore e direttore|maestro concertatore|maestro direttore|direttore d'orchestra|direttori|direttore|direzione musicale|direzione|dirige|concertatore",
    "regista": r"regia|regista|regie",
    "coreografo": r"coreografia|coreografie|coreografo|coreografi|movimenti coreografici|movimenti mimici|ripresa coreografica|riprese coreografiche",
    "scenografo": r"scene|scenografia|scenografo|bozzetti|apparato scenico",
    "costumista": r"costumi|figurini|costumista",
    "luci": r"luci|light design|disegno luci",
}
KWALL = "|".join(KW.values())
STOPL = r"(?=\s*(?:;|\]|\||/|(?<=[a-zà-ÿ0-9]{2})\.\s|\.$|$|,\s*(?i:" + KWALL + r"|maestro|interpreti)\b|\s+(?:e\s+)?(?i:" + KWALL + r")\b|\s*:\s))"
RX_DICH = re.compile(r"(?i:\b)(?P<kw>(?i:" + KWALL + r")(?:\s*(?:,|e)\s*(?i:" + KWALL + r"))*)\s*(?i:di\s+|:\s*)?(?P<nomi>[A-ZÀ-Ý][^;\]\[|/\n]*?)" + STOPL)
RX_DOPO = re.compile(r"(?P<nomi>(?:[A-ZÀ-Ý][\w'’.-]*\s+){1,3}[A-ZÀ-Ý][\w'’.-]*),\s*(?P<kw>(?i:direttore|maestro concertatore|concertatore))\b")
RX_INTERP = re.compile(r"(?i:\binterpreti(?: principali)?)\s*:?\s+(?P<nomi>[A-ZÀ-Ý][^\]\|;]*)")
RX_SOLISTA = re.compile(r"(?P<nomi>(?:[A-ZÀ-Ý][\w'’.-]*\s+){1,3}[A-ZÀ-Ý][\w'’.-]*)\s*,?\s*(?i:soprano|mezzosoprano|contralto|controtenore|tenore|baritono|basso|pianista|pianoforte|violinista|violino|violoncellista|violoncello|violista|flautista|clarinettista|organista|chitarrista|arpista|oboista|cornista|trombettista|percussionista|voce recitante|recitante)\b")
EXTRA = [  # (ruolo, regex del prefisso) - evidenze per nomi senza etichetta
    ("compositore", r"(?:libretto e musica|parole e musica|poema e musica|musiche|musica)\s+(?:di|:)"),
    ("librettista", r"(?:libretto e musica|parole e musica|poema e musica|su libretto|libretto|parole|testo|versi|dramma|poesia|dal romanzo|da)\s+(?:di|:)"),
    ("saggista", r"(?:note illustrative|note critiche|note|saggi|saggio|scritti|contributi|a cura|critica|presentazione|introduzione|prefazione|con scritti|con saggi|testi)\s+(?:di|:)"),
]
RX_EXTRA = [(r, re.compile(r"(?i:" + p + r")\s*(?P<nomi>[A-ZÀ-Ý][^;\]\[|/\n]*?)(?=\s*(?:;|\]|\||/|(?<=[a-zà-ÿ0-9]{2})\.\s|\.$|$|:\s))")) for r, p in EXTRA]

def ruoli_in(kwtext):
    k = kwtext.lower(); out = []
    for ruolo, pat in KW.items():
        if re.search(r"\b(?:" + pat + r")\b", k): out.append(ruolo)
    if "concertatore e direttore" in k and "direttore" not in out: out.append("direttore")
    return out

def dichiarazioni(text):
    """-> lista (ruolo, stringa_con_nomi) da una frase libera."""
    out = []
    t = re.sub(r"\s+", " ", text or "")
    for m in RX_DICH.finditer(t):
        for r in ruoli_in(m.group("kw")):
            out.append((r, m.group("nomi")))
    for m in RX_DOPO.finditer(t):
        out.append(("direttore", m.group("nomi")))
    for m in RX_INTERP.finditer(t):
        out.append(("interprete", m.group("nomi")))
    for m in RX_SOLISTA.finditer(t):
        out.append(("interprete", m.group("nomi")))
    for r, rx in RX_EXTRA:
        for m in rx.finditer(t):
            out.append((r, m.group("nomi")))
    return out

PARTICELLE = {"di", "de", "da", "del", "della", "dal", "van", "von", "der", "den", "la", "le", "el", "al", "del", "dos", "do", "ter", "ten", "mac", "d", "du", "des", "y"}
NON_NOME = re.compile(r"\b(scene|costumi|regia|luci|orchestra|coro|teatro|direttore|direzione|maestro|corpo|balletto|opera|atto|atti|quadri|prologo|edizioni|interpreti|con|per|alla|dal|dalla|della|nel|nella|ensemble|quartetto|trio|duo|solisti|accademia|filarmonica|bozzetti|figurini)\b", re.I)

def spezza_nomi(raw):
    """Stringa libera -> lista di nomi di persona plausibili (almeno nome e cognome, maiuscole)."""
    raw = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", raw or "")
    raw = re.sub(r"\.\s*$", "", raw.strip())
    parts = re.split(r"\s*(?:,|;|\be\b|\bed\b|\bcon\b|&|\s-\s|\s\+\s)\s*", raw)
    out = []
    for p in parts:
        p = p.strip(" .:")
        if not p: continue
        toks = p.split()
        if not (2 <= len(toks) <= 5): continue
        if NON_NOME.search(p): continue
        if not all(t[0].isupper() or t.lower().strip(".'’") in PARTICELLE or t[0] in "'’" for t in toks if t): continue
        if re.search(r"\d", p): continue
        out.append(re.sub(r"\s+", " ", p))
    return out

def pulisci_originale(val):
    """Ripulisce un valore ricavato dal titolo dalla vecchia regex: toglie 'coreografia di', 'd'orchestra:', tagli su 'musica'/'da'/':'."""
    v = re.sub(r"^(?:e libretto di|coreografia di|impianto scenico di|musicale e d'orchestra:|d'orchestra:|d'orchestra)\s*", "", val.strip(), flags=re.I)
    v = re.split(r"\s+(?:musica|musiche|da|ripresa|con la collaborazione|supervisione)\b|\s+[:.]\s+|\s*\(", v)[0]
    nomi = spezza_nomi(v)
    return "; ".join(nomi) if nomi else ""

def parola_in(chiave, s):
    return bool(chiave) and re.search(r"(?<![a-z0-9])" + re.escape(chiave) + r"(?![a-z0-9])", norm(s)) is not None

# ---------------------------------------------------------------- date
RX_DATA = re.compile(r"(?<!\d)(?P<giorni>(?:\d{1,2}\s*(?:°|º)?\.?\s*(?:,|\be\b|-|–|/|\bal\b)\s*)*\d{1,2})\s*(?:°|º)?\.?\s+(?P<mese>" + MESI_RE + r")(?:\s+(?P<anno>(?:19[5-9]\d|20[0-2]\d)))?(?!\d)", re.I)
RX_ALTRO_LUOGO = re.compile(r"\b(?:Teatro|Teatri|Auditorium|Opera|Opéra|Festival|Palazzo|Chiesa|Basilica|Duomo|Conservatorio|Sala)\s+(?!alla\s+Scala\b|degli\s+Arcimboldi|Strehler|Piccolo\b|Verdi\b|Grande\b)[A-ZÀ-Ý]\w+|\b(?:Cremona|Carcano|Montpellier|Pesaro|Salisburgo|Parigi|Londra|Vienna|Berlino|Mosca|Tokyo|New York)\b")

def date_in_testo(text):
    """-> lista di dict(iso, giorni[], tipo 'prima'|'data', scala True/False). Solo date con giorno E anno."""
    t = re.sub(r"\s+", " ", text or "")
    ms = list(RX_DATA.finditer(t))
    res = []
    for i, m in enumerate(ms):
        if not m.group("anno"):
            # "dicembre 1997" senza giorno non e' qui; ma "7 dicembre" senza anno: ignora (puo' essere ereditato dalla data dopo)
            nxt = next((x for x in ms[i + 1:] if x.group("anno")), None)
            continue
        giorni = [int(x) for x in re.findall(r"\d{1,2}", m.group("giorni"))]
        if not giorni or any(g < 1 or g > 31 for g in giorni): continue
        mese = MESI.index(m.group("mese").lower()) + 1
        anno = int(m.group("anno"))
        prima_fine = ms[i - 1].end() if i else 0
        pre = t[prima_fine:m.start()]
        pre = re.split(r"[,;.|]\s*", pre)[-1] if re.search(r"[,;.|]", pre) else pre
        pre_ctx = t[max(prima_fine, m.start() - 70):m.start()]
        dopo_fine = ms[i + 1].start() if i + 1 < len(ms) else len(t)
        dopo = t[m.end():min(dopo_fine, m.end() + 70)]
        dopo = re.split(r"[;.|]\s", dopo)[0]
        altro = bool(RX_ALTRO_LUOGO.search(pre)) or bool(RX_ALTRO_LUOGO.search(dopo.split(",")[0][:60]))
        tipo = "prima" if re.search(r"prima rappresentazione|prima assoluta|1\s*\.?\s*rappr|primo spettacolo|debutto|prima esecuzione", pre_ctx, re.I) else "data"
        for g in giorni[:1]:
            pass
        res.append(dict(iso="%04d-%02d-%02d" % (anno, mese, giorni[0]), tutti=["%04d-%02d-%02d" % (anno, mese, g) for g in giorni], tipo=tipo, scala=not altro))
    return res

def mese_in_testo(text):
    t = re.sub(r"\s+", " ", text or "")
    m = re.search(r"(?<![\w])(" + MESI_RE + r")(?:\s+(19[5-9]\d|20[0-2]\d))?(?:\s*[-–/]\s*(?:" + MESI_RE + r"))?\s*(19[5-9]\d|20[0-2]\d)(?!\d)", t, re.I)
    if m:
        return "%s-%02d" % (m.group(3), MESI.index(m.group(1).lower()) + 1)
    return ""

def stagione_da_data(iso):
    if not iso: return ""
    y, mo = int(iso[:4]), int(iso[5:7]); a = y if mo >= 9 else y - 1
    return f"{a}-{str(a+1)[2:]}"

# ---------------------------------------------------------------- principale
CAMPI_RUOLO = {"direttore": "direttore", "regista": "regista", "coreografo": "coreografo", "interprete": "interpreti",
               "scenografo": "scenografo", "costumista": "costumista", "librettista": "librettista"}

def carica_full():
    full = {}
    for f in glob.glob(os.path.join(FULL, "*.json")):
        try:
            d = json.load(open(f, encoding="utf8"))
        except Exception:
            continue
        if isinstance(d, dict) and d.get("codiceIdentificativo"): full[d["codiceIdentificativo"]] = d
    return full

def main():
    path = os.path.join(SBN, "sbn_programmi.csv")
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    campi_orig = list(rows[0].keys())
    full = carica_full()
    nuove = ["scenografo", "costumista", "librettista", "fonte_ruoli", "data_prima", "data_tipo", "date_scala", "mese_rappr", "data_fonte"]
    for c in nuove:
        if c not in campi_orig: campi_orig.append(c)

    def cop(rs, tipi):
        sel = [r for r in rs if r["tipo"] in tipi]
        return {k: (sum(1 for r in sel if r.get(k)), len(sel)) for k in ("direttore", "regista", "coreografo", "interpreti", "data_iso")}
    prima = {t: cop(rows, (t,)) for t in ("produzione", "concerto", "ospiti")}
    prima["produzione+ospiti"] = cop(rows, ("produzione", "ospiti"))

    persone = []; log = []
    for r in rows:
        bids = [r["bid"]] + [b for b in (r.get("bid_altri") or "").split("; ") if b]
        schede = [full[b] for b in bids if b in full]
        # testi: titolo originale della riga + titolo e note di ogni scheda del gruppo
        testi = [("titolo", r["titolo_originale"])]
        for s in schede:
            if s["titolo"] != r["titolo_originale"]: testi.append(("titolo", s["titolo"]))
            for n in s.get("note", []) or []: testi.append(("note", n))
        if not schede and r.get("nota_scheda"):
            for n in r["nota_scheda"].split(" | "): testi.append(("note", n))
        dich = []                                   # (ruolo, stringa, campo)
        for campo, txt in testi:
            for ruolo, s_ in dichiarazioni(txt): dich.append((ruolo, s_, campo))
        trovati = collections.OrderedDict()         # (ruolo, chiave, ini) -> dict
        def aggiungi(nome, chiave, ini, ruolo, dett, fonte, bid, tag=""):
            k = (ruolo, chiave, ini)
            solo_testo = fonte in ("titolo", "note")
            if k in trovati or any(kk[0] == ruolo and kk[1] == chiave and (solo_testo or not kk[2] or not ini or kk[2] == ini) for kk in trovati):
                return
            trovati[k] = dict(bid_riga=r["bid"], bid_scheda=bid, nome=nome, ruolo=ruolo, dettaglio=dett, fonte=fonte, etichetta=tag,
                              tipo_nome="ente" if ENTE.search(nome) else "persona")
        # 1) nomi con etichetta
        senza = []
        for s in schede:
            for raw in s.get("nomi", []) or []:
                nome, chiave, ini = nome_pulito(raw)
                if not nome: continue
                ruolo, dett, tag = ruolo_da_tag(raw)
                if ruolo and ruolo not in ("autore (non specificato)", "altro", "curatore", "ruolo_non_dichiarato", "saggista"):
                    aggiungi(nome, chiave, ini, ruolo, dett, "nomi", s["codiceIdentificativo"], tag)
                else:
                    senza.append((nome, chiave, ini, ruolo, dett, tag, s["codiceIdentificativo"]))
        # 2) nomi senza etichetta (o con etichetta generica): ruolo dalla dichiarazione di responsabilita'
        for nome, chiave, ini, ruolo0, dett0, tag, bid in senza:
            if ENTE.search(nome):
                aggiungi(nome, chiave, ini, ruolo0 or "ente (senza ruolo)", dett0, "nomi", bid, tag); continue
            ruoli_ev = []
            for ruolo, s_, campo in dich:
                if parola_in(chiave, s_) and ruolo not in ruoli_ev:
                    ruoli_ev.append(ruolo)
            if ruoli_ev:
                for ruolo in ruoli_ev:
                    aggiungi(nome, chiave, ini, ruolo, "", "nomi+titolo", bid, tag)
            else:
                aggiungi(nome, chiave, ini, ruolo0 or "nome senza ruolo", dett0, "nomi", bid, tag)
        # 3) nomi che stanno solo nel testo (titolo / note)
        bid0 = r["bid"]
        for ruolo, s_, campo in dich:
            if ruolo not in ("direttore", "regista", "coreografo", "scenografo", "costumista", "interprete"): continue
            for nome in spezza_nomi(s_):
                ch, ini = chiave_libera(nome)
                aggiungi(nome, ch, ini, ruolo, "", campo, bid0)
        lst = list(trovati.values())
        persone.extend(lst)
        # campi del programma
        fonti_usate = collections.OrderedDict()
        for ruolo, col in CAMPI_RUOLO.items():
            nuovi = [p for p in lst if p["ruolo"] == ruolo and p["tipo_nome"] == "persona"]
            if r["tipo"] == "stagione" and ruolo in ("direttore", "regista", "coreografo", "interprete"): continue
            if not nuovi: continue
            strutt = [p for p in nuovi if p["fonte"] in ("nomi", "nomi+titolo")]
            if strutt:
                # strutturati prima, poi nomi solo-testo che non ripetono lo stesso cognome
                valori = [p["nome"] for p in strutt]
                extra = [p["nome"] for p in nuovi if p["fonte"] not in ("nomi", "nomi+titolo")]
                valori += extra
                fonte = "nomi" + ("+testo" if extra else "")
            elif not r.get(col):
                valori = [p["nome"] for p in nuovi]; fonte = nuovi[0]["fonte"]
            else:
                continue
            nuovo_val = "; ".join(dict.fromkeys(valori))
            if nuovo_val != r.get(col, ""):
                log.append(dict(bid=r["bid"], anno=r["anno"], titolo=r["titolo"], campo=col, prima=r.get(col, ""), dopo=nuovo_val, fonte=fonte))
                r[col] = nuovo_val
            fonti_usate[fonte] = 1
        for col in ("direttore", "regista", "coreografo", "interpreti"):
            v0 = r.get(col, "")
            if v0 and col not in [CAMPI_RUOLO[k] for k in CAMPI_RUOLO if any(p["ruolo"] == k and p["fonte"] in ("nomi", "nomi+titolo") for p in lst)]:
                pul = pulisci_originale(v0)
                if pul != v0:
                    log.append(dict(bid=r["bid"], anno=r["anno"], titolo=r["titolo"], campo=col, prima=v0, dopo=pul, fonte="pulizia titolo"))
                    r[col] = pul
        r["fonte_ruoli"] = ",".join(fonti_usate)
        # compositore: solo se mancava
        if not r.get("compositore"):
            c = [p["nome"] for p in lst if p["ruolo"] == "compositore" and p["tipo_nome"] == "persona"]
            if c:
                r["compositore"] = "; ".join(dict.fromkeys(c))
                log.append(dict(bid=r["bid"], anno=r["anno"], titolo=r["titolo"], campo="compositore", prima="", dopo=r["compositore"], fonte="nomi"))
        # date
        dt = []
        for campo, txt in testi:
            if r["tipo"] == "stagione" and campo == "titolo": continue
            for d in date_in_testo(txt):
                d["campo"] = campo; dt.append(d)
        dt_scala = [d for d in dt if d["scala"]]
        tutte = []
        for d in dt_scala:
            for x in d["tutti"]:
                if x not in tutte: tutte.append(x)
        r["date_scala"] = ";".join(tutte)
        prime = [d for d in dt_scala if d["tipo"] == "prima"]
        scelta = prime[0] if prime else (dt_scala[0] if dt_scala else None)
        r["data_prima"] = prime[0]["iso"] if prime else ""
        if scelta:
            r["data_tipo"] = scelta["tipo"]; r["data_fonte"] = scelta["campo"]
            if r.get("data_iso") != scelta["iso"]:
                log.append(dict(bid=r["bid"], anno=r["anno"], titolo=r["titolo"], campo="data_iso", prima=r.get("data_iso", ""), dopo=scelta["iso"], fonte="data (" + scelta["campo"] + ", " + scelta["tipo"] + ")"))
                r["data_iso"] = scelta["iso"]
                if r.get("stagione_da") in ("da data", ""):
                    st = stagione_da_data(scelta["iso"])
                    if st != r.get("stagione", ""):
                        log.append(dict(bid=r["bid"], anno=r["anno"], titolo=r["titolo"], campo="stagione", prima=r.get("stagione", ""), dopo=st, fonte="da data_iso"))
                        r["stagione"] = st; r["stagione_da"] = "da data"
        else:
            r["data_tipo"] = ""; r["data_fonte"] = ""
            if not r.get("data_iso"):
                for campo, txt in testi:
                    if r["tipo"] == "stagione" and campo == "titolo": continue
                    m = mese_in_testo(txt) if campo == "note" else ""
                    if m: r["mese_rappr"] = m; break
        r.setdefault("mese_rappr", "")
        for c in nuove: r.setdefault(c, "")
        for col in ("scenografo", "costumista", "librettista"):
            pass
    dopo = {t: cop(rows, (t,)) for t in ("produzione", "concerto", "ospiti")}
    dopo["produzione+ospiti"] = cop(rows, ("produzione", "ospiti"))
    # uscite
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=campi_orig, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    with open(os.path.join(SBN, "sbn_persone.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["bid_riga", "bid_scheda", "nome", "ruolo", "dettaglio", "fonte", "etichetta", "tipo_nome"]); w.writeheader(); w.writerows(persone)
    with open(os.path.join(SBN, "sbn_nomi_log.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["bid", "anno", "titolo", "campo", "prima", "dopo", "fonte"]); w.writeheader(); w.writerows(log)
    with open(os.path.join(SBN, "sbn_nomi_copertura.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh); w.writerow(["gruppo", "campo", "righe_prima", "righe_dopo", "totale", "pct_prima", "pct_dopo"])
        for g in prima:
            for k in prima[g]:
                a, n = prima[g][k]; b, _ = dopo[g][k]
                w.writerow([g, k, a, b, n, round(100 * a / n, 1) if n else "", round(100 * b / n, 1) if n else ""])
    print("righe", len(rows), "persone", len(persone), "cambi", len(log))
    for g in prima:
        print(g, {k: f"{prima[g][k][0]}->{dopo[g][k][0]}/{prima[g][k][1]}" for k in prima[g]})
    print(collections.Counter(p["fonte"] for p in persone))
    print(collections.Counter(p["ruolo"] for p in persone).most_common(25))
    print(collections.Counter(l["campo"] for l in log))

if __name__ == "__main__":
    main()
