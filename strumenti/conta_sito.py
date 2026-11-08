"""Conta quanto è grande il sito e scrive docs/il-sito/data/conti.json.
Uso (dalla radice del progetto):  python -I -X utf8 strumenti/conta_sito.py

REGOLE DI CONTEGGIO
- Pagine: le cartelle docs/<p>/index.html elencate in docs/temi.json o in docs/menu.js (SEZIONI),
  più dati-importanti (pagina vera fuori dai temi). Escluse: anteprima, elenco, il-sito, bozze (_*).
- Grafici: nelle pagine, ogni elemento HTML che ha la classe "ch" oppure role="img" (un elemento = un grafico o una mappa).
- Numeri: in docs/<p>/data/ (anche dentro i .gz) celle numeriche dei CSV; valori numerici foglia dei JSON;
  nei GeoJSON solo i valori numerici di "properties" (non le coordinate). Valori con zero iniziale (codici) esclusi.
- File di dati e MB: tutti i file in docs/*/data/ delle pagine contate (esclusa anteprima).
- Fonti: domini (senza www, al livello "registrabile") dei link esterni nel piè di pagina <footer> e nei paragrafi
  class="src" delle pagine; esclusi github, il sito stesso, davidecaniatti.
- Anni: valori-anno (1000..anno corrente) nelle colonne/chiavi "anno"/"year" (e simili) dei dati di ogni pagina; le date
  ISO nelle colonne "data" contano come anno; gli anni futuri (previsioni) non contano. Si parte dall'anno più recente e
  si risale finché non c'è un buco di più di 3 anni tra due anni presenti: quello è l'inizio della serie. Così una
  statua del 1560 o un terremoto del 1117 (date di cose, non di misure) non allungano la serie di dati.
- Fonti: ai link del piè di pagina si aggiungono i link nelle chiavi fonti/licenze/note dei JSON di dati e nei file
  di testo delle fonti (LICENZE, altre_fonti ecc.), perché molte pagine scrivono le fonti da quei file.
"""
import os, re, json, csv, gzip, io, datetime
from urllib.parse import urlparse

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(R, 'docs')
OUT = os.path.join(DOCS, 'il-sito', 'data', 'conti.json')
ESCLUSE = {'anteprima', 'elenco', 'il-sito'}
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


def pagine_elenco():
    t = json.load(open(os.path.join(DOCS, 'temi.json'), encoding='utf-8'))
    temi = {x['id']: x for x in t['temi']}
    ps = {}
    for p in t['pagine']:
        ps[p['path'].strip('/')] = p
    menu = open(os.path.join(DOCS, 'menu.js'), encoding='utf-8').read()
    for m in re.finditer(r"path:\s*'([^']+)'\s*,\s*label:\s*'((?:[^'\\]|\\.)*)'", menu):
        k = m.group(1).strip('/')
        ps.setdefault(k, {'path': k + '/', 'label': m.group(2).replace("\\'", "'"), 'tema': None})
    if os.path.isfile(os.path.join(DOCS, 'dati-importanti', 'index.html')):
        ps.setdefault('dati-importanti', {'path': 'dati-importanti/', 'label': 'Dati importanti', 'tema': None})
    return temi, ps


tag_re = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)\b([^>]*)>')


def conta_grafici(html):
    n = 0
    for m in tag_re.finditer(html):
        a = m.group(2)
        if re.search(r'role\s*=\s*["\']img["\']', a):
            n += 1
            continue
        c = re.search(r'class\s*=\s*["\']([^"\']*)["\']', a)
        if c and 'ch' in c.group(1).split():
            n += 1
    return n


def dominio(url):
    h = (urlparse(url).hostname or '').lower()
    if h.startswith('www.'):
        h = h[4:]
    p = h.split('.')
    if len(p) >= 3 and p[-2] in ('gov', 'co', 'com', 'edu', 'org', 'ac'):
        return '.'.join(p[-3:])
    return '.'.join(p[-2:]) if len(p) >= 2 else h


def fonti_pagina(html):
    blocchi = re.findall(r'<footer\b.*?</footer>', html, re.S | re.I)
    blocchi += re.findall(r'<(?:p|div)\b[^>]*class="[^"]*\bsrc\b[^"]*"[^>]*>.*?</(?:p|div)>', html, re.S | re.I)
    ds = set()
    for b in blocchi:
        for u in re.findall(r'href="(https?://[^"]+)"', b):
            d = dominio(u)
            if d and 'github' not in d and 'davidecaniatti' not in d and d not in ESCL_DOM:
                ds.add(d)
    return ds


URL_RE = re.compile(r"https?://[^\s\"'<>)\],]+")
ESCL_DOM = ('w3.org', 'schema.org', 'localhost')
chiave_fonte = re.compile(r'font|licen|sourc|metod|limit|nota|note|credit', re.I)


def urls_in(o, ok, ds):
    if isinstance(o, str):
        if ok:
            for u in URL_RE.findall(o):
                d = dominio(u)
                if d and 'github' not in d and 'davidecaniatti' not in d and d not in ESCL_DOM:
                    ds.add(d)
    elif isinstance(o, list):
        for x in o:
            urls_in(x, ok, ds)
    elif isinstance(o, dict):
        for k, v in o.items():
            urls_in(v, ok or bool(chiave_fonte.match(str(k))), ds)


def fonti_dati(dd):
    ds = set()
    if not os.path.isdir(dd):
        return ds
    for root, _, files in os.walk(dd):
        for f in files:
            p = os.path.join(root, f)
            fl = f.lower()
            try:
                if fl.endswith('.json') and os.path.getsize(p) < 3000000:
                    urls_in(json.loads(open(p, encoding='utf-8-sig').read()), False, ds)
                elif fl.endswith(('.txt', '.md')) or chiave_fonte.search(fl) and fl.endswith('.csv'):
                    for u in URL_RE.findall(open(p, encoding='utf-8-sig', errors='replace').read()):
                        d = dominio(u)
                        if d and 'github' not in d and 'davidecaniatti' not in d and d not in ESCL_DOM:
                            ds.add(d)
            except Exception:
                pass
    return ds


def titolo(html, fallback):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S | re.I)
    if m:
        t = re.sub(r'<[^>]+>', '', m.group(1))
        t = re.sub(r'\s+', ' ', t).strip()
        if t:
            return t
    return fallback


def main():
    temi, ps = pagine_elenco()
    righe = []
    tutti_domini = set()
    tot_file = 0
    tot_byte = 0
    for k in sorted(ps):
        if k in ESCLUSE or k.startswith('_'):
            continue
        ih = os.path.join(DOCS, k, 'index.html')
        if not os.path.isfile(ih):
            continue
        html = open(ih, encoding='utf-8', errors='replace').read()
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
        ds = fonti_pagina(html) | fonti_dati(dd)
        tutti_domini |= ds
        tot_file += nf
        tot_byte += nb
        an = serie(acc.anni)
        p = ps[k]
        righe.append({'path': k + '/', 'nome': p.get('label') or k, 'titolo': titolo(html, p.get('label') or k),
                      'tema': p.get('tema') or 'altro', 'grafici': conta_grafici(html), 'numeri': acc.num,
                      'file': nf, 'mb': round(nb / 1048576, 2), 'fonti': len(ds),
                      'anno_da': an[0] if an else None, 'anno_a': an[1] if an else None})
    per_tema = []
    for tid, t in temi.items():
        n = sum(1 for r in righe if r['tema'] == tid)
        if n:
            per_tema.append({'id': tid, 'nome': t['nome'], 'colore': t['colore'], 'pagine': n})
    n = sum(1 for r in righe if r['tema'] == 'altro')
    if n:
        per_tema.append({'id': 'altro', 'nome': 'Altre pagine', 'colore': '#5f6673', 'pagine': n})
    per_tema.sort(key=lambda x: -x['pagine'])
    da = [r['anno_da'] for r in righe if r['anno_da']]
    a = [r['anno_a'] for r in righe if r['anno_a']]
    conti = {
        'aggiornato': OGGI.isoformat(),
        'pagine': len(righe), 'grafici': sum(r['grafici'] for r in righe), 'numeri': sum(r['numeri'] for r in righe),
        'file': tot_file, 'mb': round(tot_byte / 1048576, 1), 'fonti': len(tutti_domini),
        'anno_da': min(da), 'anno_a': max(a), 'anni': max(a) - min(da) + 1, 'quartieri': 88,
        'per_tema': per_tema, 'elenco': righe,
    }
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
