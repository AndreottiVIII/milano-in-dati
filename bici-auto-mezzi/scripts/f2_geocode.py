"""Geocodifica locale di indirizzi di Milano con i dati aperti: civici del Comune (ds634) + nomi delle strade di OpenStreetMap.
Livelli: 'civico' (numero trovato), 'civico_approx' (numero interpolato tra i vicini), 'incrocio' (due strade che si toccano in OSM),
'strada' (solo la via), None.  Uso come libreria: g = Geocoder(S); g.indirizzo('via Monte Rosa, 57')"""
import os, re, glob, pickle, unicodedata
import numpy as np, pandas as pd
from pyproj import Transformer

STOP = {'del', 'della', 'dello', 'dei', 'degli', 'delle', 'di', 'da', 'de', 'd', 'dell', 'dall', 'l', 'la', 'il', 'lo', 'i', 'gli', 'le', 'e', 'a', 'al', 'ai', 'in', 'sul', 'sulla'}
TIPI = {'via', 'viale', 'piazza', 'piazzale', 'corso', 'largo', 'vicolo', 'strada', 'alzaia', 'bastioni', 'foro', 'galleria', 'ripa', 'cavalcavia',
        'piazzetta', 'passaggio', 'stradone', 'viadotto', 'naviglio', 'circonvallazione', 'lungolambro', 'vialetto', 'via'}
ABBR = [(r'\bv\.?le\b', 'viale'), (r'\bp\.?zza\b', 'piazza'), (r'\bp\.?za\b', 'piazza'), (r'\bp\.?le\b', 'piazzale'), (r'\bc\.?so\b', 'corso'), (r'\bs\.\s*', 'san ')]

def strip_acc(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
def tokens(s):
    s = strip_acc(str(s).lower())
    for a, b in ABBR: s = re.sub(a, b, s)
    s = re.sub(r"[^a-z0-9 ]", ' ', s.replace("'", ' '))
    return [t for t in s.split() if t not in STOP]
def split_tipo(tk):
    if tk and tk[0] in TIPI: return tk[0], tk[1:]
    return None, tk

class Geocoder:
    def __init__(self, S):
        self.S = S
        R = S + '/../citta-15-minuti/raw/comune_milano/civici/estratto/'
        c = pd.read_csv(glob.glob(R + '*.csv')[0], sep=';', dtype=str,
                        usecols=['TIPO', 'DESCRITTIVO', 'NUMERO', 'LETTERA', 'STATOCIVICO', 'LONG_WGS84', 'LAT_WGS84'])
        c = c[c.STATOCIVICO == 'Applicato'].copy()
        c['lon'] = pd.to_numeric(c.LONG_WGS84, errors='coerce'); c['lat'] = pd.to_numeric(c.LAT_WGS84, errors='coerce')
        c = c.dropna(subset=['lon', 'lat'])
        c['num'] = pd.to_numeric(c.NUMERO, errors='coerce')
        self.n_civici = len(c)
        self.street = {}      # (tipo, frozenset(token)) -> dict(num -> [(lettera, lon, lat)]) e lista punti
        self.by_tokens = {}   # frozenset(token) -> set di chiavi (tipo, tokens)
        for tipo, dsc, num, let, lon, lat in zip(c.TIPO, c.DESCRITTIVO, c.num, c.LETTERA.fillna(''), c.lon, c.lat):
            tk = tokens(dsc); key = (str(tipo).lower(), frozenset(tk))
            e = self.street.setdefault(key, {'nums': {}, 'pts': []})
            if not np.isnan(num): e['nums'].setdefault(int(num), []).append((str(let).lower(), lon, lat))
            e['pts'].append((lon, lat))
            self.by_tokens.setdefault(frozenset(tk), set()).add(key)
        self.tok_street = {}
        for key in self.street:
            for t_ in key[1]: self.tok_street.setdefault(t_, set()).add(key)
        self.tr = Transformer.from_crs(4326, 32632, always_xy=True)
        # OSM: nomi strade -> insiemi di nodi
        D = pickle.load(open(S + '/out/osm_parsed.pkl', 'rb'))
        ids, lat_, lon_ = D['ids'], D['lat'], D['lon']
        order = np.argsort(ids); sid = ids[order]
        self.osm = {}         # (tipo, frozenset) -> list di array di indici nodo (uno per way)
        self.osm_by_tokens = {}
        for t, refs in D['ways']:
            nm = t.get('name')
            if not nm or t['highway'] in ('footway', 'steps', 'platform', 'corridor', 'elevator', 'proposed', 'construction'): continue
            tipo, rest = split_tipo(tokens(nm))
            if not rest: continue
            r = np.asarray(refs, np.int64); p = np.searchsorted(sid, r); p[p >= len(sid)] = 0; ok = sid[p] == r
            nodes = order[p[ok]]
            if len(nodes) == 0: continue
            key = (tipo, frozenset(rest))
            self.osm.setdefault(key, []).append(nodes)
            self.osm_by_tokens.setdefault(frozenset(rest), set()).add(key)
        self.tok_osm = {}
        for key in self.osm:
            for t_ in key[1]: self.tok_osm.setdefault(t_, set()).add(key)
        self.nx, self.ny = self.tr.transform(lon_, lat_); self.nlat, self.nlon = lat_, lon_
        self.nx = np.asarray(self.nx); self.ny = np.asarray(self.ny)

    # ----- ricerca della via nel registro civici
    def _find(self, tipo, tk, table, by_tokens):
        key = (tipo, frozenset(tk))
        if key in table: return key
        ks = by_tokens.get(frozenset(tk))
        if ks:
            ks = list(ks)
            return ks[0] if len(ks) == 1 else None
        if not tk: return None
        idx = self.tok_street if table is self.street else self.tok_osm
        # 1) il nome dato e' contenuto in un nome piu lungo (manca il nome di battesimo) oppure e' troncato (56 caratteri)
        cand = None
        for t_ in tk[:-1]:
            cand = set(idx.get(t_, ())) if cand is None else cand & idx.get(t_, set())
        last = tk[-1]
        if cand is None:
            cand = {k for t_, ks_ in idx.items() if t_ == last for k in ks_} | {k for t_, ks_ in idx.items() if t_.startswith(last) and len(last) >= 4 for k in ks_}
        else:
            cand = {k for k in cand if last in k[1] or any(x.startswith(last) for x in k[1] if len(last) >= 4)}
        cand = [k for k in cand if (tipo is None or k[0] is None or k[0] == tipo)]
        if len(cand) == 1: return cand[0]
        if len(cand) > 1 and tipo is not None:
            c2 = [k for k in cand if k[0] == tipo]
            if len(c2) == 1: return c2[0]
        return None

    def civico(self, tipo, tk, num, let=''):
        key = self._find(tipo, tk, self.street, self.by_tokens)
        if key is None: return None, 'no_via'
        e = self.street[key]
        if num in e['nums']:
            L = e['nums'][num]
            for l, lo, la in L:
                if l == let: return (lo, la), 'civico'
            return (L[0][1], L[0][2]), 'civico'
        # interpolazione: vicini della stessa parita
        same = [n for n in e['nums'] if n % 2 == num % 2]
        if same:
            n2 = min(same, key=lambda n: abs(n - num))
            if abs(n2 - num) <= 20: return (e['nums'][n2][0][1], e['nums'][n2][0][2]), 'civico_approx'
        pts = np.array(e['pts']); return (float(np.median(pts[:, 0])), float(np.median(pts[:, 1]))), 'strada'

    def strada_osm(self, tipo, tk):
        key = self._find(tipo, tk, self.osm, self.osm_by_tokens)
        return key

    def incrocio(self, a, b):
        """a, b = (tipo, tokens). Nodo comune a due strade OSM, altrimenti il punto piu vicino se < 80 m"""
        ka = self.strada_osm(*a); kb = self.strada_osm(*b)
        if ka is None or kb is None: return None, 'no_via'
        A = np.unique(np.concatenate(self.osm[ka])); B = np.unique(np.concatenate(self.osm[kb]))
        com = np.intersect1d(A, B)
        if len(com):
            i = com[0] if len(com) == 1 else com[len(com) // 2]
            return (float(self.nlon[i]), float(self.nlat[i])), 'incrocio'
        from scipy.spatial import cKDTree
        tb = cKDTree(np.c_[self.nx[B], self.ny[B]]); d, j = tb.query(np.c_[self.nx[A], self.ny[A]])
        k = int(np.argmin(d))
        if d[k] < 80:
            i = A[k]; return (float(self.nlon[i]), float(self.nlat[i])), 'incrocio'
        return None, 'incrocio_non_si_toccano'

    def street_only(self, tipo, tk):
        key = self._find(tipo, tk, self.street, self.by_tokens)
        if key is not None:
            pts = np.array(self.street[key]['pts']); return (float(np.median(pts[:, 0])), float(np.median(pts[:, 1]))), 'strada'
        key = self.strada_osm(tipo, tk)
        if key is not None:
            A = np.unique(np.concatenate(self.osm[key])); i = A[len(A) // 2]
            return (float(self.nlon[i]), float(self.nlat[i])), 'strada'
        return None, 'no_via'

    def indirizzo(self, s):
        """stringa libera 'via Rossi Mario, 12' / 'via A incrocio via B' / 'via A, palo luce 5' -> ((lon, lat) | None, livello)"""
        s0 = str(s or '').strip()
        s0 = re.sub(r'\s+in\s+(?:prossimit\w*|corrispondenza).*?(?:civico\s*n?\.?\s*(\d+))?\s*$', lambda m_: (', ' + m_.group(1)) if m_.group(1) else '', s0, flags=re.I)
        mf = re.match(r'^(.*?)\s+fronte\s+civico\s*n?\.?\s*(\d+)', s0, flags=re.I)
        if mf: s0 = '%s, %s' % (mf.group(1), mf.group(2))
        if re.search(r'\S\s+-\s', s0):
            parts = [p.strip() for p in s0.split(' - ') if p.strip() and p.strip() != '-']
            if not parts: return None, 'vuoto'
            if len(parts) == 1: return self.indirizzo(parts[0])
            if re.match(r'^\d+[a-zA-Z]?$', parts[1]):
                return self.indirizzo('%s, %s' % (parts[0], parts[1]))
            return self.indirizzo('%s incrocio %s' % (parts[0], parts[1]))
        m = re.split(r'\s+(?:incrocio|inc\.?|ang\.?)\s+', s0, flags=re.I)
        if len(m) == 2:
            a = split_tipo(tokens(m[0])); b = split_tipo(tokens(m[1]))
            if not a[1] or not b[1]: return None, 'vuoto'
            r, lv = self.incrocio(a, b)
            if r is None:
                r2, lv2 = self.street_only(*a)
                if r2 is not None: return r2, 'strada(da_incrocio)'
                return None, lv
            return r, lv
        m2 = re.match(r'^(.*?)[, ]+(?:n\.?\s*|civico\s*)?(\d+)\s*([a-zA-Z]?)\s*(?:/.*)?$', s0)
        palo = re.search(r'palo\s*luce', s0, flags=re.I)
        if m2 and not palo:
            tipo, rest = split_tipo(tokens(m2.group(1)))
            if not rest: return None, 'vuoto'
            r, lv = self.civico(tipo, rest, int(m2.group(2)), m2.group(3).lower())
            if r is None:
                r2, lv2 = self.street_only(tipo, rest)
                if r2 is not None: return r2, 'strada(civico_non_trovato)'
            return r, lv
        base = re.split(r',', s0)[0]
        tipo, rest = split_tipo(tokens(base))
        if not rest: return None, 'vuoto'
        r, lv = self.street_only(tipo, rest)
        return r, ('strada(palo_luce)' if (palo and r) else lv)
