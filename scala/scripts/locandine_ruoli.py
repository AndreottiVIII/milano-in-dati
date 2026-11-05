"""Prova: chi ha i ruoli principali sulle locandine dei titoli più dati.

Uso: python -I -X utf8 locandine_ruoli.py --cartella <risultati>
Per ogni titolo c'è un elenco di personaggi. Sul foglio si cerca il personaggio scritto in minuscolo (il titolo è in maiuscolo)
e il nome tutto maiuscolo più vicino, sulla stessa riga o subito sotto. Scrive ruoli_letti.csv e stampa la classifica.
"""
import argparse, collections as C, csv, difflib, glob, json, os, random, re, unicodedata

RUOLI = {
 'Balletto': {
  'Giselle': ['Giselle', 'Albrecht', 'Albert', 'Alberto', 'Loys'], 'Il lago dei cigni': ['Odette', 'Sigfrido', 'Siegfried'],
  'Romeo e Giulietta': ['Giulietta', 'Romeo'], 'La bella addormentata': ['Aurora', 'Desiderio', 'Désiré', 'Florimondo', 'Florimund'],
  'Lo schiaccianoci': ['Clara', 'Maria', 'Mascha', 'Masha'], 'Don Chisciotte': ['Kitri', 'Basilio'], 'Coppélia': ['Swanilda', 'Swanhilda', 'Franz'],
  'Onegin': ['Tatiana', 'Onegin'], "L'histoire de Manon": ['Manon', 'Des Grieux'], 'Cenerentola': ['Cenerentola'], 'La Bayadère': ['Nikiya', 'Solor'],
  'La Sylphide': ['Sylphide', 'Silfide', 'James'], 'La bisbetica domata': ['Caterina', 'Petruccio'], 'La dame aux camélias': ['Marguerite', 'Armand'],
  'Sogno di una notte di mezza estate': ['Titania', 'Oberon'], 'Excelsior': ['La Luce', 'La Civiltà', "L'Oscurantismo"]},
 'Opera': {
  'La bohème': ['Mimì', 'Rodolfo', 'Marcello', 'Musetta'], 'Madama Butterfly': ['Cio-Cio-San', 'Pinkerton', 'Sharpless'],
  'Il barbiere di Siviglia': ['Rosina', 'Figaro', 'Almaviva', 'Bartolo', 'Basilio'], 'Aida': ['Aida', 'Radames', 'Amneris', 'Amonasro'],
  "L'elisir d'amore": ['Adina', 'Nemorino', 'Belcore', 'Dulcamara'], 'Tosca': ['Floria Tosca', 'Cavaradossi', 'Scarpia'], 'Rigoletto': ['Rigoletto', 'Gilda', 'Il Duca', 'Duca di Mantova'],
  'La traviata': ['Violetta', 'Alfredo', 'Germont'], 'La Cenerentola': ['Angelina', 'Don Ramiro', 'Dandini', 'Don Magnifico'], 'Turandot': ['Turandot', 'Calaf', 'Liù'],
  'Lucia di Lammermoor': ['Lucia', 'Edgardo', 'Enrico'], 'Carmen': ['Carmen', 'Don José', 'Escamillo', 'Micaela'], 'Falstaff': ['Falstaff', 'Ford', 'Alice'],
  'Le nozze di Figaro': ['Figaro', 'Susanna', 'La Contessa', 'Il Conte'], 'Don Carlo': ['Filippo II', 'Don Carlo', 'Rodrigo', 'Elisabetta', 'Eboli'],
  'Un ballo in maschera': ['Riccardo', 'Amelia', 'Renato', 'Ulrica'], 'Don Giovanni': ['Don Giovanni', 'Leporello', 'Donna Anna', 'Donna Elvira', 'Don Ottavio'],
  'Il trovatore': ['Leonora', 'Manrico', 'Azucena', 'Il Conte di Luna'], 'Simon Boccanegra': ['Simon Boccanegra', 'Amelia', 'Gabriele Adorno', 'Fiesco'],
  'Macbeth': ['Macbeth', 'Lady Macbeth', 'Banco'], 'Norma': ['Norma', 'Pollione', 'Adalgisa'], 'Otello': ['Otello', 'Desdemona', 'Jago'],
  'Nabucco': ['Nabucco', 'Abigaille', 'Zaccaria'], 'La forza del destino': ['Leonora', 'Don Alvaro', 'Don Carlo', 'Padre Guardiano'],
  'Così fan tutte': ['Fiordiligi', 'Dorabella', 'Ferrando', 'Guglielmo', 'Despina'], 'Boris Godunov': ['Boris']},
}
VIETATE = set('TEATRO SCALA ALLA DELLA CORO ORCHESTRA MAESTRO DIRETTORE REGIA SCENE COSTUMI BALLO CORPO PRIMA SECONDA RAPPRESENTAZIONE MUSICA'.split())


def asc(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()


def nomi(testo):
    """Gruppi di 2-4 parole tutte maiuscole, con la loro posizione."""
    t = asc(testo)
    usc = []
    for m in re.finditer(r"(?:\b[A-Z][A-Z'\-]+\b[ ]?){2,4}", t):
        pz = m.group().split()
        pz = [p for p in pz if p not in VIETATE]
        if len(pz) >= 2 and any(len(p) >= 4 for p in pz):
            usc.append((m.start(), m.end(), ' '.join(pz)))
    return usc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    a = ap.parse_args()
    U = a.cartella
    T = {}
    for p in glob.glob(os.path.join(U, 'ocr3x_testo*.jsonl')):
        for l in open(p, encoding='utf-8'):
            x = json.loads(l)
            T[x['file']] = x.get('righe') or []
    rec = list(csv.DictReader(open(os.path.join(U, 'lavori_per_recita.csv'), encoding='utf-8-sig')))
    usc = []
    fogli = C.Counter()
    letti = C.Counter()
    for x in rec:
        tp = x['tipo']
        titolo = x['titolo_principale']
        if tp not in RUOLI or titolo not in RUOLI[tp] or x['per_bambini'] == 'si':
            continue
        fogli[titolo] += 1
        righe = sorted(T.get(x['file'], []), key=lambda r: r.get('y', 0))
        trov = 0
        for ruolo in RUOLI[tp][titolo]:
            pat = re.compile(r'\b' + re.escape(asc(ruolo)) + r'\b')
            for i, r in enumerate(righe):
                t = asc(r.get('t'))
                m = pat.search(t)
                if not m or (len(t) < len(ruolo) + 2 and r.get('h', 0) > 90):
                    continue
                cand = []
                for s, e, n in nomi(t):
                    gap = s - m.end() if s >= m.end() else m.start() - e
                    if gap >= 0:
                        cand.append((gap - (1 if s >= m.end() else 0), n))
                if not cand and i + 1 < len(righe):
                    cand = [(1000, n) for _, _, n in nomi(righe[i + 1].get('t'))[:1]]
                if cand:
                    cand.sort()
                    usc.append({'data': x['data'], 'tipo': tp, 'titolo': titolo, 'ruolo': ruolo, 'nome': cand[0][1], 'file': x['file'], 'riga': r.get('t')[:90]})
                    trov += 1
                    break
        if trov:
            letti[titolo] += 1
    # unire le varianti di lettura
    freq = C.Counter(u['nome'] for u in usc)
    base = C.defaultdict(list)
    mappa = {}
    for n, c in freq.most_common():
        b = base[n[0]]
        m = difflib.get_close_matches(n, b, n=1, cutoff=0.86) if c < 40 else []
        if m:
            mappa[n] = m[0]
        else:
            b.append(n)
            mappa[n] = n
    for u in usc:
        u['nome'] = mappa[u['nome']].title()
    with open(os.path.join(U, 'ruoli_letti.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(usc[0]))
        w.writeheader()
        w.writerows(usc)
    print('titoli', {k: f'{letti[k]}/{v}' for k, v in fogli.most_common()})
    for tp in RUOLI:
        c = C.defaultdict(set)
        for u in usc:
            if u['tipo'] == tp:
                c[u['nome']].add((u['data'], u['titolo']))
        print(tp, [(n, len(v)) for n, v in sorted(c.items(), key=lambda kv: -len(kv[1]))[:32]])
    for n in ('Carla Fracci', 'Maria Meneghini Callas', 'Maria Callas', 'Luciana Savignano', 'Roberto Bolle', 'Renata Tebaldi', 'Luciano Pavarotti', 'Mirella Freni'):
        q = [u for u in usc if u['nome'] == n]
        print(n, len({(u['data']) for u in q}), C.Counter(u['ruolo'] for u in q).most_common(7), sorted({u['data'][:4] for u in q})[:1], sorted({u['data'][:4] for u in q})[-1:])
    random.seed(5)
    print('campione')
    for u in random.sample(usc, 22):
        print(' ', u['data'], u['titolo'][:14], u['ruolo'], '=>', u['nome'], '|', u['riga'][:60])


if __name__ == '__main__':
    main()
