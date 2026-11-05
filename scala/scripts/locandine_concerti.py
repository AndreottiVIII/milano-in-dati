"""Quali compositori ci sono sul foglio di ogni concerto.

Uso: python -I -X utf8 locandine_concerti.py --cartella <risultati>
Legge ocr3x_testo*.jsonl, lavori_per_recita.csv e persone_per_recita.csv. Scrive concerti_compositori.csv.
Il catalogo dei concerti dà un brano solo e nessun autore: qui si cercano sul foglio i cognomi di un elenco di compositori.
Non si legge il fondo del foglio, dove stanno prezzi e indirizzi, e non vale un nome dopo "teatro", "via", "sala" e simili.
"""
import argparse, collections as C, csv, difflib, glob, json, os, random, re, unicodedata

ELENCO = '''Albéniz Albinoni Bach Barber Bartók Beethoven Bellini Berg Berio Berlioz Bernstein Bizet Bloch Boccherini Boito Borodin Boulez Brahms Britten Bruckner
Busoni Bussotti Cage Casella Castelnuovo-Tedesco Čajkovskij Chabrier Cherubini Chopin Cimarosa Clementi Copland Corelli Couperin Dallapiccola Debussy Delibes Donatoni Donizetti Dukas Dvořák
Elgar Falla Fauré Franck Frescobaldi Gabrieli Gershwin Ghedini Giordano Glinka Gluck Gounod Grieg Hándel Haydn Henze Hindemith Honegger Ives Janáček Kodály Lehár Leoncavallo Ligeti Liszt
Maderna Mahler Malipiero Mascagni Massenet Mendelssohn Messiaen Meyerbeer Milhaud Monteverdi Mozart Musorgskij Nono Offenbach Orff Paganini Paisiello Palestrina Pergolesi Petrassi
Pizzetti Poulenc Prokof'ev Puccini Purcell Rachmaninov Rameau Ravel Respighi Rimskij-Korsakov Rossini Saint-Saëns Sammartini Satie Scarlatti Schönberg Schubert Schumann Šostakovič Scriabin Sibelius
Skrjabin Smetana Stockhausen Strauss Stravinskij Szymanowski Telemann Tartini Tippett Varèse Verdi Vivaldi Wagner Weber Webern Weill Wolf-Ferrari Xenakis Zandonai'''.split()
# altre grafie sui fogli
VARIANTI = {'CIAIKOVSKIJ': 'Čajkovskij', 'CIAIKOWSKY': 'Čajkovskij', 'TCHAIKOVSKY': 'Čajkovskij', 'CAIKOVSKIJ': 'Čajkovskij', 'CAJKOVSKIJ': 'Čajkovskij', 'TCIAIKOVSKY': 'Čajkovskij', 'CIAIKOWSKI': 'Čajkovskij',
            'MUSSORGSKY': 'Musorgskij', 'MUSSORGSKIJ': 'Musorgskij', 'MOUSSORGSKY': 'Musorgskij', 'PROKOFIEV': "Prokof'ev", 'PROKOFIEFF': "Prokof'ev", 'PROKOFIEV': "Prokof'ev", 'PROKOFJEV': "Prokof'ev",
            'SCIOSTAKOVIC': 'Šostakovič', 'SHOSTAKOVICH': 'Šostakovič', 'SOSTAKOVIC': 'Šostakovič', 'SCHOENBERG': 'Schönberg', 'SCHONBERG': 'Schönberg', 'STRAWINSKY': 'Stravinskij', 'STRAWINSKIJ': 'Stravinskij', 'STRAVINSKY': 'Stravinskij', 'STRAWINSKI': 'Stravinskij',
            'HAENDEL': 'Hándel', 'HANDEL': 'Hándel', 'RACHMANINOFF': 'Rachmaninov', 'RACHMANINOW': 'Rachmaninov', 'RIMSKIJ': 'Rimskij-Korsakov', 'KORSAKOV': 'Rimskij-Korsakov', 'SKRIABIN': 'Skrjabin',
            'JANACEK': 'Janáček', 'BARTOK': 'Bartók', 'DVORAK': 'Dvořák', 'ALBENIZ': 'Albéniz', 'KODALY': 'Kodály', 'FAURE': 'Fauré', 'VARESE': 'Varèse', 'LEHAR': 'Lehár', 'SAINT': 'Saint-Saëns', 'WOLF': 'Wolf-Ferrari', 'CASTELNUOVO': 'Castelnuovo-Tedesco'}
NO_PRIMA = {'TEATRO', 'VIA', 'SALA', 'PIAZZA', 'CONSERVATORIO', 'ISTITUTO', 'CORSO', 'LARGO', 'AUDITORIUM', 'CASA', 'VIALE', 'FONDAZIONE', 'ORCHESTRA', 'SOCIETA', 'CIVICA', 'CORO', 'QUARTETTO', 'SCUOLA', 'TRIO', 'PREMIO', 'CONCORSO', 'ACCADEMIA', 'CIRCOLO', 'MARIO', 'CLAUDIO', 'FRANK', 'RICHARD', 'JOSEPH', 'MARIA'}
NON_DI_NOME = {'MARTIN', 'ROSSI', 'GABRIELE', 'GABRIELLA'}
PERSONE = {'SARA', 'GABRIELE', 'CARLO', 'ANNA', 'LUCA', 'PAOLO'}  # interpreti con cognome da compositore


def norma(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().upper()
    return re.sub(r"[^A-Z' -]+", ' ', s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    a = ap.parse_args()
    U = a.cartella
    voc = dict(VARIANTI)
    for n in ELENCO:
        voc.setdefault(norma(n).replace("'", '').replace('-', ' ').split()[0], n)
    voc = {k: v for k, v in voc.items() if k not in NON_DI_NOME}
    lunghi = [k for k in voc if len(k) >= 7]
    T = {}
    for p in glob.glob(os.path.join(U, 'ocr3x_testo*.jsonl')):
        for l in open(p, encoding='utf-8'):
            x = json.loads(l)
            T[x['file']] = x.get('righe') or []
    dire = {x['file']: norma(x['direttore']).split()[-1] if x['direttore'] else '' for x in csv.DictReader(open(os.path.join(U, 'persone_per_recita.csv'), encoding='utf-8-sig'))}
    memo = {}

    def voce(w):
        if w in memo:
            return memo[w]
        q = voc.get(w, '')
        if not q and len(w) >= 8 and w not in NON_DI_NOME:
            m = difflib.get_close_matches(w, lunghi, n=1, cutoff=.88)
            q = voc[m[0]] if m else ''
        memo[w] = q
        return q
    usc, tot = [], C.Counter()
    rec = [x for x in csv.DictReader(open(os.path.join(U, 'lavori_per_recita.csv'), encoding='utf-8-sig')) if x['tipo'] in ('Concerto', 'Recital')]
    for x in rec:
        righe = T.get(x['file'], [])
        fondo = max([r.get('y', 0) for r in righe] or [1])
        tro = C.Counter()
        for r in righe:
            if r.get('y', 0) > .88 * fondo:
                continue
            testo_riga = r.get('t') or ''
            # nome di un luogo o di un'istituzione: Conservatorio "G. Verdi", Casa Verdi
            luogo = bool(re.search(r'["«»“”]|CONSERVATORIO|CASA DI RIPOSO|ISTITUTO|FONDAZIONE|SALA VERDI', testo_riga.upper()))
            pz = re.sub(r'[\'-]', ' ', norma(testo_riga)).split()
            for i, w in enumerate(pz):
                q = voce(w) if len(w) >= 3 else ''
                if not q or (i and pz[i - 1] in NO_PRIMA):
                    continue
                if luogo and q in ('Verdi', 'Donizetti', 'Rossini', 'Puccini', 'Bellini', 'Cherubini'):
                    continue
                if q in ('Rossini', 'Bellini') and i and pz[i - 1] in PERSONE:
                    continue
                if q == 'Nono' and not (i and pz[i - 1] in ('LUIGI', 'L')):
                    continue  # "nono concerto"
                if norma(q).split()[0].replace("'", '') == dire.get(x['file']):
                    continue
                tro[q] += 1
        m = [k for k, _ in tro.most_common()]
        usc.append({'file': x['file'], 'data': x['data'], 'musiche': ' ; '.join(m)})
        tot.update(m)
    with open(os.path.join(U, 'concerti_compositori.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['file', 'data', 'musiche'])
        w.writeheader()
        w.writerows(usc)
    print('fogli', len(usc), 'con almeno un compositore', sum(1 for u in usc if u['musiche']))
    print(tot.most_common(40))
    print('per decennio', sorted(C.Counter(u['data'][:3] + '0' for u in usc if u['musiche']).items()), sorted(C.Counter(u['data'][:3] + '0' for u in usc).items()))
    print('15/1/1996', [u for u in usc if u['data'] == '19960115'])
    random.seed(23)
    print('campione', [(u['file'][:12], u['musiche'][:60]) for u in random.sample(usc, 12)])


if __name__ == '__main__':
    main()
