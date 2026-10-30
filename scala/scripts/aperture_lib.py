"""Funzioni comuni per le prime di stagione (normalizzazione di titoli e nomi)."""
import re, unicodedata
def strip_acc(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
ART = r"^(il|lo|la|le|l|i|gli|un|una|die|der|das|le|les|the|des|du|de|di|a)\b"
def ntit(s):
    s = strip_acc(str(s)).lower()
    s = s.replace("’", "'").replace("ß", "ss")
    s = re.sub(r"\[.*?\]|\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    s = re.sub(r"\b(l|d|un|dell|all)'", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    for _ in range(2):
        s = re.sub(ART, "", s).strip()
    return s
SYN = {"valchiria": "walkure", "walkure": "walkure", "walchiria": "walkure", "crepuscolo degli dei": "gotterdammerung", "gotterdammerung": "gotterdammerung",
       "sigfrido": "siegfried", "siegfried": "siegfried", "tristano e isotta": "tristan und isolde", "tristan und isolde": "tristan und isolde",
       "flauto magico": "zauberflote", "zauberflote": "zauberflote", "die zauberflote": "zauberflote", "guglielmo tell": "guglielmo tell", "guillaume tell": "guglielmo tell",
       "maestri cantori di norimberga": "meistersinger", "oro del reno": "rheingold", "armida": "armide", "armide": "armide", "iphigenie en aulide": "ifigenia in aulide",
       "ifigenia in aulide": "ifigenia in aulide", "moise et pharaon": "mose", "mose": "mose", "mose in egitto": "mose", "europa riconosciuta": "europa riconosciuta",
       "carmen": "carmen", "lucia": "lucia di lammermoor", "battaglia": "battaglia di legnano", "tosca": "tosca"}
def kt(s):
    n = ntit(s)
    for k, v in SYN.items():
        if n == k or n.startswith(k + " "): return v
    return n
def sim(a, b):
    from difflib import SequenceMatcher
    a, b = kt(a), kt(b)
    if not a or not b: return 0.0
    if a == b: return 1.0
    if a in b or b in a:
        return 0.9 if min(len(a), len(b)) >= 5 else 0.5
    return SequenceMatcher(None, a, b).ratio()
def surname(n):
    n = strip_acc(str(n)).lower()
    n = re.sub(r"\(.*?\)", "", n)
    parts = [p for p in re.split(r"[ ,;/]+", n) if p]
    out = []
    for p in parts:
        if p in ("de", "di", "van", "von", "da", "del", "della", "le", "la"): continue
        out.append(p)
    r = out[-1] if out else ""
    return {"tcherniakov": "cernjakov", "ljubimov": "ljubimov", "kabaiwanska": "kabaivanska", "wallmann": "wallmann", "musorgskij": "musorgskij"}.get(r, r)
def same_person(a, b):
    sa = surname(a); sb = surname(b)
    if not sa or not sb: return None
    return sa == sb or sa in strip_acc(str(b)).lower() or sb in strip_acc(str(a)).lower()
