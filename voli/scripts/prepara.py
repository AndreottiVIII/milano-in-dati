"""Prepara i dati della pagina «Dove si vola da Milano» (docs/voli/data/).
Uso: python -I -X utf8 voli/scripts/prepara.py        (dopo scarica.py)
Legge voli/grezzi/ e scrive file piccoli (CSV con ; e JSON) in docs/voli/data/.
Eurostat avia_par_it, passeggeri trasportati sulla rotta (PAS_CRD): per ogni coppia aeroporto principale / aeroporto
partner il numero di passeggeri nei due sensi. Si tengono le coppie con Linate (LIML), Malpensa (LIMC), Bergamo (LIME)."""
import os, json, csv, collections, math
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(R, 'grezzi')
OUT = os.path.join(os.path.dirname(R), 'docs', 'voli', 'data'); os.makedirs(OUT, exist_ok=True)
MIL = {'LIML': 'Linate', 'LIMC': 'Malpensa', 'LIME': 'Bergamo'}
ANNI = list(range(2004, 2025))          # anni completi usati per classifiche, mappa e mesi
ANNI_ROMA = list(range(1993, 2025))     # la rotta con Roma si guarda più indietro: dove Eurostat non ha dati la linea si interrompe

# ---------- lettura Eurostat (JSON-stat) ----------
def leggi(path):
    d = json.load(open(path, encoding='utf-8'))
    ap = d['dimension']['airp_pr']['category']['index']
    tm = list(d['dimension']['time']['category']['index'])
    n = len(tm); inv = {v: k for k, v in ap.items()}
    out = collections.defaultdict(dict)
    for k, v in d['value'].items():
        k = int(k); out[inv[k // n]][tm[k % n]] = v
    return out
A = leggi(os.path.join(G, 'eurostat_A.json'))
M = {}
for y in range(2002, 2025):
    p = os.path.join(G, 'eurostat_M%d.json' % y)
    if os.path.exists(p):
        for k, r in leggi(p).items(): M.setdefault(k, {}).update(r)

# ---------- aeroporti e città ----------
AIR = {}
for r in csv.DictReader(open(os.path.join(G, 'airports.csv'), encoding='utf-8')):
    AIR[r['ident']] = r
# nome italiano della città e raggruppamento degli aeroporti della stessa città
CITTA = {}
def c(nome, *codici):
    for x in codici: CITTA[x] = nome
c('Parigi', 'LFPG', 'LFPO', 'LFPB', 'LFOB'); c('Londra', 'EGLL', 'EGKK', 'EGSS', 'EGGW', 'EGLC', 'EGMC')
c('Roma', 'LIRF', 'LIRA'); c('Istanbul', 'LTFM', 'LTFJ', 'LTBA'); c('Mosca', 'UUEE', 'UUDD', 'UUWW')
c('New York', 'KJFK', 'KEWR', 'KLGA'); c('Bruxelles', 'EBBR', 'EBCI'); c('Berlino', 'EDDB', 'EDDT', 'EDDI', 'EDBR')
c('Stoccolma', 'ESSA', 'ESSB', 'ESKN'); c('Oslo', 'ENGM', 'ENTO', 'ENRY'); c('Varsavia', 'EPWA', 'EPMO')
c('Bucarest', 'LROP', 'LRBS'); c('Venezia', 'LIPZ', 'LIPH'); c('Atene', 'LGAV', 'LGAT'); c('Il Cairo', 'HECA', 'HESX')
c('Sharm el-Sheikh', 'HESH', 'HE01'); c('Catania', 'LICC'); c('Palermo', 'LICJ'); c('Barcellona', 'LEBL'); c('Madrid', 'LEMD')
c('Napoli', 'LIRN'); c('Bari', 'LIBD'); c('Cagliari', 'LIEE'); c('Amsterdam', 'EHAM'); c('Brindisi', 'LIBR'); c('Tirana', 'LATI')
c('Lamezia Terme', 'LICA'); c('Lisbona', 'LPPT'); c('Olbia', 'LIEO'); c('Francoforte', 'EDDF'); c('Vienna', 'LOWW')
c('Budapest', 'LHBP'); c('Copenaghen', 'EKCH'); c('Dubai', 'OMDB'); c('Praga', 'LKPR'); c('Doha', 'OTHH'); c('Dublino', 'EIDW')
c('Malaga', 'LEMG'); c('Manchester', 'EGCC'); c('Alghero', 'LIEA'); c('Marrakech', 'GMMX'); c('Monaco di Baviera', 'EDDM')
c('Valencia', 'LEVC'); c('Porto', 'LPPR'); c('Cracovia', 'EPKK'); c('Tenerife', 'GCTS'); c('Ibiza', 'LEIB'); c('Palma di Maiorca', 'LEPA')
c('La Valletta', 'LMML'); c('Helsinki', 'EFHK'); c('Sofia', 'LBSF'); c('Cluj-Napoca', 'LRCL'); c('Tel Aviv', 'LLBG')
c('Abu Dhabi', 'OMAA'); c('Alicante', 'LEAL'); c('Düsseldorf', 'EDDL'); c('Edimburgo', 'EGPH'); c('Casablanca', 'GMMN')
c('Iași', 'LRIA'); c('Gedda', 'OEJN'); c('Lussemburgo', 'ELLX'); c('Zurigo', 'LSZH'); c('San Paolo', 'SBGR'); c('Vilnius', 'EYVI')
c('Siviglia', 'LEZL'); c('Pechino', 'ZBAA'); c('Colonia', 'EDDK'); c('Trapani', 'LICT'); c('Eindhoven', 'EHEH'); c('Pescara', 'LIBP')
c('Reykjavík', 'BIKF'); c('Reggio Calabria', 'LICR'); c('Fuerteventura', 'GCFV'); c('Shanghai', 'ZSPD'); c('Tunisi', 'DTTA')
c('Addis Abeba', 'HAAB'); c('Nuova Delhi', 'VIDP'); c('Crotone', 'LIBC'); c('Singapore', 'WSSS'); c('Atlanta', 'KATL')
c('Marsa Alam', 'HEMA'); c('Montréal', 'CYUL'); c('Chisinau', 'LUKK'); c('Poznań', 'EPPO'); c('Taipei', 'RCTP'); c('Chicago', 'KORD')
c('Hong Kong', 'VHHH'); c('Mykonos', 'LGMK'); c('Katowice', 'EPKT'); c('Sharjah', 'OMSJ'); c('Belgrado', 'LYBE'); c('Erevan', 'UDYZ')
c('Timișoara', 'LRTR'); c('Bangkok', 'VTBS'); c('Suceava', 'LRSV'); c('Bratislava', 'LZIB'); c('Seul', 'RKSI'); c('Mascate', 'OOMS')
c('Craiova', 'LRCV'); c('Breslavia', 'EPWR'); c('Minorca', 'LEMH'); c('Salonicco', 'LGTS'); c('Stoccarda', 'EDDS')
c('Pristina', 'BKPR'); c('Creta (Candia)', 'LGIR'); c('Fez', 'GMFF'); c('Riga', 'EVRA'); c('Amburgo', 'EDDH'); c('Corfù', 'LGKR')
c('Zagabria', 'LDZA'); c('Bilbao', 'LEBB'); c('Trieste', 'LIVT'); c('Lione', 'LFLL'); c('Ginevra', 'LSGG'); c('Toronto', 'CYYZ')
c('Boston', 'KBOS'); c('Miami', 'KMIA'); c('Los Angeles', 'KLAX'); c('Washington', 'KIAD'); c('Tokyo', 'RJTT', 'RJAA')
c('Malè (Maldive)', 'VRMM'); c('Bologna', 'LIPE'); c('Pisa', 'LIRP'); c('Firenze', 'LIRQ'); c('Torino', 'LIMF'); c('Genova', 'LIMJ')
c('Verona', 'LIPX'); c('Alghero', 'LIEA'); c('Lampedusa', 'LICD'); c('Pantelleria', 'LICG'); c('Ancona', 'LIPY'); c('Rimini', 'LIPR')
c('Cuneo', 'LIMZ'); c('Comiso', 'LICB'); c('Tortolì', 'LIET'); c('Taranto', 'LIBG'); c('Foggia', 'LIBF'); c('Perugia', 'LIRZ')
c('Lourdes', 'LFBT'); c('Kos', 'LGKO'); c('Rodi', 'LGRP'); c('Zante', 'LGZA'); c('Santorini', 'LGSR'); c('Cefalonia', 'LGKF')
c('Lisbona', 'LPPT'); c('Madeira', 'LPMA'); c('Faro', 'LPFR'); c('Gran Canaria', 'GCLP'); c('Lanzarote', 'GCRR'); c('Santo Domingo', 'MDSD')
def nome_citta(icao):
    if icao in CITTA: return CITTA[icao]
    m = (AIR.get(icao, {}).get('municipality') or icao)
    return m.split('(')[0].strip()
# area della mappa
AREE = [('it', 'Italia'), ('ovest', 'Europa occidentale'), ('nord', 'Europa del nord'), ('est', 'Europa orientale e Balcani'),
        ('med', 'Mediterraneo'), ('oltre-ovest', 'Americhe e Canarie'), ('oltre-est', 'Asia, Golfo e Africa subsahariana')]
PAESI = {'it': 'IT', 'ovest': 'FR ES PT UK GB IE NL BE LU DE CH AT MC AD LI',
         'nord': 'DK SE NO FI IS EE LV LT',
         'est': 'PL CZ SK HU RO BG HR SI RS BA ME MK AL XK MD UA RU BY GE AM AZ',
         'med': 'EL GR TR CY MT MA TN DZ EG IL JO LB LY',
         'oltre-ovest': 'US CA BR AR MX CU DO CL CO PE VE JM BS PA CR CV'}
AREA_DI = {p: k for k, v in PAESI.items() for p in v.split()}
def area(paese, icao):
    if icao.startswith('GC'): return 'oltre-ovest'       # Canarie: fuori mappa, a ovest
    return AREA_DI.get(paese, 'oltre-est')

# ---------- coppie con Milano ----------
righe = []     # (aeroporto, partner icao, città, paese, serie annuale, serie mensile)
for p, serie in A.items():
    if p[3:7] not in MIL or p[7] != '_': continue
    icao = p[11:]; paese = p[8:10]
    if icao in MIL or any(ch.isdigit() for ch in icao) or icao == 'ZZZZ': continue   # sistemi di aeroporti e «sconosciuto»
    righe.append(dict(ap=MIL[p[3:7]], icao=icao, paese=paese, citta=nome_citta(icao), A=serie, M=M.get(p, {})))
# totali non attribuibili (per i limiti)
nonattr = collections.Counter()
for p, serie in A.items():
    if p[3:7] in MIL and p[7] == '_' and (any(ch.isdigit() for ch in p[11:]) or p[11:] == 'ZZZZ'):
        for t, v in serie.items(): nonattr[t] += v

def coord(citta_icaos):
    # coordinate della città: l'aeroporto con più passeggeri nel 2024 (o il primo disponibile)
    best = None
    for ic, v in citta_icaos:
        a = AIR.get(ic)
        if a and a['latitude_deg']:
            if best is None or v > best[0]: best = (v, float(a['longitude_deg']), float(a['latitude_deg']))
    return (best[1], best[2]) if best else None
COORD_FIX = {'Berlino': (13.50, 52.37), 'Atene': (23.94, 37.94), 'Sharm el-Sheikh': (34.39, 27.98)}

# ---------- città per anno ----------
tot_citta = collections.defaultdict(lambda: collections.defaultdict(int))        # citta -> anno -> pax
tot_citta_ap = collections.defaultdict(lambda: collections.defaultdict(int))     # (citta, aeroporto) -> anno -> pax
paese_citta = {}; icaos_citta = collections.defaultdict(lambda: collections.defaultdict(int))
for r in righe:
    paese_citta[r['citta']] = r['paese']
    for t, v in r['A'].items():
        y = int(t); tot_citta[r['citta']][y] += v; tot_citta_ap[(r['citta'], r['ap'])][y] += v
    icaos_citta[r['citta']][r['icao']] += r['A'].get('2024', 0)
tot_anno = {y: sum(tot_citta[c_].get(y, 0) for c_ in tot_citta) for y in range(1993, 2025)}
tot_ap_anno = {a: {y: sum(v.get(y, 0) for (c_, ap), v in tot_citta_ap.items() if ap == a) for y in range(1993, 2025)} for a in MIL.values()}

def classifica(y):
    v = sorted(((tot_citta[c_].get(y, 0), c_) for c_ in tot_citta if tot_citta[c_].get(y, 0) > 0), reverse=True)
    return [(c_, p, i + 1) for i, (p, c_) in enumerate(v)]
RANK = {y: classifica(y) for y in ANNI}

# ---------- 1. CSV: città per anno ----------
with open(os.path.join(OUT, 'citta_annuale.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['citta', 'paese', 'anno', 'passeggeri', 'linate', 'malpensa', 'bergamo'])
    for c_ in sorted(tot_citta):
        for y in ANNI:
            if tot_citta[c_].get(y):
                w.writerow([c_, paese_citta[c_], y, tot_citta[c_][y]] + [tot_citta_ap[(c_, a)].get(y, 0) for a in ('Linate', 'Malpensa', 'Bergamo')])

# ---------- 2. CSV: rotte (aeroporto di Milano - aeroporto partner) ----------
with open(os.path.join(OUT, 'rotte_annuale.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['aeroporto_milano', 'codice_partner', 'aeroporto_partner', 'citta', 'paese', 'anno', 'passeggeri'])
    for r in sorted(righe, key=lambda r: (r['ap'], r['citta'], r['icao'])):
        nm = (AIR.get(r['icao'], {}).get('name') or r['icao'])
        for t in sorted(r['A']):
            if int(t) in ANNI: w.writerow([r['ap'], r['icao'], nm, r['citta'], r['paese'], t, r['A'][t]])

# ---------- 3. CSV: mesi (le 80 città più grandi del 2024; 2015-2024) ----------
top80 = [c_ for c_, p, i in RANK[2024][:80]]
mesi_citta = collections.defaultdict(lambda: collections.defaultdict(int))
for r in righe:
    if r['citta'] in top80:
        for t, v in r['M'].items():
            y, m = int(t[:4]), int(t[5:]); mesi_citta[r['citta']][(y, m)] += v
with open(os.path.join(OUT, 'mesi_citta.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['citta', 'anno', 'mese', 'passeggeri'])
    for c_ in top80:
        for (y, m), v in sorted(mesi_citta[c_].items()):
            if y >= 2015: w.writerow([c_, y, m, v])
mesi_ap = collections.defaultdict(lambda: collections.defaultdict(int))
for r in righe:
    for t, v in r['M'].items(): mesi_ap[r['ap']][(int(t[:4]), int(t[5:]))] += v
with open(os.path.join(OUT, 'mesi_aeroporti.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['aeroporto', 'anno', 'mese', 'passeggeri'])
    for a in MIL.values():
        for (y, m), v in sorted(mesi_ap[a].items()): w.writerow([a, y, m, v])

# ---------- 4. Milano-Roma ----------
def serie_rotta(ap_cod, icao):
    return {int(t): v for t, v in A.get('IT_%s_IT_%s' % (ap_cod, icao), {}).items()}
lin_fco = serie_rotta('LIML', 'LIRF')
roma_tot = {y: tot_citta['Roma'].get(y) for y in ANNI_ROMA if tot_citta['Roma'].get(y)}
lin_altre = {y: tot_ap_anno['Linate'][y] - lin_fco.get(y, 0) for y in ANNI_ROMA if tot_ap_anno['Linate'][y] and y in lin_fco}
with open(os.path.join(OUT, 'milano_roma.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['anno', 'linate_fiumicino', 'milano_roma_tutti_gli_aeroporti', 'linate_altre_rotte'])
    for y in ANNI_ROMA:
        if y in lin_fco or y in roma_tot: w.writerow([y, lin_fco.get(y, ''), roma_tot.get(y, ''), lin_altre.get(y, '')])

# ---------- 5. mappa base (stati) ----------
from shapely.geometry import shape, box, mapping
from shapely import simplify
FIN = box(-14, 26, 62, 64)
base = []
for ft in json.load(open(os.path.join(G, 'ne50.geojson'), encoding='utf-8'))['features']:
    g = shape(ft['geometry'])
    if not g.intersects(FIN): continue
    g = simplify(g.intersection(FIN), 0.06, preserve_topology=True)
    if g.is_empty: continue
    polys = [g] if g.geom_type == 'Polygon' else [x for x in g.geoms if x.geom_type == 'Polygon']
    pp = []
    for pl in polys:
        if pl.area < 0.04: continue
        pp.append([[[round(x, 2), round(y, 2)] for x, y in pl.exterior.coords]])
    if pp: base.append({'n': ft['properties'].get('ISO_A2_EH') or ft['properties'].get('ISO_A2'), 'p': [q[0] for q in pp], 'it': (ft['properties'].get('ISO_A2_EH') == 'IT')})
json.dump({'stati': base}, open(os.path.join(OUT, 'mappa_base.json'), 'w'), separators=(',', ':'))

# ---------- 6. riepilogo ----------
def dest(c_, y):
    return dict(citta=c_, paese=paese_citta[c_], pax=tot_citta[c_].get(y, 0))
top30 = []
for c_, p, i in RANK[2024][:30]:
    xy = COORD_FIX.get(c_) or coord(list(icaos_citta[c_].items()))
    ar = area(paese_citta[c_], max(icaos_citta[c_], key=icaos_citta[c_].get))
    top30.append(dict(citta=c_, paese=paese_citta[c_], pax=p, rank=i, area=ar, lon=xy[0], lat=xy[1],
                      ap={a: tot_citta_ap[(c_, a)].get(2024, 0) for a in MIL.values()}))
# totali per area (tutte le città del 2024, non solo le prime 30)
aree_tot = collections.Counter(); aree_n = collections.Counter()
for c_ in tot_citta:
    p = tot_citta[c_].get(2024, 0)
    if p:
        ar = area(paese_citta[c_], max(icaos_citta[c_], key=icaos_citta[c_].get))
        aree_tot[ar] += p; aree_n[ar] += 1
# per le aree fuori mappa, le città più grandi (testo delle frecce)
fuori = {}
for k in ('oltre-ovest', 'oltre-est'):
    cs = sorted(((tot_citta[c_].get(2024, 0), c_) for c_ in tot_citta if tot_citta[c_].get(2024, 0) and area(paese_citta[c_], max(icaos_citta[c_], key=icaos_citta[c_].get)) == k), reverse=True)
    fuori[k] = [dict(citta=c_, pax=p) for p, c_ in cs[:4]]

# classifica che cambia: 2004, 2009, 2014, 2019, 2024
BUMP_Y = [2004, 2009, 2014, 2019, 2024]
in_top10 = []
for y in BUMP_Y:
    for c_, p, i in RANK[y][:10]:
        if c_ not in in_top10: in_top10.append(c_)
bump = []
for c_ in in_top10:
    bump.append(dict(citta=c_, rank={str(y): next((i for cc, p, i in RANK[y] if cc == c_), None) for y in BUMP_Y},
                     pax={str(y): tot_citta[c_].get(y, 0) for y in BUMP_Y}))

# stagionalità (mesi 2024): quota di ogni mese sul totale dell'anno, per le prime 80 città
stag = []
for c_ in top80:
    mm = [mesi_citta[c_].get((2024, m), 0) for m in range(1, 13)]
    t = sum(mm)
    if t < 150000: continue
    sh = [100 * x / t for x in mm]
    stag.append(dict(citta=c_, paese=paese_citta[c_], tot=t, quota=[round(x, 2) for x in sh], picco=max(sh), mese_picco=sh.index(max(sh)) + 1,
                     min=min(sh), estate=sh[6] + sh[7], dev=math.sqrt(sum((x - 100 / 12) ** 2 for x in sh) / 12)))

# Linate nel 2019: mesi
lin19 = {m: mesi_ap['Linate'].get((2019, m), 0) for m in range(1, 13)}
lin18 = {m: mesi_ap['Linate'].get((2018, m), 0) for m in range(1, 13)}
lin_fco_m = collections.defaultdict(int)
for r in righe:
    if r['ap'] == 'Linate' and r['icao'] == 'LIRF':
        for t, v in r['M'].items(): lin_fco_m[(int(t[:4]), int(t[5:]))] = v

# copertura rispetto ai passeggeri contati dagli aeroporti (ENAC, dalla pagina Aeroporti)
enac = {}
for r in csv.DictReader(open(os.path.join(os.path.dirname(R), 'docs', 'aeroporti', 'data', 'annuale_tre_aeroporti.csv'), encoding='utf-8'), delimiter=';'):
    enac[(r['aeroporto'], int(r['anno']))] = int(r['passeggeri'])
cop = {a: {y: round(100 * tot_ap_anno[a][y] / enac[(a, y)], 1) for y in range(2004, 2025) if (a, y) in enac and tot_ap_anno[a][y]} for a in MIL.values()}

n_citta = {y: sum(1 for c_ in tot_citta if tot_citta[c_].get(y, 0) > 0) for y in ANNI}
n_paesi = {y: len({paese_citta[c_] for c_ in tot_citta if tot_citta[c_].get(y, 0) > 0}) for y in ANNI}
riep = dict(
    fonte='Eurostat avia_par_it, passeggeri trasportati (PAS_CRD)', anni=ANNI,
    totale_anno={str(y): tot_anno[y] for y in range(1993, 2025) if tot_anno[y]},
    totale_ap={a: {str(y): v for y, v in s.items() if v} for a, s in tot_ap_anno.items()},
    copertura=cop, non_attribuiti={t: v for t, v in sorted(nonattr.items())},
    n_citta={str(k): v for k, v in n_citta.items()}, n_paesi={str(k): v for k, v in n_paesi.items()},
    top30=top30, aree=[dict(k=k, nome=n, pax=aree_tot[k], n=aree_n[k]) for k, n in AREE], fuori=fuori,
    bump_anni=BUMP_Y, bump=bump, rank_top20={str(y): [dict(citta=c_, pax=p) for c_, p, i in RANK[y][:20]] for y in ANNI},
    stagionalita=stag,
    roma=dict(linate_fiumicino={str(y): v for y, v in sorted(lin_fco.items())}, tutti={str(y): v for y, v in roma_tot.items()},
              linate_altre={str(y): v for y, v in lin_altre.items()}),
    linate_mesi={'2018': lin18, '2019': lin19},
    linate_fco_mesi={'%d-%02d' % k: v for k, v in sorted(lin_fco_m.items()) if k[0] in (2018, 2019)},
    mesi_aeroporti={a: {'%d-%02d' % k: v for k, v in sorted(s.items()) if k[0] in (2018, 2019)} for a, s in mesi_ap.items()},
)
json.dump(riep, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for fn in os.listdir(OUT): print(fn, os.path.getsize(os.path.join(OUT, fn)))
