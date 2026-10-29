"""Cambiasi 1881: tabella 'Serie dei melodrammi' (pagine hOCR 24-103, coppie sinistra/destra) -> pulito/_cambiasi_opere.csv
Ogni riga: anno, stagione, mese, giorno, titolo, maestro (pagina sinistra) + poeta, genere, esecutori, esito (pagina destra).
Uso: python -I -X utf8 scripts/parse_cambiasi_opere.py pulito/_cambiasi_hocr.json pulito/_cambiasi_opere.csv"""
import json, re, sys, csv, statistics

src, out = sys.argv[1], sys.argv[2]
D = json.load(open(src, encoding='utf-8'))


def cluster(words, tol=24):
    ws = sorted(words, key=lambda w: (w[1] + w[3]) / 2)
    rows = []
    for w in ws:
        yc = (w[1] + w[3]) / 2
        if rows and abs(rows[-1]['y'] - yc) < tol:
            rows[-1]['w'].append(w)
            rows[-1]['y'] = sum((x[1] + x[3]) / 2 for x in rows[-1]['w']) / len(rows[-1]['w'])
        else:
            rows.append({'y': yc, 'w': [w]})
    for r in rows:
        r['w'].sort(key=lambda w: w[0])
    return rows


def txt(ws):
    return re.sub(r'\s+', ' ', ' '.join(w[4] for w in ws)).strip()


def conf(ws):
    c = [w[5] for w in ws if w[5] >= 0]
    return sum(c) / len(c) if c else -1


STAG = {'carnevale': 'Carnevale', 'carnev': 'Carnevale', 'quaresima': 'Quaresima', 'primavera': 'Primavera', 'estate': 'Estate',
        'autunno': 'Autunno', 'avvento': 'Avvento', 'aw': 'Avvento'}
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']


def mese_norm(s):
    s0 = re.sub(r'[^a-zA-Z]', '', s).lower()
    if not s0:
        return ''
    for m in MESI:
        if m.startswith(s0[:3]) and s0[:3] != '':
            return m
    return s0


def stag_norm(s):
    s0 = re.sub(r'[^a-zA-Z]', '', s).lower()
    for k, v in STAG.items():
        if s0.startswith(k[:5]) and len(s0) >= 3:
            return v
    return s


def left_rows(pg):
    ws = pg['parole']
    yrs = [w for w in ws if re.fullmatch(r'[1I][78Sg][0-9OSIl]{2}', w[4]) and 500 < w[0] < 900]
    if not yrs:
        if pg['pagina'] == 90:   # pagina con anno illeggibile all'OCR: stessa colonna delle vicine
            yrs = [[0, 0, 0, 0, '', 0]]; yrs[0][0] = 715
        else:
            return [], None
    ax = statistics.median(w[0] for w in yrs)
    rows = cluster(ws)
    out = []
    for r in rows:
        first = r['w'][0]
        if first[4].startswith('(') and first[0] < ax + 150 and out and r['y'] > 2700 and len(r['w']) >= 5:
            break  # note a piè di pagina
        cols = {'anno': [], 'stag': [], 'mese': [], 'giorno': [], 'titolo': [], 'maestro': []}
        for w in r['w']:
            x = w[0] - ax
            if x < 100: k = 'anno'
            elif x < 380: k = 'stag'
            elif x < 540: k = 'mese'
            elif x < 700: k = 'giorno'
            elif x < 1560: k = 'titolo'
            else: k = 'maestro'
            cols[k].append(w)
        out.append({'y': r['y'], 'cols': cols, 'conf': conf(r['w'])})
    return out, ax


def right_rows(pg):
    rows = cluster(pg['parole'])
    out = []
    for r in rows:
        cols = {'poeta': [], 'genere': [], 'esec': [], 'esito': []}
        for w in r['w']:
            x = w[0]
            if x < 285: k = 'poeta'
            elif x < 440: k = 'genere'
            elif x < 1650: k = 'esec'
            else: k = 'esito'
            cols[k].append(w)
        out.append({'y': r['y'], 'cols': cols, 'conf': conf(r['w']), 'n': len(r['w'])})
    return out


rows_out = []
cy = ''
for pi in range(24, 104, 2):
    L, R = D[pi], D[pi + 1]
    lr, ax = left_rows(L)
    if not lr:
        continue
    # righe di dati a sinistra: hanno parole nel titolo o nel maestro
    data = []
    for r in lr:
        c = r['cols']
        t = txt(c['titolo'])
        if (re.search(r'[A-Za-z]{3}', t) or re.search(r'[A-Za-z]{4}', txt(c['maestro']))) and r['y'] > 600:
            data.append(r)
    rr = [r for r in right_rows(R) if r['y'] > 560 and r['n'] >= 2]
    # offset migliore
    best, bo = -1, 0
    for off in range(-200, 201, 2):
        cnt = 0
        for r in data:
            if any(abs(q['y'] - r['y'] - off) < 30 for q in rr):
                cnt += 1
        if cnt > best:
            best, bo = cnt, off
    used = set()
    pending = None
    for r in data:
        c = r['cols']
        # candidato di destra
        cand = None
        bd = 1e9
        for qi, q in enumerate(rr):
            dd = abs(q['y'] - r['y'] - bo)
            if dd < bd and qi not in used:
                bd, cand = dd, qi
        q = rr[cand] if cand is not None and bd < 40 else None
        if q is not None:
            used.add(cand)
        yr = txt(c['anno'])
        title = txt(c['titolo'])
        row = {
            'pagina_hocr': pi, 'anno_raw': yr, 'stagione_raw': txt(c['stag']), 'mese_raw': txt(c['mese']), 'giorno_raw': txt(c['giorno']),
            'titolo_raw': title, 'maestro_raw': txt(c['maestro']),
            'poeta_raw': txt(q['cols']['poeta']) if q else '', 'genere_raw': txt(q['cols']['genere']) if q else '',
            'esecutori_raw': txt(q['cols']['esec']) if q else '', 'esito_raw': txt(q['cols']['esito']) if q else '',
            'conf': round(min(r['conf'], q['conf']) if q else r['conf'], 1), 'destra_trovata': int(q is not None), 'y': int(r['y']),
        }
        # righe di titolo in continuazione (senza stagione/mese/giorno/anno e senza maestro, vicine alla precedente)
        if rows_out and not yr and not row['stagione_raw'] and not row['mese_raw'] and not row['giorno_raw'] and not row['maestro_raw'] \
                and rows_out[-1]['pagina_hocr'] == pi and r['y'] - rows_out[-1]['y'] < 70:
            rows_out[-1]['titolo_raw'] += ' ' + title
            continue
        rows_out.append(row)

cols = ['pagina_hocr', 'anno_raw', 'stagione_raw', 'mese_raw', 'giorno_raw', 'titolo_raw', 'maestro_raw', 'poeta_raw', 'genere_raw',
        'esecutori_raw', 'esito_raw', 'conf', 'destra_trovata', 'y']
with open(out, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, cols)
    w.writeheader()
    w.writerows(rows_out)
print(len(rows_out), 'righe;', sum(r['destra_trovata'] for r in rows_out), 'con metà destra')
