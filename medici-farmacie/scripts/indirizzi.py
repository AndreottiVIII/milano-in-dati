"""Funzioni comuni: pulizia e confronto degli indirizzi con i civici del Comune (ds634)."""
import re, unicodedata, difflib
import pandas as pd

PREFISSI = {"VIA", "VIALE", "VLE", "V", "LE", "PIAZZA", "PZZA", "PZA", "PIAZZALE", "CORSO", "CSO", "C", "SO", "LARGO", "L", "GO", "VICOLO", "VIC",
            "STRADA", "STR", "VIOLETTO", "ALZAIA", "PIAZZETTA", "GALLERIA", "FOROPAD", "BASTIONI", "CIRCONVALLAZIONE", "CIRC", "RIPA", "SALITA", "RACCORDO",
            "VIA", "P", "ZZA", "ZZALE", "ZA", "ZALE"}
ARTICOLI = {"DI", "DE", "DEL", "DELLA", "DELLE", "DEI", "DEGLI", "DELL", "D", "LA", "IL", "LO", "L", "SAN", "SANTA", "SANT", "S", "SS", "DA", "E"}

def _norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    s = s.replace("'", " ").replace(".", " ").replace(",", " ").replace("-", " ").replace("(", " ").replace(")", " ")
    return re.sub(r"\s+", " ", s).strip()

def token_via(s, tieni_santi=False):
    t = _norm(s).split()
    out = []
    for i, w in enumerate(t):
        if i == 0 and w in PREFISSI:
            continue
        if w in {"SAN", "SANTA", "SANT", "SS"} and not tieni_santi:
            continue
        if len(w) <= 1 or w in {"DI", "DE", "DEL", "DELLA", "DELLE", "DEI", "DEGLI", "DELL", "LA", "IL", "LO", "DA", "E"}:
            continue
        out.append(w)
    return frozenset(out)

def spezza_indirizzo(ind):
    """'Via A. Saffi, 6' -> (token, numero). Il numero e' la prima cifra dopo l'ultima virgola o in fondo."""
    s = str(ind)
    m = re.search(r"(\d+)\s*([A-Za-z]?)\s*(?:[/\-].*)?$", s)
    num = m.group(1) if m else None
    nome = s[:m.start()] if m else s
    return token_via(nome), num

def indice_civici(civici_df):
    """civici_df con DENOMINAZIONE, NUMEROCOMPLETO, lon, lat, ID_NIL -> dizionario (token) -> lista"""
    idx = {}
    for r in civici_df.itertuples(index=False):
        k = token_via(r.DENOMINAZIONE)
        n = re.match(r"0*(\d+)", str(r.NUMEROCOMPLETO))
        if not n:
            continue
        idx.setdefault((k, n.group(1)), []).append((float(r.lon), float(r.lat), int(r.ID_NIL) if pd.notna(r.ID_NIL) else None))
    return idx

def trova(idx, ind):
    """Cerca l'indirizzo tra i civici: prima corrispondenza esatta dei token, poi token dell'indirizzo contenuti
    in quelli del civico (es. 'Stradivari' in 'STRADIVARI ANTONIO'); accetta solo se tutti i candidati cadono nello stesso NIL."""
    k, n = spezza_indirizzo(ind)
    if not k or n is None:
        return None
    v = idx.get((k, n))
    tipo = "esatto"
    if not v:
        v = []
        for (kk, nn), vv in idx.items():
            if nn == n and k <= kk:
                v.extend(vv)
        tipo = "contenuto"
        if not v:
            # ultima prova: errori di battitura (Cecov / Cechov): ogni token dell'indirizzo deve somigliare (>= 0.8) a un token del civico
            for (kk, nn), vv in idx.items():
                if nn == n and all(any(difflib.SequenceMatcher(None, a, b).ratio() >= 0.8 for b in kk) for a in k):
                    v.extend(vv)
            tipo = "simile"
        if len({x[2] for x in v}) != 1:
            return None
    return (sum(x[0] for x in v) / len(v), sum(x[1] for x in v) / len(v), v[0][2], tipo)
