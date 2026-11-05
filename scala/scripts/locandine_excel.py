"""Mette insieme i conti delle serate alla Scala in un file Excel e in tabelle CSV.

Uso: python -I -X utf8 locandine_excel.py --cartella <risultati>
Legge lavori_per_recita.csv, titoli_sigle.csv e riepilogo.json. Scrive Serate_alla_Scala.xlsx,
opere.csv, balletti.csv, compositori.csv, concerti.csv, per_decennio.csv e numeri.json.
"""
import argparse, collections as C, csv, json, os, re, unicodedata
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

ARTICOLI = re.compile(r'^(IL|LO|LA|I|GLI|LE|L|UN|UNA|UNO|DIE|DER|DAS|THE|LES)\s+')
NERO = PatternFill('solid', fgColor='111111')


def norma(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().upper()
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]+', ' ', s)).strip()


def chiave(t):
    return ARTICOLI.sub('', norma(t))


def bello(t):
    """Titoli del catalogo tutti maiuscoli: solo la prima lettera resta grande."""
    if t and t.upper() == t:
        t = t.capitalize()
        t = re.sub(r"(['’])(\w)", lambda m: m.group(1) + m.group(2).lower(), t)
    return t


def scheda(wb, nome, intest, righe, larghezze=None):
    ws = wb.create_sheet(nome)
    ws.append(intest)
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = NERO
    for r in righe:
        ws.append(r)
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    for i, w in enumerate(larghezze or [], 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    return ws


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    a = ap.parse_args()
    U = a.cartella
    rec = list(csv.DictReader(open(os.path.join(U, 'lavori_per_recita.csv'), encoding='utf-8-sig')))
    rie = json.load(open(os.path.join(U, 'riepilogo.json'), encoding='utf-8'))
    sig = list(csv.DictReader(open(os.path.join(U, 'titoli_sigle.csv'), encoding='utf-8-sig')))

    # quali titoli sono opere e quali balletti: dal titolo principale delle locandine
    gen = {'Opera': {}, 'Balletto': {}}
    for x in rec:
        if x['tipo'] in gen and x['titolo_principale']:
            k = chiave(x['titolo_principale'])
            gen[x['tipo']].setdefault(k, (x['titolo_principale'], x['autore_principale']))
    conti = {'Opera': {}, 'Balletto': {}}

    def segna(tipo, titolo, autore, x, principale):
        k = chiave(titolo)
        # stesso titolo di autori diversi resta separato (Il barbiere di Rossini e di Paisiello)
        chiave_opera = (k, norma(autore) if autore and tipo == 'Opera' else '')
        if not autore and tipo == 'Opera':
            cand = [q for q in conti[tipo] if q[0] == k and q[1]]
            if cand:
                chiave_opera = max(cand, key=lambda q: conti[tipo][q]['n'])
        c = conti[tipo].setdefault(chiave_opera, {'titolo': bello(titolo), 'autore': autore, 'n': 0, 'princ': 0, 'bamb': 0, 'prima': x['data'], 'ultima': x['data'], 'anni': set(), 'decenni': C.Counter()})
        c['autore'] = c['autore'] or autore
        c['n'] += 1
        c['princ'] += principale
        c['bamb'] += x['per_bambini'] == 'si'
        c['prima'] = min(c['prima'], x['data'])
        c['ultima'] = max(c['ultima'], x['data'])
        c['anni'].add(x['data'][:4])
        c['decenni'][x['data'][:3] + '0'] += 1

    # prima i principali, così gli altri lavori trovano l'autore giusto
    for x in rec:
        if x['tipo'] in conti and x['titolo_principale']:
            segna(x['tipo'], x['titolo_principale'], x['autore_principale'], x, 1)
    for x in rec:
        for t in x['altri_lavori'].split(' ; '):
            if not t:
                continue
            k = chiave(t)
            if x['tipo'] in conti and k in gen[x['tipo']]:
                tipo = x['tipo']
            elif k in gen['Opera']:
                tipo = 'Opera'
            elif k in gen['Balletto']:
                tipo = 'Balletto'
            else:
                tipo = x['tipo'] if x['tipo'] in conti else 'Balletto'
            segna(tipo, t, gen[tipo].get(k, (t, ''))[1], x, 0)

    def d(s):
        return f'{s[6:]}/{s[4:6]}/{s[:4]}'

    opere = sorted(conti['Opera'].values(), key=lambda c: -c['n'])
    balli = sorted(conti['Balletto'].values(), key=lambda c: -c['n'])
    comp = C.defaultdict(lambda: {'n': 0, 'lav': set()})
    for c in opere:
        if c['autore']:
            q = comp[c['autore']]
            q['n'] += c['n']
            q['lav'].add(c['titolo'])
    compositori = sorted(comp.items(), key=lambda kv: -kv[1]['n'])

    # concerti: si contano per artista, dalla sigla
    art = {}
    for s in sig:
        if s['lettera'] in ('C', 'R') and s['titolo']:
            art.setdefault(s['sigla'], s['titolo'])
    con = C.Counter()
    nomi = {}
    letti = C.defaultdict(C.Counter)
    for x in rec:
        if x['tipo'] in ('Concerto', 'Recital'):
            con[x['sigla']] += 1
            nomi[x['sigla']] = art.get(x['sigla']) or ''
            for q in x['righe_grandi'].split(' | ')[:2]:
                if len(q) >= 6:
                    letti[x['sigla']][q] += 1
    origine = {}
    for k in con:
        origine[k] = 'assegnato' if nomi[k] else ''
        if not nomi[k] and letti[k]:
            # riga grande più frequente sui fogli: quasi sempre l'artista, non controllata una per una
            nomi[k] = letti[k].most_common(1)[0][0].title()
            origine[k] = 'riga più grande del foglio'
    coperti = sum(v for k, v in con.items() if nomi[k])

    # per decennio
    dec = C.defaultdict(C.Counter)
    for x in rec:
        k = x['data'][:3] + '0'
        dec[k][x['tipo'] or 'Altro'] += 1
        dec[k]['Totale'] += 1
        dec[k]['Di giorno (prima delle 18)'] += x['ora'] < '1800'
    tipi = ['Opera', 'Balletto', 'Concerto', 'Recital', 'Manifestazione', 'Diversi', 'Altro']

    # scheda per scheda
    wb = Workbook()
    wb.remove(wb.active)
    cnt = C.Counter(x['tipo'] or 'Altro' for x in rec)
    giorno = sum(x['ora'] < '1800' for x in rec)
    r = [('Quanto', 'Numero', 'Come si legge'),
         ('Locandine', rie['locandine'], 'File distinti nella cartella'),
         ('Recite', rie['recite'], 'Stessa data, ora e sigla: le copie doppie valgono una'),
         ('Date e ore distinte', rie['date_ora_distinte'], 'Il minimo: due locandine alla stessa ora valgono una sola serata'),
         ('Serate (stima)', rie['serate'], 'Data, ora e sala. Sala nota per meno di metà delle recite: numero tra il minimo e le recite'),
         ('Giorni con almeno uno spettacolo', rie['giorni'], ''),
         ('Di giorno, prima delle 18', giorno, 'Mattine e pomeriggi: non sono vere serate'),
         ('Opere diverse', len(opere), 'Stesso titolo di autori diversi resta separato'),
         ('Balletti diversi', len(balli), 'Dal catalogo: le grafie non unite a mano restano separate')]
    r += [(f'Recite: {t}', cnt[t], '') for t in tipi]
    r += [('Prima data', d(rie['prima']), ''), ('Ultima data', d(rie['ultima']), '')]
    lim = ['',
           'LIMITI',
           'Fonte: locandine dell\'archivio del Teatro alla Scala, scaricate in locale il 4/11/2026. ©Teatro alla Scala. Uso privato: non ripubblicare file o immagini.',
           'Le recite senza locandina non ci sono: confronto con Wikipedia, Wikidata e biblioteche, 428 date su 459 hanno la locandina quel giorno (93%).',
           'Dal 1951 mancano 6 prime del 7 dicembre su 75: 1951, 1956, 1971, 1973, 1986, 2012.',
           'Dal 2024 i concerti sono quasi assenti: gli ultimi anni sono contati meno del vero.',
           'I titoli delle opere non vengono dal catalogo: li ha dati una lettura automatica delle locandine, sigla per sigla. Controllati a vista su 20 locandine a caso e con il nome del compositore sul foglio; restano possibili errori sui titoli rari.',
           'Una locandina con due lavori conta per entrambi nelle classifiche: per questo la somma per titolo supera il numero di recite.',
           'La sala delle opere è una stima dal testo del foglio. Le tournée non si riconoscono: alcune recite non sono alla Scala.',
           'Le recite con programmi per bambini sono incluse e segnate a parte (colonna "per bambini").',
           'Un titolo con la colonna "verifica" uguale a "dedotto" è stato ricavato da pezzi di testo; "dubbio" vuol dire che non è stato capito.']
    ws = wb.create_sheet('Riepilogo')
    for q in r:
        ws.append(q)
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = NERO
    for q in lim:
        ws.append([q])
    ws.column_dimensions['A'].width = 36
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 90
    for row in ws.iter_rows(min_row=len(r) + 2):
        row[0].alignment = Alignment(wrap_text=False)
    ws.cell(len(r) + 2, 1).font = Font(bold=True)

    decenni = sorted(dec)
    scheda(wb, 'Per decennio', ['Decennio', 'Totale'] + tipi + ['Di giorno (prima delle 18)'],
           [[k, dec[k]['Totale']] + [dec[k][t] for t in tipi] + [dec[k]['Di giorno (prima delle 18)']] for k in decenni], [10, 9, 9, 9, 9, 9, 15, 9, 9, 26])
    for_anno = list(csv.DictReader(open(os.path.join(U, 'per_anno.csv'), encoding='utf-8-sig')))
    anni = C.defaultdict(C.Counter)
    for x in rec:
        anni[x['data'][:4]][x['tipo'] or 'Altro'] += 1
    scheda(wb, 'Per anno', ['Anno', 'Giorni', 'Serate (stima)', 'Recite'] + tipi,
           [[int(q['anno']), int(q['giorni'] or 0), int(q['serate'] or 0), int(q['recite'] or 0)] + [anni[q['anno']][t] for t in tipi] for q in for_anno], [8, 8, 14, 8])
    cop = ['Titolo', 'Autore', 'Recite', 'Come lavoro principale', 'Per bambini', 'Anni con recite', 'Prima', 'Ultima']
    riga = lambda c: [c['titolo'], c['autore'], c['n'], c['princ'], c['bamb'], len(c['anni']), d(c['prima']), d(c['ultima'])]
    scheda(wb, 'Opere', cop, [riga(c) for c in opere], [42, 28, 8, 12, 10, 10, 12, 12])
    scheda(wb, 'Compositori', ['Compositore', 'Recite', 'Lavori diversi'], [[k, v['n'], len(v['lav'])] for k, v in compositori], [34, 8, 12])
    scheda(wb, 'Balletti', cop, [riga(c) for c in balli], [42, 28, 8, 12, 10, 10, 12, 12])
    scheda(wb, 'Concerti per artista', ['Sigla', 'Artista o iniziativa', 'Recite', 'Come si è ricavato il nome'], [[k, nomi[k], v, origine[k]] for k, v in con.most_common()], [8, 50, 8, 28])
    scheda(wb, 'Tutte le recite', ['Data', 'Ora', 'Tipo', 'Titolo', 'Autore', 'Altri lavori', 'Per bambini', 'Sala', 'Stagione', 'Verifica', 'Sigla', 'File'],
           [[x['data'][:4] + '-' + x['data'][4:6] + '-' + x['data'][6:], x['ora'][:2] + ':' + x['ora'][2:], x['tipo'], bello(x['titolo_principale']), x['autore_principale'], bello(x['altri_lavori']), x['per_bambini'], x['sala'] or x['sala_stimata'], x['stagione'], x['verifica'], x['sigla'], x['file']] for x in rec],
           [11, 6, 12, 40, 26, 36, 8, 26, 12, 10, 7, 28])
    if os.path.exists(os.path.join(U, 'direttori.csv')):
        d1 = list(csv.reader(open(os.path.join(U, 'direttori.csv'), encoding='utf-8-sig')))[1:]
        scheda(wb, 'Direttori', ['Direttore', 'Recite (stima)'], [[x[0].title(), int(x[1])] for x in d1], [34, 14])
        d2 = list(csv.DictReader(open(os.path.join(U, 'interpreti_noti.csv'), encoding='utf-8-sig')))
        scheda(wb, 'Interpreti (elenco scelto)', ['Nome', 'Ruolo', 'Locandine col nome', 'Primo anno', 'Ultimo anno'], [[x['nome'], x['ruolo'], int(x['locandine']), int(x['prima'][:4]), int(x['ultima'][:4])] for x in d2], [28, 8, 18, 10, 10])
        d3 = list(csv.DictReader(open(os.path.join(U, 'prezzi_serie.csv'), encoding='utf-8-sig')))
        scheda(wb, 'Prezzi opera', ['Anno', 'Moneta', 'Poltrona di platea', 'Biglietto meno caro', 'Poltrona in euro 2025', 'Meno caro in euro 2025', 'Locandine lette'],
               [[int(x['y']), x['m'], float(x['p']), float(x['b']) if x['b'] else None, int(x['p25']), float(x['b25']) if x['b25'] else None, int(x['n'])] for x in d3], [8, 8, 18, 18, 20, 22, 14])
    if os.path.exists(os.path.join(U, 'ruoli_letti.csv')):
        d4 = C.defaultdict(set)
        for x in csv.DictReader(open(os.path.join(U, 'ruoli_letti.csv'), encoding='utf-8-sig')):
            d4[(x['nome'], x['tipo'])].add(x['file'])
        scheda(wb, 'Ruoli principali', ['Nome', 'Tipo', 'Recite (minimo)'], [[k[0], k[1], len(v)] for k, v in sorted(d4.items(), key=lambda kv: -len(kv[1]))[:300]], [32, 10, 14])
    wb.save(os.path.join(U, 'Serate_alla_Scala.xlsx'))

    def csvw(nome, intest, righe):
        with open(os.path.join(U, nome), 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerow(intest)
            w.writerows(righe)
    csvw('opere.csv', cop, [riga(c) for c in opere])
    csvw('balletti.csv', cop, [riga(c) for c in balli])
    csvw('compositori.csv', ['Compositore', 'Recite', 'Lavori diversi'], [[k, v['n'], len(v['lav'])] for k, v in compositori])
    csvw('concerti.csv', ['Sigla', 'Artista', 'Recite'], [[k, nomi[k], v] for k, v in con.most_common()])
    csvw('per_decennio.csv', ['Decennio', 'Totale'] + tipi + ['Di giorno'], [[k, dec[k]['Totale']] + [dec[k][t] for t in tipi] + [dec[k]['Di giorno (prima delle 18)']] for k in decenni])
    num = {'opere': len(opere), 'balletti': len(balli), 'giorno': giorno, 'tipi': dict(cnt), 'compositori': len(comp),
           'concerti_con_nome': coperti, 'concerti_tot': sum(con.values()), 'bambini': sum(x['per_bambini'] == 'si' for x in rec), 'decenni': {k: dict(dec[k]) for k in decenni}}
    json.dump(num, open(os.path.join(U, 'numeri.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in num.items() if k != 'decenni'}, ensure_ascii=False))
    print('OPERE', [(c['titolo'], c['autore'].split(' ')[-1] if c['autore'] else '', c['n'], c['princ'], c['bamb']) for c in opere[:25]])
    print('BALLETTI', [(c['titolo'], c['n'], c['princ']) for c in balli[:25]])
    print('COMP', [(k, v['n'], len(v['lav'])) for k, v in compositori[:15]])
    print('CONC', [(k, nomi[k], v) for k, v in con.most_common(15)])
    for k in decenni:
        print(k, dict(dec[k]))


if __name__ == '__main__':
    main()
