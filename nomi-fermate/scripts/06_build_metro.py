"""Classifica le stazioni metro: nome -> a chi/che cosa e' intitolata.
Catena: stazione -P138-> via/piazza/luogo -P138-> persona/luogo/evento (Wikidata) + controllo con donne-nelle-vie.
Regole per tipo (istanza Wikidata) in tipo_nodo(); pochi casi a mano in scripts/override_metro.json (sempre segnalati)."""
import csv, json, re, unicodedata, collections, sys

def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9 ]', ' ', s.replace("'", ' ')).split()

def nk(s):
    return ' '.join(norm(s))

CANON = {'DUOMO M1': 'Duomo', 'DUOMO M3': 'Duomo', 'CADORNA FN M1': 'Cadorna', 'CADORNA FN M2': 'Cadorna',
         'LORETO M1': 'Loreto', 'LORETO M2': 'Loreto', 'LOTTO FIERAMILANOCITY': 'Lotto', 'LOTTO M5': 'Lotto',
         'S.AMBROGIO': "Sant'Ambrogio", 'SAN AMBROGIO': "Sant'Ambrogio", 'S.AGOSTINO': "Sant'Agostino",
         'S.LEONARDO': 'San Leonardo', 'P.TA GENOVA F.S.': 'Porta Genova', 'P.TA VENEZIA': 'Porta Venezia',
         'VILLA S.G.': 'Villa San Giovanni', 'CENTRALE FS': 'Centrale', 'GARIBALDI FS': 'Garibaldi',
         'LAMBRATE FS': 'Lambrate', 'ROGOREDO FS': 'Rogoredo', 'SESTO 1 MAGGIO FS': 'Sesto 1° Maggio',
         'LODI T.I.B.B.': 'Lodi', 'AFFORI FN': 'Affori FN', 'AFFORI CENTRO': 'Affori Centro',
         'STAZIONE FORLANINI': 'Forlanini', 'SFORZA-POLICLINICO': 'Sforza-Policlinico',
         'RHO FIERAMILANO': 'Rho Fiera Milano', 'LINATE AEROPORTO': 'Linate Aeroporto',
         'ASSAGO MILANOFIORI FORUM': 'Assago Milanofiori Forum', 'ASSAGO MILANOFIORI NORD': 'Assago Milanofiori Nord',
         'CASSINA DE PECCHI': "Cassina de' Pecchi", 'SESTO RONDO': 'Sesto Rondò', 'PORTO DI MARE': 'Porto di Mare', 'VILLA FIORITA': 'Villa Fiorita', 'CA GRANDA': "Ca' Granda", 'QT8': 'QT8',
         'CERNUSCO SUL NAVIGLIO': 'Cernusco sul Naviglio', 'CONI ZUGNA': 'Coni Zugna', 'DE AMICIS': 'De Amicis',
         'DE ANGELI': 'De Angeli'}

def titolo(s):
    return CANON.get(s, s.title())

stops = list(csv.DictReader(open('raw/metro_stops_gtfs.csv', encoding='utf-8')))
st = collections.OrderedDict()
for s in stops:
    c = titolo(s['stop_name'])
    d = st.setdefault(c, {'lines': set(), 'gtfs': [], 'lat': [], 'lon': []})
    d['lines'].update(s['routes'].split(','))
    d['gtfs'].append(s['stop_name'])
    d['lat'].append(float(s['lat'])); d['lon'].append(float(s['lon']))

# ---------- Wikidata
wd = list(csv.DictReader(open('raw/wd_metro_stations.csv', encoding='utf-8')))
WDLBL = {}
for r in wd:
    k = nk(r['label'])
    WDLBL.setdefault(k, {})
    if r['named_qid']:
        t = WDLBL[k].setdefault(r['named_qid'], {'label': r['named_label'], 'inst': set(), 'sex': r['sex'], 'b': r['birth'], 'd': r['death'], 'desc': r['named_desc'], 'occ': set()})
        t['inst'].add(r['named_instance'])
ALIAS = {'Duomo': 'duomo', 'Cadorna': 'cadorna fn', 'Loreto': 'loreto', 'Lotto': 'lotto', "Sant'Ambrogio": 'sant ambrogio',
         "Sant'Agostino": 'sant agostino', 'San Leonardo': 'san leonardo', 'Porta Genova': 'porta genova',
         'Porta Venezia': 'porta venezia', 'Villa San Giovanni': 'villa san giovanni', 'Centrale': 'centrale fs',
         'Garibaldi': 'garibaldi fs', 'Lambrate': 'lambrate fs', 'Rogoredo': 'rogoredo fs',
         'Sesto 1° Maggio': 'sesto 1 maggio fs', 'Lodi': 'lodi tibb', 'Forlanini': 'stazione forlanini',
         'Rho Fiera Milano': 'rho fieramilano', 'Gambara': 'stazione di gambara', 'Ponale': 'stazione di ponale',
         'Porta Romana': 'stazione di porta romana', 'San Donato': 'stazione di san donato', 'Turro': 'stazione di turro',
         'Cernusco sul Naviglio': 'stazione di cernusco sul naviglio', 'Abbiategrasso': 'piazza abbiategrasso',
         'Affori FN': 'affori fn', 'Affori Centro': 'affori centro', 'Assago Milanofiori Forum': 'assago milanofiori forum',
         'Assago Milanofiori Nord': 'assago milanofiori nord'}

hop = {}
nodeinfo = {}
for r in csv.DictReader(open('raw/wd_hop2.csv', encoding='utf-8')):
    nodeinfo[r['named_qid']] = r['named_label']
    if r['target_qid']:
        t = hop.setdefault(r['named_qid'], {}).setdefault(r['target_qid'], {'label': r['target_label'], 'desc': r['target_desc'], 'sex': r['sex'], 'b': r['birth'], 'd': r['death'], 'occ': set(), 'inst': set()})
        if r['occupation']:
            t['occ'].add(r['occupation'])
        t['inst'].add(r['target_instance'])
        nodeinfo[r['target_qid']] = r['target_label']

# ---------- donne-nelle-vie
OCC = json.load(open('../donne-nelle-vie/out/occ_labels.json', encoding='utf-8'))
s2 = list(csv.DictReader(open('../donne-nelle-vie/out/strade_classificate_arricchite_v2.csv', encoding='utf-8-sig')))
TIPI = r'^(via|viale|piazza|piazzale|largo|corso|vicolo|galleria|strada|piazzetta|alzaia|ripa|passaggio)\s+'
def s2key(n):
    return re.sub(TIPI, '', nk(n))
S2N = collections.defaultdict(list)
S2Q = collections.defaultdict(list)
for r in s2:
    S2N[s2key(r['nome'])].append(r)
    for q in re.split(r'[;|]', r['qid']):
        if q.strip():
            S2Q[q.strip()].append(r)
PERS = collections.defaultdict(lambda: {'label': '', 'occ': []})
for r in csv.DictReader(open('raw/wd_persone.csv', encoding='utf-8')):
    p = PERS[r['qid']]; p['label'] = r['label']
    if r['occupation'] and r['occupation'] not in p['occ']:
        p['occ'].append(r['occupation'])

def occ_s2(r):
    out = []
    for x in re.split(r',\s*', r['professioni']):
        x = x.strip()
        if re.fullmatch(r'Q\d+', x):
            x = OCC.get(x, '')
        if x and x not in out:
            out.append(x)
    return out

# ---------- regole tipo nodo
def tipo_nodo(inst, label=''):
    I = ' | '.join(inst).lower()
    if 'umano' in I or 'figura umana' in I:
        return 'persona'
    if re.search(r'battaglia|referendum|concordato|accordo|festa|giorno festivo|mostra d.arte|competizione', I):
        return 'evento'
    if re.search(r'piazza|strada|via urbana', I):
        return 'via'
    if re.search(r'comune|citt|quartiere|regione|penisola|stato|paese|fiume|montagna|passo di|torrente|porta cittadina|capitale|oggetto geografico|divisione amministrativa|area protetta|nucleo di identit|distretto|frazione|cittadina', I):
        return 'luogo'
    if re.search(r'ospedale|stadio|aeroporto|aerodromo|stazione|fermata|cimitero|grattacielo|mulino|cascina|azienda|impresa|ente |impianto|ippodromo|polo fieristico|villa|monumento|edificio|business park|complesso|curia|ente finanziario|cattedrale|chiesa|basilica|certosa|oratorio|casello', I):
        return 'edificio'
    if re.search(r'taxon|bandiera', I):
        return 'altro'
    return 'ignoto'

def sub_luogo(inst):
    I = ' | '.join(inst).lower()
    for pat, n in [(r'quartiere|nucleo di identit|frazione|distretto', 'quartiere'), (r'comune', 'comune'), (r'regione|penisola|stato|paese', 'regione/stato'), (r'fiume|torrente|montagna|passo', 'natura'), (r'citt|capitale|cittadina|porta', 'città')]:
        if re.search(pat, I):
            return n
    return 'luogo'

def sub_edificio(inst):
    I = ' | '.join(inst).lower()
    for pat, n in [(r'ospedale', 'ospedale'), (r'stadio|ippodromo|impianto', 'impianto sportivo'), (r'aeroporto|aerodromo', 'aeroporto'), (r'stazione|fermata', 'stazione'), (r'cimitero', 'cimitero'), (r'grattacielo', 'grattacielo'), (r'chiesa|basilica|cattedrale|certosa|oratorio', 'chiesa'), (r'cascina', 'cascina'), (r'mulino', 'mulino'), (r'monumento', 'monumento'), (r'azienda|impresa|ente', 'azienda/ente'), (r'polo fieristico', 'fiera')]:
        if re.search(pat, I):
            return n
    return 'edificio'

GRP = [('religione', r'santo|santa|vescov|arcivescov|sacerdot|presbit|prete|monaco|gesuit|predicator|teolog|papa|cardinal|missionar|religios'),
       ('militare', r'general|militar|condott|capitano|ammiragl|ufficiale|comandante|garibaldin|soldat'),
       ('politica e patrioti', r'politic|statista|patriot|ministro|president|deputat|senator|diplomatic|monarc|sovran|duca|imperator|giurist|economist|statistic|avvocat|magistrat'),
       ('lettere', r'scrittor|poet|giornalist|drammaturg|editor|storic|filosof|letterat|saggist|critic|romanzier'),
       ('arte e architettura', r'pittor|scultor|architett|artist|disegnat|incisor|ceramist|design'),
       ('musica', r'compositor|music|cantant|direttore d.orchestra|pianist'),
       ('scienza e tecnica', r'scienziat|fisic|chimic|matematic|medic|ingegner|astronom|biolog|botanic|esplorator|inventor|biochimic|microbiolog|geolog|naturalist|aviator'),
       ('impresa', r'imprenditor|industrial|banchier|finanzier'),
       ('sport', r'calciator|sportiv|allenator|ciclist|atlet')]

def gruppo(desc, occs):
    txt = (desc or '').lower()
    first = []
    for g, p in GRP:
        m = re.search(p, txt)
        if m:
            first.append((m.start(), g))
    if first:
        return min(first)[1]
    votes = collections.Counter()
    for o in occs:
        for g, p in GRP:
            if re.search(p, o.lower()):
                votes[g] += 1
                break
    if not votes:
        return ''
    best = max(votes.values())
    for g, p in GRP:
        if votes.get(g) == best:
            return g
    return ''

def anno(d):
    if not d:
        return ''
    m = re.match(r'(-?)0*(\d+)', d)
    return (('-' if m.group(1) else '') + m.group(2)) if m else ''

def vita(b, d):
    b, d = anno(b), anno(d)
    return f'{b}–{d}' if (b or d) else ''

OV = json.load(open('scripts/override_metro.json', encoding='utf-8'))
out = []
for name, d in st.items():
    row = dict(stazione=name, linee=','.join(sorted(d['lines'])), gtfs=' / '.join(d['gtfs']), categoria='', sottocategoria='',
               riferimento_diretto='', intitolato_a='', persona='', sesso='', mestiere='', gruppo_mestiere='', nascita_morte='',
               qid='', fonte='', confidenza='', controllo_donne_nelle_vie='', note='', da_verificare='')
    flags = []
    key = ALIAS.get(name, nk(name))
    tg = WDLBL.get(key, {})
    row['fonte'] = 'wikidata_P138' if tg else ''
    ov = OV.get(name)
    full = bool(ov and 'categoria' in ov)
    tipo_dir = ''
    if full:
        for k, v in ov.items():
            if k == 'flag':
                flags.append(v)
            else:
                row[k] = v
        if not ov.get('fonte'):
            row['fonte'] = 'regola_manuale'
        if tg:
            row['riferimento_diretto'] = row['riferimento_diretto'] or '; '.join(t['label'] for t in tg.values())
    else:
        if not tg:
            flags.append('nessun dato Wikidata P138 e nessuna regola'); row['categoria'] = 'altro'
        else:
            if len(tg) > 1:
                flags.append("piu' elementi P138: " + '; '.join(t['label'] for t in tg.values()))
            ordine = {'via': 0, 'persona': 1, 'luogo': 2, 'evento': 3, 'edificio': 4, 'altro': 5, 'ignoto': 6}
            tid = sorted(tg, key=lambda k: ordine[tipo_nodo(tg[k]['inst'], tg[k]['label'])])[0]; t = tg[tid]
            row['riferimento_diretto'] = t['label']
            ninst = t['inst']; ntype = tipo_nodo(ninst, t['label']); tipo_dir = ntype
            path = [t['label']]; node = tid; person = None
            if ntype == 'persona':
                person = dict(label=t['label'], sex=t['sex'], b=t['b'], d=t['d'], desc=t['desc'], occ=set(), qid=tid)
            else:
                seen = {tid}
                for _ in range(5):
                    descend = ntype == 'via' or re.search(r'stazione|fermata', ' '.join(ninst).lower()) or nodeinfo.get(node, '').lower().startswith('porta ')
                    nxt = hop.get(node)
                    if not (descend and nxt):
                        break
                    cands = sorted(nxt.items(), key=lambda kv: 0 if tipo_nodo(kv[1]['inst'], kv[1]['label']) == 'persona' else 1)
                    nid, nt = cands[0]
                    if len(nxt) > 1 and tipo_nodo(nt['inst'], nt['label']) != 'persona':
                        flags.append("catena con piu' target a " + path[-1])
                    if nid in seen:
                        break
                    seen.add(nid); path.append(nt['label']); node = nid; ninst = nt['inst']; ntype = tipo_nodo(nt['inst'], nt['label'])
                    if ntype == 'persona':
                        person = dict(label=nt['label'], sex=nt['sex'], b=nt['b'], d=nt['d'], desc=nt['desc'], occ=nt['occ'], qid=nid)
                        break
            row['intitolato_a'] = ' > '.join(path[1:]) if len(path) > 1 else ''
            if person:
                row['categoria'] = 'persona'; row['qid'] = person['qid']
                pq = PERS.get(person['qid'])
                lab = person['label']
                s2h = S2Q.get(person['qid'], [])
                if re.fullmatch(r'Q\d+', lab):
                    # etichetta mancante in Wikidata: nome ricavato dalla via (tolto il tipo)
                    lab = re.sub(r'^(via|viale|piazza|piazzale|largo|corso)\s+', '', row['riferimento_diretto'], flags=re.I)
                row['persona'] = lab
                row['sesso'] = {'maschio': 'uomo', 'femmina': 'donna'}.get(person['sex'], '')
                occs = [o for o in (list(person['occ']) or (pq['occ'] if pq else [])) if 'guerra' not in o.lower()]
                desc = ''
                if s2h:
                    h = s2h[0]; desc = h['descrizione']
                    oc = occ_s2(h)
                    if oc:
                        occs = [o for o in oc if 'guerra' not in o.lower()]
                        row['fonte'] += '+donne-nelle-vie(mestiere)'
                row['mestiere'] = ', '.join(occs[:6])
                row['nascita_morte'] = vita(person['b'], person['d'])
                row['gruppo_mestiere'] = gruppo(desc, occs)
                row['note'] = desc
                row['confidenza'] = 'alta' if len(path) <= 2 else 'media'
                if 'leggendaria' in ' '.join(ninst).lower() or 'figura umana' in ' '.join(ninst).lower():
                    flags.append('figura leggendaria')
            else:
                if ntype == 'luogo':
                    row['categoria'] = 'luogo'; row['sottocategoria'] = sub_luogo(ninst)
                elif ntype == 'evento':
                    row['categoria'] = 'evento/data'
                elif ntype == 'edificio':
                    row['categoria'] = 'edificio/istituzione'; row['sottocategoria'] = sub_edificio(ninst)
                elif ntype == 'altro':
                    row['categoria'] = 'altro'; row['sottocategoria'] = 'simbolo' if 'bandiera' in ' '.join(ninst).lower() else 'natura/pianta'
                else:
                    row['categoria'] = 'luogo' if tipo_dir == 'via' else 'altro'; row['sottocategoria'] = 'piazza/via senza etimologia in Wikidata'
                    flags.append('nessuna etimologia in Wikidata per ' + path[-1])
                row['confidenza'] = 'alta' if row['categoria'] not in ('altro',) else 'media'
                if ntype == 'ignoto':
                    row['confidenza'] = 'bassa'
    if ov and not full:
        for k, v in ov.items():
            if k == 'flag':
                flags.append(v)
            else:
                row[k] = v
    # controllo con donne-nelle-vie (solo se il riferimento diretto e' una via/piazza)
    ref = row['riferimento_diretto']
    ctrl = ''
    if ref and (tipo_dir == 'via' or (full and tg and any(tipo_nodo(t['inst']) == 'via' for t in tg.values()))):
        hits = S2N.get(s2key(ref), [])
        if not hits and row['qid']:
            hits = S2Q.get(row['qid'], [])
        if hits:
            same = [h for h in hits if row['qid'] and row['qid'] in re.split(r'[;|]', h['qid'])]
            if not same and row['categoria'] == 'persona':
                same = [h for h in hits if h['categoria'] == row['sesso']]
                if same:
                    ctrl0 = 'concorda su persona/sesso ma QID diverso: ' + same[0]['qid']
            if same:
                h = same[0]; ctrl = f"concorda (uid {h['uid']}, {h['categoria']}, {h['confidenza']})" + (' [QID diverso: ' + h['qid'] + ']' if row['qid'] not in re.split(r'[;|]', h['qid']) else '')
                pass
            else:
                ctrl = '; '.join(f"uid {h['uid']} {h['nome']}: {h['categoria']} {h['persona']} {h['qid']}" for h in hits[:3])
                if row['categoria'] == 'persona' or any(h['categoria'] in ('uomo', 'donna') for h in hits):
                    flags.append('discordanza con donne-nelle-vie: ' + ctrl)
        else:
            ctrl = 'via non trovata nel registro'
    row['controllo_donne_nelle_vie'] = ctrl
    row['da_verificare'] = '; '.join(flags)
    if flags and row['confidenza'] == 'alta':
        row['confidenza'] = 'media'
    out.append(row)

cols = list(out[0].keys())
with open('pulito/fermate_metro_nomi.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
with open('pulito/da_verificare.csv', 'w', newline='', encoding='utf-8-sig') as f:
    c2 = ['stazione', 'categoria', 'persona', 'da_verificare', 'controllo_donne_nelle_vie']
    w = csv.DictWriter(f, fieldnames=c2); w.writeheader()
    for r in out:
        if r['da_verificare']:
            w.writerow({k: r[k] for k in c2})
print(len(out), 'stazioni;', sum(1 for r in out if r['da_verificare']), 'da verificare')
