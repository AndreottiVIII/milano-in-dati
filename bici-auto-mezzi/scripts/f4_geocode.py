"""Fase 4: geocodifica degli incidenti, estende f2_geocode.Geocoder con (1) ricerca approssimata del nome della via
(nomi di battesimo abbreviati o mancanti, 'S.' = san/santa), (2) incrocio di ripiego dal registro dei civici.
Ogni risposta ha un livello: civico | civico_approx | incrocio | incrocio_approx | strada | nessuna"""
import re, numpy as np
import f2_geocode as G
from f2_geocode import Geocoder, split_tipo, strip_acc

# --- normalizzazione dei nomi piu tollerante (vale per il registro dei civici e per OSM, stesse regole sui due lati)
_tok0 = G.tokens
ROMANI = {'secondo': 'ii', 'terzo': 'iii', 'quarto': 'iv', 'quinto': 'v', 'sesto': 'vi', 'settimo': 'vii', 'ottavo': 'viii', 'nono': 'ix',
          'decimo': 'x', 'undicesimo': 'xi', 'dodicesimo': 'xii', 'tredicesimo': 'xiii', 'ventitreesimo': 'xxiii'}
VARIANTI = {'lodovico': 'ludovico', 'niccolo': 'nicolo', 'nicolo': 'nicolo', 'giovan': 'giovanni', 'fli': 'fratelli', 'lli': 'fratelli'}
def tokens(s):
    t = strip_acc(str(s).lower())
    t = re.sub(r'f\.?\s?lli', 'fratelli', t); t = re.sub(r'g\.\s?b\.?', 'giovanni battista', t)
    out = []
    for w in _tok0(t):
        w = ROMANI.get(w, VARIANTI.get(w, w))
        if len(w) == 1 and w not in ('v', 'x'): continue
        out.append(w)
    return out
G.tokens = tokens

PICCOLE = {'del', 'della', 'dello', 'dei', 'degli', 'delle', 'di', 'da', 'de', 'dal', 'dalla', 'dalle', 'dai', 'e', 'al', 'alla', 'in', 'sul', 'sulla', 'la', 'il', 'lo', 'le', 'i', 'gli'}
def bel_nome(tipo, dsc):
    """'Piazza', 'DEL DUOMO' -> 'piazza del Duomo'"""
    w = []
    for x in str(dsc).strip().split():
        xl = x.lower()
        if xl in PICCOLE: w.append(xl)
        elif "'" in xl:
            a_, b_ = xl.split("'", 1)
            if not b_: w.append(a_[:1].upper() + a_[1:] + "'")
            elif a_ in ('d', 'dell', 'dall', 'all', 'nell', 'sull', 'l'): w.append(a_ + "'" + b_[:1].upper() + b_[1:])
            else: w.append(a_[:1].upper() + a_[1:] + "'" + b_[:1].upper() + b_[1:])
        else: w.append(xl[:1].upper() + xl[1:])
    return (str(tipo).lower() + ' ' + ' '.join(w)).strip()

class Geocoder4(Geocoder):
    def __init__(self, S):
        super().__init__(S)
        import glob, pandas as pd
        c = pd.read_csv(glob.glob(S + '/../citta-15-minuti/raw/comune_milano/civici/estratto/*.csv')[0], sep=';', dtype=str, usecols=['TIPO', 'DESCRITTIVO', 'STATOCIVICO'])
        c = c[c.STATOCIVICO == 'Applicato'].drop_duplicates(['TIPO', 'DESCRITTIVO'])
        self.regname = {}
        for tipo, dsc in zip(c.TIPO, c.DESCRITTIVO):
            self.regname[(str(tipo).lower(), frozenset(tokens(dsc)))] = bel_nome(tipo, dsc)
        self.fuzzy = False; self.multi = False; self.approx = False
    def _fuzzy(self, tipo, tk, table, idx):
        toks = list(dict.fromkeys(tk))
        if not toks: return None
        pos = [t for t in toks if len(t) >= 3 and idx.get(t)]
        if not pos: return None
        longest = min(pos, key=lambda t: (len(idx[t]), -len(t)))
        cand = set(idx.get(longest, ()))
        if len(longest) >= 5:
            for t_, ks_ in idx.items():
                if t_ != longest and len(t_) >= 5 and (t_.startswith(longest) or longest.startswith(t_)): cand |= ks_
        best = []; bs = None
        for k in cand:
            kt = k[1]
            cov = sum(1 for q in toks if any(q == x or (len(q) >= 3 and len(x) >= 3 and (x.startswith(q) or q.startswith(x))) for x in kt))
            kcov = sum(1 for x in kt if any(q == x or (len(q) >= 3 and len(x) >= 3 and (x.startswith(q) or q.startswith(x))) for q in toks))
            ok_ = (kcov == len(kt)) or (cov == len(toks)) or (len(toks) >= 3 and len(kt) >= 3 and cov >= len(toks) - 1 and kcov >= len(kt) - 1)
            if not ok_ or longest not in kt: continue
            tp = 1 if (tipo is None or k[0] is None or k[0] == tipo) else 0
            if not tp and cov < len(toks): continue
            sc = (cov + kcov, tp)
            if bs is None or sc > bs: bs = sc; best = [k]
            elif sc == bs: best.append(k)
        if len(best) == 1: return best[0]
        return None
    def _find(self, tipo, tk, table, by_tokens):
        k = super()._find(tipo, tk, table, by_tokens)
        if k is not None: return k
        idx = self.tok_street if table is self.street else self.tok_osm
        k = self._fuzzy(tipo, tk, table, idx)
        if k is not None: self.fuzzy = True
        return k
    def _tree_reg(self, key):
        if not hasattr(self, '_trc'): self._trc = {}
        if key not in self._trc:
            from scipy.spatial import cKDTree
            p = np.array(self.street[key]['pts']); x, y = self.tr.transform(p[:, 0], p[:, 1]); self._trc[key] = cKDTree(np.c_[x, y])
        return self._trc[key]
    def osm_keys(self, tipo, tk):
        """tutte le varianti plausibili del nome della via in OSM (stesso insieme di parole, oppure incluso uno nell'altro)"""
        fs = frozenset(tk); ks = set()
        if (tipo, fs) in self.osm: ks.add((tipo, fs))
        for k in self.osm_by_tokens.get(fs, ()): ks.add(k)
        if not tk: return []
        pos = [t for t in tk if self.tok_osm.get(t)]
        if not pos: return []
        longest = min(pos, key=lambda t: (len(self.tok_osm[t]), -len(t)))
        for k in self.tok_osm.get(longest, ()):
            if tipo is not None and k[0] is not None and k[0] != tipo: continue
            if fs <= k[1] or k[1] <= fs: ks.add(k)
        if not ks:
            k = super()._find(tipo, tk, self.osm, self.osm_by_tokens)
            if k is None:
                k = self._fuzzy(tipo, tk, self.osm, self.tok_osm)
                if k is not None: self.fuzzy = True
            if k is not None: ks.add(k)
        return list(ks)
    def street_nodes(self, tipo, tk):
        rk = self._find(tipo, tk, self.street, self.by_tokens)
        ks = self.osm_keys(tipo, tk)
        if rk is not None:
            ks = list(set(ks) | set(self.osm_keys(rk[0], sorted(rk[1]))))
        if not ks: return None
        nodes = np.unique(np.concatenate([n for k in ks for n in self.osm[k]]))
        if rk is not None:
            d, _ = self._tree_reg(rk).query(np.c_[self.nx[nodes], self.ny[nodes]])
            keep = d < 250
            if keep.any(): nodes = nodes[keep]
            else: return None
        return nodes
    def incrocio(self, a, b):
        A = self.street_nodes(*a); B = self.street_nodes(*b)
        if A is None or B is None: return None, 'no_via'
        com = np.intersect1d(A, B)
        if len(com):
            i = com[len(com) // 2]
            if len(com) > 1:
                xs, ys = self.nx[com], self.ny[com]
                if np.ptp(xs) > 150 or np.ptp(ys) > 150: self.multi = True
            return (float(self.nlon[i]), float(self.nlat[i])), 'incrocio'
        from scipy.spatial import cKDTree
        tb = cKDTree(np.c_[self.nx[B], self.ny[B]]); d, j = tb.query(np.c_[self.nx[A], self.ny[A]])
        k = int(np.argmin(d))
        if d[k] < 80:
            i = A[k]; return (float(self.nlon[i]), float(self.nlat[i])), 'incrocio'
        if d[k] < 250:
            i = A[k]; i2 = B[j[k]]; self.approx = True
            return (float((self.nlon[i] + self.nlon[i2]) / 2), float((self.nlat[i] + self.nlat[i2]) / 2)), 'incrocio'
        return None, 'incrocio_non_si_toccano'
    def _incrocio_civici(self, a, b):
        """ripiego: i punti dei civici delle due vie; se le due vie si avvicinano a meno di 120 m, punto medio della coppia piu vicina"""
        ka = self._find(a[0], a[1], self.street, self.by_tokens); kb = self._find(b[0], b[1], self.street, self.by_tokens)
        if ka is None or kb is None or ka == kb: return None
        pa = np.array(self.street[ka]['pts']); pb = np.array(self.street[kb]['pts'])
        xa, ya = self.tr.transform(pa[:, 0], pa[:, 1]); xb, yb = self.tr.transform(pb[:, 0], pb[:, 1])
        from scipy.spatial import cKDTree
        t = cKDTree(np.c_[xb, yb]); d, j = t.query(np.c_[xa, ya]); i = int(np.argmin(d))
        if d[i] < 120: return (float((pa[i, 0] + pb[j[i], 0]) / 2), float((pa[i, 1] + pb[j[i], 1]) / 2))
        return None
    def indirizzo4(self, s):
        """-> (lon, lat) | None, livello (civico | civico_approx | incrocio | incrocio_approx | strada | nessuna), motivo, fuzzy"""
        self.fuzzy = False; self.multi = False; self.approx = False
        s0 = str(s or '').strip()
        if not s0: return None, 'nessuna', 'vuoto', False
        if re.match(r'^(autostrada|tangenziale|a{1,2}\d|raccordo|svincolo|autosole|ss\d|sp\d|sc\b|strada (comunale|urbana|provinciale|statale|regionale)|interno)', s0, flags=re.I) \
           and not re.search(r'incrocio', s0, flags=re.I):
            return None, 'nessuna', 'autostrada_o_generico', False
        r, lv = self.indirizzo(s0)
        fz = self.fuzzy
        base = re.sub(r'\(.*\)', '', lv)
        if r is not None:
            if base == 'incrocio' and self.approx: return r, 'incrocio_approx', 'incrocio_80_250m', fz
            if base in ('civico', 'civico_approx', 'incrocio'): return r, base, lv, fz
            return r, 'strada', lv, fz
        # incrocio non trovato in OSM: ripiego sul registro dei civici
        m = re.split(r'\s+(?:incrocio|inc\.?|ang\.?)\s+', s0, flags=re.I)
        if len(m) == 2:
            a = split_tipo(tokens(m[0])); b = split_tipo(tokens(m[1]))
            if a[1] and b[1]:
                p = self._incrocio_civici(a, b)
                if p is not None: return p, 'incrocio_approx', 'incrocio_da_civici', True
        return None, 'nessuna', lv, fz

    # ---- quali vie sono nominate nella riga (per le statistiche per via)
    def vie(self, s):
        """-> lista di (chiave, nome da mostrare) per la prima e, se c'e', la seconda via; chiave None se la via non e' riconosciuta"""
        s0 = str(s or '').strip()
        s0 = re.sub(r'\s+in\s+(?:prossimit\w*|corrispondenza).*$', '', s0, flags=re.I)
        s0 = re.sub(r'\s+fronte\s+civico.*$', '', s0, flags=re.I)
        nomi = []
        if re.search(r'\S\s+-\s', s0):
            parts = [p.strip() for p in s0.split(' - ') if p.strip() and p.strip() != '-']
            if parts: nomi.append(parts[0])
            if len(parts) > 1 and not re.match(r'^\d+[a-zA-Z]?$', parts[1]) and not re.match(r'^palo', parts[1], flags=re.I): nomi.append(parts[1])
        else:
            m = re.split(r'\s+(?:incrocio|inc\.?|ang\.?)\s+', s0, flags=re.I)
            if len(m) == 2: nomi = [m[0], m[1]]
            else:
                m2 = re.match(r'^(.*?)[, ]+(?:n\.?\s*|civico\s*)?(\d+)\s*([a-zA-Z]?)\s*(?:/.*)?$', s0)
                nomi = [m2.group(1) if (m2 and not re.search(r'palo\s*luce', s0, flags=re.I)) else re.split(',', s0)[0]]
        out = []
        for n in nomi:
            tipo, rest = split_tipo(tokens(n))
            if not rest: out.append((None, n)); continue
            k = self._find(tipo, rest, self.street, self.by_tokens)
            if k is not None: out.append((k, self.regname.get(k, n))); continue
            k = self._find(tipo, rest, self.osm, self.osm_by_tokens)
            out.append((('osm',) + k if k is not None else None, n))
        return out
