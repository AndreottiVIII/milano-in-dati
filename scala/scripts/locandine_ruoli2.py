"""Chi ha i ruoli principali, usando la posizione delle parole sul foglio.

Uso: python -I -X utf8 locandine_ruoli2.py --cartella <risultati>
Legge ocrpos_testo*.jsonl (parole con posizione) e lavori_per_recita.csv. I personaggi stanno in locandine_ruoli.py.
Le parole si ricompongono in file orizzontali. Il nome tutto maiuscolo si cerca nella stessa fila, a destra o a sinistra del
personaggio secondo come è fatto quel foglio.
Se dopo i nomi ci sono le date tra parentesi (più interpreti per lo stesso ruolo) vale solo chi ha il giorno di quella recita.
"""
import argparse, collections as C, csv, difflib, glob, importlib.util, json, os, random, re, unicodedata

spec = importlib.util.spec_from_file_location('ruoli1', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locandine_ruoli.py'))
R1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R1)
RUOLI = R1.RUOLI
VIETATE = set('TEATRO SCALA ALLA DELLA DEL CORO ORCHESTRA MAESTRO DIRETTORE REGIA SCENE COSTUMI BALLO CORPO PRIMA SECONDA RAPPRESENTAZIONE MUSICA ATTO LUCI'.split())
PART = {'DE', 'DI', 'DEL', 'DELLA', 'DAL', 'VAN', 'VON', 'LA', 'LE', 'DA', 'MC', 'EL', 'DOS', 'DU', 'Y'}
PRIMA_NO = re.compile(r"^(di|del|della|dell|d'|d|degli|e|ed|of|amiche|amica|amici|amico|madre|padre|figlia|figlio|a|con|per|la|il|le|i|servo)$", re.I)


def asc(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()


def maiuscola(w):
    a = re.sub(r"[^A-Za-z]", '', asc(w))
    if len(a) < 2:
        return False
    if a.upper() == a:
        return True
    # una lettera su quattro può essere letta male (JORkTAD), ma la parola deve restare quasi tutta maiuscola
    return len(a) >= 4 and sum(c.isupper() for c in a) / len(a) >= .75


def file_orizzontali(parole):
    """Raggruppa le parole in file: stessa altezza sul foglio."""
    pp = sorted(parole, key=lambda p: p['y'] + p['h'] / 2)
    file, cor = [], []
    for p in pp:
        c = p['y'] + p['h'] / 2
        if cor and abs(c - sum(q['y'] + q['h'] / 2 for q in cor) / len(cor)) > max(6, p['h'] * .55):
            file.append(sorted(cor, key=lambda q: q['x']))
            cor = []
        cor.append(p)
    if cor:
        file.append(sorted(cor, key=lambda q: q['x']))
    return file


def nome_da(parole):
    """Prende il primo gruppo di 2-4 parole maiuscole della lista."""
    cor = []
    for p in parole:
        a = re.sub(r"[^A-Za-z']", '', asc(p['t'])).upper()
        if maiuscola(p['t']) and a not in VIETATE:
            cor.append(a)
            if len(cor) == 4:
                break
        elif cor:
            break
    return ' '.join(cor) if len(cor) >= 2 and any(len(c) >= 4 and c not in PART for c in cor) else ''


def trova_ruolo(fila, ruolo):
    """Indice della prima parola del personaggio nella fila, scritto non tutto maiuscolo. -1 se non c'è."""
    pz = asc(ruolo).split()
    ws = [re.sub(r"[^A-Za-z'\-]", '', asc(p['t'])) for p in fila]
    for i in range(len(ws) - len(pz) + 1):
        if all(ws[i + k].lower() == pz[k].lower() for k in range(len(pz))) and not all(maiuscola(fila[i + k]['t']) for k in range(len(pz))):
            if i > 0 and PRIMA_NO.match(ws[i - 1]) and fila[i]['x'] - (fila[i - 1]['x'] + fila[i - 1]['w']) < fila[i]['h'] * 1.5:
                # "Le amiche di Giulietta", "madre di Giselle": non è il personaggio
                if ws[i - 1].lower() not in ('il', 'la'):
                    continue
            if fila[i]['h'] > 80:  # scritta grande: è il titolo
                continue
            return i, i + len(pz)
    return -1, -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    a = ap.parse_args()
    U = a.cartella
    P = {}
    for p in glob.glob(os.path.join(U, 'ocrpos_testo*.jsonl')):
        for l in open(p, encoding='utf-8'):
            x = json.loads(l)
            if x.get('parole'):
                P[x['file']] = x['parole']
    rec = [x for x in csv.DictReader(open(os.path.join(U, 'lavori_per_recita.csv'), encoding='utf-8-sig'))
           if x['tipo'] in RUOLI and x['titolo_principale'] in RUOLI[x['tipo']] and x['per_bambini'] != 'si']
    usc, fogli, letti = [], C.Counter(), C.Counter()
    for x in rec:
        titolo = x['titolo_principale']
        fogli[titolo] += 1
        fl = file_orizzontali(P.get(x['file'], []))
        trovati = []
        for ruolo in RUOLI[x['tipo']][titolo]:
            for k, fila in enumerate(fl):
                i, j = trova_ruolo(fila, ruolo)
                if i < 0:
                    continue
                destra, sinistra = nome_da(fila[j:]), nome_da(list(reversed(fila[:i]))) if i else ''
                if sinistra:
                    sinistra = ' '.join(reversed(sinistra.split()))
                trovati.append((ruolo, k, i, j, destra, sinistra))
                break
        # il foglio scrive prima il personaggio o prima il nome?
        nd = sum(1 for t in trovati if t[4] and not t[5])
        ns = sum(1 for t in trovati if t[5] and not t[4])
        for ruolo, k, i, j, d, s in trovati:
            fila = fl[k]
            testo = ' '.join(p['t'] for p in fila[j:])
            nome = s if ns > nd else d
            if '(' in testo and re.search(r'\(\s*\d', testo):
                # più interpreti per lo stesso ruolo, con le date: vale chi ha il giorno di questa recita
                g = int(x['data'][6:8])
                scelto = ''
                for m in re.finditer(r"((?:[A-Z][A-Z'\-]+\s+){1,3}[A-Z][A-Z'\-]+)\s*\(([\d\s,.;\-]+)\)", asc(testo)):
                    if g in [int(n) for n in re.findall(r'\d+', m.group(2))]:
                        scelto = m.group(1)
                        break
                nome = scelto
            if nome:
                usc.append({'data': x['data'], 'tipo': x['tipo'], 'titolo': titolo, 'ruolo': ruolo, 'nome': nome, 'file': x['file'], 'riga': ' '.join(p['t'] for p in fila)[:80]})
        if any(u['file'] == x['file'] for u in usc[-len(trovati) - 1:]):
            letti[titolo] += 1
    freq = C.Counter(u['nome'] for u in usc)
    base = C.defaultdict(list)
    mappa = {}
    for n, c in freq.most_common():
        b = base[n[0]]
        m = difflib.get_close_matches(n, b, n=1, cutoff=0.85) if c < 60 else []
        # stesso nome con lettere lette male, non due persone: anche il cognome da solo deve somigliare molto (Armiato non è Barbato)
        # i cognomi corti devono essere uguali: Merli non è Meli
        if m and (difflib.SequenceMatcher(None, n.split()[-1], m[0].split()[-1]).ratio() < (.8 if min(len(n.split()[-1]), len(m[0].split()[-1])) > 6 else .99) or abs(len(n.split()[0]) - len(m[0].split()[0])) > 2):
            m = []
        mappa[n] = m[0] if m else n
        if not m:
            b.append(n)
    # due nomi attaccati (CARLA FRACCI AIDA ACCOLLA) e nomi rari con la prima lettera letta male (ORLA FRACCI)
    freq2 = C.Counter()
    for k, c in freq.items():
        freq2[mappa[k]] += c
    grandi = [k for k, c in freq2.most_common(300)]

    def pulisci(n):
        pz = n.split()
        if len(pz) >= 3:
            for t in (' '.join(pz[:2]), ' '.join(pz[-2:])):
                if freq2.get(t, 0) >= 15:
                    return t
        if len(pz) == 4:
            return ' '.join(pz[:2])
        if freq2.get(n, 0) < 10:
            for g in grandi:
                # stesso cognome e nome quasi uguale: Orla e Carla sì, Franco e Francesco no
                if g != n and pz[-1] == g.split()[-1] and abs(len(pz[0]) - len(g.split()[0])) <= 1 and difflib.SequenceMatcher(None, n, g).ratio() >= .8:
                    return g
        return n
    for u in usc:
        u['nome'] = pulisci(mappa[u['nome']]).title()
    with open(os.path.join(U, 'ruoli_letti.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(usc[0]))
        w.writeheader()
        w.writerows(usc)
    print('fogli', sum(fogli.values()), 'con almeno un ruolo', sum(letti.values()))
    print('copertura', {k: f'{letti[k]}/{v}' for k, v in fogli.most_common(14)})
    for tp in RUOLI:
        c = C.defaultdict(set)
        for u in usc:
            if u['tipo'] == tp:
                c[u['nome']].add(u['file'])
        print(tp, [(n, len(v)) for n, v in sorted(c.items(), key=lambda kv: -len(kv[1]))[:30]])
    for n in ('Carla Fracci', 'Maria Meneghini Callas', 'Luciana Savignano', 'Roberto Bolle', 'Renata Tebaldi', 'Luciano Pavarotti', 'Mirella Freni', 'Rudolf Nureyev'):
        q = [u for u in usc if u['nome'] == n]
        print(n, len({u['file'] for u in q}), C.Counter(u['ruolo'] for u in q).most_common(9), sorted({u['data'][:4] for u in q})[:1], sorted({u['data'][:4] for u in q})[-1:])
    random.seed(17)
    print('campione')
    for u in random.sample(usc, 40):
        print(' ', u['data'], u['titolo'][:12], u['ruolo'], '=>', u['nome'], '|', u['riga'][:58])


if __name__ == '__main__':
    main()
