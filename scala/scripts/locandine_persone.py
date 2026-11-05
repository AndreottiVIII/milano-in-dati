"""Dal testo delle locandine ingrandite: direttore, nomi degli interpreti, prezzo della poltrona, prime assolute.

Uso: python -I -X utf8 locandine_persone.py --cartella <risultati> --cartellone <cartellone.csv> --interpreti <locandine_interpreti_noti.csv>
Legge ocr3x_testo*.jsonl e lavori_per_recita.csv. Scrive persone_per_recita.csv, direttori.csv, nomi_grezzi.csv,
prezzi_per_anno.csv, prime_assolute.csv e stampa la prova contro il cartellone indipendente.

Direttore: si cerca sul foglio un elenco di direttori noti, a nome intero, e si tiene quello scritto più grande
vicino alle parole "concertatore", "direttore" o "orchestra". Chi non è nell'elenco resta vuoto.
Sono letture automatiche: i totali sono stime.
"""
import argparse, collections as C, csv, difflib, glob, json, os, re, statistics as ST, unicodedata

ALTRI_DIRETTORI = '''ARTURO TOSCANINI;VICTOR DE SABATA;GUIDO CANTELLI;CARLO MARIA GIULINI;HERBERT VON KARAJAN;LEONARD BERNSTEIN;TULLIO SERAFIN;ANTONINO VOTTO;
GIANANDREA GAVAZZENI;NINO SANZOGNO;FRANCESCO MOLINARI PRADELLI;FRANCO CAPUANA;CLAUDIO ABBADO;RICCARDO MUTI;RICCARDO CHAILLY;DANIEL BARENBOIM;LORIN MAAZEL;
ZUBIN MEHTA;GEORGES PRETRE;WOLFGANG SAWALLISCH;MYUNG WHUN CHUNG;CARLOS KLEIBER;KARL BOHM;THOMAS SCHIPPERS;BRUNO BARTOLETTI;NELLO SANTI;OLIVIERO DE FABRITIIS;
ALBERTO EREDE;GINO MARINUZZI;DANIELE GATTI;FABIO LUISI;GUSTAVO DUDAMEL;ANDRE CLUYTENS;IGOR MARKEVITCH;DIMITRI MITROPOULOS;ETTORE GRACIS;BRUNO MADERNA;LUCIANO BERIO;
PIERRE BOULEZ;ROBERTO ABBADO;ADAM FISCHER;ZOLTAN PESKO;GIUSEPPE PATANE;GIUSEPPE DEL CAMPO;ANTONIO GUARNIERI;MARIO ROSSI;JONEL PERLEA;ARGEO QUADRI;LOVRO VON MATACIC;
PATRICK FOURNILLIER;DAVID COLEMAN;ARMANDO GATTO;ALEXANDER LAZAREV;MICHELE MARIOTTI;ENRIQUE MAZZOLA;ANTONIO PAPPANO;SIMONE YOUNG;KIRILL PETRENKO;VALERY GERGIEV;
JEFFREY TATE;SEMYON BYCHKOV;STEFANO RANZANI;EVELINO PIDO;MICHAEL TILSON THOMAS;RAFAEL KUBELIK;SERGIU CELIBIDACHE;HERMANN SCHERCHEN;JOHN BARBIROLLI;RENE LEIBOWITZ;
LUCIANO ROSADA;PAUL CONNELLY;KEVIN RHODES;FELIX KORBINIAN;ISSAY DOBROWEN;FERNANDO PREVITALI;ETTORE PANIZZA;WILHELM FURTWANGLER;SERGIO FAILONI;GIORGIO GUALERZI;
HANS WERNER HENZE;JOHN PRITCHARD;GARY BERTINI;JOHN BARBIROLLI;PETER MAAG;MIGUEL ANGEL GOMEZ MARTINEZ;NICOLA RESCIGNO;NELLO SANTI;GIUSEPPE SINOPOLI;RICCARDO FRIZZA;
PAOLO CARIGNANI;DANIELE RUSTIONI;PINCHAS STEINBERG;ALAIN ALTINOGLU;TOMAS HANUS;ANDREA BATTISTONI;MASSIMO ZANETTI;ALBERTO ZEDDA;CLAUDIO SCIMONE;OTTAVIO ZIINO'''
NO_RIGA = re.compile(r'REGIA|SCENE|COSTUMI|COREOGRAF|LIBRETTO|MUSICA DI|OPERA IN|MELODRAMMA')
PART = {'DE', 'DI', 'DEL', 'DELLA', 'DAL', 'VAN', 'VON', 'LA', 'LE', 'DA', 'MC', 'MAC', 'EL', 'SAN', 'SANTA'}
VIETATE = set('''TEATRO SCALA ALLA DELLA ORE STAGIONE LIRICA PREZZI ORCHESTRA CORO MAESTRO DIRETTORE REGIA SCENE COSTUMI BALLO PRIMA SECONDA TERZA QUARTA QUINTA SESTA
SETTIMA OTTAVA NONA DECIMA RAPPRESENTAZIONE RECITA MUSICA ATTI ATTO DOMENICA LUNEDI MARTEDI MERCOLEDI GIOVEDI VENERDI SABATO GENNAIO FEBBRAIO MARZO APRILE MAGGIO GIUGNO
LUGLIO AGOSTO SETTEMBRE OTTOBRE NOVEMBRE DICEMBRE PLATEA GALLERIA PALCHI POLTRONE POLTRONA INGRESSO BIGLIETTI TASSE ABBONAMENTO TURNO FUORI SERATA MILANO PICCOLA PERSONAGGI
INTERPRETI OPERA MELODRAMMA LIBRETTO EDIZIONE CASA MUSICALE RICORDI SONZOGNO SPA PROPRIETA NUOVA PRODUZIONE ALLESTIMENTO BALLETTO BALLETTI CONCERTO SINFONICO STRAORDINARIO
FILARMONICA MIMI COMPARSE SIGNORI SIGNORE ENTE AUTONOMO CORPO SCUOLA ACCADEMIA INTESA SANPAOLO VIETATO FUMARE SOLISTI ARTISTICHE MASSE LABORATORI SARTORIA LUCI COREOGRAFIA
ASSISTENTE COLLABORATORE TECNICO SERVIZIO CAPO REPARTO ALLESTIMENTI TEL PER'''.split())
RE_LIRE = re.compile(r'(?:L\.?|LIRE|£)\s*(\d{1,3}(?:[. ]\d{3})+|\d{3,6})')
RE_EURO = re.compile(r'(?:€|EURO|EUR)\s*(\d{1,4})(?:[.,]\d{2})?')


def norma(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().upper()
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z ]+', ' ', s)).strip()


def nomi_in(testo):
    """Gruppi di 2-4 parole tutte maiuscole: sulle locandine i nomi degli artisti sono scritti così."""
    t = unicodedata.normalize('NFKD', testo or '').encode('ascii', 'ignore').decode()
    usc, cor = [], []
    for w in re.sub(r"[^A-Za-z' ]+", ' ', t).split() + ['']:
        if len(w) >= 2 and w.upper() == w and w.replace("'", '').isalpha() and w not in VIETATE:
            cor.append(w)
        else:
            if 2 <= len(cor) <= 4 and any(len(c) >= 4 and c not in PART for c in cor):
                usc.append(' '.join(cor))
            cor = []
    return usc


RE_POSTO = re.compile(r'POLTRONA\b|POLTRONE\b|POSTO UNICO|POSTO (DI |IN )?PLATEA|POSTI (DI |IN )?PLATEA')


def prezzo_poltrona(righe):
    """Il primo prezzo scritto dopo 'poltrona di platea' o 'posto unico'. La poltroncina non conta. None se non si legge."""
    for r in righe:
        t = (r.get('t') or '').upper()
        m = RE_POSTO.search(t)
        if not m or 'GALLERIA' in t[:m.start()]:
            continue
        coda = t[m.end():]
        # se prima del prezzo si parla di poltroncina o galleria, la riga non è quella giusta
        lire, euro = RE_LIRE.search(coda), RE_EURO.search(coda)
        if lire and not re.search(r'POLTRONCIN|GALLERIA', coda[:lire.start()]):
            v = int(re.sub(r'[. ]', '', lire.group(1)))
            if 50 <= v <= 1000000:
                return ('L', v)
        if euro and not re.search(r'POLTRONCIN|GALLERIA', coda[:euro.start()]):
            v = int(euro.group(1))
            if 5 <= v <= 3000:
                return ('E', v)
    return None


def moda(v):
    c = C.Counter(v)
    return c.most_common(1)[0][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    ap.add_argument('--cartellone', required=True)
    ap.add_argument('--interpreti', required=True)
    a = ap.parse_args()
    U = a.cartella
    testo = {}
    for p in glob.glob(os.path.join(U, 'ocr3x_testo*.jsonl')):
        with open(p, encoding='utf-8') as f:
            for l in f:
                x = json.loads(l)
                testo[x['file']] = x.get('righe') or []
    rec = list(csv.DictReader(open(os.path.join(U, 'lavori_per_recita.csv'), encoding='utf-8-sig')))
    car = [r for r in csv.DictReader(open(a.cartellone, encoding='utf-8-sig')) if re.match(r'\d{4}-\d{2}-\d{2}', r['data'] or '') and r['data'] >= '1943-12-26']

    noti = set(norma(n) for n in ALTRI_DIRETTORI.replace('\n', '').split(';'))
    for r in car:
        for n in re.split(r'[;,]| con | e ', r['direttore'] or ''):
            n = norma(n)
            if 2 <= len(n.split()) <= 3 and 'COMPOSITORE' not in n:
                noti.add(n)
    # nel cartellone il campo direttore contiene anche maestri del coro e cantanti
    noti -= {'VITTORE VENEZIANI', 'BRUNO CASONI', 'ALDA NONI', 'GINO DEL SIGNORE', 'ROMANO GANDOLFI', 'ROBERTO GABBIANI', 'ANGELO MERCURIALI', 'ENRICO CAMPI', 'GINO PENNO', 'ALBERTO MALAZZI', 'DIANA DAMRAU', 'JOSEF GREINDL GURNEMANZ', 'THOMAS HANUS', 'ARMANDO GALTO', 'WILHELM FUTRWANGER', 'SIR ANTONIO PAPPANO', 'RENAUD CAPUCON', 'ENRICO MELOZZI'}
    noti = sorted(noti)
    compatti = {n: n.replace(' ', '') for n in noti}
    # filtro veloce: parte iniziale del cognome
    per_chiave = C.defaultdict(list)
    for n in noti:
        per_chiave[n.split()[-1][:4]].append(n)
    print('direttori noti', len(noti))
    memo = {}

    def nomi_noti(riga):
        if riga in memo:
            return memo[riga]
        c = norma(riga).replace(' ', '')
        tro = set()
        for k, v in per_chiave.items():
            if k in c:
                for n in v:
                    q = compatti[n]
                    m = difflib.SequenceMatcher(None, q, c).find_longest_match(0, len(q), 0, len(c))
                    # nome intero: quasi tutto il nome deve trovarsi di fila, o in due pezzi
                    d = difflib.SequenceMatcher(None, q, c)
                    uguali = sum(b.size for b in d.get_matching_blocks() if b.size >= 3)
                    if uguali >= 0.88 * len(q) and m.size >= 5:
                        tro.add(n)
        memo[riga] = tro
        return tro

    usc = []
    cdir = C.Counter()
    cnomi = C.Counter()
    tit = C.defaultdict(C.Counter)
    for x in rec:
        righe = sorted(testo.get(x['file'], []), key=lambda r: r.get('y', 0))
        best = None
        for i, r in enumerate(righe):
            t = r.get('t') or ''
            if NO_RIGA.search(norma(t)):
                continue
            for n in nomi_noti(t):
                if n == 'ARTURO TOSCANINI' and x['data'] > '19521231':
                    continue  # dopo il 1952 è il nome di una sala o di un'orchestra, non di chi dirige
                prec = norma(righe[i - 1].get('t')) if i else ''
                qui = norma(t)
                bonus = 2000 if re.search(r'CONCERTATORE|DIRETTORE D|DIREZIONE|ORCHESTRA', prec + ' ' + qui) else 0
                malus = -2000 if re.search(r'REGIA|CORO|SCENE|COSTUMI|COREOGRAF|PIANOFORTE', prec) else 0
                s = r.get('h', 0) + bonus + malus
                if best is None or s > best[0]:
                    best = (s, n)
        d = best[1] if best else ''
        if d:
            cdir[d] += 1
        cast = set()
        if x['tipo'] in ('Opera', 'Balletto'):
            for r in righe:
                cast.update(nomi_in(r.get('t')))
        for n in cast:
            cnomi[n] += 1
        pz = prezzo_poltrona(righe)
        tutto = ' '.join((r.get('t') or '').upper() for r in righe)
        assoluta = bool(re.search(r'PRIMA\s+(RAPPRESENTAZIONE\s+|ESECUZIONE\s+)?ASSOLUTA', tutto))
        usc.append({'data': x['data'], 'ora': x['ora'], 'sigla': x['sigla'], 'tipo': x['tipo'], 'titolo': x['titolo_principale'], 'direttore': d, 'file': x['file'],
                    'prezzo': pz[1] if pz else '', 'moneta': pz[0] if pz else '', 'prima_assoluta': 'si' if assoluta else '', 'nomi': ' ; '.join(sorted(cast))})

    def scrivi(nome, campi, righe):
        with open(os.path.join(U, nome), 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(campi)
            w.writerows(righe)

    # interpreti da un elenco scelto: il nome intero deve stare sul foglio, anche con piccoli errori di lettura
    el = list(csv.DictReader(open(a.interpreti, encoding='utf-8-sig')))
    conti = C.defaultdict(lambda: {'n': 0, 'prima': '', 'ultima': '', 'tit': C.Counter()})
    memo2 = {}

    def noti_in_riga(c):
        if c in memo2:
            return memo2[c]
        tro = set()
        for e in el:
            for q in e['cerca'].split('|'):
                q = q.replace(' ', '')
                if q in c:
                    tro.add(e['nome'])
                elif q[-4:] in c or q[:4] in c:
                    # finestra lunga come il nome: tollera una o due lettere lette male, non pezzi sparsi nella riga
                    for pz in re.finditer(re.escape(q[-4:]) + '|' + re.escape(q[:4]), c):
                        ini = pz.start() - (len(q) - 4) if pz.group() == q[-4:] else pz.start()
                        fin = max(0, ini)
                        if difflib.SequenceMatcher(None, q, c[fin:fin + len(q)]).ratio() >= 0.93:
                            tro.add(e['nome'])
                            break
        memo2[c] = tro
        return tro
    per_file = {}
    ruolo = {e['nome']: e['ruolo'] for e in el}
    for x in rec:
        if x['tipo'] not in ('Opera', 'Balletto'):
            continue
        tro = set()
        for r in testo.get(x['file'], []):
            tro |= noti_in_riga(norma(r.get('t')).replace(' ', ''))
        # chi canta sta sui fogli d'opera, chi danza su quelli di balletto
        vuole = 'canto' if x['tipo'] == 'Opera' else 'danza'
        tro = {n for n in tro if ruolo[n] == vuole}
        per_file[x['file']] = tro
        for n in tro:
            k = conti[n]
            k['n'] += 1
            k['prima'] = min(k['prima'] or x['data'], x['data'])
            k['ultima'] = max(k['ultima'], x['data'])
            if x['titolo_principale']:
                k['tit'][x['titolo_principale']] += 1
    scrivi('interpreti_noti.csv', ['nome', 'ruolo', 'locandine', 'prima', 'ultima', 'titoli'],
           [(n, ruolo[n], k['n'], k['prima'], k['ultima'], ' | '.join(f'{t}:{c}' for t, c in k['tit'].most_common(5))) for n, k in sorted(conti.items(), key=lambda q: -q[1]['n'])])
    print('INTERPRETI', [(n, k['n'], k['prima'][:4], k['ultima'][:4]) for n, k in sorted(conti.items(), key=lambda q: -q[1]['n'])])
    print('CALLAS', conti['Maria Callas']['tit'].most_common(30))
    # prova: cast del cartellone, per decennio, cognome sul foglio
    pd = C.defaultdict(list)
    for x in rec:
        pd[x['data']].append(x)
    prova = C.defaultdict(lambda: [0, 0])
    for r in car:
        if not r['interpreti']:
            continue
        d = r['data'].replace('-', '')
        if d not in pd:
            continue
        tt = ' '.join(norma(q.get('t')) for x in pd[d] for q in testo.get(x['file'], [])).replace(' ', '')
        for nn in re.split(r'[;,|]', r['interpreti']):
            nn = norma(nn)
            if len(nn) < 5 or len(nn.split()) < 2:
                continue
            prova[d[:3]][0] += 1
            prova[d[:3]][1] += nn.split()[-1] in tt
    print('PROVA cast per decennio (attesi, sul foglio)', sorted((k, v) for k, v in prova.items()))
    with open(os.path.join(U, 'persone_per_recita.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(usc[0]))
        w.writeheader()
        w.writerows(usc)
    scrivi('direttori.csv', ['nome', 'recite'], cdir.most_common())
    scrivi('nomi_grezzi.csv', ['nome', 'locandine'], [q for q in cnomi.most_common() if q[1] >= 5])

    anni = C.defaultdict(list)
    for x in usc:
        if x['moneta'] and x['tipo'] == 'Opera':
            anni[(x['data'][:4], x['moneta'])].append(x['prezzo'])
    op_anno = C.Counter(x['data'][:4] for x in usc if x['tipo'] == 'Opera')
    pr = [(y, m, len(v), op_anno[y], moda(v), ST.median(v), min(v), max(v)) for (y, m), v in sorted(anni.items())]
    scrivi('prezzi_per_anno.csv', ['anno', 'moneta', 'locandine_con_prezzo', 'opere_anno', 'prezzo_piu_frequente', 'mediana', 'min', 'max'], pr)

    pa = C.defaultdict(list)
    for x in usc:
        if x['prima_assoluta'] and x['tipo'] in ('Opera', 'Balletto'):
            pa[(x['sigla'], x['titolo'])].append(x['data'])
    scrivi('prime_assolute.csv', ['sigla', 'titolo', 'prima_data', 'locandine'], sorted(((k[0], k[1], min(v), len(v)) for k, v in pa.items()), key=lambda q: q[2]))

    print('direttore letto', sum(1 for x in usc if x['direttore']), 'su', len(usc), 'per tipo', [(t, sum(1 for x in usc if x['tipo'] == t and x['direttore']), sum(1 for x in usc if x['tipo'] == t)) for t in ('Opera', 'Balletto', 'Concerto')])
    print('DIRETTORI', cdir.most_common(30))
    print('PREZZI', [(q[0], q[1], q[2], q[4], q[5]) for q in pr])
    print('PRIME', sorted(((min(v), k[1], len(v)) for k, v in pa.items())))
    print('NOMI', cnomi.most_common(40))

    per_data = C.defaultdict(list)
    for x in usc:
        per_data[x['data']].append(x)
    tot = ok = vuoti = 0
    sb = []
    visti = set()
    per_dec = C.defaultdict(lambda: [0, 0, 0])
    for r in car:
        if not r['direttore'] or 'COMPOSITORE' in norma(r['direttore']):
            continue
        d = r['data'].replace('-', '')
        k = (d, r['direttore'])
        if d not in per_data or k in visti:
            continue
        visti.add(k)
        c = norma(re.split(r'[;,]| con ', r['direttore'])[0]).split()[-1]
        nos = [x['direttore'] for x in per_data[d]]
        tot += 1
        q = per_dec[d[:3]]
        q[0] += 1
        if any(c in n for n in nos):
            ok += 1
            q[1] += 1
        elif not any(nos):
            vuoti += 1
            q[2] += 1
        elif len(sb) < 30:
            sb.append((r['data'], r['titolo'], r['direttore'], nos))
    print('PROVA direttore: confronti', tot, 'giusti', ok, 'vuoti', vuoti, 'diversi', tot - ok - vuoti)
    print('per decennio (confronti, giusti, vuoti)', sorted((k, v) for k, v in per_dec.items()))
    print(sb)


if __name__ == '__main__':
    main()
