"""Conta quanto è grande il sito e scrive docs/il-sito/data/conti.json.
Uso (dalla radice del progetto):  python -I -X utf8 strumenti/conta_sito.py

REGOLE DI CONTEGGIO
- Pagine: le voci del menu, cioè l'elenco SEZIONI in docs/menu.js (tutte, comprese elenco e il-sito). È l'unica
  definizione di "pagina": lo stesso numero va in home, il-sito e fonti.
- Grafici: nelle pagine, ogni elemento HTML che ha la classe "ch" oppure role="img" (un elemento = un grafico o una mappa).
- Numeri: in docs/<p>/data/ (anche dentro i .gz) celle numeriche dei CSV; valori numerici foglia dei JSON;
  nei GeoJSON solo i valori numerici di "properties" (non le coordinate). Valori con zero iniziale (codici) esclusi.
- File di dati e MB: tutti i file in docs/*/data/ delle pagine contate.
- Fonti: gli editori dei dati elencati in docs/fonti/data/fonti.json (stesso conteggio della pagina Fonti e metodo:
  "editori diversi"). Per ogni pagina, il numero di editori citati per quella pagina. Le pagine che non sono nella
  tabella delle fonti (dati-importanti, elenco, il-sito, fonti) hanno 0.
- Anni: per ogni pagina l'inizio e la fine dei dati sono quelli scritti nella tabella ANNI qui sotto, presa dalle
  descrizioni di docs/temi.json e dal testo delle pagine. Le pagine che non sono nella tabella ripiegano su un calcolo
  automatico: valori-anno (1000..anno corrente) nelle colonne/chiavi "anno"/"year" dei dati; si parte dall'anno più
  recente e si risale finché non c'è un buco di più di 3 anni. Le pagine nella tabella con (None, None) non hanno una
  serie di anni (riepiloghi, giochi, elenchi di cose datate) e restano fuori dal grafico del tempo.
- Temi: quelli di docs/temi.json. Le pagine che non sono in nessun tema (dati-importanti, elenco, il-sito) stanno nel
  gruppo "Riepiloghi e guide".
"""
import os, re, json, csv, gzip, io, html, datetime

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(R, 'docs')
OUT = os.path.join(DOCS, 'il-sito', 'data', 'conti.json')
OGGI = datetime.date.today()
ANNO_MAX = OGGI.year
ANNO_MIN = 1000
BUCO = 3  # anni: una serie si ferma a un buco più lungo di così

num_re = re.compile(r'^-?\d+(?:[.,]\d+)?$')


def cella_num(s):
    s = s.strip()
    if not num_re.match(s):
        return False
    t = s.lstrip('-')
    if len(t) > 1 and t[0] == '0' and t[1] not in '.,':
        return False
    return True


anno_key = re.compile(r'^(anno|year|anni)(_.*)?$|.*_(anno|year)$', re.I)
data_key = re.compile(r'^(data|date)(_.*)?$|.*_(data|date)$', re.I)


class Acc:
    def __init__(s):
        s.num = 0
        s.anni = []

    def anno(s, v):
        if ANNO_MIN <= v <= ANNO_MAX:
            s.anni.append(v)


def json_walk(o, acc, chiave=None):
    if isinstance(o, bool) or o is None:
        return
    if isinstance(o, (int, float)):
        acc.num += 1
        if chiave and anno_key.match(chiave) and float(o).is_integer():
            acc.anno(int(o))
        return
    if isinstance(o, str):
        if chiave and anno_key.match(chiave) and re.fullmatch(r'\d{4}', o):
            acc.anno(int(o))
        elif chiave and data_key.match(chiave) and re.match(r'\d{4}-\d\d', o):
            acc.anno(int(o[:4]))
        return
    if isinstance(o, list):
        for x in o:
            json_walk(x, acc, chiave)
    elif isinstance(o, dict):
        for k, v in o.items():
            json_walk(v, acc, k)


def geo_props(o, acc):
    feats = o.get('features', []) if isinstance(o, dict) else []
    for f in feats:
        json_walk((f or {}).get('properties') or {}, acc)


def leggi(path):
    nome = os.path.basename(path).lower()
    raw = open(path, 'rb').read()
    if nome.endswith('.gz'):
        raw = gzip.decompress(raw)
        nome = nome[:-3]
    return nome, raw.decode('utf-8-sig', errors='replace')


def conta_file(path, acc):
    try:
        nome, testo = leggi(path)
    except Exception:
        return
    if nome.endswith('.csv'):
        riga0 = testo.split('\n', 1)[0]
        d = max([';', ',', '\t'], key=riga0.count)
        rd = csv.reader(io.StringIO(testo), delimiter=d)
        try:
            testa = next(rd)
        except StopIteration:
            return
        ia = [i for i, h in enumerate(testa) if anno_key.match(h.strip())]
        idt = [i for i, h in enumerate(testa) if data_key.match(h.strip())]
        for r in rd:
            for c in r:
                if cella_num(c):
                    acc.num += 1
            for i in ia:
                if i < len(r) and re.fullmatch(r'\d{4}', r[i].strip()):
                    acc.anno(int(r[i]))
            for i in idt:
                if i < len(r) and re.match(r'\d{4}-\d\d', r[i].strip()):
                    acc.anno(int(r[i].strip()[:4]))
    elif nome.endswith('.json') or nome.endswith('.geojson'):
        try:
            o = json.loads(testo)
        except Exception:
            return
        if nome.endswith('.geojson') or (isinstance(o, dict) and 'features' in o and o.get('type') == 'FeatureCollection'):
            geo_props(o, acc)
        else:
            json_walk(o, acc)


def serie(anni):
    ys = sorted(set(anni))
    if not ys:
        return None
    i = len(ys) - 1
    while i > 0 and ys[i] - ys[i - 1] <= BUCO:
        i -= 1
    return ys[i], ys[-1]


ANNI = {
    # slug: (primo anno, ultimo anno); None = si usa quello calcolato dai dati.
    # Fonte: descrizioni di docs/temi.json e testo delle pagine.
    'temperature': (1763, None), 'beni-culturali': (2022, 2023), 'elezioni': (1946, None), 'aria': (1971, None),
    'area-c': (2016, None), 'bici-auto-mezzi': (2010, 2024), 'scala': (1778, None), 'violenza-politica': (1919, 2019),
    'neve-e-nebbia': (1952, 2025), 'derby': (1909, None), 'cinema-spariti': (1896, None),
    'acqua-del-sindaco': (2021, 2026), 'censimenti': (1861, 2023), 'prezzi-case': (2006, None),
    'bilancio-comune': (2015, 2025), 'appalti': (2019, 2025), 'affitti-brevi': (2012, 2025), 'alberi': (2023, 2025),
    'cani': (2011, 2024), 'morti': (2011, None), 'matrimoni': (1948, 2024), 'biblioteche': (2013, None),
    'redditi': (2000, 2024), 'scuole': (2009, 2024), 'pioggia': (1858, 2025), 'caldo': (2017, 2026),
    'costo-vita': (2005, None), 'metro': (2016, 2025), 'ristoranti': (2019, None), 'turisti': (2000, 2025),
    'luoghi-cercati': (2015, 2026), 'quartieri-che-cambiano': (2011, 2026), 'pollini': (2007, None),
    'voto-reddito': (2016, None), 'antenne': (2021, 2025), 'costruzioni': (2014, 2024),
    'arrivi-partenze': (2002, 2024), 'comunita': (1999, 2025), 'eta': (1999, 2025), 'benessere': (2004, 2024),
    'incroci': (2010, 2025), 'amministratori': (1946, None), 'botteghe': (2017, 2026), 'suolo': (2006, None),
    'pendolari': (1991, 2021), 'reati': (2004, 2024), 'permettersi': (2011, 2024), 'case-vuote': (1991, 2023),
    'divisa': (1999, 2025), 'sfratti': (2001, 2025), 'lavoro': (1991, 2023), 'rigenerazione': (2012, 2026),
    'rifiuti': (2010, 2024), 'poverta-educativa': (2004, 2024), 'palazzi': (2011, 2024),
    'il-tuo-giorno': (1763, None), 'milano-trema': (1065, 2016), 'omicidi': (1983, 2024), 'nascite': (2003, 2025),
    'tribunale': (2019, 2025), 'auto': (2007, 2025), 'carceri': (2019, 2026), 'musei': (1996, 2025),
    'aeroporti': (1994, None), 'bici': (2011, None), 'consiglio': (2016, 2026), 'verde': (2011, 2024),
    'imprese': (2000, 2025), 'hinterland': (2001, 2026), 'tasse': (2000, 2025), 'vibrazioni': (2019, 2026),
    'consumi': (2000, 2024),
    'beni-confiscati': (2014, 2026), 'case-popolari': (2018, 2025), 'fogne': (2013, 2025), 'fondi-quartieri': (2014, 2025),
    'medici-farmacie': (2005, 2026), 'milano-raccontata': (1900, None), 'parcheggi': (2023, 2025),
    'pietre-inciampo': (2017, 2026), 'reati-citta': (2004, 2024), 'scuole-domani': (2009, 2024),
    'speranza-vita': (2012, 2024), 'telefoni-pubblici': (2019, 2026), 'terzo-settore': (2011, 2026),
    'violenza-donne': (2017, 2024),
    # senza una serie di anni: riepiloghi, giochi, elenchi di cose datate
    'vie': (None, None), 'statue': (None, None), 'targhe': (None, None), 'citta-15-minuti': (None, None),
    'nomi-fermate': (None, None), 'case-servizi-reddito': (None, None), 'quartiere': (None, None),
    'quartiere-ideale': (None, None), 'indovina-quartiere': (None, None), 'chilometri-duomo': (None, None),
    'viaggio-linea': (None, None), 'attesa-fermata': (None, None), 'anno-covid': (None, None),
    'storia-case': (None, None), 'storia-centro': (None, None), 'oltre-il-reddito': (None, None),
    'sport': (None, None), 'dati-importanti': (None, None), 'elenco': (None, None), 'il-sito': (None, None),
    'fonti': (None, None),
}
SOLO_PAGINA = {'milano-trema'}
GRUPPO_ALTRO = {'id': 'guide', 'nome': 'Riepiloghi e guide', 'colore': '#5f6673'}


def pagine_elenco():
    """Le pagine sono le voci del menu (SEZIONI in docs/menu.js). Da temi.json solo tema ed etichetta."""
    t = json.load(open(os.path.join(DOCS, 'temi.json'), encoding='utf-8'))
    temi = {x['id']: x for x in t['temi']}
    tp = {p['path'].strip('/'): p for p in t['pagine']}
    menu = open(os.path.join(DOCS, 'menu.js'), encoding='utf-8').read()
    ps = {}
    voce = re.compile(r"""path:\s*'([^']+)'\s*,\s*label:\s*(?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""")
    for m in voce.finditer(menu):
        k = m.group(1).strip('/')
        lab = (m.group(2) if m.group(2) is not None else m.group(3)).replace("\\'", "'")
        ps[k] = {'path': k + '/', 'label': (tp.get(k) or {}).get('label') or lab, 'tema': (tp.get(k) or {}).get('tema')}
    return temi, ps


def fonti_da_tabella():
    """Editori per pagina e totale degli editori, da docs/fonti/data/fonti.json (quello che dice la pagina Fonti)."""
    f = json.load(open(os.path.join(DOCS, 'fonti', 'data', 'fonti.json'), encoding='utf-8'))
    per_pagina = {}
    for x in f['fonti']:
        per_pagina.setdefault(x['pagina'], set()).add(x['editore'])
    return {k: len(v) for k, v in per_pagina.items()}, len(f['editori'])


tag_re = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>')


def conta_grafici(h):
    n = 0
    for m in tag_re.finditer(h):
        a = m.group(2)
        if re.search(r'role\s*=\s*["\']img["\']', a):
            n += 1
            continue
        c = re.search(r'class\s*=\s*["\']([^"\']*)["\']', a)
        if c and 'ch' in c.group(1).split():
            n += 1
    return n


def titolo(h, fallback):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S | re.I)
    if m:
        t = re.sub(r'<[^>]+>', '', m.group(1))
        t = re.sub(r'\s+', ' ', html.unescape(t)).strip()
        if t:
            return t
    return fallback


def main():
    temi, ps = pagine_elenco()
    fonti_pag, n_editori = fonti_da_tabella()
    righe = []
    tot_file = 0
    tot_byte = 0
    senza_tabella = []
    for k in sorted(ps):
        ih = os.path.join(DOCS, k, 'index.html')
        if not os.path.isfile(ih):
            print('ATTENZIONE: manca docs/%s/index.html' % k)
            continue
        h = open(ih, encoding='utf-8', errors='replace').read()
        acc = Acc()
        nf = 0
        nb = 0
        dd = os.path.join(DOCS, k, 'data')
        if os.path.isdir(dd):
            for root, _, files in os.walk(dd):
                for f in files:
                    p = os.path.join(root, f)
                    nf += 1
                    nb += os.path.getsize(p)
                    conta_file(p, acc)
        tot_file += nf
        tot_byte += nb
        an = serie(acc.anni)
        if k in ANNI:
            da, a = ANNI[k]
            if da is None:
                an = None
            else:
                an = (da, a if a is not None else (an[1] if an else da))
        else:
            senza_tabella.append(k)
        p = ps[k]
        righe.append({'path': k + '/', 'nome': p.get('label') or k, 'titolo': titolo(h, p.get('label') or k),
                      'tema': p.get('tema') or GRUPPO_ALTRO['id'], 'grafici': conta_grafici(h), 'numeri': acc.num,
                      'file': nf, 'mb': round(nb / 1048576, 2), 'fonti': fonti_pag.get(k, 0),
                      'anno_da': an[0] if an else None, 'anno_a': an[1] if an else None})
    if senza_tabella:
        print('Pagine non nella tabella ANNI (anni calcolati dai dati, da controllare):', ', '.join(senza_tabella))
    per_tema = []
    for tid, t in temi.items():
        n = sum(1 for r in righe if r['tema'] == tid)
        if n:
            per_tema.append({'id': tid, 'nome': t['nome'], 'colore': t['colore'], 'pagine': n})
    n = sum(1 for r in righe if r['tema'] == GRUPPO_ALTRO['id'])
    if n and GRUPPO_ALTRO['id'] not in temi:  # se il gruppo è già in temi.json non va contato due volte
        per_tema.append({'id': GRUPPO_ALTRO['id'], 'nome': GRUPPO_ALTRO['nome'], 'colore': GRUPPO_ALTRO['colore'], 'pagine': n})
    per_tema.sort(key=lambda x: -x['pagine'])
    # il titolo di testa parte dalle misure vere: un catalogo di eventi lontani (terremoti dal 1065) resta nella sua pagina
    da = [r['anno_da'] for r in righe if r['anno_da'] and r['path'].strip('/') not in SOLO_PAGINA]
    a = [r['anno_a'] for r in righe if r['anno_a']]
    conti = {
        'aggiornato': OGGI.isoformat(),
        'pagine': len(righe), 'grafici': sum(r['grafici'] for r in righe), 'numeri': sum(r['numeri'] for r in righe),
        'file': tot_file, 'mb': round(tot_byte / 1048576, 1), 'fonti': n_editori,
        'anno_da': min(da), 'anno_a': max(a), 'anni': max(a) - min(da) + 1, 'quartieri': 88,
        'per_tema': per_tema, 'elenco': righe,
    }
    # la data cambia solo quando cambiano i conti, non ogni giorno
    try:
        vecchio = json.load(open(OUT, encoding='utf-8'))
        if {k: v for k, v in vecchio.items() if k != 'aggiornato'} == {k: v for k, v in conti.items() if k != 'aggiornato'}:
            conti['aggiornato'] = vecchio.get('aggiornato', conti['aggiornato'])
    except Exception:
        pass
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(conti, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print({k: v for k, v in conti.items() if k not in ('per_tema', 'elenco')})
    return conti


if __name__ == '__main__':
    c = main()
    import sys
    if '-v' in sys.argv:
        for r in c['elenco']:
            print(r['path'], r['grafici'], r['numeri'], r['anno_da'], r['anno_a'], r['fonti'])
