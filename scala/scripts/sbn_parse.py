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
    if re.match(r"\s*(stagione|teatro alla scala\s*:?\s*stagione|piccola scala|concerti\s+\d{4}|miscellanea|stagione di balletti|programma di sala della stagione)", t, re.I) and \
            not re.search(r"\d+\.?\s*concerto", t):
        return "stagione"
    if re.search(r"(^|\W)\d+[.ºª°]?\s*concerto|concerto sinfonico|(primo|secondo|terzo|quarto|quinto|sesto|settimo|ottavo|nono|decimo|undicesimo|dodicesimo|tredicesimo|quattordicesimo|quindicesimo|sedicesimo|diciassettesimo|diciottesimo|diciannovesimo|ventesimo)\s+concerto|ciclo di concerti|musica da camera|recital|solisti della scala|\b(soprano|tenore|baritono|mezzosoprano|basso|pianista|violinista|violoncellista)\s*$|^concerto|concerto (di|per|dell)", t, re.I):
        return "concerto"
    if re.search(r"^\s*(\d{4}[-/]\d{2,4}|ente autonomo|programma|libretto|notiziario|bollettino)", t, re.I):
        return "altro"
    return "produzione"

def clean_title(s):
    s = s.replace("*", "")
    s = re.sub(r"\bL' ", "L'", s)
    s = re.sub(r"\s+", " ", s).strip(" .;,:")
    return s

def split_title(t):
    # titolo = parte prima di " : " o " / " o " ; "
    head = re.split(r"\s+[:/]\s+|\s+;\s+", t, maxsplit=1)[0]
    return clean_title(head)

def grab(pattern, text, flags=re.I):
    m = re.search(pattern, text, flags)
    return clean_title(m.group(1)) if m else ""

STOP = r"([^;\]\[]+?)\s*(?:;|\]|$)"
def campi(t):
    d = {}
    d["direttore"] = grab(r"(?:concertatore e direttore(?: d'orchestra)?|concertatore e direzione|maestro concertatore e direttore|maestro direttore|direttore(?: d'orchestra)?|direzione musicale|dirige)\s+(?:di\s+)?" + STOP, t)
    d["regista"] = grab(r"\bregi[ae](?:[ ,]+(?:e\s+)?(?:scene|scena|costumi|luci|e|bozzetti|figurini|ideazione))*\s*(?:di\s+)?" + STOP, t)
    d["coreografo"] = grab(r"(?:coreografi[ae]|coreografo|movimenti coreografici|movimenti mimici|ripresa coreografica)(?:\s+e\s+regia)?\s+(?:di\s+)?" + STOP, t)
    d["interpreti"] = grab(r"interpreti(?: principali)?\s*:\s*(.+?)(?:\]|$)", t)
    c = grab(r"(?:parole e musica|poema e musica|musiche?|musica)\s+(?:di\s+)?([^;\]/\[]+?)\s*(?:;|\]|/|\s\.\s|\s:\s|,\s*opus|$)", t)
    if not c:
        c = grab(r"/\s*(?:di\s+)?([A-ZÀ-Ý][\w'’.À-ÿ-]+(?:\s+(?:[A-ZÀ-Ý][\w'’.À-ÿ-]+|de|di|van|von|da))*)\s*(?:[;:\]]|$)", t, 0)
    d["compositore"] = c
    return d

def data_in(text):
    m = re.search(r"(\d{1,2})(?:\s*(?:e|-|,)\s*\d{1,2})?\s+(" + "|".join(MESI) + r")(?:\s+(\d{4}))?", text or "", re.I)
    if m:
        return m.group(0)
    return ""

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
        c = campi(t)
        # compositore dal record completo se c'e'
        nomi = f.get("nomi", [])
        comp = [re.sub(r"^\[Compositore\]\s*", "", n) for n in nomi if n.startswith("[Compositore]")]
        if comp: c["compositore"] = "; ".join(comp)
        note = " | ".join(f.get("note", []) or [])
        stag = stagione_esplicita(t + " " + (r.get("pubblicazione") or ""))
        biblio = []
        for loc in f.get("localizzazioni", []) or []:
            sm = loc.get("shelfmarks") or [{}]
            biblio.append(f"{sm[0].get('shelfmark','')} ({loc.get('isil','')})")
        rows.append(dict(
            stagione=stag, anno=anno, anno_nota=flag, tipo=cls,
            titolo=split_title(t) if cls in ("produzione", "concerto") else clean_title(re.split(r"\s+/\s+", t)[0]),
            compositore=c["compositore"], direttore=c["direttore"], regista=c["regista"], coreografo=c["coreografo"],
            interpreti=c["interpreti"], sala=sala(r, cls), data=data_in(note) or data_in(t),
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
        for fld in ("compositore", "direttore", "regista", "coreografo", "interpreti", "data", "stagione"):
            if not best[fld]:
                for x in g:
                    if x[fld]: best[fld] = x[fld]; break
        out.append(best)
    out.sort(key=lambda x: (x["anno"], x["tipo"], norm(x["titolo"])))
    cols = ["stagione", "anno", "anno_nota", "tipo", "titolo", "compositore", "direttore", "regista", "coreografo", "interpreti",
            "sala", "data", "nota_scheda", "bid", "bid_altri", "n_record", "biblioteche", "n_biblioteche", "url", "scheda_completa",
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
