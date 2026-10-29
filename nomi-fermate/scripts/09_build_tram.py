"""Tram: fermate -> componenti (le fermate tram sono incroci 'via A via B') -> abbinamento con donne-nelle-vie.
Unita' di output: denominazione di strada/luogo che compare nei nomi delle fermate tram (route_type 0)."""
import csv, re, json, unicodedata, collections

def strip_acc(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return ''.join(c for c in s if not unicodedata.combining(c))

TYPES = {'v.le': 'viale', 'vle': 'viale', 'viale': 'viale', 'via': 'via', 'p.za': 'piazza', 'pza': 'piazza', 'piazza': 'piazza',
         'c.so': 'corso', 'corso': 'corso', 'l.go': 'largo', 'largo': 'largo', 'p.le': 'piazzale', 'piazzale': 'piazzale',
         'v.lo': 'vicolo', 'vicolo': 'vicolo', 'strada': 'strada', 'str.': 'strada', 'alzaia': 'alzaia', 'galleria': 'galleria',
         'g.ria': 'galleria', 'foro': 'foro', 'p.zetta': 'piazzetta', 'piazzetta': 'piazzetta', 'ripa': 'ripa', 'bastioni': 'bastioni', 'b.ni': 'bastioni'}
ABBR = {'s.': 'san', 'sant.': 'sant', 'p.ta': 'porta', 'p.ta.': 'porta', 'm.te': 'monte', 'f.lli': 'fratelli', 'fr.lli': 'fratelli', 'g.': 'g', 'b.': 'b',
        'ss.': 'santi', 'dott.': 'dottor', 'gen.': 'generale', 'ing.': 'ingegner', 'c.na': 'cascina', 'cascina': 'cascina', 'ten.': 'tenente',
        'col.': 'colonnello', 'm.llo': 'maresciallo', 'cap.': 'capitano', 'avv.': 'avvocato', 'prof.': 'professor', 'ang.': ''}

NUM = {str(i): w for i, w in enumerate('zero uno due tre quattro cinque sei sette otto nove dieci undici dodici tredici quattordici quindici sedici diciassette diciotto diciannove venti ventuno ventidue ventitre ventiquattro venticinque ventisei ventisette ventotto ventinove trenta trentuno'.split())}
NUM['0'] = '0'

def tokens(s):
    s = strip_acc(s)
    s = s.replace("'", ' ')
    out = []
    for t in s.split():
        t = t.strip(',;')
        if not t:
            continue
        if t in ABBR:
            out.append(ABBR[t]); continue
        t = re.sub(r'\.', ' ', t).split()
        out.extend(t)
    return [NUM.get(t, t) for t in out if t]

FUORI = {'rozzano', 'cinisello b.', 'sesto s.g.', 'osp.bassini'}

def parse(name):
    n = name.lower()
    comune = ''
    m = re.search(r'\(([^)]*)\)', n)
    while m:
        if m.group(1).strip() in FUORI:
            comune = m.group(1).strip()
        n = n.replace(m.group(0), ' '); m = re.search(r'\(([^)]*)\)', n)
    if re.match(r'^(cinisello|rozzano)', n.strip()):
        comune = comune or n.split()[0]
    n = re.sub(r',\s*\d+\w*', ' ', n)
    n = re.sub(r'\b(m[1-5])\b', ' ', n)
    n = re.sub(r'\bfs\b|\bfn\b', ' ', n)
    parts = []; cur = []; curtype = ''
    for raw in n.split():
        key = raw.strip(',')
        if key in TYPES:
            if cur:
                parts.append((curtype, cur))
            cur = []; curtype = TYPES[key]
        else:
            cur.append(key)
    if cur:
        parts.append((curtype, cur))
    res = []
    for t, c in parts:
        tk = tokens(' '.join(c))
        if tk:
            res.append((t, tk))
    return res, comune

# ---- registro strade (donne-nelle-vie)
s2 = list(csv.DictReader(open('../donne-nelle-vie/out/strade_classificate_arricchite_v2.csv', encoding='utf-8-sig')))
OCC = json.load(open('../donne-nelle-vie/out/occ_labels.json', encoding='utf-8'))
TIPI = {'via', 'viale', 'piazza', 'piazzale', 'largo', 'corso', 'vicolo', 'galleria', 'strada', 'piazzetta', 'alzaia', 'ripa', 'passaggio', 'bastioni', 'vicoletto', 'cavalcavia', 'foro', 'lungolago'}
reg = []
for r in s2:
    tk = tokens(r['nome'])
    t = r['tipo'].lower() if r['tipo'] else ''
    if tk and tk[0] in TIPI:
        t2 = tk[0]; tk = tk[1:]
        t = t or t2
    reg.append((t, tk, r))
byLast = collections.defaultdict(list)
byFirst = collections.defaultdict(list)
for t, tk, r in reg:
    if tk:
        byLast[tk[-1]].append((t, tk, r))
        byFirst[tk[0]].append((t, tk, r))

def tokcompat(a, b):
    """a: token della fermata (puo' essere iniziale), b: token del registro"""
    if a == b:
        return True
    if len(a) == 1 and b.startswith(a):
        return True
    if len(b) == 1 and a.startswith(b):
        return True
    if a in ('san', 'sant', 'santa', 'santo') and b in ('san', 'sant', 'santa', 'santo', 'sant'):
        return True
    return False

def match(typ, tk):
    cands = byLast.get(tk[-1], [])
    exact = []; suffix = []
    for t, rk, r in cands:
        if len(rk) == len(tk) and all(tokcompat(a, b) for a, b in zip(tk, rk)):
            exact.append((t, rk, r))
        elif len(rk) > len(tk) and all(tokcompat(a, b) for a, b in zip(tk[::-1], rk[::-1])):
            suffix.append((t, rk, r))
    prefix = []
    if not exact and not suffix:
        for t, rk, r in byFirst.get(tk[0], []):
            if len(rk) > len(tk) and all(tokcompat(a, b) for a, b in zip(tk, rk)):
                prefix.append((t, rk, r))
        pp = [x for x in prefix if x[0] == typ] or prefix
        if len({x[2]['qid'] or x[2]['nome'] for x in pp}) != 1:
            prefix = []
    for pool, lab in ((exact, 'esatto'), (suffix, 'suffisso'), (prefix, 'prefisso')):
        same = [x for x in pool if x[0] == typ]
        if len(same) >= 1:
            return same, lab + '+tipo'
        if pool:
            return pool, lab
    return [], ''

def occ_s2(r):
    out = []
    for x in re.split(r',\s*', r['professioni']):
        x = x.strip()
        if re.fullmatch(r'Q\d+', x):
            x = OCC.get(x, '')
        if x and x not in out and 'guerra' not in x.lower():
            out.append(x)
    return out

GRP = [('religione', r'santo|santa|vescov|sacerdot|presbit|prete|monaco|gesuit|predicator|teolog|papa|cardinal|missionar|religios|abate|arcivescov|frate'),
       ('militare', r'general|militar|condott|capitano|ammiragl|ufficiale|comandante|garibaldin|soldat|eroe'),
       ('politica e patrioti', r'politic|statista|patriot|ministro|president|deputat|senator|diplomatic|monarc|sovran|duca|imperator|giurist|economist|statistic|avvocat|magistrat|re di|sindaco|partigian|antifascist|resistenza'),
       ('lettere', r'scrittor|poet|giornalist|drammaturg|editor|storic|filosof|letterat|saggist|critic|romanzier'),
       ('arte e architettura', r'pittor|scultor|architett|artist|disegnat|incisor|ceramist|design|attore|attrice|regista'),
       ('musica', r'compositor|music|cantant|direttore d.orchestra|pianist|violinist'),
       ('scienza e tecnica', r'scienziat|fisic|chimic|matematic|medic|ingegner|astronom|biolog|botanic|esplorator|inventor|biochimic|microbiolog|geolog|naturalist|aviator|geograf|anatom'),
       ('impresa', r'imprenditor|industrial|banchier|finanzier'),
       ('sport', r'calciator|sportiv|allenator|ciclist|atlet')]

def gruppo(desc, occs):
    txt = ((desc or '') + ' ' + ' '.join(occs[:1])).lower()
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
                votes[g] += 1; break
    if votes:
        best = max(votes.values())
        for g, p in GRP:
            if votes.get(g) == best:
                return g
    return ''

def pick_persona(r):
    parts = [x.strip() for x in r['persona'].split('|') if x.strip()]
    if len(parts) <= 1:
        return r['persona']
    last = strip_acc(r['nome']).replace("'", ' ').split()[-1]
    for x in parts:
        if last in strip_acc(x).replace("'", ' ').split():
            return x
    return parts[0]

def classifica(r, quality):
    """da riga del registro -> categoria"""
    cat = r['categoria']; out = dict(categoria='', sottocategoria='', persona='', sesso='', mestiere='', gruppo='', nascita_morte='', qid='', note='')
    if r['santa'] == '1' or r['santo'] == '1':
        out['categoria'] = 'santo/santa'
        out['sesso'] = 'donna' if r['santa'] == '1' else 'uomo'
        out['persona'] = pick_persona(r); out['qid'] = r['qid']
        out['gruppo'] = 'religione'
        out['nascita_morte'] = f"{r['nascita']}–{r['morte']}" if (r['nascita'] or r['morte']) else ''
        return out
    if cat in ('uomo', 'donna'):
        out['categoria'] = 'persona'; out['sesso'] = cat; out['persona'] = pick_persona(r); out['qid'] = r['qid']
        oc = occ_s2(r); out['mestiere'] = ', '.join(oc[:6]); out['gruppo'] = gruppo(r['descrizione'], oc)
        out['nascita_morte'] = f"{r['nascita']}–{r['morte']}" if (r['nascita'] or r['morte']) else ''
        out['note'] = r['descrizione']
        return out
    if cat == 'misto':
        out['categoria'] = 'persone (gruppo/coppia)'; out['persona'] = pick_persona(r); out['note'] = 'categoria misto in donne-nelle-vie'
        return out
    if cat == 'sconosciuto':
        out['categoria'] = 'non classificato'; out['sottocategoria'] = 'nome proprio non identificato'
        return out
    m = r['motivo'].lower()
    if 'data/evento' in m:
        out['categoria'] = 'evento/data'
    elif 'cognome' in m or 'prenome' in m:
        out['categoria'] = 'non classificato'; out['sottocategoria'] = 'cognome/nome proprio (probabile persona, non identificata)'
    elif 'luogo' in m or 'parola chiave' in m or 'tag osm' in m:
        out['categoria'] = 'luogo/altro (non persona)'
        out['sottocategoria'] = 'luogo (Wikidata)' if 'wikidata' in m else ('luogo/oggetto (OSM)' if 'osm' in m else 'parola chiave non personale')
    elif 'stazione della metropolitana' in m:
        out['categoria'] = 'luogo/altro (non persona)'; out['sottocategoria'] = 'stazione/luogo'
    else:
        out['categoria'] = 'luogo/altro (non persona)'; out['sottocategoria'] = 'entita non umana: ' + r['motivo'][-50:]
    return out

# ---- fermate tram
stops = list(csv.DictReader(open('raw/tram_stops_gtfs.csv', encoding='utf-8')))
metro_names = {strip_acc(r['stazione']) for r in csv.DictReader(open('pulito/fermate_metro_nomi.csv', encoding='utf-8-sig'))}
comp = collections.OrderedDict()
for s in stops:
    parts, comune = parse(s['stop_name'])
    if not parts:
        continue
    for typ, tk in parts:
        key = (typ, ' '.join(tk), comune)
        d = comp.setdefault(key, {'stops': set(), 'lines': set(), 'ex': set()})
        d['stops'].add(s['stop_id']); d['lines'].update(s['routes'].split(',')); d['ex'].add(s['stop_name'])

METRO = {}
for r in csv.DictReader(open('pulito/fermate_metro_nomi.csv', encoding='utf-8-sig')):
    METRO[' '.join(tokens(r['stazione']))] = r
PLACE_RULES = [(r'^(teatro|palazzo|arco|universita|politecnico|ospedale|osp|cimitero|castello|museo|stadio|scuola|biblioteca|duomo|basilica|chiesa|santuario|camera|forum|arena)|(arena|ateneo|ospedale|universita)', 'edificio/istituzione', 'edificio/istituzione (parola chiave)'),
               (r'^(colonne|ponte|monumento|porta|arco)', 'edificio/istituzione', 'monumento/infrastruttura (parola chiave)'),
               (r'^(parco|giardini|navigli|naviglio|darsena)', 'luogo/altro (non persona)', 'parco/acqua (parola chiave)')]
rows = []
for (typ, name, comune), d in comp.items():
    tk = name.split()
    row = dict(denominazione=((typ + ' ') if typ else '') + name, tipo=typ, comune=comune or 'Milano', linee=','.join(sorted(d['lines'], key=lambda x: (len(x), x))),
               n_fermate=len(d['stops']), esempio_fermata=sorted(d['ex'])[0], categoria='', sottocategoria='', persona='', sesso='', mestiere='', gruppo_mestiere='',
               nascita_morte='', qid='', fonte='', confidenza='', registro_via='', note='', da_verificare='')
    flags = []
    if comune and strip_acc(comune) not in ('milano',):
        row['categoria'] = 'fuori Milano (non classificato)'; row['fonte'] = 'comune fuori registro Milano'; row['confidenza'] = ''
        # ma proviamo comunque il nome se e' un luogo noto? no: il registro copre solo Milano
        rows.append(row); continue
    hits, how = match(typ, tk)
    if not typ:
        k = ' '.join(t for t in tk if t not in ('stazione', 'fs', 'fn'))
        mr = METRO.get(k)
        if mr and k:
            row.update(categoria=mr['categoria'], sottocategoria=mr['sottocategoria'], persona=mr['persona'], sesso=mr['sesso'], mestiere=mr['mestiere'],
                       gruppo_mestiere=mr['gruppo_mestiere'], nascita_morte=mr['nascita_morte'], qid=mr['qid'], fonte='come stazione metro/ferroviaria ' + mr['stazione'],
                       confidenza=mr['confidenza'], note='nome uguale a una stazione metro/ferroviaria (stessa classificazione)')
            row['da_verificare'] = mr['da_verificare']
            rows.append(row); continue
        found = False
        for pat, cat, sub in PLACE_RULES:
            if re.search(pat, ' '.join(tk)):
                row.update(categoria=cat, sottocategoria=sub, fonte='regola_parola_chiave', confidenza='media', da_verificare='nome senza tipo di via: classificato per parola chiave')
                found = True; break
        if found:
            rows.append(row); continue
    hits, how = match(typ, tk)
    if not hits:
        row['categoria'] = 'non classificato'; row['sottocategoria'] = 'non trovato nel registro delle vie'; row['fonte'] = ''
        row['da_verificare'] = 'nessun abbinamento con il registro vie' if typ else 'nome di luogo senza tipo (non e\' una via): da classificare'
        rows.append(row); continue
    if len(hits) > 1:
        cats = {h[2]['categoria'] for h in hits}
        qids = {h[2]['qid'] for h in hits}
        if len(cats) > 1 or len(qids) > 1:
            flags.append('piu\' vie candidate: ' + '; '.join(f"{h[2]['nome']} ({h[2]['categoria']})" for h in hits[:4]))
    h = sorted(hits, key=lambda x: {'sicuro': 0, 'incerto': 1, 'nessuno': 2}.get(x[2]['confidenza'], 3))[0][2]
    out = classifica(h, how)
    row.update(categoria=out['categoria'], sottocategoria=out['sottocategoria'], persona=out['persona'], sesso=out['sesso'], mestiere=out['mestiere'],
               gruppo_mestiere=out['gruppo'], nascita_morte=out['nascita_morte'], qid=out['qid'], note=out['note'])
    row['registro_via'] = f"uid {h['uid']} {h['nome']} [{h['categoria']}/{h['confidenza']}; {how}]"
    row['fonte'] = 'donne-nelle-vie (' + h['fonte'] + ')'
    conf = h['confidenza']
    row['confidenza'] = {'sicuro': 'alta', 'incerto': 'media', 'nessuno': 'media'}.get(conf, 'media')
    if h['categoria'] == 'non_persona' and conf == 'nessuno':
        row['confidenza'] = 'media'
    if how.startswith('suffisso'):
        row['confidenza'] = 'media'
        if '+tipo' not in how:
            flags.append('abbinamento per parte finale del nome con tipo di via diverso (' + h['nome'] + ')')
    if how.startswith('prefisso'):
        flags.append('abbinamento per parte iniziale del nome (' + h['nome'] + ')'); row['confidenza'] = 'bassa'
    if conf == 'incerto' and out['categoria'] in ('persona', 'santo/santa'):
        flags.append('persona incerta in donne-nelle-vie')
    if out['categoria'] == 'non classificato':
        flags.append(out['sottocategoria'])
    row['da_verificare'] = '; '.join(flags)
    rows.append(row)

cols = list(rows[0].keys())
with open('pulito/fermate_tram_nomi.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
with open('pulito/da_verificare_tram.csv', 'w', newline='', encoding='utf-8-sig') as f:
    c2 = ['denominazione', 'linee', 'n_fermate', 'categoria', 'persona', 'da_verificare', 'registro_via', 'esempio_fermata']
    w = csv.DictWriter(f, fieldnames=c2); w.writeheader()
    for r in rows:
        if r['da_verificare']:
            w.writerow({k: r[k] for k in c2})
print(len(rows), 'denominazioni;', sum(1 for r in rows if r['da_verificare']), 'da verificare')
print(collections.Counter(r['categoria'] for r in rows))
