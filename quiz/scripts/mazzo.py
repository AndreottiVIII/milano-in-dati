"""Attrezzi comuni per il mazzo del gioco "Quante ne sai di Milano?".

Ogni domanda prende i suoi numeri SOLO dai file pubblicati in docs/<pagina>/data/,
attraverso un oggetto Prove: ogni lettura registra file, percorso e valore.
Alla fine controlla.py rilegge ogni file da capo (senza cache) e verifica che
- ogni valore registrato sia ancora lì, uguale;
- ogni numero mostrato dalla domanda sia uno dei valori registrati, o un calcolo
  dichiarato (p.calc) che si ricalcola dai valori riletti.

Uso nei moduli fatti_*.py:

    def domande():
        out = []
        p = Prove()
        auto = p.v('auto/data/riepilogo.json', 'serie', '[a=2025]', 'auto')
        alb  = p.v('alberi/data/riepilogo.json', 'citta', 'alberi', '2025')
        out.append(piuomeno(p, id='auto-alberi', pagina='auto', diff='facile',
            domanda='A Milano ci sono più auto dei residenti o più alberi del Comune?',
            a=('auto dei residenti (2025)', auto, ''), b=('alberi del Comune (marzo 2025)', alb, ''),
            spiega='...', anno='2025', fonte='...', licenza='CC BY 4.0'))
        return out

Percorsi: argomenti separati. '[k=v]' sceglie il primo elemento di una lista di
dizionari (o la prima riga di un CSV) con str(el[k]) == v; '[3]' è un indice; '[-1]' l'ultimo.
CSV: separatore ';' o ',' riconosciuto dalla prima riga; i valori numerici diventano int/float.
"""
import csv, gzip, io, json, os

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS = os.path.join(R, 'docs')
_cache = {}


def _num(s):
    if isinstance(s, str):
        t = s.strip()
        if t == '':
            return None
        try:
            if t.lstrip('-').isdigit():
                return int(t)
            return float(t)
        except ValueError:
            return s
    return s


def carica(rel, cache=True):
    """Legge un file di docs/ (json o csv). Con cache=False rilegge dal disco."""
    if cache and rel in _cache:
        return _cache[rel]
    path = os.path.join(DOCS, rel.replace('/', os.sep))
    if rel.endswith('.gz'):
        raw = gzip.open(path, 'rb').read().decode('utf-8-sig')
        rel2 = rel[:-3]
    else:
        raw = open(path, encoding='utf-8-sig').read()
        rel2 = rel
    if rel2.endswith('.json') or rel2.endswith('.geojson'):
        d = json.loads(raw)
    elif rel2.endswith('.csv'):
        prima = raw.split('\n', 1)[0]
        sep = ';' if prima.count(';') > prima.count(',') else ','
        d = [{k: _num(v) for k, v in r.items()} for r in csv.DictReader(io.StringIO(raw), delimiter=sep)]
    else:
        raise ValueError('tipo di file non gestito: ' + rel)
    if cache:
        _cache[rel] = d
    return d


def risolvi(d, path):
    cur = d
    for seg in path:
        if isinstance(seg, str) and seg.startswith('[') and seg.endswith(']'):
            inner = seg[1:-1]
            if '=' in inner:
                k, v = inner.split('=', 1)
                trovato = None
                for el in cur:
                    if isinstance(el, dict) and str(el.get(k)) == v:
                        trovato = el
                        break
                if trovato is None:
                    raise KeyError('nessun elemento con %s=%s' % (k, v))
                cur = trovato
            else:
                cur = cur[int(inner)]
        else:
            if isinstance(cur, list):
                cur = cur[int(seg)]
            else:
                if seg not in cur:
                    raise KeyError('chiave mancante: %r' % (seg,))
                cur = cur[seg]
    return cur


class Prove:
    """Registro delle letture di una domanda (o di un gruppo di domande)."""

    def __init__(self):
        self.letture = []   # (file, path, valore)
        self.calcoli = []   # (espressione, valore) ; espressione usa p[i] = valore della lettura i

    def v(self, rel, *path):
        val = risolvi(carica(rel), path)
        if isinstance(val, str):
            val2 = _num(val)
            val = val2
        self.letture.append((rel, list(path), val))
        return val

    def i(self):
        """Indice dell'ultima lettura (per p.calc)."""
        return len(self.letture) - 1

    def calc(self, espr, ctx=None):
        """Valore derivato: espr è un'espressione Python con p[i] (letture) e funzioni sicure.
        Esempio: x = p.calc('p[0] + p[1]')"""
        vals = [l[2] for l in self.letture]
        val = eval(espr, {'__builtins__': {}}, dict(SICURE, p=vals))
        self.calcoli.append((espr, val))
        return val

    def copia(self):
        q = Prove()
        q.letture = list(self.letture)
        q.calcoli = list(self.calcoli)
        return q


SICURE = {'round': round, 'abs': abs, 'min': min, 'max': max, 'sum': sum, 'len': len, 'sorted': sorted}

TIPI = ('piuomeno', 'numero', 'vf', 'quartiere', 'ordine', 'anno')
DIFF = ('facile', 'media', 'difficile')


def _base(p, tipo, id, pagina, diff, domanda, spiega, anno, fonte, licenza, serie=None, extra=None):
    assert tipo in TIPI, tipo
    assert diff in DIFF, (id, diff)
    q = {'id': id, 'tipo': tipo, 'diff': diff, 'pagina': pagina, 'domanda': domanda,
         'spiega': spiega, 'anno': str(anno), 'fonte': fonte, 'licenza': licenza}
    if serie:
        q['serie'] = serie
    if extra:
        q.update(extra)
    q['_prove'] = {'letture': [[f, pth, v] for f, pth, v in p.letture], 'calcoli': [[e, v] for e, v in p.calcoli]}
    return q


def _vx(t):
    """(etichetta, valore, unità) -> dict"""
    d = {'et': t[0], 'v': t[1]}
    if len(t) > 2 and t[2]:
        d['u'] = t[2]
    return d


def piuomeno(p, id, pagina, diff, domanda, a, b, spiega, anno, fonte, licenza, dec=0, serie=None):
    """Due cose, chi è più grande. a e b = (etichetta, valore, unità)."""
    A, B = _vx(a), _vx(b)
    assert A['v'] != B['v'], id
    return _base(p, 'piuomeno', id, pagina, diff, domanda, spiega, anno, fonte, licenza, serie,
                 {'a': A, 'b': B, 'dec': dec, 'giusta': 'a' if A['v'] > B['v'] else 'b'})


def numero(p, id, pagina, diff, domanda, v, lo, hi, passo, unita, spiega, anno, fonte, licenza, dec=0, serie=None, confronto=None):
    """Indovina il numero con un cursore da lo a hi."""
    assert lo < v < hi, (id, lo, v, hi)
    ex = {'v': v, 'lo': lo, 'hi': hi, 'passo': passo, 'u': unita, 'dec': dec}
    if confronto:
        ex['confronto'] = [_vx(c) for c in confronto]
    return _base(p, 'numero', id, pagina, diff, domanda, spiega, anno, fonte, licenza, serie, ex)


def vf(p, id, pagina, diff, affermazione, vero, confronto, spiega, anno, fonte, licenza, dec=0, serie=None):
    """Vero o falso. confronto = lista di (etichetta, valore, unità) per il grafico della rivelazione."""
    return _base(p, 'vf', id, pagina, diff, affermazione, spiega, anno, fonte, licenza, serie,
                 {'vero': bool(vero), 'confronto': [_vx(c) for c in confronto], 'dec': dec})


def quartiere(p, id, pagina, diff, domanda, opzioni, verso, unita, spiega, anno, fonte, licenza, dec=0, citta=None, misura=None):
    """Tra tre quartieri, chi ha il valore più alto (verso='max') o più basso ('min')."""
    O = [{'nome': n, 'v': v} for n, v in opzioni]
    vals = [o['v'] for o in O]
    assert len(set(vals)) == len(vals), id
    best = max(vals) if verso == 'max' else min(vals)
    ex = {'opzioni': O, 'verso': verso, 'u': unita, 'dec': dec, 'giusta': vals.index(best)}
    if citta is not None:
        ex['citta'] = citta
    if misura:
        ex['misura'] = misura
    return _base(p, 'quartiere', id, pagina, diff, domanda, spiega, anno, fonte, licenza, None, ex)


def ordine(p, id, pagina, diff, domanda, elementi, unita, spiega, anno, fonte, licenza, dec=0, verso='desc'):
    """Tre cose da mettere in ordine (dal più grande, verso='desc')."""
    E = [_vx(e) for e in elementi]
    vals = [e['v'] for e in E]
    assert len(set(vals)) == len(vals), id
    return _base(p, 'ordine', id, pagina, diff, domanda, spiega, anno, fonte, licenza, None,
                 {'elementi': E, 'u': unita, 'dec': dec, 'verso': verso})


def anno_q(p, id, pagina, diff, domanda, v, lo, hi, spiega, anno, fonte, licenza, serie=None):
    """In che anno: cursore sugli anni. serie = {'anni':[...], 'linee':[{'et','v':[...]}]} per la rivelazione."""
    assert lo < v < hi, (id, lo, v, hi)
    return _base(p, 'anno', id, pagina, diff, domanda, spiega, anno, fonte, licenza, serie,
                 {'v': v, 'lo': lo, 'hi': hi})


def serie_da(anni, linee):
    """Aiuto per la serie della rivelazione: anni e linee [(etichetta, valori, colore-opzionale)]."""
    out = {'anni': list(anni), 'linee': []}
    for l in linee:
        d = {'et': l[0], 'v': list(l[1])}
        if len(l) > 2 and l[2]:
            d['c'] = l[2]
        out['linee'].append(d)
    return out


def primo_sorpasso(anni, a, b):
    """Primo anno in cui a > b dopo che a <= b (None se non succede)."""
    prima = None
    for y, x, z in zip(anni, a, b):
        if x is None or z is None:
            continue
        if prima is not None and prima and x > z:
            return y
        prima = x <= z
    return None
