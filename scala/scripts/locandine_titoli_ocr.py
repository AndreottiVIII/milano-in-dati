"""Dal testo letto sulle locandine alle righe più grandi per ogni sigla: la base per dare un titolo alle sigle.

Uso: python -I -X utf8 locandine_titoli_ocr.py --cartella <risultati>
Scrive sigle_da_leggere.csv: una riga per sigla e lettera, solo per le recite senza scheda del catalogo.
"""
import argparse, collections as C, csv, glob, json, os, re, unicodedata

VIETATE = re.compile(r'TEATRO|SCALA|STAGIONE|ENTE AUTONOMO|DOMENICA|LUNEDI|MARTEDI|MERCOLEDI|GIOVEDI|VENERDI|SABATO|'
                     r'GENNAIO|FEBBRAIO|MARZO|APRILE|MAGGIO|GIUGNO|LUGLIO|AGOSTO|SETTEMBRE|OTTOBRE|NOVEMBRE|DICEMBRE|'
                     r'ORE \d|PREZZI|BIGLIETT|VIETATO|RAPPRESENTAZIONE|RECITA|ABBONAMENTO|TURNO|POLTRON|PLATEA|'
                     r'INGRESSO|PERSONAGGI|LIRICA|MILANO|DIRETTORE|MAESTRO|MUSICA DI|REGIA|ORCHESTRA|CORO')


def norma(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().upper()
    return re.sub(r'\s+', ' ', re.sub(r'[^A-Z0-9 ]+', ' ', s)).strip()


def righe_grandi(righe, quante=3):
    """Le righe con le lettere più alte, tolte intestazione, date e prezzi."""
    buone = []
    for r in righe:
        n = norma(r.get('t'))
        if len(re.sub(r'[^A-Z]', '', n)) < 3 or VIETATE.search(n):
            continue
        buone.append((r.get('h', 0), n))
    buone.sort(key=lambda x: -x[0])
    return [n for _, n in buone[:quante]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    a = ap.parse_args()
    testo = {}
    for p in glob.glob(os.path.join(a.cartella, 'ocr_testo*.jsonl')):
        with open(p, encoding='utf-8') as f:
            for l in f:
                x = json.loads(l)
                testo[x['file']] = x.get('righe') or []
    gruppi = C.defaultdict(list)
    for x in csv.DictReader(open(os.path.join(a.cartella, 'recite.csv'), encoding='utf-8-sig')):
        if x['origine_titolo'] != 'scheda':
            gruppi[(x['sigla'], x['lettera'])].append(x)
    usc = []
    for (s, l), v in gruppi.items():
        c = C.Counter()
        for x in v:
            c.update(set(righe_grandi(testo.get(x['file'], []))))
        v.sort(key=lambda x: x['data'])
        usc.append({'sigla': s, 'lettera': l, 'recite': len(v), 'prima': v[0]['data'], 'ultima': v[-1]['data'],
                    'righe': ' | '.join(f'{k}*{n}' for k, n in c.most_common(5))})
    usc.sort(key=lambda x: -x['recite'])
    with open(os.path.join(a.cartella, 'sigle_da_leggere.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(usc[0]))
        w.writeheader()
        w.writerows(usc)
    print('gruppi', len(usc), 'recite', sum(x['recite'] for x in usc), 'per lettera', C.Counter(x['lettera'] for x in usc).most_common())


if __name__ == '__main__':
    main()
