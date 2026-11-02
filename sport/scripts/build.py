"""Sport: unisce le fonti in un elenco di "luoghi" (sedi) dove si fa sport e li assegna ai NIL.
Uso: python -I -X utf8 build.py <ABS sport> <ABS citta-15-minuti>
Scrive pulito/siti.csv, pulito/siti_per_fonte.csv, pulito/build_log.json.
Regole (tutte nel NOTE.md):
 - un "luogo" = punti di fonti diverse piu' vicini di RAGGIO m contati una volta (default 80 m; prova a 50 e 150 m nel log)
 - ordine di priorita' delle fonti: ds34 -> ds2941 -> ds32 -> ds1867 -> ds1640 -> Regione 2016 -> OSM centri/piscine/palestre -> OSM campi
 - gestione: milanosport (concessionario Milanosport nell'elenco ds2941, feb 2025) > comune_concessione (altri concessionari, ds2941) > comune_da_verificare (Milanosport/Comune solo secondo ds34 e ds32, vecchi) > comune_libero (campi dei giardini, ds1640) > scuola > altro (non risulta comunale)
"""
import sys, os, json, glob, re
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.prepared import prep
S, C = sys.argv[1].rstrip('\\/'), sys.argv[2].rstrip('\\/')
RAGGIO = float(sys.argv[3]) if len(sys.argv) > 3 else 80.0
SCRIVI = len(sys.argv) <= 3
tr = Transformer.from_crs(4326, 32632, always_xy=True)
LOG = {}
def norm(s): return re.sub(r'\s+', ' ', str(s or '').strip().upper())
STOP = {'VIA', 'VIALE', 'VLE', 'V', 'PLE', 'PIAZZA', 'PZA', 'PIAZZALE', 'P', 'LE', 'LARGO', 'L', 'CORSO', 'C', 'SO', 'DI', 'DEL', 'DELLA', 'DE', 'DEI', 'DEGLI', 'D', 'SNC', 'SN', 'FR', 'GIOVANNI', 'S', 'ST'}
def addrkey(a):
    t = re.sub(r"[^A-Z0-9 ]", ' ', norm(a).replace("'", ''))
    toks = t.split()
    nums = [w for w in toks if w[0].isdigit()]
    words = {w for w in toks if not w[0].isdigit() and w not in STOP and len(w) > 1}
    return (nums[0] if nums else None), words
def addr_match(k1, k2):
    if k1[0] is None or k2[0] is None or k1[0] != k2[0] or not k1[1] or not k2[1]: return False
    return k1[1] <= k2[1] or k2[1] <= k1[1]
RANK = {'milanosport': 6, 'comune_concessione': 5, 'comune_da_verificare': 4, 'comune_libero': 3, 'scuola': 2, 'altro': 1}

# ------------------------------------------------------------- confine e NIL
conf = shape(json.load(open(glob.glob(C + '/raw/comune_milano/confine_comune/*.geojson')[0], encoding='utf-8'))['features'][0]['geometry'])
from shapely.ops import transform
confm = transform(lambda x, y, z=None: tr.transform(x, y), conf)
cbuf = prep(confm.buffer(200))
nilg = json.load(open(C + '/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson', encoding='utf-8'))['features']
nil_poly = [(f['properties']['ID_NIL'], f['properties']['NIL'], prep(transform(lambda x, y, z=None: tr.transform(x, y), shape(f['geometry'])))) for f in nilg]

# ------------------------------------------------------------- tipi
PISC = {'NUOTO', 'PISCINA', 'CENTRO BALNEARE', 'TUFFI', 'PALLANUOTO', 'ATTIVITA SUBACQUEA'}
PAL = {'FITNESS MACCHINE', 'FITNESS', 'PALESTRA', 'BODY BUILDING', 'GINNASTICA', 'GINNASTICA ATTREZZISTICA', 'BOXE', 'SCHERMA', 'DANZA', 'BALLO', 'ATTIVITA CIRCENSE'}
def tipi_da_info(infos):
    s = {norm(i) for i in infos}
    return {'piscina': bool(s & PISC), 'palestra': bool(s & PAL), 'centro': 'CENTRO SPORTIVO' in s or len(s) >= 3,
            'campo': bool(s - PISC - PAL - {'CENTRO SPORTIVO', 'PARCHEGGIO', 'BRIDGE', 'BILIARDO-BOCCETTE', 'BALLO', 'DANZA'})}
def tipi_da_testo(t):
    t = norm(t)
    return {'piscina': bool(re.search(r'NUOT|PISCIN|TUFFI|PALLANUOTO|SUBACQ', t)),
            'palestra': bool(re.search(r'FITNESS|PALESTRA|GINNASTICA|ARTI MARZIALI|MOTORIE|BOXE|DANZA|SCHERMA|YOGA|PESI', t)),
            'campo': bool(re.search(r'CALCIO|TENNIS|PALLACANESTRO|PALLAVOLO|BASKET|BEACH|BOCCE|RUGBY|BASEBALL|ATLETICA|HOCKEY|PALLAMANO|PADEL|BADMINTON|SQUASH|PATTIN|SOFTBALL|FOOTBALL', t)),
            'centro': False}

# ------------------------------------------------------------- record
REC = []   # dict: fonte, nome, indirizzo, lon, lat, tipi, gestione, extra
def add(fonte, nome, ind, lon, lat, tipi, gestione, **kw):
    x, y = tr.transform(lon, lat)
    REC.append(dict(fonte=fonte, nome=nome, indirizzo=ind, lon=lon, lat=lat, x=x, y=y, **{k: bool(tipi.get(k)) for k in ['piscina', 'palestra', 'campo', 'centro']}, gestione=gestione, **kw))

# ds34
d = pd.read_csv(S + '/raw/comune_ds34/ds34_impianti_sportivi_final.csv', sep=';', dtype=str)
d['lon'] = d.LONG_X_4326.astype(float); d['lat'] = d.LAT_Y_4326.astype(float)
d['k'] = d.lon.round(5).astype(str) + '_' + d.lat.round(5).astype(str)
LOG['ds34_righe'] = len(d); LOG['ds34_punti'] = int(d.k.nunique())
ms_rows = d.URL.fillna('').str.contains('milanosport', case=False) | d.Nome.fillna('').str.contains('MILANO SPORT SPA', case=False)
d['ms'] = ms_rows
for k, g in d.groupby('k'):
    nomi = [n for n in g.Nome.dropna() if norm(n) != 'NON ATTRIBUITO']
    nome = pd.Series(nomi).mode().iloc[0] if nomi else 'non attribuito'
    t = tipi_da_info(g['info'].dropna())
    add('ds34', nome.title(), norm(g.Indirizzo.iloc[0]).title(), g.lon.iloc[0], g.lat.iloc[0], t, 'comune_da_verificare' if g.ms.any() else 'altro', info='|'.join(sorted(set(g['info'].dropna()))))
# ds2941 concessioni
c = pd.read_csv(S + '/raw/comune_ds2941/impianti-in-concessione_febb_2025milanosport_.csv', sep=';', dtype=str)
for _, r in c.iterrows():
    t = tipi_da_testo(r['Attività svolta nel centro sportivo'])
    if r['Attività svolta nel centro sportivo'] and norm(r['Attività svolta nel centro sportivo']) == 'AREA PARCHEGGIO': continue
    nome = r['Denominazione Impianto'] if norm(r['Denominazione Impianto']) != 'IMPIANTO SPORTIVO' else r['Denominazione Concessionario']
    add('ds2941', str(nome).title(), norm(r['Indirizzo']).title(), float(r.LONG_X_4326), float(r.LAT_Y_4326), t, 'milanosport' if 'MILANOSPORT' in norm(r['Denominazione Concessionario']).replace(' ', '') else 'comune_concessione', info=str(r['Attività svolta nel centro sportivo']))
LOG['ds2941_righe'] = len(c)
# ds32 piscine / centri balneari (gestione Milanosport: i nomi sono quelli dei complessi Milanosport di ds1491)
f = pd.read_csv(S + '/raw/comune_ds32/centri_balneari_milano__final.csv', sep=';', dtype=str)
ms19 = pd.read_csv(S + '/raw/comune_ds1491/milanosport_2019.csv', sep=';', dtype=str, encoding='utf-8')['Complesso'].tolist()
def in_ms19(den):
    t = re.sub(r"[^A-Z ]", ' ', norm(den).replace("'", ''))
    toks = [w for w in t.split() if len(w) > 3 and w not in ('CENTRO', 'PISCINA', 'CENTRI', 'MT')]
    return any(all(w in re.sub(r"[^A-Z ]", ' ', norm(c_).replace("'", '')) for w in toks[:1]) for c_ in ms19) if toks else False
LOG['ds32_non_in_elenco_ms2019'] = []
for _, r in f.iterrows():
    ok = in_ms19(r.DENOMINAZIONE)
    if not ok: LOG['ds32_non_in_elenco_ms2019'].append(r.DENOMINAZIONE)
    add('ds32', str(r.DENOMINAZIONE).title(), norm(r.INDIRIZZO).title(), float(r.x), float(r.y), {'piscina': True}, 'comune_da_verificare' if ok else 'altro', info=r.TIPOLOGIA)
# ds1867 palestre/piscine scolastiche (statali, a.s. 2020/21)
g = pd.read_csv(S + '/raw/comune_ds1867/ds1867_destinazione_uso_degli_spazi_as2020-2021.csv', sep=';', dtype=str)
g = g[(g.PALESTRA == 'SI') | (g.PISCINA == 'SI')].drop_duplicates('CODICEEDIFICIO')
for _, r in g.iterrows():
    add('ds1867', str(r.DENOMINAZIONESCUOLA).title(), norm(r.INDIRIZZOSCUOLA).title(), float(r.LONG_X_4326), float(r.LAT_Y_4326), {'palestra': r.PALESTRA == 'SI', 'piscina': r.PISCINA == 'SI'}, 'scuola', info='palestra' if r.PALESTRA == 'SI' else 'piscina')
LOG['ds1867_edifici_con_palestra_o_piscina'] = len(g)
# ds1640 campi nei giardini (esclusi piste ciclabili e "altro")
gj = json.load(open(S + '/raw/comune_ds1640/ds1640_impianti_sportivi.geojson', encoding='utf-8'))['features']
n1640 = 0
for ft in gj:
    p = ft['properties']; desc = norm(p['descrizione_codice'])
    if 'PISTA CICLABILE' in desc: continue
    ce = shape(ft['geometry']).centroid; n1640 += 1
    add('ds1640', str(p.get('località') or p.get('localit�') or p['id_area']), '', ce.x, ce.y, {'campo': True}, 'comune_libero', info=desc.replace('IMPIANTI SPORTIVI - ', '').lower())
LOG['ds1640_poligoni_totali'] = len(gj); LOG['ds1640_usati_senza_piste_ciclabili'] = n1640
# Regione Lombardia 2016
rg = pd.read_csv(S + '/raw/regione/qkfs-wmmh_centri_sportivi_lombardia.csv', dtype=str)
rg = rg[rg.comune.str.upper().str.strip() == 'MILANO']
LOG['regione_milano_righe'] = len(rg); LOG['regione_milano_con_coordinate'] = int(rg.lat.notna().sum())
for _, r in rg[rg.lat.notna()].iterrows():
    nome = norm(r.denominazione_centro)
    ges = 'scuola' if re.search(r'SCUOL|ISTITUTO|LICEO', nome) else 'altro'
    add('regione2016', nome.title(), norm(r.indirizzo).title(), float(r.lng), float(r.lat), tipi_da_testo(r.disciplina), ges, info=str(r.disciplina))
# OSM
osm = json.load(open(S + '/raw/osm/overpass_sport_milano.json', encoding='utf-8'))['elements']
def pos(e): return (e['center']['lon'], e['center']['lat']) if 'center' in e else (e['lon'], e['lat'])
PRIV = {'private', 'no', 'customers', 'members', 'permit'}
cnt = {'centri': 0, 'piscine': 0, 'palestre': 0, 'altri': 0}; pitches = []
for e in osm:
    t = e['tags']; lei = t.get('leisure'); lon, lat = pos(e); name = t.get('name', '')
    acc = t.get('access')
    if lei == 'pitch':
        if acc in PRIV: continue
        pitches.append((lon, lat, t.get('sport', ''))); continue
    if lei == 'swimming_pool':
        if acc in PRIV or not name or not re.search(r'piscin|nuoto|pool|acqua|aqua|swim|centro sportivo|club|terme', name, re.I): continue
        add('osm', name, '', lon, lat, {'piscina': True}, 'altro', info='swimming_pool'); cnt['piscine'] += 1
    elif lei in ('sports_centre', 'fitness_centre', 'sports_hall', 'stadium', 'ice_rink', 'track', 'golf_course', 'horse_riding') or t.get('amenity') == 'gym' or t.get('building') == 'sports_hall':
        if acc in {'private', 'no'}: continue
        if lei == 'track' and not name: continue
        sp = t.get('sport', '')
        tp = {'piscina': 'swim' in sp, 'palestra': lei in ('fitness_centre', 'sports_hall') or t.get('amenity') == 'gym' or bool(re.search(r'gymnastics|climbing|martial|boxing|fitness|yoga|dance', sp)),
              'campo': lei in ('stadium', 'ice_rink', 'track', 'golf_course', 'horse_riding') or bool(re.search(r'soccer|tennis|basket|volley|padel|athletics|rugby|baseball|multi|futsal|golf|squash|badminton', sp)),
              'centro': lei == 'sports_centre'}
        if lei == 'sports_centre' and not any(tp.values()): tp['campo'] = True
        add('osm', name or '(senza nome)', '', lon, lat, tp, 'altro', info=f"{lei}:{sp}"); cnt['centri'] += 1
LOG['osm_elementi_totali'] = len(osm); LOG['osm_aggiunti_centri_piscine_palestre'] = cnt; LOG['osm_pitch_pubblicabili_non_privati'] = len(pitches)
# cluster dei pitch OSM (30 m, componenti connesse) -> 1 punto per cluster
pxy = np.array([tr.transform(a, b) for a, b, _ in pitches]); tree = cKDTree(pxy)
lab = -np.ones(len(pxy), int); ncl = 0
for i in range(len(pxy)):
    if lab[i] >= 0: continue
    st = [i]; lab[i] = ncl
    while st:
        j = st.pop()
        for k2 in tree.query_ball_point(pxy[j], 30):
            if lab[k2] < 0: lab[k2] = ncl; st.append(k2)
    ncl += 1
LOG['osm_pitch_cluster_30m'] = ncl
for cl in range(ncl):
    idx = np.where(lab == cl)[0]; m = pxy[idx].mean(axis=0); lo, la = Transformer.from_crs(32632, 4326, always_xy=True).transform(*m)
    sp = pd.Series([pitches[i][2] for i in idx]).replace('', np.nan).dropna()
    add('osm_campi', '(campi OSM)', '', lo, la, {'campo': True}, 'altro', info=(sp.mode().iloc[0] if len(sp) else 'campo') + f' x{len(idx)}')

R = pd.DataFrame(REC)
R['x'] = R.x.astype(float); R['y'] = R.y.astype(float)
# dentro il Comune (+200 m)
okc = np.array([cbuf.contains(Point(a, b)) for a, b in zip(R.x, R.y)])
LOG['fuori_confine_scartati_per_fonte'] = R[~okc].fonte.value_counts().to_dict()
R = R[okc].reset_index(drop=True)
LOG['record_per_fonte_dentro'] = R.fonte.value_counts().to_dict()

# ------------------------------------------------------------- unione in luoghi
ORD = ['ds34', 'ds2941', 'ds32', 'ds1867', 'ds1640', 'regione2016', 'osm', 'osm_campi']
EXPL = {'ds34', 'ds2941', 'ds32'}   # fonti che possono cambiare la gestione di un luogo gia' esistente
sites = []   # liste di dict
skeys = []
sx = []; stree = None
def rebuild():
    global stree
    stree = cKDTree(np.array(sx)) if sx else None
for fonte in ORD:
    sub = R[R.fonte == fonte]
    for _, r in sub.iterrows():
        j = -1
        if sx:
            # ricerca lineare vettoriale (poche migliaia di luoghi)
            dd = np.hypot(np.array(sx)[:, 0] - r.x, np.array(sx)[:, 1] - r.y)
            jm = int(dd.argmin())
            if dd[jm] <= RAGGIO: j = jm
            elif r.indirizzo and fonte not in ('osm', 'osm_campi', 'ds1640'):
                rk = addrkey(r.indirizzo)
                for jj in np.where(dd <= 350)[0]:
                    if addr_match(rk, skeys[jj]): j = int(jj); break
        if j < 0:
            sites.append(dict(nome=r.nome, indirizzo=r.indirizzo, lon=r.lon, lat=r.lat, x=r.x, y=r.y, piscina=r.piscina, palestra=r.palestra, campo=r.campo, centro=r.centro,
                              gestione=r.gestione, fonti={fonte}, info=[f"{fonte}:{r['info']}"], nomi_alt=[]))
            sx.append((r.x, r.y)); skeys.append(addrkey(r.indirizzo))
        else:
            s_ = sites[j]
            for k in ['piscina', 'palestra', 'campo', 'centro']: s_[k] = bool(s_[k] or r[k])
            if skeys[j][0] is None and r.indirizzo: skeys[j] = addrkey(r.indirizzo)
            s_['fonti'].add(fonte); s_['info'].append(f"{fonte}:{r['info']}")
            if fonte in EXPL and RANK[r.gestione] > RANK[s_['gestione']]: s_['gestione'] = r.gestione
            elif fonte == 'regione2016' and s_['gestione'] == 'altro' and r.gestione == 'scuola': s_['gestione'] = 'scuola'
            elif fonte in ('ds1867',) and s_['gestione'] == 'altro': s_['gestione'] = 'scuola'
            if r.nome not in (s_['nome'],) and len(s_['nomi_alt']) < 4: s_['nomi_alt'].append(r.nome)
P = pd.DataFrame(sites)
P['livello'] = P.fonti.map(lambda f: 'impianto' if set(f) & {'ds34', 'ds2941', 'ds32', 'ds1867', 'regione2016', 'osm'} else 'campo_libero')
P['n_fonti'] = P.fonti.map(len); P['fonti'] = P.fonti.map(lambda s: '|'.join(sorted(s))); P['info'] = P['info'].map(lambda l: ' ; '.join(l)[:400]); P['nomi_alt'] = P.nomi_alt.map(' | '.join)
# NIL
def nil_of(x, y):
    p = Point(x, y)
    for i, n, pg in nil_poly:
        if pg.contains(p): return i, n
    return None, None
nl = [nil_of(a, b) for a, b in zip(P.x, P.y)]
P['ID_NIL'] = [a for a, _ in nl]; P['NIL'] = [b for _, b in nl]
LOG['luoghi_totali'] = len(P); LOG['luoghi_senza_NIL_(tra_confine_e_+200m)'] = int(P.ID_NIL.isna().sum())
P['ID_NIL'] = P.ID_NIL.astype('Int64')
P.insert(0, 'sito_id', ['S%04d' % i for i in range(1, len(P) + 1)])
if SCRIVI:
    os.makedirs(S + '/pulito', exist_ok=True)
    P.drop(columns=['x', 'y']).assign(x=P.x.round(1), y=P.y.round(1)).to_csv(S + '/pulito/siti.csv', index=False, encoding='utf-8')
    R.drop(columns=['info']).to_csv(S + '/pulito/siti_per_fonte.csv', index=False, encoding='utf-8')
    LOG['luoghi_dentro_comune_piu_200m'] = len(P)
    LOG['livello'] = P.livello.value_counts().to_dict()
    LOG['gestione'] = P.gestione.value_counts().to_dict()
    LOG['tipi'] = {k: int(P[k].sum()) for k in ['piscina', 'palestra', 'campo', 'centro']}
    import subprocess
    LOG['sensibilita_raggio'] = {}
    for rr in (50, 150):
        out = subprocess.run([sys.executable, '-W', 'ignore', '-I', '-X', 'utf8', os.path.abspath(__file__), S, C, str(rr)], capture_output=True, text=True).stdout
        m = re.search(r'luoghi: (\d+) impianti: (\d+) campi liberi: (\d+)', out)
        LOG['sensibilita_raggio'][str(rr)] = {'luoghi': int(m.group(1)), 'impianti': int(m.group(2)), 'campi_liberi': int(m.group(3))}
    Q = P[P.ID_NIL.notna()]; LOG['sensibilita_raggio']['80'] = {'luoghi': len(Q), 'impianti': int((Q.livello == 'impianto').sum()), 'campi_liberi': int((Q.livello == 'campo_libero').sum())}
    json.dump(LOG, open(S + '/pulito/build_log.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(LOG, ensure_ascii=False, indent=1, default=str))
else:
    Q = P[P.ID_NIL.notna()]; print(RAGGIO, 'luoghi:', len(Q), 'impianti:', int((Q.livello == 'impianto').sum()), 'campi liberi:', int((Q.livello == 'campo_libero').sum()))
