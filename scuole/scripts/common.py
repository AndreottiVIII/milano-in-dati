"""Funzioni comuni (indirizzi, percentuali)."""
import re, unicodedata
STOP = set("VIA VIALE V VLE CORSO CSO C SO PIAZZA P ZZA PZA PIAZZALE PLE LARGO LGO L GO N SNC DI DEL DELLA DELLE DEI DEGLI DELL DA D A E LO LA IL GLI LE AL ALLA ALLE ALL SAN S SANTA SANTO ST BIS".split())
def _strip(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9 ]", " ", s)
TIPI_VIA = r"\b(VIA|VIALE|VLE|PIAZZA|CORSO|CSO|LARGO)\b"
def addr_key(addr):
    """(frozenset di parole della via, civico) da un indirizzo. Con piu' sedi nello stesso campo tiene la prima."""
    raw = str(addr)
    if re.search(r"\(\s*ORD", raw, re.I):
        raw = re.split(r"\(\s*ORD", raw, flags=re.I)[0]
    elif len(re.findall(TIPI_VIA, raw, re.I)) >= 2:
        raw = re.split(r"\s*-\s*", raw)[0]
    s = _strip(raw)
    s = re.sub(r"([A-Z])(\d)", r"\1 \2", s)  # "GONZAGA4" -> "GONZAGA 4"
    s = re.sub(r"\bN\s*(\d)", r" \1", s)
    toks = s.split()
    civ = None
    i = len(toks)
    while i > 0 and re.match(r"^\d", toks[i - 1]):  # coda numerica: "17/19" -> 17
        i -= 1
    if i < len(toks):
        civ = re.match(r"^(\d+)", toks[i]).group(1)
    else:  # numero in mezzo ("VIA X 12 BIS"): primo numero da destra
        for t in reversed(toks):
            m = re.match(r"^(\d+)", t)
            if m:
                civ = m.group(1)
                break
    words = [t for t in toks if not re.match(r"^\d", t) and t not in STOP and len(t) > 1]
    return frozenset(words), civ
def pct(a, b):
    return None if not b else round(100.0 * a / b, 2)
