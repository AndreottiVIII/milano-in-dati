"""Estrae il Comune di Milano dagli zip Eligendo scaricati e scrive pulito/milano_pre1979.csv.
Uso: python -I 33_eligendo_milano.py <raw_eligendo> <uscita.csv>
Livello dei dati: COMUNE (una riga per lista). Senato: Milano e' diviso in piu' collegi -> si sommano.
Elettori/votanti/bianche: nel file sono ripetuti su ogni riga lista; qui si prende un valore per (collegio/ambito)."""
import sys, os, io, csv, zipfile, glob, datetime, collections
import openpyxl

raw, out = sys.argv[1], sys.argv[2]
rows = []   # dict
log = []

def decode(b):
    try: return b.decode('utf-8')
    except UnicodeDecodeError: return b.decode('cp1252')

def num(x):
    if x is None: return None
    s = str(x).strip().strip('"')
    if s == '': return None
    return int(float(s))

def read_txt(zpath, name):
    zf = zipfile.ZipFile(zpath)
    txt = decode(zf.read(name))
    return list(csv.DictReader(io.StringIO(txt), delimiter=';', quotechar='"'))

def fmt(d): return d.strftime('%Y-%m-%d')

def add_liste(tipo, data, ambito_key_fn, recs, fonte, listacol='LISTA', votcol='VOTI_LISTA'):
    """recs: righe comune Milano. ambito = collegio (Senato) o unico."""
    for r in recs:
        rows.append(dict(tipo=tipo, elezione_id='%s_%s' % (tipo, data), data=data, quesito='',
                         lista=r[listacol].strip(), voti=num(r[votcol]), seggi='',
                         _amb=ambito_key_fn(r), _el=num(r.get('ELETTORI')), _vo=num(r.get('VOTANTI')),
                         _bi=num(r.get('SCHEDE_BIANCHE')), fonte=fonte))

def comune_mi(rs):
    return [r for r in rs if r['COMUNE'].strip().upper() == 'MILANO']

# --- file txt a livello comune
specs = [('assemblea_costituente', '19460602', 'costituente'),
         ('camera', None, 'camera'), ('senato', None, 'senato'),
         ('regionali', None, 'regionali')]
for z in sorted(glob.glob(os.path.join(raw, '*', '*.zip'))):
    b = os.path.basename(z)[:-4]
    tipo_f, d = b.rsplit('-', 1)
    data = '%s-%s-%s' % (d[:4], d[4:6], d[6:])
    zf = zipfile.ZipFile(z)
    main = [i.filename for i in zf.infolist() if i.filename.endswith('.txt') and 'prefer' not in i.filename.lower() and 'candlista' not in i.filename.lower()]
    if tipo_f in ('assemblea_costituente', 'camera', 'senato', 'regionali'):
        tipo = {'assemblea_costituente': 'costituente'}.get(tipo_f, tipo_f)
        rs = comune_mi(read_txt(z, main[0]))
        key = (lambda r: r['COLLEGIO'].strip()) if tipo == 'senato' else (lambda r: 'MILANO')
        add_liste(tipo, data, key, rs, os.path.basename(z))
        log.append((b, len(rs)))
    elif tipo_f == 'referendum':
        rs = comune_mi(read_txt(z, main[0]))
        for r in rs:
            q = '%s - %s' % (r['NUM_REFERENDUM'].strip(), r['QUESITO'].strip())
            common = dict(tipo='referendum', elezione_id='referendum_%s' % data, data=data, quesito=q, seggi='',
                          _amb=q, _el=num(r['ELETTORI']), _vo=num(r['VOTANTI']), _bi=num(r['SCHEDE_BIANCHE']), fonte=os.path.basename(z))
            rows.append(dict(common, lista='SI', voti=num(r['NUMVOTISI'])))
            rows.append(dict(common, lista='NO', voti=num(r['NUMVOTINO'])))
        log.append((b, len(rs)))
    elif tipo_f == 'comunali':
        sheets = {}
        for i in zf.infolist():
            wb = openpyxl.load_workbook(io.BytesIO(zf.read(i.filename)), read_only=True)
            rr = list(wb.worksheets[0].iter_rows(values_only=True))
            hdr = [str(h).upper() for h in rr[0]]
            sheets['liste' if 'LISTE' in i.filename.upper() else 'scrutini'] = (hdr, rr[1:])
        h, sc = sheets['scrutini']
        sc = [r for r in sc if str(r[3]).strip().upper() == 'MILANO']
        assert len(sc) == 1, sc
        el, vo, bi = num(sc[0][4]), num(sc[0][5]), num(sc[0][6])
        h, li = sheets['liste']
        li = [r for r in li if str(r[3]).strip().upper() == 'MILANO']
        for r in li:
            rows.append(dict(tipo='comunali', elezione_id='comunali_%s' % data, data=data, quesito='', lista=str(r[4]).strip(),
                             voti=num(r[5]), seggi=num(r[6]), _amb='MILANO', _el=el, _vo=vo, _bi=bi, fonte=os.path.basename(z)))
        log.append((b, len(li)))

# --- aggrega elettori/votanti/bianche (una volta per ambito) e somma delle liste
tot = collections.defaultdict(lambda: dict(el=0, vo=0, bi=0, amb=set()))
for r in rows:
    t = tot[(r['elezione_id'], r['quesito'])]
    if r['_amb'] not in t['amb']:
        t['amb'].add(r['_amb']); t['el'] += r['_el'] or 0; t['vo'] += r['_vo'] or 0; t['bi'] += r['_bi'] or 0
# Senato: somma per collegio (voti per lista)
res = collections.OrderedDict()
for r in rows:
    k = (r['elezione_id'], r['quesito'], r['lista'])
    if k in res:
        res[k]['voti'] += r['voti'] or 0
        if r['seggi'] != '' : res[k]['seggi'] = (res[k]['seggi'] or 0) + r['seggi']
    else:
        res[k] = dict(r)
sumlist = collections.defaultdict(int)
for k, r in res.items():
    if r['tipo'] != 'referendum': sumlist[(k[0], k[1])] += r['voti'] or 0
cols = ['elezione_id', 'tipo', 'data', 'quesito', 'lista', 'voti', 'seggi', 'elettori', 'votanti', 'schede_bianche', 'somma_voti_liste', 'n_collegi', 'fonte']
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, delimiter=',')
    w.writerow(cols)
    for k, r in sorted(res.items(), key=lambda kv: (kv[1]['data'], kv[1]['tipo'], kv[0][1], -(kv[1]['voti'] or 0))):
        t = tot[(k[0], k[1])]
        w.writerow([r['elezione_id'], r['tipo'], r['data'], r['quesito'], r['lista'], r['voti'], r['seggi'],
                    t['el'], t['vo'], t['bi'], sumlist.get((k[0], k[1]), '') , len(t['amb']) if r['tipo'] == 'senato' else '', r['fonte']])
print(len(res), 'righe scritte')
for l in log: print(l)
