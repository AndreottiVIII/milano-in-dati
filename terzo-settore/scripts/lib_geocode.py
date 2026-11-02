"""Funzioni comuni: normalizzazione di nomi e indirizzi, geocodifica sul file dei civici del Comune (ds634).
Importato dagli altri script con sys.path.insert(0, cartella scripts)."""
import re, unicodedata, csv, math, collections

def sa(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c))

PART = {"di", "del", "della", "dello", "dei", "degli", "delle", "da", "de", "dal", "dalla", "alla", "al", "allo", "ai", "agli", "alle", "dell", "d", "l", "la", "il", "lo", "le", "i", "e", "ed", "in", "su", "a", "san", "s", "ss", "sn"}
TIPI = {"via", "viale", "corso", "piazza", "piazzale", "largo", "galleria", "foro", "alzaia", "ripa", "vicolo", "bastioni", "piazzetta", "passaggio", "strada", "parco", "cavalcavia", "giardino", "sottopasso",
        "vle", "cso", "pza", "pzza", "ple", "lgo", "gall", "vl", "p", "c", "v", "l", "g"}
ABBR = [(r"\bv\.?\s?le\b", "viale"), (r"\bc\.?\s?so\b", "corso"), (r"\bp\.?\s?zza\b", "piazza"), (r"\bp\.?\s?za\b", "piazza"), (r"\bp\.?\s?le\b", "piazzale"), (r"\bl\.?\s?go\b", "largo"), (r"\bgall\.", "galleria"), (r"\bs\.\s?", "san "), (r"\bss\.\s?", "santi ")]

TIPO_ABBR = {"vle": "viale", "v.le": "viale", "cso": "corso", "c.so": "corso", "pza": "piazza", "p.za": "piazza", "p.zza": "piazza", "pzza": "piazza", "ple": "piazzale", "p.le": "piazzale", "lgo": "largo", "l.go": "largo", "gall.": "galleria", "gall": "galleria"}
def tipo_query(street):
    t = sa(street).lower().split()
    if not t: return None
    w = t[0]
    w = TIPO_ABBR.get(w, w)
    return w if w in {"via", "viale", "corso", "piazza", "piazzale", "largo", "galleria", "foro", "alzaia", "ripa", "vicolo", "bastioni", "piazzetta", "passaggio", "strada"} else None

def toks_street(s):
    s = sa(s).lower()
    for a, b in ABBR: s = re.sub(a, b, s)
    s = re.sub(r"[^a-z0-9' ]", " ", s).replace("'", " ")
    t = [w for w in s.split() if w not in PART and w not in TIPI and not w.isdigit()]
    # niente iniziali (1 lettera); tengo i token >=2
    return frozenset(w for w in t if len(w) >= 2)

def parse_ind(ind):
    """-> (street_text, civico_num:int|None, lettera:str, ok)"""
    s = (ind or "").strip()
    if "#" in s:
        main, resto = s.split("#", 1)
        m2 = re.search(r",\s*(\d+)\s*$", resto)
        s = main.strip() if (re.search(r"\d", main) or not m2) else main.strip() + " " + m2.group(1)
    s = re.split(r"\bRECAPITO\b", s, flags=re.I)[0].strip()
    s = s.replace(" ,", ",")
    m = re.search(r"(\d+)\s*[/ -]?\s*([A-Za-z])?\s*(?:/\s*\S+)?\s*(?:INT\.?\s*\S+)?\s*$", s)
    if not m: return s, None, ""
    street = s[:m.start()].strip(" ,")
    return street, int(m.group(1)), (m.group(2) or "").upper()

class Geocoder:
    def __init__(self, path):
        r = csv.DictReader(open(path, encoding="utf-8-sig"), delimiter=";")
        self.strade = {}   # codice_via -> tokens
        self.tipo = {}
        self.punti = collections.defaultdict(list)  # (codice_via, num) -> [(lett, lon, lat, nil, idnil, stato)]
        for x in r:
            if x["STATOCIVICO"] != "Applicato": continue
            cv = x["CODICE_VIA"]
            if cv not in self.strade:
                self.strade[cv] = toks_street(x["DESCRITTIVO"]) | toks_street(x["DENOMINAZIONE"])
                self.tipo[cv] = x["TIPO"].lower().split()[0]
            try: n = int(x["NUMERO"])
            except: continue
            self.punti[(cv, n)].append((x["LETTERA"].strip().upper(), float(x["LONG_WGS84"]), float(x["LAT_WGS84"]), x["NIL"], x["ID_NIL"]))
        self.inv = collections.defaultdict(set)
        for cv, t in self.strade.items():
            for w in t: self.inv[w].add(cv)
    def trova_via(self, street):
        t = toks_street(street)
        if not t: return None, 0
        tq = tipo_query(street)
        cand = collections.Counter()
        t2 = set()
        for w in t:
            if w in self.inv:
                t2.add(w)
                for cv in sorted(self.inv[w]): cand[cv] += 1
            elif len(w) >= 3:   # abbreviazione (es. "ang." -> angelico)
                ks = sorted(k for k in self.inv if k.startswith(w))
                if len(ks) <= 6:
                    for k in ks:
                        t2.add(k)
                        for cv in sorted(self.inv[k]): cand[cv] += 1
        t = frozenset(t2) if len(t2) >= len(t) * 0.5 else t
        best, bs = None, 0
        for cv, c in sorted(cand.items(), key=lambda kv: (-kv[1], kv[0]))[:40]:
            u = self.strade[cv]
            j = len(t & u) / len(t | u)
            if tq and self.tipo.get(cv) != tq: j -= 0.3
            # accetto anche se t e' contenuto in u (es. "venezia" in "porta venezia")? no: richiedo j alto
            if j > bs: best, bs = cv, j
        return best, bs
    def geocodifica(self, ind):
        """-> dict(lon, lat, nil, idnil, esito) ; esito: ok / ok_senza_lettera / civico_non_trovato / via_non_trovata / senza_civico"""
        street, n, let = parse_ind(ind)
        if n is None: return dict(esito="senza_civico")
        cv, j = self.trova_via(street)
        if cv is None or j < 0.5: return dict(esito="via_non_trovata", via_j=round(j, 2))
        pts = self.punti.get((cv, n))
        if not pts:
            return dict(esito="civico_non_trovato", via_j=round(j, 2))
        ex = [p for p in pts if p[0] == let] if let else [p for p in pts if p[0] == ""]
        esito = "ok"
        if not ex:
            ex = pts; esito = "ok_senza_lettera"
        lon = sum(p[1] for p in ex) / len(ex); lat = sum(p[2] for p in ex) / len(ex)
        return dict(lon=lon, lat=lat, nil=ex[0][3], idnil=ex[0][4], esito=esito, via_j=round(j, 2))

def dist_m(lon1, lat1, lon2, lat2):
    k = 111320.0
    dx = (lon1 - lon2) * k * math.cos(math.radians((lat1 + lat2) / 2)); dy = (lat1 - lat2) * k
    return math.hypot(dx, dy)

STOPN = PART | {"snc", "srl", "sas", "spa", "s", "n", "c", "ditta", "individuale", "casa", "fondata", "nel", "dal", "dott", "dottor", "f.lli", "fratelli", "fli", "figli", "sig", "soc", "societa", "coop", "di", "antica", "storica", "dal", "negozio", "bottega", "srls", "sapa", "sacs", "sdf", "ss", "unipersonale", "co"}
def toks_nome(s):
    s = sa(s).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s.replace("'", " "))
    return frozenset(w for w in s.split() if w not in STOPN and len(w) >= 2 and not (w.isdigit() and len(w) == 4))

def sim_nome(a, b):
    ta, tb = toks_nome(a), toks_nome(b)
    if not ta or not tb: return 0.0
    inter = len(ta & tb)
    return max(inter / len(ta | tb), 0.8 * inter / min(len(ta), len(tb)))
