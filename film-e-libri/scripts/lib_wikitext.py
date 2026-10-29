"""Lettura del wikitext salvato in raw/wikitext/: sezioni, testo pulito, link, frasi."""
import os, re, json, glob
from lib_luoghi import norm

def carica_articoli(base):
    """-> {(lang, titolo_richiesto): (titolo_finale, wikitext)}"""
    res = {}
    for f in sorted(glob.glob(os.path.join(base, "raw", "wikitext", "??_?????.json"))):
        lang = os.path.basename(f)[:2]
        d = json.load(open(f, encoding="utf8"))
        q = d["query"]
        mapa = {}
        for n in q.get("normalized", []): mapa[n["from"]] = n["to"]
        red = {r["from"]: r["to"] for r in q.get("redirects", [])}
        pagine = {p["title"]: p for p in q["pages"]}
        for rich in d["_richiesti"]:
            t = mapa.get(rich, rich)
            t = red.get(t, t)
            p = pagine.get(t)
            if p and not p.get("missing") and p.get("revisions"):
                res[(lang, rich)] = (t, p["revisions"][0]["slots"]["main"]["content"])
    return res

def _rimuovi_annidati(s, apri, chiudi, ok=None):
    """Rimuove blocchi annidati apri...chiudi (es. {{ }}); se ok(testo) torna una stringa la sostituisce."""
    out = []; i = 0; n = len(s)
    while i < n:
        if s.startswith(apri, i):
            depth = 0; j = i
            while j < n:
                if s.startswith(apri, j): depth += 1; j += len(apri)
                elif s.startswith(chiudi, j):
                    depth -= 1; j += len(chiudi)
                    if depth == 0: break
                else: j += 1
            blocco = s[i:j]
            if ok:
                r = ok(blocco)
                if r: out.append(r)
            i = j
        else:
            out.append(s[i]); i += 1
    return "".join(out)

FILE_RE = re.compile(r"^\[\[\s*(file|immagine|image|categoria|category|media)\s*:", re.I)
def pulisci(w):
    w = re.sub(r"<!--.*?-->", "", w, flags=re.S)
    w = re.sub(r"<ref[^>/]*/>", "", w)
    w = re.sub(r"<ref[^>]*>.*?</ref>", "", w, flags=re.S)
    w = re.sub(r"<(gallery|timeline|math|syntaxhighlight|source|imagemap)[^>]*>.*?</\1>", "", w, flags=re.S | re.I)
    w = _rimuovi_annidati(w, "{{", "}}")
    w = _rimuovi_annidati(w, "{|", "|}")
    w = _rimuovi_annidati(w, "[[", "]]", ok=lambda b: None if FILE_RE.match(b) else _keep_link(b))
    w = re.sub(r"<br\s*/?>", " ", w, flags=re.I)
    w = re.sub(r"</?[a-zA-Z][^>]*>", "", w)
    w = w.replace("'''", "").replace("''", "")
    w = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", w)
    w = re.sub(r"\[https?://\S+\]", "", w)
    return w
def _keep_link(b):
    # i link annidati dentro un link normale (rari) si lasciano com'e
    return b

HEAD = re.compile(r"^(={2,6})\s*(.*?)\s*\1\s*$", re.M)
def sezioni(w):
    """Lista di (livello, titolo, testo grezzo) con la voce iniziale come (1, '', testo)."""
    out = []; pos = 0; cur = (1, "", 0)
    for m in HEAD.finditer(w):
        out.append((cur[0], cur[1], w[cur[2]:m.start()]))
        cur = (len(m.group(1)), m.group(2), m.end())
    out.append((cur[0], cur[1], w[cur[2]:]))
    return out

LINK = re.compile(r"\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|([^\[\]]*))?\]\]")
def paragrafi(testo):
    """testo pulito -> lista di (testo_piano, [(s,e,target)])"""
    res = []
    for riga in testo.split("\n"):
        riga = riga.strip()
        if not riga or riga.startswith(("__", "=")): continue
        riga = riga.lstrip("*#:; ").strip()
        spans = []; out = []; last = 0; pos = 0
        for m in LINK.finditer(riga):
            out.append(riga[last:m.start()]); pos += m.start() - last
            vis = (m.group(2) if m.group(2) is not None else m.group(1)).strip()
            if re.match(r"^\s*(file|immagine|image|categoria|category)\s*:", m.group(1), re.I): vis = ""
            else: spans.append((pos, pos + len(vis), m.group(1).strip()))
            out.append(vis); pos += len(vis); last = m.end()
        out.append(riga[last:])
        piano = "".join(out)
        piano = re.sub(r"\[\[|\]\]", "", piano)
        if len(piano) > 20: res.append((piano, spans))
    return res

SENT_END = re.compile(r"(?<=[.!?])[\"'»)]*\s+(?=[A-Z0-9\"«(])")
def frasi(piano):
    """-> lista di (start, end)"""
    out = []; i = 0
    for m in SENT_END.finditer(piano):
        # evita di spezzare dopo abbreviazioni tipiche (Dr. S. ecc.)
        prev = piano[max(0, m.start()-4):m.start()+1]
        if re.search(r"(\b[A-Z]\.|\bDr\.|\bSig\.|\bSt\.|\bMr\.|\bMrs\.|\bn\.|\bvia\.|\bec\.)$", prev): continue
        out.append((i, m.start()+1)); i = m.end()
    out.append((i, len(piano)))
    return [(a, b) for a, b in out if b - a > 8]

# ---------- classificazione sezioni
EXCL = re.compile(r"(collegamenti esterni|external links|note|notes|references|bibliografia|bibliography|voci correlate|see also|altri progetti|riconoscimenti|premi|awards|accolta|accoglienza|reception|critica|critical|incassi|box office|distribuzione|release|home video|colonna sonora|soundtrack|tracce|cast|interpreti|edizioni|editions|publication|storia editoriale|remake|sequel|cultural|influenza|adattament|adaptation|further reading|sources|fonti)")
RIPRESE = re.compile(r"(ripres|filming|photography|girat|location|set design|scenograf)")
PROD = re.compile(r"(produzione|production|sviluppo|development|genesi|realizzazione|preparazione|curiosit|trivia|background|origini|scrittura|writing|pre-production|retroscena|note di produzione)")
TRAMA = re.compile(r"(trama|plot|synopsis|sinossi|contenuto|riassunto|argomento|soggetto|summary|premise|premessa|^storia$|^story$|racconto|sviluppo della trama|episodi|personaggi|characters|ambientazione|setting|luoghi|contesto|content)")
def classifica_sezione(titolo, ereditata):
    t = norm(titolo)
    if t == "": return "intro"
    if RIPRESE.search(t): return "riprese"
    if PROD.search(t): return "produzione"
    if TRAMA.search(t): return "trama"
    if EXCL.search(t): return None
    return ereditata   # sottosezione senza nome noto: eredita
