"""Programmi di sala 2002-2011 aperti su Internet Archive (raw/ia_programmi/<id>/testo.txt, scaricati da ia_programmi_scarica.py) ->
  pulito/ia_programmi_2002_2011.csv            una riga per programma (titolo, compositore, date, direttore, regia, interpreti per ruolo dove il testo li da')
  pulito/ia_programmi_storico_alla_scala.csv   le "alla Scala dal ... al ..." dei programmi grandi (Carmen, Don Giovanni, Elisir, Rosenkavalier):
                                               una riga per produzione storica con data, n. recite, direttore, regia, scene, costumi (il cast e' solo in 'interpreti_grezzo', in ordine sparso: colonne OCR mescolate)
Uso (dalla cartella scala/): python -I -X utf8 scripts/ia_programmi_estrai.py"""
import sys, os, re, csv, json, glob, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "raw", "ia_programmi")
OUT1 = os.path.join(ROOT, "pulito", "ia_programmi_2002_2011.csv")
OUT2 = os.path.join(ROOT, "pulito", "ia_programmi_storico_alla_scala.csv")
MES = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
MESI_RX = "|".join(MES)
GIORNI = r"(?:Luned[iì]|Marted[iì]|Mercoled[iì]|Gioved[iì]|Venerd[iì]|Sabato|Domenica)"
def mese_n(s): return MES.index(s.lower()) + 1
def iso(g, m, a): return "%04d-%02d-%02d" % (int(a), mese_n(m), int(g))
def pul(s): return re.sub(r"\s+", " ", s or "").strip(" ,;.-")

# ------------------------------------------------------------------ dati fissi per programma (titolo/compositore dal titolo IA; a mano solo dove il titolo non basta)
def meta(d):
    return json.load(open(os.path.join(RAW, d, "metadata.json"), encoding="utf-8"))["metadata"]

def sommario_persone(t):
    """Persone nel sommario ('PAGINA 31 / Antonio Pappano'): biografie di direttore, solisti, regista..."""
    s = re.search(r"SOMMARIO(.{0,2500})", t, re.S)
    if not s: return []
    out = []
    for m in re.finditer(r"PAGINA\s+\d+\s*\n\s*([^\n]+)\n([^\n]*\n[^\n]*)", s.group(1)):
        n = pul(m.group(1))
        if re.search(r"(?i)cronolog", m.group(2)): continue            # compositore: segue "Cronologia della vita e delle opere"
        if re.search(r"(?i)cronolog|teatro|orchestra|coro|filarmonica|discografia|letture|soggetto|di [A-Z]|a cura|^[\W\d]", n): continue
        n = n.rstrip(".")
        if not re.fullmatch(r"[A-Z][\wà-ÿ'’-]+(?: [A-Z][\wà-ÿ'’-]+){1,3}", n): continue
        out.append(n)
    return out

def cast_gala(t):
    """Programma gala: 'Placido Domingo / Siegmund' (nome poi ruolo) + 'Direttore / Daniel Barenboim'."""
    s = re.search(r"\nPROGRAMMA\s*\n(.{0,900})", t, re.S)
    if not s: return "", ""
    L = [pul(x) for x in s.group(1).split("\n") if pul(x)]
    cast, dirett = [], ""
    for i, l in enumerate(L):
        if l.lower() == "direttore" and i + 1 < len(L): dirett = L[i + 1]
    # coppie nome / ruolo: due righe consecutive, la seconda e' un ruolo (parola singola o 'Don ...') e la prima e' un nome di 2+ parole
    for i in range(len(L) - 1):
        if len(L[i].split()) >= 2 and re.fullmatch(r"[A-Z][a-z]+( [A-Z][a-z]+)?", L[i + 1]) and not re.search(r"Wagner|Tristan|Walk|atto|Orchestra|Direttore|Daniel", L[i] + L[i + 1]) and re.match(r"[A-Z]\w+ [A-Z]", L[i]):
            cast.append("%s: %s" % (L[i + 1], L[i]))
    return dirett, "; ".join(cast)

def date_complete(t):
    """Date esplicite 'Martedì 10 novembre 2009, ore 20' nella parte iniziale."""
    head = t[:9000]
    ds = []
    for m in re.finditer(r"(?i)" + GIORNI + r"\s*,?\s*(\d{1,2})\s*°?\s+(" + MESI_RX + r")\s+(\d{4})", head):
        d = iso(m.group(1), m.group(2), m.group(3))
        if d not in ds and int(m.group(3)) >= 2000: ds.append(d)
    return ds

def prima_e_repliche(t):
    """'PRIMA RAPPRESENTAZIONE / Martedi 15 febbraio 2011' + repliche ('Febbraio' poi 'Giovedi 17, ore 20'): -> (prima, [date repliche], repliche_complete)"""
    m = re.search(r"(?i)prima\s+rappresentazione\s*(?:dell.opera)?[^\n]*\n(?:[^\n]*\n){0,5}?\s*" + GIORNI + r"\s*,?\s*(\d{1,2})\s+(" + MESI_RX + r")\s+(\d{4})", t)
    if not m: return "", [], False
    prima = iso(m.group(1), m.group(2), m.group(3))
    y, m0 = int(m.group(3)), mese_n(m.group(2))
    r = re.search(r"(?i)repliche?", t[max(0, m.start() - 600):m.end() + 600])
    base = (max(0, m.start() - 600) + r.end()) if r else m.end()
    win = t[base:base + 1400]
    cut = re.search(r"(?i)in copertina|testi tratti|opera in |melodramma|dramma |libretto|musica di|dispensa", win)
    if cut: win = win[:cut.start()]
    reps, complete, mese, prev, yy = [], True, MES[m0 - 1], m0, y      # senza intestazione di mese valgono le repliche dello stesso mese della prima
    for tok in re.finditer(r"(?i)(?:(?<![A-Za-z])(" + MESI_RX + r")(?![A-Za-z]))|(" + GIORNI + r")(?:[^A-Za-z0-9\n]{0,4}(\d{1,2})(?!\d))?", win):
        if tok.group(1):
            mese = tok.group(1).lower(); continue
        if tok.group(3) and mese:
            mn = mese_n(mese)
            if mn < prev: yy += 1
            prev = mn
            reps.append(iso(tok.group(3), mese, yy))
        elif not tok.group(3):
            complete = False
    return prima, reps, bool(reps)


# ------------------------------------------------------------------ programmi (una riga per elemento IA)
rows = []
for d in sorted(os.listdir(RAW)):
    if not d.startswith("teatro-alla-scala-"): continue
    tp = os.path.join(RAW, d, "testo.txt")
    if not os.path.exists(tp): continue
    t = open(tp, encoding="utf-8").read()
    md = meta(d)
    titolo_ia = pul(md.get("title", ""))
    url = "https://archive.org/details/" + d
    r = dict(identificativo=d, tipo="", titolo="", compositore="", stagione="", data_prima="", date_tutte="", n_date=0, direttore="", regia="", scene="", costumi="", interpreti="",
             interpreti_ruoli="no", programma="", fonte_direttore="", url=url, titolo_ia=titolo_ia, nota="")
    # stagione dal titolo
    ms = re.search(r"(20\d\d)\s*[-/]\s*(20\d\d|\d\d)", titolo_ia)
    if ms: r["stagione"] = "%s-%s" % (ms.group(1), ms.group(2)[-2:])
    if re.search(r"(?i)filarmonica|orchestra e coro|gala", titolo_ia):
        r["tipo"] = "concerto"
        r["titolo"] = re.sub(r"(?i)^teatro alla scala\s*-\s*", "", titolo_ia)
        r["titolo"] = re.sub(r"\s*-\s*(Stagione|Concerti)[^-]*$", "", r["titolo"]) if False else r["titolo"]
        mdir = re.search(r"-\s*([A-Z][\wà-ÿ.' ]+?)\s+Direttore\b", titolo_ia)
        if mdir: r["direttore"] = pul(mdir.group(1)); r["fonte_direttore"] = "titolo del programma"
        ds = date_complete(t)
        if not ds:                      # date nel titolo: "16, 18 e 19 ottobre 2011"
            mt_ = re.search(r"((?:\d{1,2}, )*\d{1,2}(?:,? e \d{1,2})?)\s+(" + MESI_RX + r")\s+(\d{4})", titolo_ia)
            if mt_: ds = [iso(g, mt_.group(2), mt_.group(3)) for g in re.findall(r"\d{1,2}", mt_.group(1))]
        r["date_tutte"] = ";".join(ds); r["n_date"] = len(ds); r["data_prima"] = ds[0] if ds else ""
        pers = sommario_persone(t)
        if r["direttore"]:               # grafia del sommario se quasi uguale (il titolo IA ha refusi: "Barendoim")
            import difflib
            for p_ in pers:
                if difflib.SequenceMatcher(None, p_.lower(), r["direttore"].lower()).ratio() > 0.85: r["direttore"] = p_; break
        if "gala" in titolo_ia.lower():
            dd, cc = cast_gala(t)
            if dd: r["direttore"] = dd; r["fonte_direttore"] = "pagina Programma"
            r["interpreti"] = cc; r["interpreti_ruoli"] = "si" if cc else "no"
            r["titolo"] = "Gala Placido Domingo (40 anni dal debutto alla Scala)"
        else:
            sol = [p for p in pers if not (r["direttore"] and p.split()[-1] == r["direttore"].split()[-1])]
            if sol: r["interpreti"] = "; ".join(sol[:4]); r["nota"] = "interpreti = biografie nel sommario (solisti), senza ruolo"
        # programma: righe dopo PROGRAMMA fino al primo capoverso lungo
        sp = re.search(r"\nPROGRAMMA\s*\n(.{0,700})", t, re.S)
        if sp: r["programma"] = pul(" | ".join(x.strip() for x in sp.group(1).split("\n") if x.strip())[:260])
        r["compositore"] = ""
        if "Pappano" in titolo_ia: r["compositore"] = "Glinka; Sostakovic; Rachmaninov"
        elif "Robertson" in titolo_ia: r["compositore"] = "Fedele; Stravinskij"
        elif "Jordan" in titolo_ia: r["compositore"] = "Brahms; Bartok"
        elif "arendoim" in titolo_ia: r["compositore"] = "Verdi"; r["titolo"] = "Messa da Requiem (Orchestra e Coro del Teatro alla Scala)"
        if r["compositore"] and "Requiem" not in r["titolo"]: r["titolo"] = "Filarmonica della Scala: " + r["compositore"].replace(";", ",")
    else:
        r["tipo"] = "opera"
        mt = re.search(r"(?i)(?:stagione\s+\d{4}\s*[/-]\s*\d{2,4}\s+|teatro alla scala\s*-\s*)?(.+?)\s+di\s+([A-Z][\wà-ÿ. ]+?)(?:\s*-?\s*(?:stagione|staginoe|$)|\s*$)", re.sub(r"(?i)^teatro alla scala\s*(?:-\s*)?(?:stagione\s+\d{4}\s*[/-]\s*\d{2,4}\s*)?", "", titolo_ia))
        r["titolo"] = pul(mt.group(1)) if mt else titolo_ia
        r["compositore"] = pul(mt.group(2)) if mt else ""
        r["titolo"] = re.sub(r"(?i)^teatro alla scala\s*-?\s*", "", r["titolo"])
        prima, reps, complete = prima_e_repliche(t)
        r["data_prima"] = prima
        alld = [prima] + reps if prima else []
        r["date_tutte"] = ";".join(alld) if reps else prima
        r["n_date"] = len(alld) if reps else (1 if prima else 0)
        if not prima:
            ds = date_complete(t)
            if ds: r["data_prima"] = ds[0]; r["date_tutte"] = ";".join(ds); r["n_date"] = len(ds)
        if prima and not reps: r["nota"] = "repliche non lette (OCR a colonne): solo la prima"
        # direttore/regia dal sommario (biografie nell'ordine direttore, regista, scene, costumi) o dalla didascalia di copertina
        pers = sommario_persone(t)
        cop = re.search(r"(?s)In copertina:\s*(.{0,400}?)(?:\n\s*\n\s*\n|SOMMARIO)", t)
        capt = pul(cop.group(1)) if cop else ""
        mreg = re.search(r"[Rr]egia(?:, scene)?(?: e costumi)? di ([A-Z][\wà-ÿ. ]+?)(?:,| scene| e |\.|;)", capt)
        mdr = re.search(r"Direttore ([A-Z][\wà-ÿ. ]+?)(?:,| regia|\.)", capt)
        if mdr: r["direttore"] = pul(mdr.group(1)); r["fonte_direttore"] = "didascalia di copertina (puo' essere un allestimento precedente)"
        msc = re.search(r"[Ss]cene(?: e costumi)? di ([A-Z][\wà-ÿ. ]+?)(?: e luci| e costumi|,|\.|;)", capt)
        mco = re.search(r"(?:[Rr]egia, scene e costumi|[Rr]egia e costumi|[Cc]ostumi) di ([A-Z][\wà-ÿ. ]+?)(?:,|\.|;| scene| e scene)", capt)
        if msc: r["scene"] = pul(msc.group(1))
        if mco: r["costumi"] = pul(mco.group(1))
        # biografie nel sommario dopo la riga "... alla Scala dal ..."
        sm = re.search(r"SOMMARIO(.{0,3500})", t, re.S)
        if sm:
            blk = sm.group(1)
            ia = re.search(r"alla Scala dal \d{4} al \d{4}[^\n]*\n(.*?)(?:\n[^\n]*Cronologia|\n\s*\d+\.?\s*[A-Z][a-z]+ [A-Z][a-z]+\.\s*\n)", blk, re.S)
            names = []
            if ia:
                for line in ia.group(1).split("\n"):
                    ln = pul(re.sub(r"^[\s{}\d.]+", "", line))
                    if re.fullmatch(r"[A-Z][\wà-ÿ'-]+(?: [A-Z][\wà-ÿ'-]+){1,3}", ln) and ln not in names: names.append(ln)
            if names:
                r["direttore"] = names[0]; r["fonte_direttore"] = "sommario: biografie in ordine direttore, regia, scene, costumi (nuova produzione)"
                if len(names) > 1: r["regia"] = names[1]
                if not r["scene"] and len(names) > 3 and "don-giovanni" in r["identificativo"]: r["costumi"] = names[2]; r["scene"] = names[3]
        if mreg and not r["regia"]: r["regia"] = pul(mreg.group(1))
    rows.append(r)

COLS1 = ["identificativo", "tipo", "titolo", "compositore", "stagione", "data_prima", "date_tutte", "n_date", "direttore", "regia", "scene", "costumi", "interpreti", "interpreti_ruoli", "programma", "fonte_direttore", "nota", "titolo_ia", "url"]
with open(OUT1, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, COLS1); w.writeheader(); w.writerows(rows)
print("programmi:", len(rows))

# ------------------------------------------------------------------ produzioni storiche "alla Scala dal ... al ..."
LAB = [("direttore", r"(?:Maestro )?(?:Concertatore e )?Direttore(?: d.Orchestra)?(?: e Concertatore)?|Direzione musicale"),
       ("regia", r"Regia|Regista"),
       ("scene", r"Scene|Scenografi?a?|Bozzetti|Direttore ed Inventore delle Scene"),
       ("costumi", r"Costumi|Figurini|Vestiario"),
       ("coro", r"Maestro del Coro|Maestro Direttore dei Cori|Maestro dei Cori"),
       ("coreografia", r"Coreografia|Movimenti Coreografici"),
       ("luci", r"Luci")]
STOP = r"(?i)^(?:orchestra|interpreti|ispettore|sartoria|compagnia|maestro suggeritore|regia ripresa|ripresa|\(|\d{3}\b)"
LABW = r"(?:regia|regista|di|e|ed|scene|scenografia|scenografi|bozzetti|figurini|costumi|vestiario|direttore|direzione|musicale|d.orchestra|maestro|concertatore|del|dei|coro|cori|coreografia|danze|delle|movimenti|coreografici|luci|ripresa|da|allestimento|collaborazione|ai|ideazione|assistente)"
def label_fields(l):
    """Se la riga e' un'etichetta ('Scene e Costumi', 'Regia, Bozzetti e Figurini', 'Maestro del Coro') -> lista dei campi che introduce; altrimenti None."""
    s = re.sub(r"[,.]", " ", l.lower()).strip()
    words = s.split()
    if not words or not all(re.fullmatch(LABW, w) for w in words): return None
    if re.search(r"allestimento|collaborazione|ripresa|assistente|ideazione", s): return []
    f = []
    if re.search(r"coro|cori", s): f.append("coro")
    elif re.search(r"direttore|direzione|concertatore", s): f.append("direttore")
    if re.search(r"coreograf|danze", s): f.append("coreografia")
    if re.search(r"regia|regista", s): f.append("regia")
    if re.search(r"scene|scenograf|bozzetti", s): f.append("scene")
    if re.search(r"costumi|figurini|vestiario", s): f.append("costumi")
    if re.fullmatch(r"luci", s): f.append("luci")
    return f
HDR = re.compile(r"(?m)^\s*(\d{1,2}|1[°º]|Il)\s+(" + MESI_RX + r")\s+(\d{4})\s*\n+\s*(\d+)\s+(?:rappresentazion|recit)[^\n]*\n(?:\s*\n)*\s*(?:\(\s*(?:repliche|replica)?[^)]*\)?)?")
hist = []
for d in sorted(os.listdir(RAW)):
    tp = os.path.join(RAW, d, "testo.txt")
    if not os.path.exists(tp): continue
    t = open(tp, encoding="utf-8").read()
    ms = list(HDR.finditer(t))
    if len(ms) < 3: continue
    rowp = next(x for x in rows if x["identificativo"] == d)
    opera = rowp["titolo"]; comp = rowp["compositore"]
    for k, m in enumerate(ms):
        end = ms[k + 1].start() if k + 1 < len(ms) else m.end() + 3000
        blk = t[m.end():min(end, m.end() + 3200)]
        head = t[m.start():m.end()]
        giorno = m.group(1)
        if giorno in ("Il",) or giorno.endswith(("°", "º")):
            giorno = "1" if giorno != "Il" else ""          # "Il" = OCR di 11: giorno incerto
        data = iso(giorno, m.group(2), m.group(3)) if giorno else "%s-%02d" % (m.group(3), mese_n(m.group(2)))
        h = dict(opera=opera, compositore=comp, data=data, anno=int(m.group(3)), n_rappresentazioni=int(m.group(4)), repliche=pul(re.search(r"\(.*", head, re.S).group(0)) if "(" in head else "",
                 direttore="", regia="", scene="", costumi="", coro="", coreografia="", luci="", interpreti_grezzo="", programma_fonte=d, url="https://archive.org/details/" + d)
        # etichette (Direttore, Regia, Scene...): di solito PRIMA di INTERPRETI; se mancano, il primo blocco DOPO INTERPRETI (impaginazione a colonne)
        ii = re.search(r"INTERPRETI", blk)
        def leggi_etichette(righe, ferma_al_secondo_direttore):
            cur, visto_dir = [], False
            for l in righe:
                fl = label_fields(l)
                if fl is not None:
                    if ferma_al_secondo_direttore and "direttore" in fl:
                        if visto_dir: break
                        visto_dir = True
                    cur = fl; continue
                if re.match(STOP, l): cur = []; continue
                if cur and re.search(r"[A-Za-z]{3}", l) and len(l) < 60 and not re.search(r"\d", l):
                    for key in cur:
                        if l not in h[key].split("; "): h[key] = (h[key] + "; " + l) if h[key] else l
        pre = blk[:ii.start()] if ii else blk[:700]
        leggi_etichette([pul(x) for x in pre.split("\n") if pul(x)], False)
        if not h["direttore"] and ii:
            leggi_etichette([pul(x) for x in blk[ii.end():].split("\n") if pul(x)], True)
        if ii:
            post = blk[ii.end():ii.end() + 1800]
            post = re.split(r"(?i)\n\s*(?:foto|in alto|a sinistra|a destra|da sinistra|in basso)\b|\n\s*\d{3}\s*\|?\s*\n|\n\s*!|\n\s*\*\s", post)[0]
            names = [pul(x) for x in post.split("\n") if pul(x)]
            h["interpreti_grezzo"] = " | ".join(names)[:700]
        # la riga non e' un'edizione con data utile se manca ogni dato
        hist.append(h)
COLS2 = ["opera", "compositore", "data", "anno", "n_rappresentazioni", "repliche", "direttore", "regia", "scene", "costumi", "coro", "coreografia", "luci", "interpreti_grezzo", "programma_fonte", "url"]
with open(OUT2, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, COLS2); w.writeheader(); w.writerows(hist)
print("produzioni storiche:", len(hist), "dal", min(h["anno"] for h in hist), "al", max(h["anno"] for h in hist), "dopo il 1945:", sum(1 for h in hist if h["anno"] >= 1946), "con direttore:", sum(1 for h in hist if h["direttore"]), "con regia:", sum(1 for h in hist if h["regia"]))
