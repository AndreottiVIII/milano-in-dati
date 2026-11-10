"""Genera il mazzo del gioco "Quante ne sai di Milano?" e lo controlla.

    python -I -X utf8 quiz/scripts/genera.py              # tutti i moduli fatti_*.py, scrive docs/quiz/data/
    python -I -X utf8 quiz/scripts/genera.py --solo fatti_a   # controlla un modulo solo, non scrive nulla

Controlli (si ferma al primo errore grave, stampa gli avvisi):
1. ogni lettura registrata viene rifatta da capo sul file (senza cache) e deve dare lo stesso valore;
2. ogni calcolo dichiarato viene rifatto sui valori riletti;
3. ogni numero mostrato (valori delle risposte, dei grafici, delle serie) deve essere una lettura o un calcolo;
4. ogni numero scritto nel testo (domanda, spiegazione) deve corrispondere, arrotondato, a una lettura o a un calcolo
   (anni e numeri piccoli esclusi): se no, è un avviso;
5. la pagina del sito esiste, il tema viene da temi.json, la licenza è una di quelle della pagina in fonti.json;
6. niente parole vietate nel testo visibile; id unici; il file del mazzo sta sotto i 300 KB.
"""
import glob, importlib, json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mazzo  # noqa: E402
from mazzo import DOCS, R, carica, risolvi  # noqa: E402

# numeri che nel testo fanno parte di un'unità di misura («ogni 1.000 abitanti», «a 15 minuti», «over 65»)
UNITA_TESTO = {14, 15, 65, 80, 100, 1000, 10000, 100000}
VIETATE = ['trappol', '.csv', '.json', '.py', 'claude', ' ia ', 'ocr', 'riepilogo', 'scripts/', 'data/']


def temi_e_pagine():
    t = carica('temi.json')
    tema = {p['path'].strip('/'): p['tema'] for p in t['pagine']}
    nomi = {x['id']: x for x in t['temi']}
    label = {p['path'].strip('/'): p['label'] for p in t['pagine']}
    return tema, nomi, label


def licenze_pagine():
    d = carica('fonti/data/fonti.json')
    L = {}
    for f in d['fonti']:
        L.setdefault(f['pagina'], set()).add(f['licenza_tipo'])
    return L


def _uguale(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
    return a == b


def valori_ammessi(q):
    """Tutti i numeri che la domanda può mostrare: letture (anche elementi di liste) e calcoli."""
    vals = []
    for f, pth, v in q['_prove']['letture']:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            vals.append(v)
        elif isinstance(v, list):
            vals += [x for x in v if isinstance(x, (int, float)) and not isinstance(x, bool)]
    for e, v in q['_prove']['calcoli']:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            vals.append(v)
        elif isinstance(v, list):
            vals += [x for x in v if isinstance(x, (int, float))]
    return vals


def numeri_mostrati(q):
    out = []
    t = q['tipo']
    if t == 'piuomeno':
        out += [q['a']['v'], q['b']['v']]
    if t in ('numero', 'anno'):
        out.append(q['v'])
    for k in ('confronto', 'elementi'):
        for c in q.get(k, []):
            out.append(c['v'])
    for o in q.get('opzioni', []):
        out.append(o['v'])
    if q.get('citta') is not None:
        out.append(q['citta'])
    if q.get('serie'):
        for l in q['serie']['linee']:
            out += [x for x in l['v'] if x is not None]
    return [x for x in out if isinstance(x, (int, float))]


NUM_RE = re.compile(r'(?<![\w/])[−-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?|(?<![\w/])[−-]?\d+(?:,\d+)?')


def numeri_testo(s):
    out = []
    for m in NUM_RE.finditer(s):
        t = m.group(0).replace('−', '-')
        dec = len(t.split(',')[1]) if ',' in t else 0
        x = float(t.replace('.', '').replace(',', '.'))
        out.append((m.group(0), x, dec))
    return out


def anni_ammessi(q):
    s = set()
    for f, pth, v in q['_prove']['letture']:
        for seg in [f] + [str(x) for x in pth]:
            for y in re.findall(r'(1[6-9]\d\d|20[0-3]\d)', seg):
                s.add(int(y))
    for y in re.findall(r'(1[6-9]\d\d|20[0-3]\d)', q['anno']):
        s.add(int(y))
    if q.get('serie'):
        s.update(int(a) for a in q['serie']['anni'] if isinstance(a, (int, float)))
    if q['tipo'] == 'anno':
        s.add(int(q['v']))
    for v in valori_ammessi(q):
        if float(v).is_integer() and 1600 <= v <= 2035:
            s.add(int(v))
    # numeri dentro i valori di testo letti (date come «2003-08-11»)
    for f, pth, v in q['_prove']['letture']:
        if isinstance(v, str):
            s.update(int(x) for x in re.findall(r'\d+', v))
    return s


def numero_ok(x, dec, vals):
    for v in vals:
        for k in (1, 1000, 1e6, 0.01, 1e9):
            w = v / k
            if round(abs(w), dec) == abs(x) or round(abs(w) + 1e-9, dec) == abs(x):
                return True
            # arrotondamenti all'intero del testo («circa 9 mila»)
    return False


def controlla(qs, tema, label, lic):
    errori, avvisi = [], []
    ids = set()
    cache_fresca = {}
    for q in qs:
        qid = q['id']
        if qid in ids:
            errori.append('%s: id ripetuto' % qid)
        ids.add(qid)
        # 1. letture rifatte da capo
        rilette = []
        for f, pth, v in q['_prove']['letture']:
            if f not in cache_fresca:
                cache_fresca[f] = carica(f, cache=False)
            try:
                w = risolvi(cache_fresca[f], pth)
                if isinstance(w, str):
                    w = mazzo._num(w)
            except Exception as e:  # noqa: BLE001
                errori.append('%s: lettura impossibile %s %s (%s)' % (qid, f, pth, e))
                continue
            if isinstance(v, list):
                ok = isinstance(w, list) and len(v) == len(w) and all(_uguale(a, b) for a, b in zip(v, w))
            else:
                ok = _uguale(v, w)
            if not ok:
                errori.append('%s: valore cambiato in %s %s: %r contro %r' % (qid, f, pth, v, w))
            rilette.append(w)
        # 2. calcoli rifatti
        for e, v in q['_prove']['calcoli']:
            w = eval(e, {'__builtins__': {}}, dict(mazzo.SICURE, p=rilette))
            if not (_uguale(v, w) if not isinstance(v, list) else v == w):
                errori.append('%s: calcolo %s dà %r e non %r' % (qid, e, w, v))
        # 3. numeri mostrati
        vals = valori_ammessi(q)
        for x in numeri_mostrati(q):
            if not any(_uguale(x, v) for v in vals):
                errori.append('%s: numero mostrato %r non viene dai dati' % (qid, x))
        # 4. numeri nel testo
        anni = anni_ammessi(q)
        testi = [q['domanda'], q['spiega']] + [c.get('et', '') for c in q.get('confronto', []) + q.get('elementi', [])]
        if q['tipo'] == 'piuomeno':
            testi += [q['a']['et'], q['b']['et']]
        for s in testi:
            for raw, x, dec in numeri_testo(s):
                if dec == 0 and x.is_integer() and (int(x) in anni or abs(x) <= 10 or int(x) in UNITA_TESTO or (1900 <= x <= 2020 and x % 10 == 0)):  # decenni
                    continue
                if not numero_ok(x, dec, vals):
                    avvisi.append('%s: nel testo «%s» il numero %s non torna con i dati' % (qid, s[:70], raw))
        # 5. pagina, tema, licenza
        pg = q['pagina']
        if not os.path.exists(os.path.join(DOCS, pg, 'index.html')):
            errori.append('%s: la pagina %s/ non esiste' % (qid, pg))
        if pg not in tema:
            errori.append('%s: pagina %s non in temi.json' % (qid, pg))
        else:
            q['tema'] = tema[pg]
            q['pagina_nome'] = label[pg]
        if pg in lic:
            norm = q['licenza'].lower()
            if not any(t.lower().split(' (')[0].split(' —')[0] in norm for t in lic[pg]):
                errori.append('%s: licenza «%s» non tra quelle della pagina %s: %s' % (qid, q['licenza'], pg, sorted(lic[pg])))
        else:
            avvisi.append('%s: pagina %s senza voce in fonti.json, licenza non controllata' % (qid, pg))
        # 6. parole vietate
        tutto = ' '.join([q['domanda'], q['spiega'], q['fonte']] + [str(c.get('et', '')) for c in q.get('confronto', []) + q.get('elementi', [])]).lower()
        for w in VIETATE:
            if w in ' ' + tutto + ' ':
                errori.append('%s: parola vietata «%s»' % (qid, w.strip()))
    return errori, avvisi


def moduli(solo=None):
    nomi = sorted(os.path.basename(f)[:-3] for f in glob.glob(os.path.join(os.path.dirname(__file__), 'fatti_*.py')))
    if solo:
        nomi = [n for n in nomi if n == solo]
    qs = []
    for n in nomi:
        m = importlib.import_module(n)
        lst = m.domande()
        for q in lst:
            q['_modulo'] = n
        qs += lst
        print('%-22s %3d domande' % (n, len(lst)))
    return qs


def main():
    solo = sys.argv[sys.argv.index('--solo') + 1] if '--solo' in sys.argv else None
    tema, nomi, label = temi_e_pagine()
    lic = licenze_pagine()
    qs = moduli(solo)
    errori, avvisi = controlla(qs, tema, label, lic)
    for a in avvisi:
        print('AVVISO', a)
    for e in errori:
        print('ERRORE', e)
    from collections import Counter
    print('\nDomande:', len(qs))
    print('per tipo:', dict(Counter(q['tipo'] for q in qs)))
    print('per difficoltà:', dict(Counter(q['diff'] for q in qs)))
    print('per tema:', dict(Counter(q.get('tema') for q in qs)))
    if errori:
        print('\n%d errori: niente scritto.' % len(errori))
        sys.exit(1)
    if solo:
        return
    # scrittura: il mazzo pubblico senza le prove (che vanno in un file a parte, per il controllo)
    pub = []
    for q in qs:
        d = {k: v for k, v in q.items() if not k.startswith('_')}
        pub.append(d)
    temi_usati = sorted(set(q['tema'] for q in qs))
    out = {'generato': __import__('datetime').date.today().isoformat(), 'n': len(pub),
           'temi': [{'id': t, 'nome': nomi[t]['nome'], 'colore': nomi[t]['colore'], 'testo': nomi[t]['testo']} for t in temi_usati],
           'domande': pub}
    path = os.path.join(DOCS, 'quiz', 'data', 'mazzo.json')
    s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    open(path, 'w', encoding='utf-8').write(s)
    kb = len(s.encode('utf-8')) / 1024
    print('scritto mazzo: %.1f KB' % kb)
    assert kb < 300, 'mazzo oltre 300 KB'
    prove = {q['id']: q['_prove'] for q in qs}
    open(os.path.join(R, 'quiz', 'prove_mazzo.json'), 'w', encoding='utf-8').write(json.dumps(prove, ensure_ascii=False, indent=0))
    # dati del gioco per quartiere
    import quartieri_gioco
    quartieri_gioco.scrivi()


if __name__ == '__main__':
    main()
