"""Legge le iscrizioni delle lapidi (tag OSM `inscription`) e ricava la persona SOLO quando il testo ne scrive il nome per esteso.
Metodo prudente: si prendono le sequenze di 2-4 parole con la maiuscola ("Giulio Natta"), si cercano su Wikidata e si accetta una corrispondenza esatta con UNA persona.
Se nel testo ci sono piu' persone riconosciute, l'opera NON riceve un soggetto (resta 'piu' persone nominate'). Le iscrizioni tutte in maiuscolo non si leggono (non si distinguono i nomi).
Il sesso viene poi dal campo P21 di Wikidata, mai dal nome.
Uso: python -I -X utf8 06b_soggetti_da_iscrizioni.py <statue>
Legge pulito/_lavoro/stage2.json, scrive stage3.json e pulito/_lavoro/iscrizioni_soggetti.csv"""
import sys, os, re, json, time, csv, collections, requests
S = sys.argv[1]
sys.path.insert(0, os.path.join(S, "scripts"))
from wdlib import WD, norm
UA = {"User-Agent": "milano-in-dati/0.3 (davide.caniatti@gmail.com; research on statues and monuments in Milan)"}
CF = os.path.join(S, "raw/wikidata/entities_cache.json")
wd = WD(CF)
SF = os.path.join(S, "raw/wikidata/search_cache.json")
sc = json.load(open(SF, encoding="utf8")) if os.path.exists(SF) else {}
SLF = os.path.join(S, "raw/wikidata/sitelinks_cache.json")
slc = json.load(open(SLF, encoding="utf8")) if os.path.exists(SLF) else {}
works = json.load(open(os.path.join(S, "pulito/_lavoro/stage2.json"), encoding="utf8"))
ITA = {"Q38", "Q172579", "Q165154", "Q15913", "Q1384446", "Q23402", "Q9068", "Q2500325", "Q27306", "Q4948", "Q150509"}
PART = {"de", "di", "da", "del", "della", "dei", "degli", "dal", "dalla", "van", "von", "la", "le", "d'", "d’", "du", "des"}
TITLES = {"mons.", "monsignor", "monsignore", "marchese", "conte", "duca", "generale", "dottor", "dottore", "ingegnere", "cavalier", "cavaliere", "don", "padre", "fra", "il", "la", "presidente", "ragioniere", "commissario", "maestro", "cardinale", "beato", "san", "santo", "santa", "sant'", "sant’", "prof.", "professor", "avv.", "avvocato", "on.", "senatore", "contessa", "principe", "re", "papa", "capitano", "colonnello", "tenente", "maggiore", "sergente", "dott.", "ing."}
STOPS = {"milano", "città", "comune", "via", "piazza", "casa", "qui", "questa", "questo", "palazzo", "nobel", "premio", "associazione", "gloria", "italia", "italiano", "italiana", "stato", "maggiore", "guardia", "pubblica", "sicurezza", "reparto", "celere", "medaglia", "resistenza", "liberazione", "mazzini"}
ROMAN = re.compile(r"^(?=[IVXLCDM]{2,}$)M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
WORD = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-]*\.?|[,;:/()\"“”«»]|\d+")

def seqs(text):
    """sequenze di parole con la maiuscola (2-4), con particelle in mezzo"""
    letters = [c for c in text if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) / len(letters) > 0.55: return []  # tutto maiuscolo: non si leggono i nomi
    toks = WORD.findall(text.replace("|", " / ").replace("\n", " / "))
    out, cur, pend = [], [], []
    def flush():
        nonlocal cur, pend
        if len([t for t in cur if t.lower() not in PART]) >= 2: out.append(list(cur))
        cur, pend = [], []
    for t in toks:
        tl = t.lower()
        if re.fullmatch(r"[,;:/()\"“”«»]|\d+", t): flush(); continue
        if ROMAN.match(t): flush(); continue
        if re.match(r"[A-ZÀ-Ý]", t) and (len(t) > 2 or t.endswith(".")) and tl not in ("il", "la", "in", "per", "qui", "che", "con", "dal", "del", "dei", "gli", "una", "nel", "alla"):
            cur += pend; pend = []; cur.append(t)
        elif cur and tl in PART:
            pend.append(t)
        else:
            flush()
    flush()
    res = []
    for sq in out:
        # togli i titoli iniziali
        while sq and sq[0].lower() in TITLES: sq = sq[1:]
        sq = [t.rstrip(".") if not re.fullmatch(r"[A-Z]\.", t) else t for t in sq]
        core = [t for t in sq if t.lower() not in PART]
        if 2 <= len(core) <= 4 and not any(t.lower() in STOPS for t in core): res.append(" ".join(sq))
    seen = []
    for r in res:
        w_ = r.split(" ")
        cands_ = [r]
        core_n = len([t for t in w_ if t.lower() not in PART])
        if core_n >= 3:  # "Ornella Vanoni Cantante Artista": prova anche le finestre iniziali e finali
            for n_ in (2, 3):
                if n_ < core_n:
                    cands_.append(" ".join(w_[:n_] if not any(t.lower() in PART for t in w_[:n_ + 1]) else w_[:n_ + 1]))
                    cands_.append(" ".join(w_[-n_:]))
        for c_ in cands_:
            if c_ not in seen and len(c_.split()) >= 2: seen.append(c_)
    return seen

def search(q):
    if q in sc: return sc[q]
    for a in range(8):
        r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbsearchentities", search=q, language="it", uselang="it", type="item", limit=10, format="json"), headers=UA, timeout=60)
        j = r.json() if r.status_code == 200 else {}
        if "search" in j and "error" not in j:
            sc[q] = [dict(id=x["id"], label=x.get("label", ""), desc=x.get("description", ""), match=x.get("match", {}).get("text", "")) for x in j["search"]]
            time.sleep(0.4)
            return sc[q]
        time.sleep(min(60, 4 * 2 ** a))
    sc[q] = None
    return None
def fetch(qs):
    need = sorted({q for q in qs if re.fullmatch(r"Q\d+", q)} - set(wd.C), key=lambda x: int(x[1:]))
    for i in range(0, len(need), 50):
        for a in range(8):
            r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbgetentities", ids="|".join(need[i:i + 50]), props="labels|descriptions|claims", languages="it|en", format="json"), headers=UA, timeout=90)
            j = r.json() if r.status_code == 200 else {}
            if "entities" in j: wd.C.update(j["entities"]); break
            time.sleep(min(60, 4 * 2 ** a))
        time.sleep(1)
def sitelinks(qs):
    need = [q for q in qs if q not in slc]
    for i in range(0, len(need), 50):
        for a in range(8):
            r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbgetentities", ids="|".join(need[i:i + 50]), props="sitelinks", format="json"), headers=UA, timeout=90)
            j = r.json() if r.status_code == 200 else {}
            if "entities" in j:
                for q, e in j["entities"].items(): slc[q] = len(e.get("sitelinks", {}))
                break
            time.sleep(min(60, 4 * 2 ** a))
    json.dump(slc, open(SLF, "w"))
    return {q: slc.get(q, 0) for q in qs}

todo = []
for w in works:
    t = w.get("osm_tags", {})
    ins = t.get("inscription", "")
    if not ins or w["subj_persone_struct"] or w.get("subj_persone_nome"): continue
    sq = seqs(ins)
    if sq: todo.append((w, sq))
print("opere con iscrizione leggibile e senza soggetto:", len(todo), flush=True)
queries = sorted({s for _, sq in todo for s in sq})
print("ricerche:", len(queries), "(in cache:", sum(q in sc for q in queries), ")", flush=True)
for i, q in enumerate(queries):
    search(q)
    if i % 25 == 0: json.dump(sc, open(SF, "w", encoding="utf8"), ensure_ascii=False); print(i, flush=True)
json.dump(sc, open(SF, "w", encoding="utf8"), ensure_ascii=False)
exact = {q: [x["id"] for x in (sc.get(q) or []) if norm(x["match"] or x["label"]) == norm(q) or norm(x["label"]) == norm(q)] for q in queries}
fetch({i for v in exact.values() for i in v})
refs = set()
for v in exact.values():
    for i in v:
        for p in ("P106", "P27", "P21", "P31", "P411"): refs |= set(wd.ids(i, p))
fetch(refs)
json.dump(wd.C, open(CF, "w", encoding="utf8"), ensure_ascii=False)

def resolve(q):
    hum = [i for i in exact.get(q, []) if wd.is_human(i) and not wd.nonreal(i)]
    if len(hum) == 1: return hum[0], "nome_unico"
    if len(hum) > 1:
        it = [i for i in hum if set(wd.ids(i, "P27")) & ITA]
        if len(it) == 1: return it[0], "unico_italiano_tra_omonimi"
        sl = sitelinks(hum); o = sorted(hum, key=lambda i: -sl.get(i, 0))
        if sl.get(o[0], 0) >= 15 and sl.get(o[0], 0) >= 5 * max(1, sl.get(o[1], 0)): return o[0], "omonimo_molto_piu_noto"
    return None, "nessuno" if not hum else "omonimi"
rows = []
for w, sq in todo:
    found = {}
    for s_ in sq:
        q, m = resolve(s_)
        if q: found.setdefault(q, (s_, m))
    w["subj_persone_iscrizione"] = None
    # se una sequenza e' contenuta in un'altra ("Giuseppe Crivelli" in "Giuseppe Crivelli Serbelloni") vale la piu' lunga
    found = {q: v for q, v in found.items() if not any(v[0] != v2[0] and v[0] in v2[0] for q2, v2 in found.items() if q2 != q)}
    if len(found) == 1:
        q, (s_, m) = next(iter(found.items()))
        # coerenza: la persona non puo' essere nata dopo l'anno della targa/opera
        b = [y for y, p in wd.times(q, "P569")]
        if w["anno"] and b and min(b) > w["anno"]: esito, motivo = "scartato", "nata dopo la posa"
        else:
            w["subj_persone_iscrizione"] = dict(qid=q, metodo=m, testo=s_); esito, motivo = "accettato", m
    elif len(found) > 1: esito, motivo = "non assegnato", "piu' persone nominate"
    else: esito, motivo = "non assegnato", "nessuna persona su Wikidata"
    rows.append(dict(id=w["id"], tipo=w["tipo"], nome=w["nome"], osm=" ".join(w["osm"]), sequenze=" | ".join(sq), persone_trovate=" | ".join(f"{wd.lab(q)} ({q})" for q in found), esito=esito, motivo=motivo,
                     iscrizione=w["osm_tags"]["inscription"].replace("\n", " / ")[:300]))
with open(os.path.join(S, "pulito/_lavoro/iscrizioni_soggetti.csv"), "w", newline="", encoding="utf-8-sig") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
json.dump(works, open(os.path.join(S, "pulito/_lavoro/stage3.json"), "w", encoding="utf8"), ensure_ascii=False)
print(collections.Counter(r["esito"] + ": " + r["motivo"] for r in rows).most_common())
