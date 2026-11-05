"""Quali lavori ci sono su ogni locandina: il titolo della sigla più gli altri titoli grandi letti sul foglio.

Uso: python -I -X utf8 locandine_lavori.py --cartella <risultati> [--correzioni locandine_correzioni_sigle.csv]
Legge recite.csv, titoli_sigle.csv e ocr_testo*.jsonl. Scrive lavori_per_recita.csv e controllo_titoli.csv.
Una serata con due lavori (Tosca più Coppelia) conta per ciascuno dei due.
"""
import argparse, collections as C, csv, difflib, glob, json, os, re, unicodedata

ARTICOLI = re.compile(r'^(IL|LO|LA|I|GLI|LE|L|UN|UNA|UNO|DIE|DER|DAS|THE|LES)\s+')
ESCLUSE = re.compile(r'TEATRO|SCALA|STAGIONE|ORE \d|PREZZI|BIGLIETT|RECITA|ABBONAMENTO|PERSONAGGI|POLTRON|PLATEA|INGRESSO|'
                     r'GENNAIO|FEBBRAIO|MARZO|APRILE|MAGGIO|GIUGNO|LUGLIO|AGOSTO|SETTEMBRE|OTTOBRE|NOVEMBRE|DICEMBRE')
SALE = [('Piccola Scala', r'PICCOLA ?SCALA'), ('Arcimboldi', r'ARCIMBOLD'), ('Palazzo dello Sport', r'PALAZZO DELLO SPORT'), ('Teatro Lirico', r'TEATRO LIRICO')]
# stesso balletto scritto in modi diversi nel catalogo
ALIAS = {'CINDERELLA': 'Cenerentola', 'CENERENTOLA': 'Cenerentola', 'BELLA ADDORMENTATA NEL BOSCO': 'La bella addormentata',
         'BELLA ADDORMENTATA': 'La bella addormentata', 'SLEEPING BEAUTY': 'La bella addormentata', 'PETRUSKA': 'Petruška', 'PETROUCHKA': 'Petruška', 'PETRUSHKA': 'Petruška',
         'PETRUCHKA': 'Petruška', 'COPPELIA': 'Coppélia', 'GISELLE': 'Giselle', 'LAGO DEI CIGNI': 'Il lago dei cigni', 'ROMEO E GIULIETTA': 'Romeo e Giulietta',
         'SCHIACCIANOCI': 'Lo schiaccianoci', 'DON CHISCIOTTE': 'Don Chisciotte', 'HISTOIRE DE MANON': "L'histoire de Manon", 'ONEGIN': 'Onegin',
         'EXCELSIOR': 'Excelsior', 'SOGNO DI UNA NOTTE DI MEZZA ESTATE': 'Sogno di una notte di mezza estate', 'BAYADERE': 'La Bayadère',
         'BISBETICA DOMATA': 'La bisbetica domata', 'UCCELLO DI FUOCO': "L'uccello di fuoco", 'DAME AUX CAMELIAS': 'La dame aux camélias',
         'SERENADE': 'Serenade', 'CORSAIRE': 'Le Corsaire', 'SYLPHIDE': 'La Sylphide', 'SILFIDI': 'Le Silfidi', 'SAGRA DELLA PRIMAVERA': 'La sagra della primavera',
         'BOLERO': 'Boléro', 'APOLLON MUSAGETE': 'Apollon musagète', 'APOLLO MUSAGETA': 'Apollon musagète', 'SACRE DU PRINTEMPS': 'La sagra della primavera',
         'FIGLIUOL PRODIGO': 'Il figliol prodigo', 'FIGLIOL PRODIGO': 'Il figliol prodigo', 'QUATTRO STAGIONI DA I VESPRI SICILIANI': 'Le quattro stagioni',
         'PINK FLOYD BALLET': 'Pink Floyd Ballet', 'THEME AND VARIATIONS': 'Theme and Variations', 'TRICORNO': 'Il tricorno', 'CAPPELLO A TRE PUNTE': 'Il tricorno'}


def norma(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().upper()
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]+', ' ', s)).replace(' DL ', ' DI ').strip()


def chiave(t):
    return ARTICOLI.sub('', norma(t))


def bello(t):
    return ALIAS.get(chiave(t), t)


def grandi(righe, quante=6):
    """Le righe più alte del foglio, tolte intestazione e date. Le scritte piccole in fondo non contano."""
    buone = [(r.get('h', 0), norma(r.get('t'))) for r in righe]
    buone = [(h, n) for h, n in buone if len(n) >= 4 and not ESCLUSE.search(n)]
    if not buone:
        return []
    buone.sort(key=lambda x: -x[0])
    soglia = buone[0][0] * 0.45
    return [n for h, n in buone[:quante] if h >= soglia]


def sala_stimata(righe):
    fondo = max([r.get('y', 0) + r.get('h', 0) for r in righe] or [1])
    alto = [norma(r.get('t')) for r in righe if r.get('y', 0) < 0.5 * fondo]
    for nome, pat in SALE:
        if any(re.search(pat, n) for n in alto):
            return nome
    return ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    ap.add_argument('--correzioni', default='')
    ap.add_argument('--regole', default='')
    a = ap.parse_args()
    U = a.cartella
    testo = {}
    for p in glob.glob(os.path.join(U, 'ocr_testo*.jsonl')):
        with open(p, encoding='utf-8') as f:
            for l in f:
                x = json.loads(l)
                testo[x['file']] = x.get('righe') or []
    sig = {(x['sigla'], x['lettera']): x for x in csv.DictReader(open(os.path.join(U, 'titoli_sigle.csv'), encoding='utf-8-sig'))}
    corr = {}
    if a.correzioni:
        for x in csv.DictReader(open(a.correzioni, encoding='utf-8-sig')):
            corr[(x['sigla'], x['lettera'])] = x
            b = sig.setdefault((x['sigla'], x['lettera']), dict(x))
            b.update({'titolo': x['titolo'], 'autore': x['autore'], 'altri_lavori': x['altri_lavori'], 'verifica': 'corretto a mano'})
    regole = C.defaultdict(list)
    if a.regole:
        for x in csv.DictReader(open(a.regole, encoding='utf-8-sig')):
            regole[(x['sigla'], x['lettera'])].append(x)
    recite = list(csv.DictReader(open(os.path.join(U, 'recite.csv'), encoding='utf-8-sig')))

    # sigla di balletto con un titolo dominante nel catalogo
    per_sigla = C.defaultdict(C.Counter)
    for x in recite:
        if x['tipo'] == 'Balletto' and x['origine_titolo'] == 'scheda':
            per_sigla[x['sigla']][bello(x['titolo'])] += 1
    dominante = {}
    for s, c in per_sigla.items():
        t, n = c.most_common(1)[0]
        if n / sum(c.values()) >= 0.5:
            dominante[s] = t

    # vocabolario dei lavori, senza nomi di persone
    voc = {}
    for x in sig.values():
        if x['lettera'] in ('O', 'B') and x['titolo'] and (x['sigla'], x['lettera']) not in (('MUTI', 'O'), ('BURG', 'O'), ('GRUB', 'O')):
            voc.setdefault(chiave(x['titolo']), bello(x['titolo']))
        for t in (x.get('altri_lavori') or '').split(' ; '):
            if t.strip():
                voc.setdefault(chiave(t), bello(t.strip()))
    for x in recite:
        if x['tipo'] == 'Balletto' and x['titolo']:
            voc.setdefault(chiave(x['titolo']), bello(x['titolo']))
    nomi = set()
    for x in sig.values():
        if x.get('autore'):
            nomi.add(norma(x['autore']))
            nomi.add(norma(x['autore']).split(' ')[-1])
    voc = {k: v for k, v in voc.items() if len(k) >= 5 and k not in nomi}
    print('vocabolario', len(voc))

    memo = {}

    def lavori_in_riga(r):
        """Titoli riconosciuti in una riga: riga intera quasi uguale, o titolo lungo contenuto per intero."""
        if r in memo:
            return memo[r]
        rr = ARTICOLI.sub('', r)
        trovati = set()
        for k, t in voc.items():
            if len(k) < 8:  # titoli corti: Fedra non è Fedora, solo uguaglianza
                if k == rr:
                    trovati.add(t)
            elif abs(len(rr) - len(k)) <= max(1, len(k) // 8) and difflib.SequenceMatcher(None, k, rr).ratio() >= 0.9:
                trovati.add(t)
            elif len(k) >= 10 and ' ' in k and re.search(r'\b' + re.escape(k) + r'\b', r):
                trovati.add(t)
        memo[r] = trovati
        return trovati

    usc = []
    conferme = C.defaultdict(lambda: [0, 0])
    autori = C.defaultdict(lambda: [0, 0])
    for x in recite:
        righe = testo.get(x['file'], [])
        g = grandi(righe)
        alte = ' '.join(norma(r.get('t')) for r in sorted(righe, key=lambda r: -r.get('h', 0))[:12]).replace(' ', '')
        s = sig.get((x['sigla'], x['lettera']), {})
        c = corr.get((x['sigla'], x['lettera']))
        princ = (c['titolo'] if c else '') or x['titolo'] or s.get('titolo', '')
        autore = (c['autore'] if c else '') or x['autore'] or s.get('autore', '')
        tipo = (c.get('tipo') if c else '') or x['tipo']
        # stessa sigla riusata per lavori diversi: decide il foglio
        for q in regole.get((x['sigla'], x['lettera']), []):
            if q['parola'] in alte:
                princ, autore = q['titolo'], q['autore']
        if x['tipo'] == 'Balletto':
            princ = bello(princ)
        lavori = {princ} if princ and tipo in ('Opera', 'Balletto') else set()
        if tipo == 'Balletto' and x['sigla'] in dominante:
            lavori.add(dominante[x['sigla']])
        if tipo in ('Opera', 'Balletto') or x['mista']:
            for r in g:
                lavori |= lavori_in_riga(r)
            for t in (s.get('altri_lavori') or '').split(' ; '):
                if t.strip() and chiave(t) in {chiave(q) for r in g for q in lavori_in_riga(r)}:
                    lavori.add(bello(t.strip()))
        # togli i doppioni con il titolo principale e i titoli contenuti in altri (Cavalleria / Cavalleria rusticana)
        kp = chiave(princ)
        altri = sorted({t for t in lavori if chiave(t) != kp and (not kp or (chiave(t) not in kp and kp not in chiave(t)))})
        if princ and x['origine_titolo'] != 'scheda':
            q = conferme[(x['sigla'], x['lettera'], princ)]
            q[0] += 1
            q[1] += any(kp in r or difflib.SequenceMatcher(None, kp, ARTICOLI.sub('', r)).ratio() >= .84 for r in g)
        if autore and tipo == 'Opera':
            cog = norma(autore).split(' ')[-1]
            q = autori[(x['sigla'], x['lettera'], princ, autore)]
            q[0] += 1
            tt = ' '.join(norma(r.get('t')) for r in righe).replace(' ', '')
            q[1] += cog in tt or cog[:5] in tt
        usc.append(dict(x, tipo=tipo, titolo_principale=princ, autore_principale=autore,
                        verifica=s.get('verifica', 'scheda' if x['titolo'] else ''), altri_lavori=' ; '.join(altri),
                        per_bambini='si' if any('BAMBINI' in r for r in g) else '',
                        sala_stimata=x['sala_tipo'] or sala_stimata(righe), righe_grandi=' | '.join(g[:3])))
    campi = list(recite[0]) + ['titolo_principale', 'autore_principale', 'verifica', 'altri_lavori', 'per_bambini', 'sala_stimata', 'righe_grandi']
    with open(os.path.join(U, 'lavori_per_recita.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        w.writerows(usc)
    with open(os.path.join(U, 'controllo_titoli.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['sigla', 'lettera', 'titolo', 'recite', 'locandine_dove_si_legge', 'quota'])
        for (s, l, t), (n, ok) in sorted(conferme.items(), key=lambda kv: kv[1][1] / kv[1][0]):
            w.writerow([s, l, t, n, ok, round(ok / n, 2)])
    with open(os.path.join(U, 'controllo_autori.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['sigla', 'lettera', 'titolo', 'autore', 'recite', 'cognome_sul_foglio', 'quota'])
        for (s, l, t, au), (n, ok) in sorted(autori.items(), key=lambda kv: kv[1][1] / kv[1][0]):
            w.writerow([s, l, t, au, n, ok, round(ok / n, 2)])
    tot = sum(v[0] for v in conferme.values())
    ok = sum(v[1] for v in conferme.values())
    print('recite con titolo da sigla', tot, 'titolo letto sul foglio', ok, 'senza titolo', sum(1 for x in usc if not x['titolo_principale']),
          'con altri lavori', sum(1 for x in usc if x['altri_lavori']), 'per bambini', sum(1 for x in usc if x['per_bambini']))
    print('tipi', C.Counter(x['tipo'] for x in usc).most_common())
    print('altri lavori piu frequenti', C.Counter(t for x in usc for t in x['altri_lavori'].split(' ; ') if t).most_common(30))
    print('sala stimata opere', C.Counter(x['sala_stimata'] or '(Scala o sconosciuta)' for x in usc if x['tipo'] == 'Opera').most_common())
    print('autori dubbi (cognome su meno del 40% dei fogli, almeno 3 recite)')
    for (s, l, t, au), (n, ok) in sorted(autori.items(), key=lambda kv: kv[1][1] / kv[1][0]):
        if n >= 3 and ok / n < .4:
            print(' ', s, l, t, au, n, ok)


if __name__ == '__main__':
    main()
