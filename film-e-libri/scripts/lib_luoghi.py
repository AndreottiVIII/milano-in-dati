"""Funzioni comuni: normalizzazione testo."""
import re, unicodedata
def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()
TOK = re.compile(r"[^\W_]+", re.U)
def tokens(s):
    return [norm(t) for t in TOK.findall(s)]
ARTICOLI = {"del","della","dello","dei","degli","delle","di","d","dell","da","de","il","la","lo","le","l","i","gli","al","alla","ai","dal","dalla","nel","nella","sul","sulla"}
