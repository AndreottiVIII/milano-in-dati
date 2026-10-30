"""Costruisce i dati della pagina docs/nomi-fermate/data/ (stazioni.json, riepilogo.json, tram.json, stazioni_metro.csv).
Parte da pulito/fermate_metro_nomi_finale.csv (dopo le decisioni di Davide, script 11), raw/metro_stops_gtfs.csv (coordinate),
raw/wd_sitelinks.json (link Wikipedia, script 12) e pulito/fermate_tram_nomi.csv. Niente numeri scritti a mano: tutto calcolato qui."""
import csv, json, re, os, collections, unicodedata, urllib.parse
OUT = '../docs/nomi-fermate/data'
os.makedirs(OUT, exist_ok=True)

def nk(s):
    s = unicodedata.normalize('NFKD', s.lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', s.replace("'", ' ')).split())

rows = list(csv.DictReader(open('pulito/fermate_metro_nomi_finale.csv', encoding='utf-8-sig')))
gt = {r['stop_name']: r for r in csv.DictReader(open('raw/metro_stops_gtfs.csv', encoding='utf-8'))}
SL = json.load(open('raw/wd_sitelinks.json', encoding='utf-8'))
wdn = collections.defaultdict(set)
for r in csv.DictReader(open('raw/wd_metro_stations.csv', encoding='utf-8')):
    if r['named_qid']:
        wdn[nk(r['label'])].add(r['named_qid'])

SEC = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX']
PERSONE = ('persona', 'persona leggendaria', 'santo/santa')

def secolo(nm):
    m = re.match(r'^(-?\d+)?–', nm or '')
    if not m or not m.group(1):
        return 'non noto'
    a = int(m.group(1))
    return 'prima di Cristo' if a <= 0 else SEC[(a - 1) // 100 + 1] + ' secolo'

def secolo_ord(s):
    if s == 'prima di Cristo':
        return -1
    if s == 'non noto':
        return 99
    return SEC.index(s.split()[0])

def pulisci(x):
    return re.sub(r'\s+', ' ', x or '').strip()

st = []
for r in rows:
    pts = [(float(gt[g]['lat']), float(gt[g]['lon'])) for g in r['gtfs'].split(' / ') if g in gt]
    lat = sum(p[0] for p in pts) / len(pts)
    lon = sum(p[1] for p in pts) / len(pts)
    cat = r['categoria']
    if cat == 'persona':
        k = 'donna' if r['sesso'] == 'donna' else 'uomo'
    else:
        k = {'persona leggendaria': 'leggendaria', 'santo/santa': 'santo', 'luogo': 'luogo', 'evento/data': 'evento',
             'edificio/istituzione': 'edificio', 'altro': 'altro'}[cat]
    # catena stazione -> via -> persona/luogo
    parts = [r['stazione']]
    ref = r['riferimento_diretto'].split(';')[0]
    extra = [r['persona']] if cat in PERSONE else []
    for x in re.split(r'\s*>\s*', ref) + re.split(r'\s*>\s*', r['intitolato_a']) + extra:
        x = pulisci(x)
        if x and not re.fullmatch(r'Q\d+', x) and nk(re.sub(r'\(.*?\)', '', x)) not in [nk(re.sub(r'\(.*?\)', '', p)) for p in parts]:
            parts.append(x)
    qid = r['qid'] if re.fullmatch(r'Q\d+', r['qid']) else ''
    qtipo = ('persona' if cat in PERSONE else 'luogo') if qid else ''
    if not qid:
        cand = set()
        for g in [r['stazione']] + r['gtfs'].split(' / '):
            cand |= wdn.get(nk(g), set())
        if len(cand) == 1:
            qid = next(iter(cand))
            qtipo = 'collegato'
    sl = SL.get(qid, {})
    wp = sl.get('it') or sl.get('en') or ''
    st.append(dict(n=r['stazione'], l=r['linee'].split(','), lat=round(lat, 5), lon=round(lon, 5), k=k, cat=cat, sc=r['sottocategoria'],
                   p=r['persona'] if cat in PERSONE else '', s=r['sesso'] if cat in PERSONE else '',
                   g=r['gruppo_mestiere'], m=r['mestiere'], v=r['nascita_morte'], sec=secolo(r['nascita_morte']) if cat == 'persona' else '',
                   catena=parts, qid=qid, qtipo=qtipo, wp=wp, wpt=urllib.parse.unquote(wp.split('/wiki/')[-1]).replace('_', ' ') if wp else '', wpl='it' if sl.get('it') else ('en' if sl.get('en') else ''),
                   dec=r['decisione_davide'], nota=pulisci(r['note']) if cat in PERSONE else ''))
json.dump(st, open(f'{OUT}/stazioni.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

with open(f'{OUT}/stazioni_metro.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['stazione', 'linee', 'categoria', 'sottocategoria', 'persona', 'sesso', 'mestiere', 'nascita_morte', 'catena', 'wikidata', 'decisa_da_davide'])
    for s in st:
        w.writerow([s['n'], ','.join(s['l']), s['cat'], s['sc'], s['p'], s['s'], s['m'], s['v'], ' > '.join(s['catena']), s['qid'], 'si' if s['dec'] else ''])

# ---------------- riepilogo metro
KEYS = ['donna', 'uomo', 'leggendaria', 'santo', 'luogo', 'evento', 'edificio', 'altro']
LINES = ['M1', 'M2', 'M3', 'M4', 'M5']
tab = {k: dict(tot=0, **{l: 0 for l in LINES}) for k in KEYS}
for s in st:
    tab[s['k']]['tot'] += 1
    for l in s['l']:
        tab[s['k']][l] += 1
linee_tot = {l: sum(1 for s in st if l in s['l']) for l in LINES}
reali = [s for s in st if s['cat'] == 'persona']
donne = [s for s in reali if s['s'] == 'donna']
uomini = [s for s in reali if s['s'] == 'uomo']
santi = [s for s in st if s['cat'] == 'santo/santa']
gr = collections.OrderedDict()
sec = {}
for s in reali:
    sx = 'donne' if s['s'] == 'donna' else 'uomini'
    g = s['g'] or 'non classificato'
    gr.setdefault(g, {'uomini': 0, 'donne': 0})[sx] += 1
    sec.setdefault(s['sec'], {'uomini': 0, 'donne': 0})[sx] += 1
rie = dict(
    fermate_fisiche=len(gt),
    stazioni=len(st), tab=tab, linee_tot=linee_tot,
    persone_reali=len(reali), uomini=len(uomini), donne=len(donne), donne_nomi=[s['p'] for s in donne],
    leggendarie=[s['p'] for s in st if s['k'] == 'leggendaria'],
    santi=dict(uomini=sum(1 for s in santi if s['s'] == 'uomo'), donne=sum(1 for s in santi if s['s'] == 'donna'),
               nomi=[s['p'] for s in santi], donne_nomi=[s['p'] for s in santi if s['s'] == 'donna']),
    mestieri=sorted([[g, v['uomini'], v['donne']] for g, v in gr.items()], key=lambda x: -(x[1] + x[2])),
    secoli=sorted([[k, v['uomini'], v['donne']] for k, v in sec.items()], key=lambda x: secolo_ord(x[0])),
    decise=sum(1 for s in st if s['dec']),
    decise_elenco=[[s['n'], s['cat'], s['dec']] for s in st if s['dec']],
)

# ---------------- tram
tram = list(csv.DictReader(open('pulito/fermate_tram_nomi.csv', encoding='utf-8-sig')))
cat_t = collections.OrderedDict()
for r in tram:
    c = cat_t.setdefault(r['categoria'], {'den': 0, 'fermate': 0, 'dubbi': 0})
    c['den'] += 1
    c['fermate'] += int(r['n_fermate'])
    c['dubbi'] += 1 if r['da_verificare'] else 0
tp = [r for r in tram if r['categoria'] == 'persona']
ts = [r for r in tram if r['categoria'] == 'santo/santa']
tg = collections.OrderedDict()
tsec = {}
for r in tp:
    sx = 'donne' if r['sesso'] == 'donna' else 'uomini'
    g = r['gruppo_mestiere'] or 'non classificato'
    tg.setdefault(g, {'uomini': 0, 'donne': 0})[sx] += 1
    tsec.setdefault(secolo(r['nascita_morte']), {'uomini': 0, 'donne': 0})[sx] += 1
trm = dict(
    fermate_fisiche=sum(1 for _ in csv.DictReader(open('raw/tram_stops_gtfs.csv', encoding='utf-8'))),
    denominazioni=len(tram), dubbi=sum(1 for r in tram if r['da_verificare']),
    categorie=sorted([[k, v['den'], v['fermate'], v['dubbi']] for k, v in cat_t.items()], key=lambda x: -x[1]),
    persone=len(tp), uomini=sum(1 for r in tp if r['sesso'] == 'uomo'), donne=sum(1 for r in tp if r['sesso'] == 'donna'),
    donne_nomi=[(r['persona'] or r['denominazione']) + (' (da verificare)' if r['da_verificare'] else '') for r in tp if r['sesso'] == 'donna'],
    persone_dubbie=sum(1 for r in tp if r['da_verificare']),
    santi=dict(uomini=sum(1 for r in ts if r['sesso'] == 'uomo'), donne=sum(1 for r in ts if r['sesso'] == 'donna'),
               donne_nomi=[(r['persona'] or r['denominazione']) for r in ts if r['sesso'] == 'donna']),
    mestieri=sorted([[g, v['uomini'], v['donne']] for g, v in tg.items()], key=lambda x: -(x[1] + x[2])),
    secoli=sorted([[k, v['uomini'], v['donne']] for k, v in tsec.items()], key=lambda x: secolo_ord(x[0])),
    dubbi_elenco=[[r['denominazione'], r['linee'], r['categoria'], r['persona'], r['da_verificare']] for r in tram if r['da_verificare']],
)
json.dump(rie, open(f'{OUT}/riepilogo.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(trm, open(f'{OUT}/tram.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('stazioni', len(st), '| donne', len(donne), 'uomini', len(uomini), 'santi', rie['santi']['uomini'], rie['santi']['donne'], 'leggendarie', rie['leggendarie'])
print({k: v['tot'] for k, v in tab.items()})
print(rie['mestieri'])
print(rie['secoli'])
print('con link Wikipedia:', sum(1 for s in st if s['wp']), '| con qid:', sum(1 for s in st if s['qid']))
print('tram', trm['persone'], trm['uomini'], trm['donne'], trm['dubbi'], trm['categorie'])
print(trm['donne_nomi'], trm['santi'], trm['mestieri'], trm['secoli'])
