"""Conta le serate della Scala dall'archivio delle locandine scaricato in locale.

Uso:
  python -I -X utf8 locandine_conta.py --archivio <cartella locandine> --uscita <cartella risultati>

Si può rilanciare quando arrivano nuovi file: legge tutti i *_manifest.csv che trova
(balletti, concerti, recital, opere...), non scarica nulla e non tocca la cartella di partenza.

Da dove viene ogni dato
- Il nome del file dà data, ora, sigla e lettera: 19460817TOSC_2030_O.jpg.
- La scheda del catalogo, quando c'è, dà titolo, tipo, stagione e sala.
- Se la data della scheda non coincide con il nome del file, la scheda è sospetta: non la uso.

Tre modi di contare, dal più largo al più stretto
- locandine: file distinti;
- recite: data + ora + sigla (le versioni doppie dello stesso file valgono una);
- serate: data + ora + sala. Due locandine alla stessa ora nella stessa sala, o con sala
  ignota, valgono una serata sola (per esempio due lavori nello stesso programma).
"""
import argparse, collections as C, csv, glob, json, os, re, unicodedata
from datetime import date

MESI = 'gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre'.split()
LETTERE = {'O': 'Opera', 'B': 'Balletto', 'C': 'Concerto', 'R': 'Recital', 'M': 'Manifestazione', 'X': 'Altro'}
CARTELLE = ('foto', 'Balletti', 'Concerti', 'Manifestazioni', 'Recital', 'Opere', 'Opera')
NOME = re.compile(r'^(\d{8})([A-Za-z0-9]{4})_(\d{4})')


def leggi_nome(nome):
    """Dal nome del file a data, ora, sigla, lettera. Corregge le varianti viste nei file."""
    pulito = nome[:-4].replace(' ', '')
    m = NOME.match(pulito)
    if not m:
        return None
    resto = pulito[m.end():].strip('_').upper()
    # resto: '', 'O', '0', 'O_1', 'W_O', 'X'...
    pezzi = [p for p in resto.split('_') if p]
    lettera, versione = '', ''
    for p in pezzi:
        q = 'O' if p == '0' else p
        if q in LETTERE:
            lettera = q
        else:
            versione = p
    return {'data': m.group(1), 'ora': m.group(3), 'sigla': m.group(2).upper(), 'lettera': lettera, 'versione': versione}


def data_scheda(s):
    m = re.match(r'(\d+)\s+(\w+)\s+(\d{4})', s or '')
    if not m or m.group(2).lower() not in MESI:
        return ''
    return f'{m.group(3)}{MESI.index(m.group(2).lower()) + 1:02d}{int(m.group(1)):02d}'


def norma(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().upper()
    return re.sub(r'\s+', ' ', re.sub(r"[^A-Z0-9 ]+", ' ', s)).strip()


def sala_tipo(s):
    n = norma(s)
    if not n:
        return ''
    if n == 'TEATRO ALLA SCALA':
        return 'Teatro alla Scala'
    if 'PICCOLA SCALA' in n:
        return 'Piccola Scala'
    if 'RIDOTTO' in n:
        return 'Ridotto dei palchi'
    if 'ARCIMBOLDI' in n:
        return 'Arcimboldi'
    if n.startswith('MILANO') or n.startswith('MI '):
        return 'Altra sede a Milano'
    return 'Fuori Milano'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archivio', required=True)
    ap.add_argument('--uscita', required=True)
    ap.add_argument('--titoli-opere', default='', help='CSV facoltativo: sigla,lettera,titolo,autore,verifica')
    a = ap.parse_args()
    R = a.archivio
    os.makedirs(a.uscita, exist_ok=True)

    # 1. tutti i file su disco
    file = {}
    for d in sorted(os.listdir(R), key=lambda q: q != 'foto'):  # tutte le sottocartelle, prima foto
        p = os.path.join(R, d)
        if os.path.isdir(p):
            for n in os.listdir(p):
                if n.lower().endswith('.jpg'):
                    file.setdefault(n, d)
    irregolari = [n for n in file if not leggi_nome(n)]

    # 2. tutte le schede del catalogo
    schede = C.defaultdict(list)
    liste = {}
    for p in sorted(glob.glob(os.path.join(R, '*_manifest.csv'))):
        nome = os.path.basename(p).replace('_manifest.csv', '')
        if nome == 'archive':
            continue
        with open(p, encoding='utf-8-sig', newline='') as f:
            righe = list(csv.DictReader(f))
        liste[nome] = len(righe)
        for x in righe:
            schede[x.get('local_filename', '')].append(x)

    titoli_extra = {}
    if a.titoli_opere and os.path.exists(a.titoli_opere):
        with open(a.titoli_opere, encoding='utf-8-sig', newline='') as f:
            for x in csv.DictReader(f):
                titoli_extra[(x['sigla'], x['lettera'])] = x

    # 3. una riga per locandina
    loc = []
    sospette = []
    for n in sorted(file):
        q = leggi_nome(n)
        if not q:
            continue
        s = schede.get(n, [])
        buona = None
        scarto = {}
        for x in s:
            d = data_scheda(x.get('date'))
            if d:
                # uno o pochi giorni di differenza: stessa locandina, data scritta male da una delle due parti
                gg = abs((date(int(d[:4]), int(d[4:6]), int(d[6:])) - date(int(q['data'][:4]), int(q['data'][4:6]), int(q['data'][6:]))).days)
                scarto[id(x)] = gg
                if gg <= 3 and (buona is None or gg < scarto[id(buona)]):
                    buona = x
        if s and not buona:
            sospette.append((n, s[0].get('title'), s[0].get('date'), s[0].get('season')))
        tipo_lettera = LETTERE.get(q['lettera'], '')
        tipi = sorted({x['type'].strip() for x in s if scarto.get(id(x), 99) <= 3 and x.get('type')})
        tipo = tipi[0] if tipi else tipo_lettera
        titolo = buona['title'].strip() if buona else ''
        origine = 'scheda' if buona else 'nessuna'
        autore = ''
        if not titolo:
            e = titoli_extra.get((q['sigla'], q['lettera'])) or titoli_extra.get((q['sigla'], ''))
            if e:
                titolo, autore, origine = e['titolo'], e.get('autore', ''), 'sigla letta sulla locandina'
        loc.append({'file': n, 'data': q['data'], 'ora': q['ora'], 'sigla': q['sigla'], 'lettera': q['lettera'],
                    'versione': q['versione'], 'tipo': tipo, 'tipo_da_lettera': tipo_lettera, 'titolo': titolo,
                    'autore': autore, 'origine_titolo': origine, 'stagione': buona['season'].strip() if buona else '',
                    'sala': buona['venue'].strip() if buona else '', 'sala_tipo': sala_tipo(buona['venue']) if buona else '',
                    'scheda_sospetta': 'si' if (s and not buona) else ''})

    # 4. recite: data + ora + sigla
    rec = {}
    for x in loc:
        k = (x['data'], x['ora'], x['sigla'])
        if k not in rec:
            rec[k] = dict(x, n_file=1)
        else:
            rec[k]['n_file'] += 1
            for c in ('titolo', 'sala', 'sala_tipo', 'stagione', 'autore'):
                rec[k][c] = rec[k][c] or x[c]
    recite = sorted(rec.values(), key=lambda x: (x['data'], x['ora'], x['sigla']))

    # 5. serate: data + ora + sala (sala ignota = si unisce alle altre della stessa ora)
    per_ora = C.defaultdict(list)
    for x in recite:
        per_ora[(x['data'], x['ora'])].append(x)
    n_serate = 0
    serata_id = {}
    for k, v in sorted(per_ora.items()):
        sale = sorted({norma(x['sala']) for x in v if x['sala']})
        gruppi = sale or ['']
        ids = {}
        for s in gruppi:
            n_serate += 1
            ids[s] = n_serate
        for x in v:
            x['serata'] = ids.get(norma(x['sala']), ids[gruppi[0]])
            serata_id[(x['data'], x['ora'], x['sigla'])] = x['serata']
    giorni = {x['data'] for x in recite}

    # tipo della serata e tipi misti
    per_serata = C.defaultdict(list)
    for x in recite:
        per_serata[x['serata']].append(x)
    for x in recite:
        x['mista'] = ''
        tt = {y['tipo'] for y in per_serata[x['serata']]} | {y['tipo_da_lettera'] for y in per_serata[x['serata']]}
        tt -= {'', 'Altro'}
        if len(tt) > 1:
            x['mista'] = ' + '.join(sorted(tt))

    # 6. riepiloghi
    per_tipo = C.Counter(x['tipo'] or '(senza tipo)' for x in recite)
    per_anno = C.defaultdict(C.Counter)
    for x in recite:
        per_anno[x['data'][:4]]['recite'] += 1
        per_anno[x['data'][:4]][x['tipo'] or '(senza tipo)'] += 1
    for sid, v in per_serata.items():
        per_anno[v[0]['data'][:4]]['serate'] += 1
    for g in giorni:
        per_anno[g[:4]]['giorni'] += 1

    per_titolo = C.defaultdict(lambda: {'n': 0, 'prima': '', 'ultima': '', 'sigle': C.Counter(), 'autore': ''})
    for x in recite:
        if x['titolo']:
            t = per_titolo[(x['tipo'], norma(x['titolo']))]
            t['n'] += 1
            t['nome'] = t.get('nome') or x['titolo']
            t['autore'] = t['autore'] or x['autore']
            t['prima'] = min(t['prima'] or x['data'], x['data'])
            t['ultima'] = max(t['ultima'], x['data'])
            t['sigle'][x['sigla']] += 1
    per_sigla = C.defaultdict(lambda: {'n': 0, 'prima': '', 'ultima': '', 'titoli': C.Counter(), 'tipi': C.Counter()})
    for x in recite:
        t = per_sigla[x['sigla']]
        t['n'] += 1
        t['prima'] = min(t['prima'] or x['data'], x['data'])
        t['ultima'] = max(t['ultima'], x['data'])
        if x['titolo']:
            t['titoli'][x['titolo']] += 1
        t['tipi'][x['tipo']] += 1

    # 7. scrittura
    def scrivi(nome, righe, campi):
        with open(os.path.join(a.uscita, nome), 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=campi, extrasaction='ignore')
            w.writeheader()
            w.writerows(righe)

    scrivi('recite.csv', recite, ['serata', 'data', 'ora', 'sigla', 'lettera', 'tipo', 'tipo_da_lettera', 'titolo', 'autore',
                                  'origine_titolo', 'stagione', 'sala', 'sala_tipo', 'mista', 'n_file', 'scheda_sospetta', 'file'])
    scrivi('titoli.csv', [{'tipo': k[0], 'titolo': v['nome'], 'autore': v['autore'], 'recite': v['n'], 'prima': v['prima'], 'ultima': v['ultima'],
                           'sigle': ' '.join(s for s, _ in v['sigle'].most_common(5))}
                          for k, v in sorted(per_titolo.items(), key=lambda kv: (kv[0][0], -kv[1]['n']))],
           ['tipo', 'titolo', 'autore', 'recite', 'prima', 'ultima', 'sigle'])
    scrivi('sigle.csv', [{'sigla': k, 'recite': v['n'], 'prima': v['prima'], 'ultima': v['ultima'],
                          'tipi': ' '.join(f'{a}:{b}' for a, b in v['tipi'].most_common()),
                          'titoli_scheda': ' | '.join(f'{a}:{b}' for a, b in v['titoli'].most_common(4))}
                         for k, v in sorted(per_sigla.items(), key=lambda kv: -kv[1]['n'])],
           ['sigla', 'recite', 'prima', 'ultima', 'tipi', 'titoli_scheda'])
    scrivi('sospette.csv', [dict(zip(('file', 'titolo', 'data_scheda', 'stagione_scheda'), s)) for s in sospette],
           ['file', 'titolo', 'data_scheda', 'stagione_scheda'])
    tipi = [t for t, _ in per_tipo.most_common()]
    scrivi('per_anno.csv', [dict(anno=y, **per_anno[y]) for y in sorted(per_anno)], ['anno', 'giorni', 'serate', 'recite'] + tipi)

    ris = {'file_su_disco': len(file), 'nomi_irregolari': irregolari, 'schede_per_lista': liste,
           'locandine': len(loc), 'recite': len(recite), 'serate': n_serate, 'giorni': len(giorni),
           'date_ora_distinte': len(per_ora), 'recite_stessa_ora': sum(1 for v in per_ora.values() if len(v) > 1),
           'prima': min(giorni), 'ultima': max(giorni), 'per_tipo': dict(per_tipo.most_common()),
           'serate_miste': len({x['serata'] for x in recite if x['mista']}),
           'con_scheda': sum(1 for x in recite if x['origine_titolo'] == 'scheda'),
           'schede_sospette': len(sospette),
           'per_sala_tipo': dict(C.Counter(x['sala_tipo'] or '(sala ignota)' for x in recite).most_common()),
           'titoli_per_tipo': dict(C.Counter(k[0] for k in per_titolo).most_common()), 'sigle': len(per_sigla)}
    json.dump(ris, open(os.path.join(a.uscita, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(ris, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
