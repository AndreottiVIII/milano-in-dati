"""Dati per la parte "serata per serata" della pagina docs/scala/.

Uso: python -I -X utf8 locandine_pagina.py --cartella <risultati> --uscita <docs/scala/data/serate>
Legge lavori_per_recita.csv, persone_per_recita.csv, opere.csv, balletti.csv, compositori.csv, direttori.csv,
interpreti_noti.csv, prezzi_per_anno.csv, per_anno.csv, riepilogo.json, numeri.json e prime_assolute_verificate.csv.
Nessun nome di file, nessun indirizzo di immagine: solo fatti (data, ora, tipo, titolo, autore, altri lavori, sala, direttore, per bambini, fonte).
"""
import argparse, collections as C, csv, json, os, re, unicodedata

ARTICOLI = re.compile(r'^(IL|LO|LA|I|GLI|LE|L|UN|UNA|UNO|DIE|DER|DAS|THE|LES)\s+')
TIPI = {'Opera': 'O', 'Balletto': 'B', 'Concerto': 'C', 'Recital': 'R', 'Manifestazione': 'M', 'Diversi': 'D', 'Altro': 'A', '': 'A'}
NOMI_DIR = {'GIANANDREA GAVAZZENI': 'Gianandrea Gavazzeni', 'VICTOR DE SABATA': 'Victor de Sabata', 'HERBERT VON KARAJAN': 'Herbert von Karajan',
            'LOVRO VON MATACIC': 'Lovro von Matačić', 'GEORGES PRETRE': 'Georges Prêtre', 'MYUNG WHUN CHUNG': 'Myung-whun Chung', 'KARL BOHM': 'Karl Böhm',
            'GIUSEPPE PATANE': 'Giuseppe Patanè', 'ANDRE CLUYTENS': 'André Cluytens', 'ZOLTAN PESKO': 'Zoltán Peskó', 'OLIVIERO DE FABRITIIS': 'Oliviero De Fabritiis',
            'GIUSEPPE DEL CAMPO': 'Giuseppe Del Campo', 'EVELINO PIDO': 'Evelino Pidò', 'BERTRAND DE BILLY': 'Bertrand de Billy', 'WILHELM FURTWANGLER': 'Wilhelm Furtwängler'}


# compositore dei balletti più dati. La lettura automatica attacca ai balletti l'autore sbagliato: fuori da qui resta vuoto.
MUSICA_BALLETTI = {'IL LAGO DEI CIGNI': "Pëtr Il'ič Čajkovskij", 'LAGO DEI CIGNI': "Pëtr Il'ič Čajkovskij", 'GISELLE': 'Adolphe Adam', 'ROMEO E GIULIETTA': "Sergej Prokof'ev",
                   'LO SCHIACCIANOCI': "Pëtr Il'ič Čajkovskij", 'SCHIACCIANOCI': "Pëtr Il'ič Čajkovskij", 'BELLA ADDORMENTATA': "Pëtr Il'ič Čajkovskij", 'DON CHISCIOTTE': 'Ludwig Minkus',
                   'CENERENTOLA': "Sergej Prokof'ev", 'COPPELIA': 'Léo Delibes', 'PETRUSKA': 'Igor Stravinskij', 'UCCELLO DI FUOCO': 'Igor Stravinskij', 'BOLERO': 'Maurice Ravel',
                   'EXCELSIOR': 'Romualdo Marenco', 'BAYADERE': 'Ludwig Minkus', 'APOLLON MUSAGETE': 'Igor Stravinskij', 'SAGRA DELLA PRIMAVERA': 'Igor Stravinskij',
                   'SILFIDI': 'Fryderyk Chopin', 'TRICORNO': 'Manuel de Falla', 'AMORE STREGONE': 'Manuel de Falla', 'QUATTRO STAGIONI': 'Giuseppe Verdi',
                   'CAPRICCIO SPAGNOLO': 'Nikolaj Rimskij-Korsakov', 'APRES MIDI D UN FAUNE': 'Claude Debussy', 'SERENADE': "Pëtr Il'ič Čajkovskij", 'CORSAIRE': 'Adolphe Adam',
                   'SOGNO DI UNA NOTTE DI MEZZA ESTATE': 'Felix Mendelssohn', 'STRADA': 'Nino Rota', 'FIGLIOL PRODIGO': "Sergej Prokof'ev", 'QUATTRO TEMPERAMENTI': 'Paul Hindemith',
                   'THEME AND VARIATIONS': "Pëtr Il'ič Čajkovskij", 'BALLETTO IMPERIALE': "Pëtr Il'ič Čajkovskij", 'ONEGIN': "Pëtr Il'ič Čajkovskij", 'HISTOIRE DE MANON': 'Jules Massenet',
                   'DAME AUX CAMELIAS': 'Fryderyk Chopin', 'BISBETICA DOMATA': 'Domenico Scarlatti'}


def musica(t):
    return MUSICA_BALLETTI.get(chiave(t), '')


def bello(t):
    if t and t.upper() == t:
        t = t.capitalize()
        t = re.sub(r"(['’])(\w)", lambda m: m.group(1) + m.group(2).lower(), t)
    return t


def chiave(t):
    s = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode().upper()
    return ARTICOLI.sub('', re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]+', ' ', s)).strip())


def nome(n):
    return NOMI_DIR.get(n) or n.title()


def leggi(U, f):
    return list(csv.DictReader(open(os.path.join(U, f), encoding='utf-8-sig')))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    ap.add_argument('--uscita', required=True)
    a = ap.parse_args()
    U, O = a.cartella, a.uscita
    os.makedirs(O, exist_ok=True)
    rec = leggi(U, 'lavori_per_recita.csv')
    per = {x['file']: x for x in leggi(U, 'persone_per_recita.csv')}
    rie = json.load(open(os.path.join(U, 'riepilogo.json'), encoding='utf-8'))
    num = json.load(open(os.path.join(U, 'numeri.json'), encoding='utf-8'))

    # una riga per recita, un file per decennio
    dec = C.defaultdict(list)
    for x in rec:
        d = nome(per[x['file']]['direttore']) if per[x['file']]['direttore'] else ''
        t = bello(x['titolo_principale'])
        if x['verifica'] == 'dubbio' and x['origine_titolo'] != 'scheda':
            t = ''
        sala = x['sala'] or x['sala_stimata']
        dec[x['data'][:3] + '0'].append([x['data'], x['ora'], TIPI.get(x['tipo'], 'A'), t, musica(t) if x['tipo'] == 'Balletto' else x['autore_principale'], bello(x['altri_lavori']), sala, d, 1 if x['per_bambini'] == 'si' else 0])
    # fino al 2023 comandano le locandine. Dal 2024 sono incomplete (concerti quasi assenti): si aggiunge il sito della Scala.
    # Colonna 9: '' locandina, 's' sito della Scala, 'a' altre fonti (aperture di stagione senza locandina).
    for v in dec.values():
        for r in v:
            r.append('')
    pul = os.path.join(U, '..', 'pulito')
    viste = C.defaultdict(list)
    for v in dec.values():
        for r in v:
            viste[r[0]].append(chiave(r[3]))
    for x in csv.DictReader(open(os.path.join(pul, '_scala_sito.csv'), encoding='utf-8-sig')):
        d = (x['data'] or '').replace('-', '')
        if len(d) != 8 or d < '20240101':
            continue
        t = chiave(x['titolo'])
        if any(t and (t in q or q in t) for q in viste[d] if q):
            continue
        g = x['genere'] or ''
        tipo = 'O' if g.startswith('opera') else 'B' if g.startswith('balletto') else 'C' if g.startswith('concerto') else 'A'
        dec[d[:3] + '0'].append([d, '', tipo, x['titolo'], x['autore'] if tipo in 'OB' else '', '', x['sala'], x['direttore'].title() if x['direttore'] else '', 0, 's'])
        viste[d].append(t)
    for x in csv.DictReader(open(os.path.join(pul, 'aperture.csv'), encoding='utf-8-sig')):
        d = (x['data'] or '').replace('-', '')
        if len(d) == 8 and '19431226' <= d <= '20231231' and d not in viste:
            dec[d[:3] + '0'].append([d, '', 'O', re.sub(r'\s*\(.*?\)', '', x['titolo']), x['compositore'], '', '', x['direttore'], 0, 'a'])
            viste[d].append(chiave(x['titolo']))
    # titolo per anno, per il cartellone della pagina: 1944-2023 solo locandine
    ta = C.defaultdict(lambda: {'n': 0, 'autore': '', 'dir': C.Counter(), 'sale': C.Counter()})
    gen = {'Opera': 'opera', 'Balletto': 'balletto', 'Concerto': 'concerto', 'Recital': 'concerto'}
    for x in rec:
        tipi_riga = [(x['titolo_principale'], x['tipo'], x['autore_principale'])] + [(t, x['tipo'], '') for t in x['altri_lavori'].split(' ; ') if t]
        for t, tp, au in tipi_riga:
            if not t or (x['verifica'] == 'dubbio' and x['origine_titolo'] != 'scheda'):
                continue
            q = ta[(x['data'][:4], chiave(t), gen.get(tp, 'altro'))]
            q['titolo'] = q.get('titolo') or bello(t)
            q['autore'] = musica(t) if tp == 'Balletto' else (q['autore'] or au)
            q['n'] += 1
            if per[x['file']]['direttore']:
                q['dir'][nome(per[x['file']]['direttore'])] += 1
            if x['sala'] or x['sala_stimata']:
                q['sale'][x['sala'] or x['sala_stimata']] += 1
    with open(os.path.join(U, 'titoli_anno_locandine.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['anno', 'titolo', 'autore', 'genere', 'recite', 'direttori', 'sala'])
        for (y, _, g), q in sorted(ta.items()):
            w.writerow([y, q['titolo'], q['autore'], g, q['n'], ' ; '.join(n for n, _ in q['dir'].most_common(3)), q['sale'].most_common(1)[0][0] if q['sale'] else ''])
    for k, v in dec.items():
        v.sort(key=lambda r: (r[0], r[1]))
        json.dump(v, open(os.path.join(O, f'{k}.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

    # classifiche
    opere = leggi(U, 'opere.csv')
    balli = leggi(U, 'balletti.csv')
    comp = leggi(U, 'compositori.csv')
    dirs = leggi(U, 'direttori.csv')
    inter = leggi(U, 'interpreti_noti.csv')
    def r_op(x):
        return {'t': x['Titolo'], 'a': musica(x['Titolo']) if x in balli else x['Autore'], 'n': int(x['Recite']), 'b': int(x['Per bambini'] or 0), 'da': x['Prima'][-4:], 'al': x['Ultima'][-4:]}

    # opere per decennio
    pd = C.defaultdict(C.Counter)
    for x in rec:
        if x['tipo'] == 'Opera' and x['titolo_principale']:
            pd[x['data'][:3] + '0'][x['titolo_principale']] += 1
    per_dec = {k: [{'t': bello(t), 'n': n} for t, n in v.most_common(10)] for k, v in sorted(pd.items())}

    pz = []
    for x in leggi(U, 'prezzi_per_anno.csv'):
        if x['moneta'] == 'L' and int(x['locandine_con_prezzo']) >= 10 and '1953' <= x['anno'] <= '1993':
            pz.append({'y': int(x['anno']), 'l': round(float(x['mediana'])), 'n': int(x['locandine_con_prezzo'])})

    anni = C.defaultdict(C.Counter)
    for x in rec:
        anni[x['data'][:4]][TIPI.get(x['tipo'], 'A')] += 1
    per_anno = [dict(y=int(k), **v) for k, v in sorted(anni.items())]
    decenni = {}
    for k, v in num['decenni'].items():
        decenni[k] = {'t': v.get('Totale', 0), 'O': v.get('Opera', 0), 'B': v.get('Balletto', 0), 'C': v.get('Concerto', 0) + v.get('Recital', 0),
                      'A': v.get('Altro', 0) + v.get('Manifestazione', 0) + v.get('Diversi', 0), 'g': v.get('Di giorno (prima delle 18)', 0)}
    prime = leggi(U, 'prime_assolute_verificate.csv') if os.path.exists(os.path.join(U, 'prime_assolute_verificate.csv')) else []
    tipi = num['tipi']

    def per_decennio(ruolo):
        # i primi 5 di ogni decennio: una classifica unica favorirebbe gli anni con più recite
        d = C.defaultdict(list)
        for x in inter:
            if x['ruolo'] == ruolo:
                for k, c in json.loads(x['decenni']).items():
                    d[k].append({'c': x['nome'], 'n': c})
        return {k: sorted(v, key=lambda q: -q['n'])[:5] for k, v in sorted(d.items())}
    json.dump({'numeri': {'locandine': rie['locandine'], 'recite': rie['recite'], 'date_ore': rie['date_ora_distinte'], 'serate': rie['serate'], 'giorni': rie['giorni'],
                          'di_giorno': num['giorno'], 'opere': num['opere'], 'balletti': num['balletti'], 'compositori': num['compositori'], 'prima': rie['prima'], 'ultima': rie['ultima'],
                          'tipi': {k: tipi.get(k, 0) for k in ('Opera', 'Balletto', 'Concerto', 'Recital', 'Manifestazione', 'Diversi', 'Altro')}, 'bambini': num['bambini']},
               'decenni': decenni, 'per_anno': per_anno,
               'opere': [r_op(x) for x in opere[:40]], 'balletti': [r_op(x) for x in balli[:40]],
               'compositori': [{'c': x['Compositore'], 'n': int(x['Recite']), 'l': int(x['Lavori diversi'])} for x in comp[:20]],
               'opere_per_decennio': per_dec,
               'direttori': [{'c': nome(x['nome']), 'n': int(x['recite'])} for x in dirs[:25]],
               'canto': [{'c': x['nome'], 'n': int(x['locandine']), 'da': x['prima'][:4], 'al': x['ultima'][:4]} for x in inter if x['ruolo'] == 'canto'],
               'danza': [{'c': x['nome'], 'n': int(x['locandine']), 'da': x['prima'][:4], 'al': x['ultima'][:4]} for x in inter if x['ruolo'] == 'danza'],
               'canto_dec': per_decennio('canto'), 'danza_dec': per_decennio('danza'),
               'prezzi': pz, 'prime': prime, 'generato': '2026-11-05'},
              open(os.path.join(O, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print({k: len(v) for k, v in dec.items()}, sum(os.path.getsize(os.path.join(O, f)) for f in os.listdir(O)))
    print('prezzi', pz)


if __name__ == '__main__':
    main()
