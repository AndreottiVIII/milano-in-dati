"""Dati compatti per la pagina docs/scala/ (La Scala, 1778-2027).
Uso (dalla cartella scala/):   python -I -X utf8 scripts/pagina_dati.py
Legge:  pulito/cartellone.csv, sbn/sbn_programmi.csv (se c'e'), raw/wikidata/premiere_p4647.json, pulito/_wp_aperture.csv
Scrive: ../docs/scala/data/{copertura,titoli,classifiche,prime,sette_dicembre,fonti}.json

Regole di licenza (vedi NOTE.md):
 - ripubblicabile=no (Gatti vol. I): si pubblicano SOLO titolo, compositore, stagione/anno e direttore; mai testo, mai pagine,
   mai regista/interpreti/genere.
 - Marangoni-Vanbianchi (ripubblicabile=no, licenza non verificata): SOLO conteggi per anno nel grafico; nessuna riga nelle tabelle.
 - SBN: fatti bibliografici (titolo, compositore, direttore, regista, interpreti, data), citazione "Catalogo SBN - ICCU".
 - Wikipedia: CC BY-SA 4.0 (citata nella pagina 'Fonti'); Wikidata: CC0.
Una riga della pagina = un titolo in un anno, con le fonti che lo confermano (le righe delle fonti si fondono per anno e titolo)."""
import sys, os, csv, json, re, unicodedata, difflib, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                         # .../scala
OUT = os.path.join(os.path.dirname(BASE), "docs", "scala", "data")
os.makedirs(OUT, exist_ok=True)
Y0, Y1 = 1778, 2027

# ------------------------------------------------------------------ fonti
# id nel cartellone -> (codice, priorita' generale, priorita' titolo)
SRC = {
    "scala_sito_pubblico":          ("S", 0),
    "sbn":                          ("B", 1),
    "cambiasi_1881":                ("C", 2),
    "romani_1862":                  ("R", 3),
    "gatti_vol1":                   ("G", 4),
    "marangoni_vanbianchi_1922":    ("M", 5),
    "wikipedia_it_stagioni_liriche": ("W", 6),
    "wikidata_prime":               ("D", 7),
    "ia_programmi":                 ("I", 1),     # programmi di sala 2002-2011 su Internet Archive (+ "alla Scala dal..." storici)
    "sbn_registrazioni":            ("V", 1),     # registrazioni sonore dal vivo alla Scala (Catalogo SBN)
}
CODE = {k: v[0] for k, v in SRC.items()}
PRIO = {v[0]: v[1] for v in SRC.values()}
TITLE_PRIO = "SIBWDRGCVM"          # da quale fonte prendere il titolo (piu' pulito prima)
CAST_PRIO = "SIVBWCRG"
DATE_PRIO = "SIBVDWC"
SEASON_PRIO = "SIBVGMWCR"
WITHHELD_ROWS = {"M"}            # solo conteggi
RESTRICTED_KEEP = ("titolo", "autore", "stagione", "anno", "direttore")   # per ripubblicabile=no


def unaccent(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


ART = {"il", "lo", "la", "le", "gli", "i", "l", "un", "uno", "una", "the", "les", "le", "der", "die", "das", "de", "des"}


def normtitle(t):
    t = unaccent(t.lower())
    t = re.sub(r"\([^)]*\)", " ", t)
    t = re.sub(r"[^a-z0-9 ]+", " ", t.replace("'", " "))
    w = [x for x in t.split() if x]
    while w and w[0] in ART:
        w = w[1:]
    return " ".join(w)


ALIAS = {"paesiello": "paisiello", "stravinski": "stravinskij", "strawinsky": "stravinskij", "stravinsky": "stravinskij", "franchetty": "franchetti",
         "cajkovskij": "cajkovskij", "ciaikovski": "cajkovskij", "cajkovski": "cajkovskij", "tchaikovsky": "cajkovskij", "ciaikovskij": "cajkovskij",
         "musorgskij": "musorgskij", "mussorgsky": "musorgskij", "mussorgski": "musorgskij", "prokofev": "prokofiev", "prokof'ev": "prokofiev", "prokofiev": "prokofiev",
         "sostakovic": "sostakovic", "šostakovič": "sostakovic", "shostakovich": "sostakovic"}
AMBIG = {"strauss", "bach", "scarlatti", "ricci", "gluck", "crescentini", "mozart_"}


def clean_composer(a):
    """Toglie gli artefatti dei campi autore (titolo prima di 'di', sottotitoli, elenchi lunghi)."""
    a = (a or "").replace(" : ", " ").strip().strip(";").strip()
    a = re.sub(r"\s*;\s*(traduzione|revisione|versione|testo).*$", "", a, flags=re.I)
    a = re.sub(r"\s+(Dramma|Melodramma|Opera|Commedia|Tragedia|Azione|Farsa|Balletto).*$", "", a)
    a = re.sub(r"(?<=\w{3})\.\s+[A-Z][a-z]+.*$", "", a)
    if " di " in a:
        tail = a.rsplit(" di ", 1)[1].strip()
        if len(tail.split()) >= 2 and tail[:1].isupper():
            a = tail
    if a.count(",") >= 2 or len(a) > 60 or re.search(r"\d", a) or (a[:1].islower() and not a.startswith(("de ", "van ", "von "))):
        return ""
    return re.sub(r"\s+", " ", a).strip()


def clean_person(a):
    a = (a or "").strip().strip(";,").strip()
    a = re.sub(r"^(e\s+)?(direttore(\s+d'orchestra)?|d'orchestra|concertatore e direttore|regia|regista|scene|e scene|scene e costumi)\s*:\s*", "", a, flags=re.I)
    return a.strip().strip(";,").strip()


def composer_key(a):
    a = clean_composer(a)
    if not a:
        return ""
    first = re.split(r"[;/]", a)[0].strip()
    w = [x for x in re.sub(r"[^\w\s'.-]", " ", unaccent(first.lower())).split() if x]
    if not w:
        return ""
    sur = ALIAS.get(w[-1].strip("."), w[-1].strip("."))
    if sur in AMBIG and len(w) > 1:
        return w[0][0] + " " + sur
    return sur


def ratio_ok(a, b, thr=0.9):
    if len(a) < 6 or len(b) < 6 or abs(len(a) - len(b)) > 3:
        return False
    sm = difflib.SequenceMatcher(None, a, b)
    return sm.real_quick_ratio() >= thr and sm.quick_ratio() >= thr and sm.ratio() >= thr


def same_title(a, b, thr=0.9):
    if a == b:
        return True
    sh, lo = (a, b) if len(a) <= len(b) else (b, a)
    if len(sh) >= 7 and lo.startswith(sh + " "):
        return True
    return ratio_ok(a, b, thr)


def kind_of(genere, tipo=""):
    g = (genere or "").lower()
    if tipo == "concerto" or g.startswith("concerto"):
        return "concerto"
    if tipo == "tournee" or g.startswith("tournee"):
        return "tournee"
    if tipo == "ospiti" or "ospiti" in g:
        return "ospiti"
    if "non distinto" in g:
        return "opera/balletto"
    if "balletto" in g or g.startswith("ballo") or "tersicore" in g or "choreograph" in g:
        return "balletto"
    if "ragazzi" in g:
        return "ragazzi"
    return "opera"


REL = {"alta": 2, "media": 1, "bassa": 0}


def short_season(s):
    s = (s or "").strip()
    return s if len(s) <= 34 else ""


# ------------------------------------------------------------------ lettura
rows = []   # righe unificate
stats = collections.OrderedDict()
for k in SRC:
    stats[k] = dict(righe_fonte=0, righe_usate=0, escluse_note=[])

with open(os.path.join(BASE, "pulito", "cartellone.csv"), encoding="utf-8-sig") as f:
    cart = list(csv.DictReader(f))

p4647 = set()
with open(os.path.join(BASE, "raw", "wikidata", "premiere_p4647.json"), encoding="utf-8") as f:
    for b in json.load(f)["results"]["bindings"]:
        p4647.add(b["work"]["value"].rsplit("/", 1)[-1])

for x in cart:
    src = x["fonte"]
    if src not in SRC or not x["anno"].isdigit():
        continue
    stats[src]["righe_fonte"] += 1
    y = int(x["anno"])
    if not (Y0 <= y <= Y1) or not x["titolo"].strip() or re.match(r"^Q\d+$", x["titolo"].strip()):
        continue                                   # (voci Wikidata senza etichetta in italiano)
    gen = x["genere"]
    prima = 0
    if src == "wikidata_prime":
        q = x["riga_fonte"].rsplit("/", 1)[-1]
        if q in p4647:
            prima = 2
        gen = re.sub(r"\s*\(prima assoluta\)", "", gen)        # nel cartellone ogni riga Wikidata porta l'etichetta, ma solo P4647 e' una prima
        if not prima:
            gen = (gen + " (produzione)").strip()
    elif src == "wikipedia_it_stagioni_liriche":
        if "prima assoluta" in gen:
            prima = 2
        gen = gen.replace(" (prima assoluta)", "")
    elif src == "cambiasi_1881":
        if "scritta per la Scala" in gen:
            prima = 1
        gen = gen.replace(" (scritta per la Scala)", "")
    titolo = re.sub(r"\s*[-–]\s*7 dicembre.*$", "", x["titolo"].strip())
    r = dict(src=CODE[src], anno=y, stagione=short_season(x["stagione"]), data=x["data"], titolo=titolo,
             autore=clean_composer(x["autore"]), kind=kind_of(gen), direttore=clean_person(x["direttore"]), regista=clean_person(x["regista"]),
             interpreti=x["interpreti"].strip(), sala="" if x["sala"] in ("", "Teatro alla Scala") else x["sala"],
             rel=REL.get(x["affidabilita"], 0), prima=prima, ripub=x["ripubblicabile"] == "si")
    if src == "scala_sito_pubblico" and r["interpreti"]:
        keep = []
        for t in r["interpreti"].split(";"):
            t = t.strip()
            if t == "Programma":
                break
            if t and t not in ("Direttore", "Artisti ospiti", "Étoile", "Etoile") and not t.startswith(("*", "Allievo", "Allievi")):
                keep.append(t.rstrip("*"))
        r["interpreti"] = "; ".join(keep)[:300]
    if src == "cambiasi_1881" and r["rel"] == 0:
        r["interpreti"] = ""                      # nomi storpiati dall'OCR: non si pubblicano
    if not r["ripub"]:
        for k in list(r):
            if k not in RESTRICTED_KEEP + ("src", "kind", "rel", "ripub", "prima"):
                r[k] = ""
        r["kind"] = "opera" if r["kind"] == "opera/balletto" else r["kind"]
        if src == "gatti_vol1":
            r["kind"] = kind_of(x["genere"])      # serve solo a separare i concerti
    rows.append(r)
    stats[src]["righe_usate"] += 1

SBN_PATH = os.path.join(BASE, "sbn", "sbn_programmi.csv")
sbn_present = os.path.exists(SBN_PATH)
sbn_info = dict(righe=0, produzioni=0, ospiti=0, concerti=0, libretti_stagione=0, tournee=0, da_verificare=0, senza_anno=0)
if sbn_present:
    with open(SBN_PATH, encoding="utf-8-sig") as f:
        sb = list(csv.DictReader(f))
    for x in sb:
        sbn_info["righe"] += 1
        tipo = x.get("tipo", "")
        if tipo == "stagione":
            sbn_info["libretti_stagione"] += 1; continue
        if tipo == "tournee":
            sbn_info["tournee"] += 1; continue
        if tipo == "da_verificare":
            sbn_info["da_verificare"] += 1; continue
        if tipo not in ("produzione", "concerto", "ospiti"):
            continue
        if x.get("ripubblicabile", "si") == "no":
            continue
        if not (x.get("anno") or "").isdigit():
            sbn_info["senza_anno"] += 1; continue
        y = int(x["anno"])
        if not (Y0 <= y <= Y1):
            continue
        sbn_info[{"produzione": "produzioni", "ospiti": "ospiti", "concerto": "concerti"}[tipo]] += 1
        coreo = x.get("coreografo", "")
        reg = x.get("regista", "")
        if coreo and coreo not in reg:
            reg = (reg + " ; coreografia " + coreo).strip(" ;") if reg else "coreografia " + coreo
        deboli = x.get("anno_nota") == "incerto" or (not x.get("data_iso") and x.get("stagione_da") != "esplicita" and not x.get("stagione"))
        sala = x.get("sala", "")
        r = dict(src="B", anno=y, stagione=short_season(x.get("stagione", "")), data=x.get("data_iso", ""),
                 titolo=re.sub(r"\s+", " ", x["titolo"]).strip()[:110], autore=clean_composer(x.get("compositore", "").replace(";", " /")),
                 kind={"produzione": kind_of("", ""), "ospiti": "ospiti", "concerto": "concerto"}[tipo],
                 direttore=clean_person(x.get("direttore", "")), regista=clean_person(reg), interpreti=x.get("interpreti", "").strip(),
                 sala="" if sala in ("", "Scala") else sala, rel=0 if deboli else 1, prima=0, ripub=True)
        if "balletto" in x.get("titolo_originale", "").lower()[:200] or coreo:
            if r["kind"] == "opera":
                r["kind"] = "balletto"
        if re.match(r"^\d+$", r["titolo"]) or len(r["titolo"]) < 2:
            # difetto di sbn_parse.py: il numero d'ordine della scheda ("3: I due Foscari : ...") finisce nel titolo
            m = re.match(r"^\s*\d+\s*[:.]\s*(?:\d+\s*[:.]\s*)?(.+?)(?:\s+[:/=]\s+|\s*$)", x.get("titolo_originale", ""))
            r["titolo"] = re.sub(r"\s+", " ", m.group(1)).strip()[:110] if m else ""
            sbn_info["titoli_numerici_riparati"] = sbn_info.get("titoli_numerici_riparati", 0) + (1 if r["titolo"] else 0)
        if not r["titolo"]:
            continue
        rows.append(r)
        stats.setdefault("sbn", dict(righe_fonte=0, righe_usate=0, escluse_note=[]))
        stats["sbn"]["righe_usate"] += 1
    stats["sbn"]["righe_fonte"] = sbn_info["righe"]

# ------------------------------------------------------------------ fusione per anno
class G:
    __slots__ = ("anno", "rows", "nk", "ck", "srcs", "dates")

    def __init__(self, r):
        self.anno = r["anno"]; self.rows = [r]; self.nk = normtitle(r["titolo"]); self.ck = composer_key(r["autore"])
        self.srcs = {r["src"]}; self.dates = {r["data"]} if r["data"] else set()

    def add(self, r):
        self.rows.append(r); self.srcs.add(r["src"])
        if r["data"]: self.dates.add(r["data"])
        if not self.ck: self.ck = composer_key(r["autore"])


groups_by_year = collections.defaultdict(list)
for r in sorted(rows, key=lambda r: (r["anno"], PRIO[r["src"]])):
    nk = normtitle(r["titolo"])
    if not nk:
        continue
    ck = composer_key(r["autore"])
    isconc = r["kind"] == "concerto"
    found = None
    for g in groups_by_year[r["anno"]]:
        if (g.rows[0]["kind"] == "concerto") != isconc:
            continue
        if g.nk == nk:
            found = g; break
    if not found:
        for g in groups_by_year[r["anno"]]:
            if (g.rows[0]["kind"] == "concerto") != isconc or r["src"] in g.srcs:
                continue
            if g.ck and ck and g.ck != ck:
                continue
            if same_title(g.nk, nk):
                found = g; break
    if found:
        found.add(r)
    else:
        groups_by_year[r["anno"]].append(G(r))

# fase 2: gruppi solo Wikipedia/Wikidata si agganciano all'anno teatrale di Cambiasi/Romani (anno prima/dopo)
n_adj = 0
for y in sorted(groups_by_year):
    if y > 1881:
        continue
    for g in list(groups_by_year[y]):
        if not g.srcs <= {"W", "D"}:
            continue
        for y2 in (y + 1, y - 1):
            tgt = None
            for h in groups_by_year.get(y2, []):
                if h.srcs & {"C", "R"} and not (h.srcs & {"W", "D"}) and (h.nk == g.nk or (not (h.ck and g.ck and h.ck != g.ck) and same_title(h.nk, g.nk))):
                    tgt = h; break
            if tgt:
                for r in g.rows: tgt.add(r)
                groups_by_year[y].remove(g); n_adj += 1
                break

# ------------------------------------------------------------------ campi finali dei gruppi
def pick(rows_, field, prio, extra_ok=lambda r: True):
    for c in prio:
        for r in rows_:
            if r["src"] == c and r[field] and extra_ok(r):
                return r[field]
    return ""


def best_composer(rows_):
    cands = []
    for c in TITLE_PRIO:
        for r in rows_:
            if r["src"] == c and r["autore"]:
                cands.append(r["autore"])
    if not cands:
        return ""
    best = cands[0]
    for c in cands[1:]:
        if len(c.split()) > len(best.split()) and composer_key(c) == composer_key(best):
            best = c
    return best


def in_closure(rec_rows, y):
    """1943-46: teatro distrutto (15-16 agosto 1943), riaperto l'11 maggio 1946."""
    if y in (1944, 1945):
        return True
    ds = [r["data"] for r in rec_rows if re.match(r"^\d{4}-\d\d-\d\d$", r["data"] or "")]
    if ds:
        d = min(ds)
        return "1943-08-16" <= d < "1946-05-11"
    st = " ".join(r["stagione"] for r in rec_rows)
    return y in (1943, 1946) and (("1943-44" in st) or ("1945-46" in st))


pub = []         # righe pubblicate
ALLG = []        # tutti i gruppi (anche solo-Marangoni) per grafico e classifiche
for y in sorted(groups_by_year):
    for g in groups_by_year[y]:
        rs = g.rows
        pr = {c: 0 for c in PRIO}
        title = pick(rs, "titolo", TITLE_PRIO)
        comp = best_composer(rs)
        kind = collections.Counter(r["kind"] for r in rs if r["src"] not in "G").most_common(1)
        kind = kind[0][0] if kind else rs[0]["kind"]
        if kind == "opera/balletto" and any(r["src"] == "G" and r["kind"] != "opera/balletto" for r in rs):
            kind = "opera"
        srcs = "".join(sorted(g.srcs, key=lambda c: PRIO[c]))
        top = min(g.srcs, key=lambda c: PRIO[c])
        prima = max(r["prima"] for r in rs)
        rec = dict(anno=y, titolo=title, autore=comp, kind=kind, srcs=srcs, top=top, ck=composer_key(comp), nk=g.nk,
                   dates=g.dates, prima=prima, concerto=(kind == "concerto"))
        # campi per la pubblicazione: mai da Marangoni
        pubrs = [r for r in rs if r["src"] not in WITHHELD_ROWS]
        rec["publish"] = bool(pubrs)
        if pubrs:
            rec["stagione"] = pick(pubrs, "stagione", SEASON_PRIO)
            rec["data"] = pick(pubrs, "data", DATE_PRIO, lambda r: bool(re.match(r"^\d{4}-\d\d-\d\d$", r["data"])))
            rec["direttore"] = pick(pubrs, "direttore", CAST_PRIO)
            rec["regista"] = pick(pubrs, "regista", CAST_PRIO)
            rec["interpreti"] = pick(pubrs, "interpreti", CAST_PRIO)
            rec["sala"] = pick(pubrs, "sala", "SB")
            if not rec["sala"] and 1943 <= y <= 1946 and in_closure(pubrs, y):
                rec["sala"] = "teatro distrutto: altra sala?"
            rec["rel"] = max(r["rel"] for r in pubrs)
            rec["pubsrcs"] = "".join(sorted({r["src"] for r in pubrs}, key=lambda c: PRIO[c]))
            rec["n_righe_pub"] = collections.Counter(r["src"] for r in pubrs)
        ALLG.append(rec)
        if pubrs:
            pub.append(rec)

# se una riga e' fatta solo di Gatti, genere non distinto: va bene; tolgo i 'solo Marangoni' dalla pubblicazione (gia' fatto)

# ------------------------------------------------------------------ titoli.json
GCODE = {"opera": "o", "balletto": "b", "concerto": "c", "ospiti": "g", "ragazzi": "r", "opera/balletto": "x", "tournee": "t"}
GCOUNT = collections.Counter()
titoli = []
for rec in sorted(pub, key=lambda r: (r["anno"], r["data"] or "9999", r["titolo"].lower())):
    titoli.append([rec["anno"], rec["stagione"], rec["data"], rec["titolo"], rec["autore"], GCODE.get(rec["kind"], "o"),
                   rec["direttore"], rec["regista"], rec["interpreti"], rec["pubsrcs"], rec["rel"], rec["prima"], rec["sala"]])
published_by_src = collections.Counter()
for rec in pub:
    for c, n in rec["n_righe_pub"].items():
        published_by_src[c] += n

# ------------------------------------------------------------------ copertura.json (grafico: ogni titolo una volta, colore = fonte migliore)
CLASS = {"S": "S", "B": "B", "I": "B", "V": "B", "C": "C", "R": "C", "G": "G", "M": "G", "W": "W", "D": "W"}
cov = {y: collections.Counter() for y in range(Y0, Y1 + 1)}
cov_src = {y: collections.defaultdict(set) for y in range(Y0, Y1 + 1)}
for rec in ALLG:
    if rec["kind"] in ("concerto", "tournee"):
        continue
    cov[rec["anno"]][CLASS[rec["top"]]] += 1
    for c in rec["srcs"]:
        cov_src[rec["anno"]][c].add(rec["nk"])
anni = []
for y in range(Y0, Y1 + 1):
    d = dict(y=y, S=cov[y]["S"], B=cov[y]["B"], C=cov[y]["C"], G=cov[y]["G"], W=cov[y]["W"])
    d["t"] = d["S"] + d["B"] + d["C"] + d["G"] + d["W"]
    anni.append(d)

PERIODI = [
    (1778, 1881, "Cambiasi 1881, Romani 1862 (Wikipedia e Wikidata a controllo)"),
    (1882, 1905, "Gatti vol. I, Wikipedia, Wikidata: nessuna cronologia dopo Cambiasi"),
    (1906, 1920, "Marangoni-Vanbianchi (solo conteggi), Gatti vol. I, Wikipedia, Wikidata"),
    (1921, 1942, "Gatti vol. I, Wikipedia, Wikidata"),
    (1943, 1946, "bombardamento e ricostruzione: quasi nulla"),
    (1947, 1963, "Gatti vol. I, Wikipedia, Wikidata"),
    (1964, 2022, "programmi di sala del Catalogo SBN, Wikipedia, Wikidata"),
    (2023, 2027, "sito della Scala (stagioni 2023-24 ... 2026-27)"),
]
periodi = []
for a, b, fonti_txt in PERIODI:
    ys = [d for d in anni if a <= d["y"] <= b]
    con = [d for d in ys if d["t"] > 0]
    periodi.append(dict(da=a, a=b, anni=len(ys), anni_con_dati=len(con),
                        media=round(sum(d["t"] for d in con) / len(con), 1) if con else 0,
                        anni_con_5=sum(1 for d in ys if d["t"] >= 5), fonti=fonti_txt))
vuoti = [d["y"] for d in anni if d["t"] == 0]
json.dump(dict(anni=anni, periodi=periodi, anni_vuoti=vuoti), open(os.path.join(OUT, "copertura.json"), "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------------ classifiche
opere = [r for r in ALLG if r["kind"] not in ("concerto", "tournee", "ospiti") and r["nk"] and not (r["kind"] == "balletto" and r["anno"] <= 1881)]   # i balli di Cambiasi (1778-1881) non entrano nelle classifiche delle opere
# cluster dei titoli (varianti ortografiche) per compositore; i gruppi senza compositore si agganciano al cluster piu' vicino nel tempo
reps = []                     # (nk, ck, cid)
byblock = collections.defaultdict(list)
bykey = {}
cl_years = collections.defaultdict(list)
cnt = collections.Counter((r["nk"], r["ck"]) for r in opere if r["ck"])
for (nk, ck), n in sorted(cnt.items(), key=lambda kv: -kv[1]):
    cid = None
    for (rnk, rck, rid) in byblock[nk[:2]]:
        if rck == ck and same_title(rnk, nk):
            cid = rid; break
    if cid is None:
        cid = len(reps); reps.append((nk, ck, cid)); byblock[nk[:2]].append((nk, ck, cid))
    bykey[(nk, ck)] = cid
cluster_comp = {}
for r in opere:
    if r["ck"]:
        cid = bykey[(r["nk"], r["ck"])]
        r["cid"] = cid; r["wck"] = r["ck"]
        cl_years[cid].append(r["anno"]); cluster_comp[cid] = r["ck"]
nocomp = {}
for r in opere:
    if r["ck"]:
        continue
    best = None
    for (rnk, rck, rid) in byblock[r["nk"][:2]]:
        if same_title(rnk, r["nk"]):
            dist = min(abs(r["anno"] - y) for y in cl_years[rid])
            if dist <= 30 and (best is None or dist < best[0]):
                best = (dist, rid)
    if best:
        r["cid"] = best[1]; r["wck"] = cluster_comp[best[1]]
    else:
        k = nocomp.setdefault(r["nk"], 10000 + len(nocomp))
        r["cid"] = k; r["wck"] = ""

comp_names = collections.defaultdict(collections.Counter)
for r in opere:
    if r["ck"] and r["autore"]:
        first = re.split(r"[;/]", r["autore"])[0].strip()
        comp_names[r["ck"]][first] += 1


def comp_display(ck):
    c = comp_names.get(ck)
    if not c:
        return ck.title()
    # il nome piu' lungo tra i piu' frequenti
    top = [n for n, k in c.most_common(8)]
    return max(top, key=lambda n: (len(n.split()[0].strip(".")) > 1, len(n.split()) >= 2, c[n]))


title_names = collections.defaultdict(collections.Counter)
for r in opere:
    title_names[r["cid"]][r["titolo"]] += 1

PER_CL = [("1778-1881", 1778, 1881), ("1882-1963", 1882, 1963), ("1964-2027", 1964, 2027), ("1778-2027", 1778, 2027)]
classifiche = {}
for name, a, b in PER_CL:
    sel = [r for r in opere if a <= r["anno"] <= b]
    wy = collections.defaultdict(set)
    for r in sel:
        wy[r["cid"]].add(r["anno"])
    top = sorted(wy.items(), key=lambda kv: (-len(kv[1]), min(kv[1])))[:20]
    tl = []
    for cid, ys in top:
        tnames = title_names[cid]
        ck = cluster_comp.get(cid, "")
        tl.append(dict(titolo=tnames.most_common(1)[0][0], autore=comp_display(ck) if ck else "", n=len(ys), da=min(ys), a=max(ys)))
    cy = collections.defaultdict(set)
    cw = collections.defaultdict(set)
    for r in sel:
        if r["wck"]:
            cy[r["wck"]].add((r["cid"], r["anno"]))
            cw[r["wck"]].add(r["cid"])
    topc = sorted(cy.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:20]
    cl = [dict(autore=comp_display(ck), n=len(v), opere=len(cw[ck])) for ck, v in topc]
    senza = len({(r["cid"], r["anno"]) for r in sel if not r["wck"]})
    classifiche[name] = dict(da=a, a=b, titoli=tl, compositori=cl, totale_titoli_anno=len({(r["cid"], r["anno"]) for r in sel}),
                             senza_compositore=senza)
json.dump(classifiche, open(os.path.join(OUT, "classifiche.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------------ prime assolute
prime = []
for rec in sorted(pub, key=lambda r: (r["anno"], r["data"] or "9999", r["titolo"].lower())):
    if rec["prima"] and rec["kind"] not in ("concerto",):
        prime.append([rec["anno"], rec["data"], rec["titolo"], rec["autore"], GCODE.get(rec["kind"], "o"), rec["pubsrcs"], rec["prima"]])
json.dump(prime, open(os.path.join(OUT, "prime.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------------ 7 dicembre
sette = []
by_y = collections.defaultdict(list)
for rec in pub:
    if [d for d in rec["dates"] if d.endswith("-12-07")] and rec["kind"] != "concerto":
        by_y[int(sorted(d for d in rec["dates"] if d.endswith("-12-07"))[0][:4])].append(rec)
for y, lst in by_y.items():
    # per l'apertura fanno fede Wikipedia (data) e il sito della Scala; le schede SBN con la stessa data vengono dopo
    auth = [r for r in lst if set(r["pubsrcs"]) & {"S", "W"}]
    sette += [dict(r, anno=y) for r in (auth or lst)]
sette.sort(key=lambda r: (r["anno"], r["titolo"].lower()))
serate = [[r["anno"], r["titolo"], r["autore"], r["direttore"], r["regista"], r["pubsrcs"], r["rel"]] for r in sette]
anni_sette = sorted({r["anno"] for r in sette})
aper = []
aper_path = os.path.join(BASE, "pulito", "_wp_aperture.csv")
if os.path.exists(aper_path):
    for x in csv.DictReader(open(aper_path, encoding="utf-8-sig")):
        m = re.match(r"(\d{4})", x["stagione"])
        if m and int(m.group(1)) >= 1951 and int(m.group(1)) not in anni_sette:
            aper.append([int(m.group(1)), x["titolo"], x["compositore"]])
aper.sort()
json.dump(dict(serate=serate, anni_con_data=anni_sette, aperture_senza_data=aper), open(os.path.join(OUT, "sette_dicembre.json"), "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------------ fonti.json
y_by_src = collections.defaultdict(list)
for r in rows:
    y_by_src[r["src"]].append(r["anno"])
FONTI = [
    dict(c="S", nome="Sito pubblico del Teatro alla Scala", dettaglio="pagine di stagione 2023-24 ... 2026-27 (spettacoli e concerti, con cast)",
         licenza="Dati del Teatro; citare: (c) Teatro alla Scala.", pubblicate="titolo, autore, data, direttore, regia, interpreti", note="Affidabilita alta. Concerti senza programma."),
    dict(c="B", nome="Catalogo SBN - ICCU (programmi di sala)", dettaglio="schede bibliografiche dei programmi di sala della Scala, 1963-2024, cercate per anno e per stagione",
         licenza="Dati bibliografici del Servizio Bibliotecario Nazionale; citare: Catalogo SBN - ICCU (opac.sbn.it).", pubblicate="titolo, compositore, direttore, regia/coreografia, interpreti principali, data",
         note="Una riga per produzione, non per serata. Direttore, regia, coreografia e interpreti vengono dai nomi con ruolo della scheda e dal titolo: presenti solo per una parte dei programmi. Affidabilita media; bassa se l'anno viene solo dall'anno di stampa del programma o e' incerto. Non usati: %d libretti di stagione, %d schede da verificare, %d tournee, e le schede senza anno." % (sbn_info["libretti_stagione"], sbn_info["da_verificare"], sbn_info["tournee"])),
    dict(c="C", nome="Cambiasi, Teatro alla Scala 1778-1881", dettaglio="serie delle opere in musica e serie dei balli per stagione (Ricordi 1881), da testo OCR di Internet Archive",
         licenza="Libro di pubblico dominio; si pubblicano i fatti estratti, non la scansione.", pubblicate="opere: titolo, maestro, genere, data, interpreti (solo dove l'OCR e' buono); balli: titolo, coreografo, compositore, data",
         note="Non e' l'elenco delle sere: un titolo vale una volta per stagione. OCR con errori nei nomi. Anni 1832 e 1835 vuoti per le opere. I balli (1778-1881, 104 anni su 104) sono letti dal testo a stagioni; controllo a mano su 3 stagioni; le prime ballerine non sono pubblicate."),
    dict(c="R", nome="Romani, Teatro alla Scala: cronologia di tutti gli spettacoli (1862)", dettaglio="stagione per stagione 1778-1862, da testo OCR",
         licenza="Libro di pubblico dominio; si pubblicano i fatti estratti.", pubblicate="titolo, maestro, genere", note="Letti 46 anni su 85: mancano quelli con intestazione illeggibile."),
    dict(c="G", nome="C. Gatti, Il Teatro alla Scala nella storia e nell'arte, vol. I (Ricordi, Milano 1964)", dettaglio="titoli citati come rappresentati nel racconto, 1882-1963",
         licenza="Libro ancora protetto: dal libro si ricavano solo fatti (titolo, compositore, stagione, direttore). Nessun testo, nessuna pagina riprodotta.", pubblicate="titolo, compositore, stagione, direttore",
         note="Il volume I e' un racconto, non la cronologia (che e' nel vol. II): nomina 10-12 titoli per stagione su 20-30. Precisione controllata a mano: 87% su 70 righe."),
    dict(c="M", nome="Marangoni e Vanbianchi, La Scala. Studi e ricerche, note storiche e statistiche 1906-1920 (1922)", dettaglio="cartelloni di stagione 1906-1918 (OCR)",
         licenza="Stato dei diritti non verificato: dal libro si pubblicano solo i conteggi per anno nel grafico, nessuna riga nelle tabelle.", pubblicate="solo conteggi",
         note="Mancano 1914-15, 1917-18, 1919-20."),
    dict(c="W", nome="Wikipedia in italiano: Stagioni liriche del Teatro alla Scala", dettaglio="cronistoria 1778-2024, titoli con date, direttori e interpreti (revisione 152735080 del 3/10/2026); anche le aperture di stagione",
         licenza="CC BY-SA 4.0: le righe derivate si possono riusare citando la pagina, con la stessa licenza.", pubblicate="titolo, compositore, data, direttore, regia, interpreti, prima assoluta",
         note="Pochi titoli per anno (2-5 tra 1906 e 1943); alcuni titoli troncati. Anno del calendario, non anno teatrale."),
    dict(c="D", nome="Wikidata (query SPARQL del 29/10/2026)", dettaglio="'luogo della prima rappresentazione' (P4647) e 'luogo' (P276/P291) uguale al Teatro alla Scala, con data",
         licenza="CC0 (pubblico dominio).", pubblicate="titolo, compositore (dove c'e'), data, genere",
         note="Solo le voci con P4647 sono prime assolute (%d); le altre %d sono produzioni e sono segnate cosi'." % (sum(1 for r in rows if r["src"] == "D" and r["prima"] == 2), sum(1 for r in rows if r["src"] == "D" and r["prima"] != 2))),
    dict(c="I", nome="Programmi di sala del Teatro alla Scala 2002-2011 (Internet Archive)", dettaglio="14 programmi aperti con testo OCR (opere, concerti, gala), piu' i capitoli 'alla Scala dal... al...' di 4 programmi (Carmen, Don Giovanni, L'elisir d'amore, Der Rosenkavalier) con data, direttore, regia di ogni produzione storica",
         licenza="Edizioni del Teatro alla Scala, messe su Internet Archive: si pubblicano solo fatti (titolo, data, direttore, regia, solisti), non testi ne' pagine.", pubblicate="titolo, compositore, data, direttore, regia, interpreti (dove il testo li da' per ruolo)",
         note="Affidabilita alta per i programmi, media per le produzioni storiche (OCR a colonne: i cast per ruolo non sono letti). La data e' quella della prima; le repliche sono lette solo dove l'OCR le tiene in ordine."),
    dict(c="V", nome="Catalogo SBN - registrazioni sonore dal vivo alla Scala", dettaglio="schede di registrazioni sonore con la nota 'Registrazione dal vivo, Milano, Teatro alla Scala, <data>', lette per circa 3.000 candidati; tenute solo le esecuzioni alla Scala, non le incisioni in studio",
         licenza="Dati bibliografici del Servizio Bibliotecario Nazionale; citare: Catalogo SBN - ICCU (opac.sbn.it).", pubblicate="titolo, compositore, data dell'esecuzione, direttore, interpreti",
         note="E' la data dell'esecuzione registrata (una sera), non l'intera produzione. Affidabilita alta se la nota nomina il Teatro alla Scala e il giorno; media se il luogo e' solo 'Milano' con orchestra della Scala o la data e' solo mese/anno."),
]
fonti = []
for fd in FONTI:
    c = fd["c"]
    ys = y_by_src.get(c, [])
    nrows = len(ys)
    fonti.append(dict(fd, anni=("%d-%d" % (min(ys), max(ys))) if ys else "", righe_lette=nrows, righe_pubblicate=published_by_src.get(c, 0),
                      anni_distinti=len(set(ys))))
tot_pub_titles = len(titoli)
meta = dict(generato=datetime.date.today().isoformat(), righe_pagina=tot_pub_titles, gruppi_totali=len(ALLG), sbn_presente=sbn_present, sbn=sbn_info,
            agganci_anno_adiacente=n_adj, prime=len(prime), serate_7_dicembre=len(serate), anni_7_dicembre=len(anni_sette))
json.dump(dict(fonti=fonti, meta=meta), open(os.path.join(OUT, "fonti.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(titoli, open(os.path.join(OUT, "titoli.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

print("OK", meta)
for fd in fonti:
    print(fd["c"], fd["nome"][:40], "anni", fd["anni"], "lette", fd["righe_lette"], "pubblicate", fd["righe_pubblicate"])
print("righe pagina", tot_pub_titles, "prime", len(prime), "7 dic", len(serate), "anni 7 dic", len(anni_sette), "aperture senza data", len(aper))
