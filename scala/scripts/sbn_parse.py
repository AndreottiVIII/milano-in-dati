"""Legge tutte le risposte in raw/sbn/search (e raw/sbn/full se ci sono), tiene i programmi di sala della Scala,
li classifica, estrae i campi e scrive sbn/sbn_programmi.csv (+ sbn/_tutti_record.csv per tracciabilita')."""
import sys, os, re, json, glob, csv, unicodedata, collections
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "raw", "sbn")
OUT = os.path.join(ROOT, "sbn")
os.makedirs(OUT, exist_ok=True)
MESI = "gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre".split("|")

def load():
    recs = {}
    for f in sorted(glob.glob(os.path.join(RAW, "search", "*.json"))):
        for r in json.load(open(f, encoding="utf8")).get("briefRecords", []):
            recs.setdefault(r["codiceIdentificativo"], r)
    full = {}
    for f in glob.glob(os.path.join(RAW, "full", "*.json")):
        try:
            d = json.load(open(f, encoding="utf8"))
        except Exception:
            continue
        if isinstance(d, dict) and d.get("codiceIdentificativo"):
            full[d["codiceIdentificativo"]] = d
    return recs, full

def bid_corto(bid):
    BS = chr(92)
    return bid.replace("IT" + BS + "ICCU" + BS, "").replace(BS, "")

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def years_in(pub):
    return [int(y) for y in re.findall(r"(?<!\d)(19[5-9]\d|20[0-2]\d)(?!\d)", pub or "")]

def anno_di(r):
    pub = r.get("pubblicazione") or ""
    # stampa 1965 / [1976?] / 1975-1976 / 1967-68
    ys = years_in(pub)
    if not ys:
        return None, ""
    flag = "incerto" if re.search(r"\?|\[", pub) else ""
    return ys[0], flag

def stagione_esplicita(text):
    m = re.search(r"(?<!\d)(19[5-9]\d|20[0-2]\d)\s*[-/]\s*(\d{4}|\d{2})(?!\d)", text or "")
    if m:
        a = int(m.group(1)); b = m.group(2)
        b2 = int(b) if len(b) == 4 else (a // 100) * 100 + int(b)
        if len(b) == 2 and int(b) < a % 100: b2 += 100
        if b2 == a + 1:
            return f"{a}-{str(b2)[2:]}"
    return ""

def classifica(r):
    t = r["titolo"]; pub = r.get("pubblicazione") or ""; aut = r.get("autorePrincipale") or ""
    blob = t + " " + pub + " " + aut
    if not re.search(r"scala", pub + " " + aut, re.I):
        return "fuori_scala"
    if re.search(r"museo teatrale|amici della scala|amici del loggione|allemandi|ricordi|catalogo|mostra|iconografi|cimeli|scenografie", blob, re.I) and \
            not re.search(r"edizioni (della|del teatro alla) scala", pub, re.I):
        return "altro_museo_libro"
    if re.search(r"museo teatrale alla scala|manifestazion[ie]", t, re.I):
        return "altro_museo_libro"
    if re.search(r"^\s*(la scala (a|in|al)|teatro alla scala (a|in)|la scala\s*:\s*montreal)|tourn[ée]e|festival mondial|a mosca|a berlino|a vienna|a parigi", t, re.I):
        return "tournee"
    if re.match(r"\s*(toscanini e la scala|la scala \d{4}|celebrazioni|commemorazione)", t, re.I):
        return "altro"
    if re.match(r"\s*(\[\d+\]\s*:|la stagione|stagione|teatro alla scala\s*:?\s*stagione|piccola scala|concerti[- ]balletti|concerti\s+\d{4}|concerti di canto|miscellanea|estate d'arte|programma generale|rassegna)", t, re.I) and             not re.search(r"\d+\.?\s*concerto", t):
        return "stagione"
    if re.search(r"bolscio|bolshoi|royal (opera|house|ballet)|kirov|covent garden|opera di (vienna|parigi|stato)", t, re.I):
        return "ospiti"
    if re.match(r"\s*invito al concerto", t, re.I):
        return "concerto"
        return "stagione"
    if re.search(r"(^|\W)\d+[.ºª°]?\s*concerto|concerto sinfonico|(primo|secondo|terzo|quarto|quinto|sesto|settimo|ottavo|nono|decimo|undicesimo|dodicesimo|tredicesimo|quattordicesimo|quindicesimo|sedicesimo|diciassettesimo|diciottesimo|diciannovesimo|ventesimo)\s+concerto|ciclo di concerti|musica da camera|recital|solisti della scala|\b(soprano|tenore|baritono|mezzosoprano|basso|pianista|violinista|violoncellista)\s*$|^concerto|concerto (di|per|dell)", t, re.I):
        return "concerto"
    if re.search(r"^\s*(\d{4}[-/]\d{2,4}|ente autonomo|programma|libretto|notiziario|bollettino)", t, re.I):
        return "altro"
    return "produzione"

def clean_title(s):
    s = s.replace("*", "")
    s = re.sub(r"^\d{1,2}\s*[.:]\s+", "", s)
    s = re.sub(r"\bL' ", "L'", s)
    s = re.sub(r"\s+", " ", s).strip(" .;,:")
    return s

def split_title(t):
    # titolo = parte prima di " : " o " / " o " ; "
    head = re.split(r"\s*:\s+|\s+/\s+|\s+;\s+", t, maxsplit=1)[0]
    return clean_title(head)

def grab(pattern, text, flags=re.I):
    m = re.search(pattern, text, flags)
    return clean_title(m.group(1)) if m else ""

STOP = r"([^;\]\[]+?)\s*(?:;|\]|\s\.\s|\s/\s|$)"
def campi(t):
    d = {}
    d["direttore"] = grab(r"(?:concertatore e direttore(?: d'orchestra)?|concertatore e direzione|maestro concertatore e direttore|maestro direttore|direttore(?: d'orchestra)?|direzione musicale|dirige)\s+(?:di\s+)?" + STOP, t)
    d["regista"] = grab(r"\bregi[ae](?:[ ,]+(?:e\s+)?(?:scene|scena|costumi|luci|e|bozzetti|figurini|ideazione))*\s*(?:di\s+)?" + STOP, t)
    d["coreografo"] = grab(r"(?:coreografi[ae]|coreografo|movimenti coreografici|movimenti mimici|ripresa coreografica)(?:\s+e\s+regia)?\s+(?:di\s+)?" + STOP, t)
    d["interpreti"] = grab(r"interpreti(?: principali)?\s*:\s*(.+?)(?:\]|$)", t)
    c = grab(r"(?:parole e musica|poema e musica|musiche?|musica)\s+(?:di\s+)?([^;\]/\[]+?)\s*(?:;|\]|/|\s\.\s|\s:\s|,\s*opus|$)", t)
    if not c:
        c = grab(r"/\s*(?:di\s+)?([A-ZÀ-Ý][\w'’.À-ÿ-]+(?:\s+(?:[A-ZÀ-Ý][\w'’.À-ÿ-]+|de|di|van|von|da))*)\s*(?:[;:\]]|$)", t, 0)
    if c and (re.search(r"\b(atti|atto|quadri|parti|tempi)\b", c, re.I) or not re.match(r"[A-ZÀ-Ý0-9]", c)):
        c = ""
    d["compositore"] = c
    return d

def data_in(text):
    m = re.search(r"(\d{1,2})(?:\s*(?:e|-|,)\s*\d{1,2})?\s+(" + "|".join(MESI) + r")(?:\s+(\d{4}))?", text or "", re.I)
    if m:
        return m.group(0)
    return ""

def data_iso(text):
    """Prima data completa (giorno singolo, mese, anno) trovata nel testo, in formato AAAA-MM-GG; altrimenti ''."""
    m = re.search(r"(?<!"+chr(92)+"d)(" + chr(92) + "d{1,2})" + chr(92) + "s+(" + "|".join(MESI) + ")" + chr(92) + "s+(19[5-9]" + chr(92) + "d|20[0-2]" + chr(92) + "d)", text or "", re.I)
    if not m: return ""
    return f"{m.group(3)}-{MESI.index(m.group(2).lower())+1:02d}-{int(m.group(1)):02d}"

def stagione_da_data(iso):
    if not iso: return ""
    y, mo = int(iso[:4]), int(iso[5:7])
    a = y if mo >= 9 else y - 1
    return f"{a}-{str(a+1)[2:]}"

def nome_diretto(n):
    n = re.sub(r"<[^>]*>", "", n).strip()
    n = re.sub(r"[ʹ]", "", n)
    if "," in n:
        a, b = n.split(",", 1)
        n = (b.strip() + " " + a.strip()).strip()
    return n

def riclassifica(t):
    if re.search(r"a cura di|prefazione|storia|bilancio|alla scala\s*(/|$)|deux cents|presidente della repubblica|saggio|catalogo|milano,\s*\d{4}|documentazion", t, re.I):
        return "altro"
    if re.search(r"\b(opera|balletto|balletti|dramma|melodramma|commedia|atti|atto|quadri|farsa|azione|favola|fiaba|coreograf\w*|musica di|musiche|libretto|parole e musica|spettacolo|serata|tragedia|intermezzo|oratorio|mistero)\b", t, re.I) or re.search(r"^[^/]{3,90}\s/\s+(di|musica di)\s+[A-ZÀ-Ý]", t) or ((" . " in t) and not re.search(r"direttore|pianist", t, re.I)):
        return "produzione"
    if re.search(r"baritono|soprano|tenore|mezzosoprano|pianist|violin|direttore|orchestra|filarmonica|quartetto|duo|recital|concerto|solisti|ore \d|sala verdi|teatro alla scala,|\d{1,2} (gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)", t, re.I):
        return "concerto"
    return "da_verificare"

def sala(r, cls):
    blob = r["titolo"] + " " + (r.get("pubblicazione") or "")
    if cls == "tournee": return "tournée"
    if re.search(r"piccola scala", blob, re.I): return "Piccola Scala"
    if re.search(r"arcimboldi", blob, re.I): return "Arcimboldi"
    return "Scala"

def main():
    recs, full = load()
    rows = []; allrows = []
    for bid, r in recs.items():
        cls = classifica(r)
        anno, flag = anno_di(r)
        f = full.get(bid, {})
        allrows.append([bid, cls, anno or "", r["titolo"], r.get("pubblicazione", "")])
        if cls in ("fuori_scala", "altro_museo_libro", "altro") or not anno or not (1963 <= anno <= 2024):
            continue
        t = r["titolo"]
        if cls in ("produzione",):
            cls = riclassifica(t)
            if cls == "altro": continue
        c = campi(t) if cls in ("produzione", "ospiti", "tournee", "da_verificare") else dict(direttore="", regista="", coreografo="", interpreti="", compositore="")
        # compositore dal record completo se c'e'
        nomi = f.get("nomi", [])
        comp = [nome_diretto(re.sub(r"^\[Compositore\]\s*", "", n)) for n in nomi if n.startswith("[Compositore]")]
        if comp: c["compositore"] = "; ".join(comp)
        note = " | ".join(f.get("note", []) or [])
        stag = stagione_esplicita(t + " " + (r.get("pubblicazione") or "") + " " + note)
        iso = data_iso(note) or data_iso(t)
        stag_da = "esplicita" if stag else ""
        if not stag and iso:
            stag = stagione_da_data(iso); stag_da = "da data"
        biblio = []
        for loc in f.get("localizzazioni", []) or []:
            sm = loc.get("shelfmarks") or [{}]
            biblio.append(f"{sm[0].get('shelfmark','')} ({loc.get('isil','')})")
        rows.append(dict(
            stagione=stag, anno=anno, anno_nota=flag, tipo=cls,
            titolo=split_title(t) if cls in ("produzione", "concerto") else clean_title(re.split(r"\s+/\s+", t)[0]),
            compositore=c["compositore"], direttore=c["direttore"], regista=c["regista"], coreografo=c["coreografo"],
            interpreti=c["interpreti"], sala=sala(r, cls), data=data_in(note) or data_in(t), data_iso=iso, stagione_da=stag_da,
            nota_scheda=note, bid=bid, biblioteche="; ".join(biblio), n_biblioteche=len(biblio),
            url="https://opac.sbn.it/bid/" + bid_corto(bid),
            titolo_originale=t, pubblicazione=r.get("pubblicazione", ""), editore_anno_originale=r.get("pubblicazione", ""),
            scheda_completa="si" if f else "no"))
    # dedupe: stessa produzione, stesso anno
    groups = collections.OrderedDict()
    for row in rows:
        key = (row["tipo"], row["anno"], norm(row["titolo"])[:60], norm(row["interpreti"])[:30] if row["tipo"] == "concerto" else "")
        groups.setdefault(key, []).append(row)
    out = []
    for key, g in groups.items():
        g.sort(key=lambda x: -len(x["titolo_originale"]))
        best = dict(g[0])
        best["bid_altri"] = "; ".join(x["bid"] for x in g[1:])
        best["n_record"] = len(g)
        libs = []
        for x in g:
            for b in x["biblioteche"].split("; "):
                if b and b not in libs: libs.append(b)
        best["biblioteche"] = "; ".join(libs); best["n_biblioteche"] = len(libs)
        for fld in ("compositore", "direttore", "regista", "coreografo", "interpreti", "data", "data_iso", "stagione", "stagione_da"):
            if not best[fld]:
                for x in g:
                    if x[fld]: best[fld] = x[fld]; break
        out.append(best)
    out.sort(key=lambda x: (x["anno"], x["tipo"], norm(x["titolo"])))
    cols = ["stagione", "stagione_da", "anno", "anno_nota", "tipo", "titolo", "compositore", "direttore", "regista", "coreografo", "interpreti",
            "sala", "data", "data_iso", "nota_scheda", "bid", "bid_altri", "n_record", "biblioteche", "n_biblioteche", "url", "scheda_completa",
            "titolo_originale", "pubblicazione"]
    with open(os.path.join(OUT, "sbn_programmi.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(out)
    with open(os.path.join(OUT, "_tutti_record_classificati.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh); w.writerow(["bid", "classe", "anno", "titolo", "pubblicazione"]); w.writerows(allrows)
    cnt = collections.Counter(r["tipo"] for r in out)
    print("record totali", len(recs), "tenuti prima del dedupe", len(rows), "dopo", len(out), dict(cnt), "schede complete", len(full))
    return out

if __name__ == "__main__":
    main()
