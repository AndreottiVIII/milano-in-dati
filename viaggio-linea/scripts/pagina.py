"""Costruisce i dati della pagina docs/viaggio-linea/ (viaggio per linea, fermata per fermata).

Per ogni fermata di ogni linea:
  - il NIL in cui cade (punto nel poligono del Comune, ds964; entro 40 m dal bordo se la fermata e' sul confine);
  - la zona OMI in cui cade (perimetri 2026/1 dell'Agenzia delle Entrate, come in prezzi-case/);
  - i valori degli indicatori di quel NIL (e, per il prezzo, di quella zona OMI), letti dai file dei filoni gia' pubblicati.
Il valore e' del NIL o della zona, NON della fermata: tutte le fermate dello stesso NIL hanno lo stesso valore.

Entrate (tutte sotto <milano-in-dati>):
  viaggio-linea/out/linee_gtfs.json                         (01_linee.py: linee e fermate dal GTFS ATM/AMAT)
  citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson   (confini NIL, Comune di Milano, CC BY)
  prezzi-case/raw/geopoi/F205_20261.json                    (zone OMI 2026/1, perimetri)
  docs/prezzi-case/data/zone_ultimo_semestre.csv            (prezzi di compravendita OMI per zona, 2026/1)
  quartieri-che-cambiano/out/indicatori_nil.csv             (reddito 2024, stranieri 2025: portati dai CAP/anagrafe ai NIL)
  docs/eta/data/nil_eta_centenari.csv                       (eta' media 2025)
  docs/alberi/data/nil.csv                                  (alberi ogni 1.000 abitanti, residenti 2024)
  docs/affitti-brevi/data/nil.csv                           (annunci ogni 100 abitazioni, settembre 2026)
  docs/citta-15-minuti/data/nil_punteggi.csv                (punteggio 15 minuti su 10)
  docs/scuole/data/nil_scuole.csv                           (scuole 2024/25 per ordine)
  docs/elezioni/data/nil/comunali_sindaco_2021-10-03.json + docs/elezioni/data/index.json (voti per NIL)
Uscite (docs/viaggio-linea/data/): linee.json, nil_linee.geojson, fermate_indicatori.csv, nil_indicatori.csv,
  salti.csv, riepilogo.json. Intermedi in viaggio-linea/out/.

Uso: python -I -X utf8 pagina.py <milano-in-dati-assoluto>      (rieseguibile: riscrive tutto)
"""
import sys, os, json, re, csv, math
from functools import reduce
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import Polygon, mapping
from shapely.strtree import STRtree
from shapely.validation import make_valid
from pyproj import Transformer

BASE = os.path.abspath(sys.argv[1])
P = lambda *a: os.path.join(BASE, *a)
OUT = P('viaggio-linea', 'out')
DOC = P('docs', 'viaggio-linea', 'data')
os.makedirs(OUT, exist_ok=True)
os.makedirs(DOC, exist_ok=True)

TOL_M = 40          # una fermata sul bordo di un poligono viene assegnata al poligono piu' vicino entro 40 m
SOGLIA_RES = 1000   # sotto questi residenti il NIL e' senza valori di quartiere (eta', stranieri, reddito, servizi)
SOGLIA_RES_PC = 5000  # sotto questi residenti niente valori "per abitante" (alberi, scuole): come nella pagina Alberi
SOGLIA_VOTI = 500   # voti validi minimi per mostrare la quota di voto di un NIL

TR = Transformer.from_crs(4326, 32632, always_xy=True)
TR_INV = Transformer.from_crs(32632, 4326, always_xy=True)


def r1(x, d=1):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), d)


def leggi_csv(path, **kw):
    with open(path, encoding='utf-8-sig') as f:
        riga = f.readline()
    sep = ';' if riga.count(';') > riga.count(',') else ','
    return pd.read_csv(path, sep=sep, **kw)


# ---------------------------------------------------------------- 1. poligoni
def geom_utm(feat):
    """Anelli con OR esclusivo (regola pari/dispari), come in quartieri-che-cambiano/scripts/01_collegamenti.py."""
    ps = []
    g = feat['geometry']
    rings = g['coordinates'] if g['type'] == 'Polygon' else [r for poly in g['coordinates'] for r in poly]
    for ring in rings:
        a = np.array(ring, dtype=float)
        x, y = TR.transform(a[:, 0], a[:, 1])
        ps.append(make_valid(Polygon(np.column_stack([x, y]))))
    return reduce(lambda p, q: p.symmetric_difference(q), ps)


nil_gj = json.load(open(P('citta-15-minuti', 'raw', 'comune_milano', 'nil_vigenti', 'ds964_nil_wm.geojson'), encoding='utf-8'))
nil_geom = {}
for f in nil_gj['features']:
    i = int(f['properties']['ID_NIL'])
    g = geom_utm(f)
    nil_geom[i] = nil_geom[i].union(g) if i in nil_geom else g
omi_gj = json.load(open(P('prezzi-case', 'raw', 'geopoi', 'F205_20261.json'), encoding='utf-8'))
omi_geom = {}
for f in omi_gj['dat']['features']:
    c = f['properties']['zona']
    g = geom_utm(f)
    omi_geom[c] = omi_geom[c].union(g) if c in omi_geom else g


def assegna(x, y, geoms):
    """Ritorna (codice, distanza_m): dentro il poligono distanza 0; altrimenti il piu' vicino entro TOL_M."""
    codici = list(geoms)
    tree = STRtree([geoms[c] for c in codici])
    pt = shapely.points(x, y)
    res = []
    for k, p in enumerate(pt):
        hit = tree.query(p, predicate='within')
        if len(hit):
            res.append((codici[hit[0]], 0.0))
            continue
        j = int(tree.nearest(p))
        d = float(geoms[codici[j]].distance(p))
        res.append((codici[j], d) if d <= TOL_M else (None, d))
    return res


# ---------------------------------------------------------------- 2. tabelle per NIL
nome_nil = leggi_csv(P('docs', 'alberi', 'data', 'nil.csv')).set_index('id_nil')
T = pd.DataFrame(index=sorted(nome_nil.index))
T['nil'] = nome_nil.nil
T['residenti_2024'] = nome_nil.abitanti_2024
qc = leggi_csv(P('quartieri-che-cambiano', 'out', 'indicatori_nil.csv')).set_index('id_nil')
eta = leggi_csv(P('docs', 'eta', 'data', 'nil_eta_centenari.csv')).set_index('id_nil')
T['residenti_2025'] = eta.residenti_2025
ok1 = T.residenti_2025 >= SOGLIA_RES
T['reddito'] = qc.reddito_2024.where(ok1)
T['eta'] = eta.eta_media_2025.where(ok1)
T['stranieri'] = qc.stranieri_2025.where(ok1)
T['alberi'] = nome_nil.alberi_per_1000_abitanti_2025.where(nome_nil.in_classifica_almeno_5000_abitanti == 1)
ab = leggi_csv(P('docs', 'affitti-brevi', 'data', 'nil.csv')).set_index('nil')
T['airbnb'] = ab.annunci_per_100_abitazioni.where(~ab.piccolo_denominatore.astype(bool))
pu = leggi_csv(P('docs', 'citta-15-minuti', 'data', 'nil_punteggi.csv')).set_index('ID_NIL')
T['servizi'] = pu.punteggio_su_10.where(pu.stato == 'in classifica')
sc = leggi_csv(P('docs', 'scuole', 'data', 'nil_scuole.csv')).set_index('id_nil')
n_sc = sc.s24_0 + sc.s24_1 + sc.s24_2
T['n_scuole'] = n_sc
T['scuole'] = (n_sc / T.residenti_2024 * 10000).where(T.residenti_2024 >= SOGLIA_RES_PC)

# voto: sindaco 2021, famiglie dal file indice delle elezioni
EL = 'comunali_sindaco_2021-10-03'
idx = json.load(open(P('docs', 'elezioni', 'data', 'index.json'), encoding='utf-8'))
el = [e for e in idx['elezioni'] if e['id'] == EL][0]
fam = el['fam']
par = el['par']
vot = json.load(open(P('docs', 'elezioni', 'data', 'nil', EL + '.json'), encoding='utf-8'))['p']
sx, dx = [], []
tot_v = []
for i in T.index:
    d = vot.get(str(i))
    if not d:
        sx.append(np.nan); dx.append(np.nan); tot_v.append(0); continue
    v = d['v']
    per = {f: 0 for f in fam}
    for (nome, k), n in zip(par, v):
        per[fam[k]] += n
    tot = sum(v)
    tot_v.append(tot)
    if tot < SOGLIA_VOTI:
        sx.append(np.nan); dx.append(np.nan)
    else:
        sx.append(100 * per['Centrosinistra'] / tot)
        dx.append(100 * per['Centrodestra'] / tot)
T['voti_validi_2021'] = tot_v
T['voto_sx'] = sx
T['voto_dx'] = dx

# totali della citta' (stessa elezione): dall'indice delle elezioni
cv = el['city']
per_citta = {f: 0 for f in fam}
for (nome, k), n in zip(par, cv['v']):
    per_citta[fam[k]] += n
VOTO = dict(elezione=EL, data=el['data'], affluenza_pct=round(100 * cv['vt'] / cv['e'], 1), voti_candidati=int(sum(cv['v'])),
            centrosinistra_pct=round(100 * per_citta['Centrosinistra'] / sum(cv['v']), 1), centrodestra_pct=round(100 * per_citta['Centrodestra'] / sum(cv['v']), 1),
            sinistra_pct=round(100 * per_citta['Sinistra'] / sum(cv['v']), 1), altri_pct=round(100 * per_citta['Altri'] / sum(cv['v']), 1),
            candidati=[n for n, k in par],
            nota='quota sul totale dei voti ai candidati sindaco; centrosinistra = famiglia Centrosinistra (Sala), centrodestra = famiglia Centrodestra (Bernardo)')

zo = leggi_csv(P('docs', 'prezzi-case', 'data', 'zone_ultimo_semestre.csv')).set_index('zona')

# ---------------------------------------------------------------- 3. indicatori (metadati)
IND = [
    dict(id='reddito', et='Reddito', lungo='Reddito medio per contribuente', unita='€', dec=0, liv='NIL', anno="anno d'imposta 2024 (euro 2025)",
         fonte='Ministero dell\'Economia, redditi per CAP, portati ai quartieri con i civici', pagina='../redditi/', pagina_et='Redditi'),
    dict(id='prezzo', et='Prezzo casa', lungo='Prezzo medio di una casa (OMI)', unita='€/m²', dec=0, liv='OMI', anno='1° semestre 2026',
         fonte='Agenzia delle Entrate, Osservatorio del Mercato Immobiliare (zone OMI)', pagina='../prezzi-case/', pagina_et='Prezzi delle case'),
    dict(id='eta', et='Età media', lungo='Età media dei residenti', unita='anni', dec=1, liv='NIL', anno='31/12/2025',
         fonte='Comune di Milano, anagrafe (ds27)', pagina='../eta/', pagina_et='Età'),
    dict(id='stranieri', et='Stranieri', lungo='Residenti stranieri', unita='%', dec=1, liv='NIL', anno='31/12/2025',
         fonte='Comune di Milano, anagrafe (ds27)', pagina='../comunita/', pagina_et='Comunità'),
    dict(id='alberi', et='Alberi', lungo='Alberi del Comune ogni 1.000 abitanti', unita='alberi', dec=0, liv='NIL', anno='31/3/2025',
         fonte='Comune di Milano, censimento alberi (ds2484)', pagina='../alberi/', pagina_et='Alberi'),
    dict(id='airbnb', et='Airbnb', lungo='Annunci Airbnb ogni 100 abitazioni', unita='annunci', dec=1, liv='NIL', anno='settembre 2026',
         fonte='Inside Airbnb (annunci, snapshot 19/9/2026) e ISTAT, censimento 2023 (abitazioni)', pagina='../affitti-brevi/', pagina_et='Affitti brevi'),
    dict(id='servizi', et='Servizi a 15 minuti', lungo='Punteggio «città dei 15 minuti» (su 10)', unita='su 10', dec=1, liv='NIL', anno='2025',
         fonte='Comune di Milano e OpenStreetMap, calcolo di questo sito', pagina='../citta-15-minuti/', pagina_et='La città dei 15 minuti'),
    dict(id='scuole', et='Scuole', lungo='Scuole (infanzia, primaria, media) ogni 10.000 residenti', unita='scuole', dec=1, liv='NIL', anno='a.s. 2024/25',
         fonte='Comune di Milano e Ministero dell\'Istruzione', pagina='../scuole/', pagina_et='Scuole'),
    dict(id='voto_sx', et='Voto centrosinistra', lungo='Voto al candidato del centrosinistra (sindaco 2021)', unita='%', dec=1, liv='NIL', anno='3 ottobre 2021',
         fonte='Comune di Milano, risultati per sezione, portati ai quartieri con i civici', pagina='../elezioni/', pagina_et='Elezioni'),
    dict(id='voto_dx', et='Voto centrodestra', lungo='Voto al candidato del centrodestra (sindaco 2021)', unita='%', dec=1, liv='NIL', anno='3 ottobre 2021',
         fonte='Comune di Milano, risultati per sezione, portati ai quartieri con i civici', pagina='../elezioni/', pagina_et='Elezioni'),
]
IDS = [d['id'] for d in IND]

# riferimento della citta' e classi di colore: distribuzione dei valori validi dei NIL (o delle zone OMI)
for d in IND:
    if d['id'] == 'prezzo':
        vals = zo.compr_centro.dropna().values.astype(float)
        d['n_unita'] = int(len(vals))
    else:
        vals = T[d['id']].dropna().values.astype(float)
        d['n_unita'] = int(len(vals))
    d['mediana'] = r1(np.median(vals), 2)
    d['min'] = r1(vals.min(), 2)
    d['max'] = r1(vals.max(), 2)
    d['sd'] = float(np.std(vals))
    d['soglie'] = [r1(np.quantile(vals, q), 2) for q in (0.2, 0.4, 0.6, 0.8)]


# ---------------------------------------------------------------- 4. linee
def bello(nome, tipo):
    """Nome leggibile della fermata: dal nome GTFS in minuscolo. Sigle e abbreviazioni sciolte solo quando sono sicure."""
    t = nome.lower().strip()
    sp = {'rho fieramilano': 'Rho Fiera Milano', 'lotto fieramilanocity': 'Lotto Fiera Milano City', 'qt8': 'QT8',
          'villa s.g.': 'Villa San Giovanni', 'sesto 1 maggio fs': 'Sesto 1° Maggio FS', 'cadorna fn m1': 'Cadorna FN',
          'cadorna fn m2': 'Cadorna FN', 'affori fn': 'Affori FN', 's.agostino': "Sant'Agostino", 's.ambrogio': "Sant'Ambrogio",
          'san ambrogio': "Sant'Ambrogio", 's.sofia m4': 'Santa Sofia', 'ca granda': "Ca' Granda", 'cassina de pecchi': "Cassina de' Pecchi",
          'lodi t.i.b.b.': 'Lodi T.I.B.B.', 'sforza-policlinico': 'Sforza-Policlinico', 'p.ta genova f.s.': 'Porta Genova FS',
          'cernusco sul naviglio': 'Cernusco sul Naviglio', 'p.ta genova m2': 'Porta Genova'}
    if t in sp:
        return sp[t]
    esp = {'v.le': 'viale', 'p.za': 'piazza', 'p.le': 'piazzale', 'l.go': 'largo', 'c.so': 'corso', 'p.ta': 'porta',
           'f.s.': 'FS', 'fs': 'FS', 'fn': 'FN', 'stz': 'stazione', 'm.te': 'monte', 'osp.': 'ospedale'}
    minus = {'di', 'del', 'della', 'delle', 'dei', 'de', 'da', 'e', 'al', 'alla', 'd', 'degli', 'dello', 'in', 'a', 'sul'}
    tipi = {'via', 'viale', 'piazza', 'piazzale', 'largo', 'corso', 'ponte', 'stazione', 'ospedale', 'scuola', 'isola'}
    out = []
    k = 0
    for w in t.split():
        ap = '(' if w.startswith('(') else ''
        ch = ')' if w.endswith(')') else ''
        x = w.strip('()')
        if re.fullmatch(r'm[1-5]', x):
            if ch and out:
                out[-1] += ')'  # la sigla della linea cade, la parentesi che la chiudeva resta
            continue  # sigle delle linee del metro: nel nome non servono
        x = esp.get(x, x)
        m = re.fullmatch(r's\.(\w+)', x)
        if m:
            x = 'san ' + m.group(1)
        if x in ('FS', 'FN'):
            y = x
        elif x in minus and k > 0:
            y = x
        elif x in tipi and k > 0:
            y = x
        else:
            y = re.sub(r'(^|[.\-])([a-zàèéìòù])', lambda mm: mm.group(1) + mm.group(2).upper(), x)
            y = re.sub(r'\.(?=[A-Z])', '. ', y)
            if re.fullmatch(r'[ivx]+', x):
                y = x.upper()
        out.append(ap + y + ch)
        k += 1
    s = ' '.join(out)
    return s[0].upper() + s[1:] if s else nome


def it(x, d=0):
    if x is None:
        return '–'
    s = f'{abs(x):,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('−' if x < 0 else '') + s


def fmt(ind, v):
    d = {i['id']: i for i in IND}[ind]
    if v is None:
        return '–'
    s = it(v, d['dec'])
    u = d['unita']
    return s + ('%' if u == '%' else (' €' if u == '€' else (' €/m²' if u == '€/m²' else '')))


linee_gtfs = json.load(open(os.path.join(OUT, 'linee_gtfs.json'), encoding='utf-8'))
nil_titolo = {int(i): r.nil for i, r in T.iterrows()}
tutte = []
tocc = set()
for L in linee_gtfs['linee']:
    xs, ys = TR.transform([f['lon'] for f in L['fermate']], [f['lat'] for f in L['fermate']])
    an = assegna(xs, ys, nil_geom)
    ao = assegna(xs, ys, omi_geom)
    fer = []
    for k, f in enumerate(L['fermate']):
        nid, dn = an[k]
        oz, do_ = ao[k]
        v = {}
        for d in IND:
            if d['id'] == 'prezzo':
                v['prezzo'] = r1(zo.loc[oz, 'compr_centro'], 0) if oz in zo.index else None
            else:
                x = T.loc[nid, d['id']] if nid in T.index else np.nan
                v[d['id']] = None if (nid is None or pd.isna(x)) else r1(x, 2)
        if nid is not None:
            tocc.add(nid)
        fer.append({'n': bello(f['nome'], L['tipo']), 'gtfs': f['nome'], 'stop_id': f['stop_id'], 'lat': round(f['lat'], 5), 'lon': round(f['lon'], 5),
                    'nil_id': nid, 'nil': nil_titolo.get(nid) if nid is not None else None, 'nil_dist_m': round(dn, 1),
                    'omi': oz, 'omi_nome': (zo.loc[oz, 'nome'] if oz in zo.index else None),
                    'res': (int(T.loc[nid, 'residenti_2025']) if nid is not None and not pd.isna(T.loc[nid, 'residenti_2025']) else None), 'v': v})
    tutte.append(dict(id=L['id'], nome=L['nome'], tipo=L['tipo'], colore=L['colore'], nota=L['nota'], trip_id=L['trip_id'],
                      shape=L['shape'], fermate=fer))
    print(L['id'], len(fer), 'fermate; fuori NIL:', sum(1 for f in fer if f['nil_id'] is None), '; fuori OMI:', sum(1 for f in fer if f['omi'] is None),
          '; sul bordo (>0 m):', sum(1 for f in fer if f['nil_id'] is not None and f['nil_dist_m'] > 0))

IDX = {d['id']: d for d in IND}


# ---------------------------------------------------------------- 5. gruppi di fermate consecutive nello stesso NIL
def gruppi(fer):
    g = []
    for k, f in enumerate(fer):
        chiave = f['nil_id']
        if g and g[-1]['nil_id'] == chiave:
            g[-1]['a'] = k
        else:
            g.append({'nil_id': chiave, 'nil': f['nil'] or 'fuori Milano', 'da': k, 'a': k})
    return g


# ---------------------------------------------------------------- 6. salti tra fermate consecutive
PERC = {d['id']: (zo.compr_centro.dropna().values.astype(float) if d['id'] == 'prezzo' else T[d['id']].dropna().values.astype(float)) for d in IND}
salti = []
for L in tutte:
    fer = L['fermate']
    for k in range(len(fer) - 1):
        a, b = fer[k], fer[k + 1]
        if (a['res'] or 0) < SOGLIA_RES_PC or (b['res'] or 0) < SOGLIA_RES_PC:
            continue  # niente salti con quartieri piccoli (parchi, cascine): i valori per abitante non sono stabili
        for d in IND:
            i = d['id']
            va, vb = a['v'][i], b['v'][i]
            if va is None or vb is None:
                continue
            unit_a = a['omi'] if i == 'prezzo' else a['nil_id']
            unit_b = b['omi'] if i == 'prezzo' else b['nil_id']
            if unit_a == unit_b:
                continue
            z = abs(vb - va) / d['sd']
            pa = float(np.mean(PERC[i] <= va))
            pb = float(np.mean(PERC[i] <= vb))
            salti.append(dict(linea=L['id'], linea_nome=L['nome'], ind=i, da=k, a=k + 1, da_n=a['n'], a_n=b['n'],
                              da_unita=(a['omi'] if i == 'prezzo' else a['nil']), a_unita=(b['omi'] if i == 'prezzo' else b['nil']),
                              v_da=va, v_a=vb, sd_citta=round(z, 2), perc=round(abs(pb - pa), 3),
                              chiave=tuple(sorted([str(unit_a), str(unit_b)])),
                              rapporto=round(max(va, vb) / min(va, vb), 2) if min(va, vb) > 0 else None))
sal = pd.DataFrame(salti)
# ordine: differenza di posizione nella classifica dei quartieri (0 = stessa, 1 = dal piu' basso al piu' alto), poi scarti standard
sal = sal.sort_values(['perc', 'sd_citta'], ascending=False)


ART = {'reddito': ('il reddito medio', False), 'prezzo': ('il prezzo delle case', False), 'eta': ("l'età media", False),
       'stranieri': ('la quota di stranieri', False), 'alberi': ('gli alberi per abitante', True), 'airbnb': ('gli annunci Airbnb', True),
       'servizi': ('il punteggio dei servizi a 15 minuti', False), 'scuole': ('le scuole per abitante', True),
       'voto_sx': ('il voto al centrosinistra', False), 'voto_dx': ('il voto al centrodestra', False)}


def articolo_ind(i):
    return ART[i][0]


def passa(i):
    return 'passano' if ART[i][1] else 'passa'


def testo_salto(s):
    return (f"Tra {s['da_n']} e {s['a_n']} ({s['linea_nome']}) {articolo_ind(s['ind'])} {passa(s['ind'])} da {fmt(s['ind'], s['v_da'])} a {fmt(s['ind'], s['v_a'])} "
            f"({'zona' if s['ind'] == 'prezzo' else 'quartiere'} {s['da_unita']} → {s['a_unita']}).")


# il salto piu' grande per ogni indicatore (in unita' di deviazione standard della citta') e i primi in assoluto
top_ind = []
for d in IND:
    s = sal[sal.ind == d['id']]
    if len(s):
        top_ind.append(s.iloc[0])
# primi in assoluto: un solo salto per coppia di fermate (nome) e per indicatore
visti = set()
# nei titoli niente scuole e alberi (rapporti per abitante instabili); restano nella tabella completa
top_abs = sorted([s for s in top_ind if s['ind'] not in ('scuole', 'alberi')], key=lambda s: -s['perc'])[:4]


def pack(s, extra=None):
    o = dict(linea=s['linea'], linea_nome=s['linea_nome'], ind=s['ind'], da=int(s['da']), a=int(s['a']), da_n=s['da_n'], a_n=s['a_n'],
             da_unita=s['da_unita'], a_unita=s['a_unita'], v_da=s['v_da'], v_a=s['v_a'], sd=float(s['sd_citta']), perc=float(s['perc']), rapporto=(None if pd.isna(s['rapporto']) else float(s['rapporto'])),
             testo=testo_salto(s))
    return o


# ---------------------------------------------------------------- 7. testi automatici per linea
def frase_tratto(fer, i):
    """Frase su un indicatore lungo la linea: dal punto piu' basso a quello piu' alto, nel verso di marcia."""
    d = IDX[i]
    pts = [(k, f['v'][i]) for k, f in enumerate(fer) if f['v'][i] is not None and (f['res'] or 0) >= SOGLIA_RES_PC]
    if len(pts) < 3:
        return None
    lo = min(pts, key=lambda t: t[1])
    hi = max(pts, key=lambda t: t[1])
    if lo[1] == hi[1] or lo[1] <= 0:
        return None
    r = hi[1] / lo[1]
    a, b = (lo, hi) if lo[0] < hi[0] else (hi, lo)
    sale = a[1] < b[1]
    nm = articolo_ind(i)
    pl = ART[i][1]
    na, nb = fer[a[0]]['n'], fer[b[0]]['n']
    if d['unita'] in ('%', 'anni', 'su 10'):
        um = 'punti' if d['unita'] == '%' else d['unita']
        verbo = ('sale' if sale else 'scende') if not pl else ('salgono' if sale else 'scendono')
        t = f"Tra {na} e {nb} {nm} {verbo} da {fmt(i, a[1])} a {fmt(i, b[1])}: {it(abs(hi[1] - lo[1]), d['dec'])} {um} di differenza."
    elif 1.9 <= r <= 2.1:
        if sale:
            t = f"Tra {na} e {nb} {nm} {'raddoppiano' if pl else 'raddoppia'}, da {fmt(i, a[1])} a {fmt(i, b[1])}."
        else:
            t = f"Tra {na} e {nb} {nm} {'si dimezzano' if pl else 'si dimezza'}, da {fmt(i, a[1])} a {fmt(i, b[1])}."
    else:
        verbo = ('sale' if sale else 'scende') if not pl else ('salgono' if sale else 'scendono')
        t = f"Tra {na} e {nb} {nm} {verbo} da {fmt(i, a[1])} a {fmt(i, b[1])}: il valore più alto è {it(r, 1)} volte il più basso."
    return dict(ind=i, a=a[0], b=b[0], rapporto=round(r, 2), testo=t)


def pack_rev(o, n):
    """Lo stesso salto letto nel verso opposto della linea."""
    o = dict(o)
    o['da'], o['a'] = n - 1 - o['a'], n - 1 - o['da']
    o['da_n'], o['a_n'] = o['a_n'], o['da_n']
    o['da_unita'], o['a_unita'] = o['a_unita'], o['da_unita']
    o['v_da'], o['v_a'] = o['v_a'], o['v_da']
    return o


def plur(n, uno, molti):
    return uno if n == 1 else molti


def analisi(L, rev):
    fer = L['fermate'][::-1] if rev else L['fermate']
    n = len(fer)
    dentro = [f for f in fer if f['nil_id'] is not None]
    nil_distinti = []
    for f in dentro:
        if f['nil_id'] not in nil_distinti:
            nil_distinti.append(f['nil_id'])
    n_fuori = n - len(dentro)
    n_omi = len({f['omi'] for f in fer if f['omi']})
    tratti = {i: frase_tratto(fer, i) for i in IDS}
    sl = sal[sal.linea == L['id']]
    salto = None
    if len(sl):
        salto = pack(sl.iloc[0])
        if rev:
            salto = pack_rev(salto, n)
            salto['testo'] = testo_salto(dict(linea_nome=salto['linea_nome'], ind=salto['ind'], da_n=salto['da_n'], a_n=salto['a_n'],
                                              v_da=salto['v_da'], v_a=salto['v_a'], da_unita=salto['da_unita'], a_unita=salto['a_unita']))
    t = [f"{n} fermate, {len(nil_distinti)} {plur(len(nil_distinti), 'quartiere attraversato', 'quartieri attraversati')} "
         f"e {n_omi} {plur(n_omi, 'zona dei prezzi', 'zone dei prezzi')}."]
    if n_fuori:
        t.append(f"{n_fuori} {plur(n_fuori, 'fermata è fuori dal Comune di Milano e resta senza valori', 'fermate sono fuori dal Comune di Milano e restano senza valori')}.")
    for i in ('reddito', 'prezzo', 'stranieri'):
        if tratti[i]:
            t.append(tratti[i]['testo'])
    if salto:
        t.append('Il salto più brusco tra due fermate vicine: ' + salto['testo'][0].lower() + salto['testo'][1:])
    return dict(gruppi=gruppi(fer), tratti=tratti, salto=salto, testo=t,
                n_fermate=n, n_fuori=n_fuori, n_nil=len(nil_distinti), n_omi=n_omi)


for L in tutte:
    L['d'] = [analisi(L, False), analisi(L, True)]
    L['n_fermate'] = L['d'][0]['n_fermate']
    L['n_fuori'] = L['d'][0]['n_fuori']
    L['n_nil'] = L['d'][0]['n_nil']
    L['n_omi'] = L['d'][0]['n_omi']

# ---------------------------------------------------------------- 8. file di uscita
# poligoni dei NIL toccati dalle linee (semplificati a ~15 m, per la mappa)
feats = []
for i in sorted(tocc):
    g = nil_geom[i].simplify(15, preserve_topology=True)
    g = shapely.transform(g, lambda c: np.column_stack(TR_INV.transform(c[:, 0], c[:, 1])))
    m = mapping(g)

    def arr(c):
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            return [round(c[0], 5), round(c[1], 5)]
        return [arr(x) for x in c]
    m = {'type': m['type'], 'coordinates': arr(m['coordinates'])}
    feats.append({'type': 'Feature', 'properties': {'i': i, 'n': nil_titolo[i]}, 'geometry': m})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(DOC, 'nil_linee.geojson'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

out = dict(generato=pd.Timestamp.now().strftime('%Y-%m-%d'), gtfs=linee_gtfs['gtfs'], voto=VOTO,
           indicatori=[{k: v for k, v in d.items() if k != 'sd'} for d in IND],
           salti_per_indicatore=[pack(s) for s in top_ind], salti_primi=[pack(s) for s in top_abs],
           linee=[{k: v for k, v in L.items()} for L in tutte])
json.dump(out, open(os.path.join(DOC, 'linee.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), allow_nan=False)

# CSV scaricabili
rows = []
for L in tutte:
    for k, f in enumerate(L['fermate']):
        r = dict(linea=L['nome'], posizione=k + 1, fermata=f['n'], nome_gtfs=f['gtfs'], stop_id=f['stop_id'], lat=f['lat'], lon=f['lon'],
                 id_nil=f['nil_id'], nil=f['nil'], residenti_nil_2025=f['res'], distanza_dal_nil_m=f['nil_dist_m'], zona_omi=f['omi'], zona_omi_nome=f['omi_nome'])
        for i in IDS:
            r[i] = f['v'][i]
        rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(DOC, 'fermate_indicatori.csv'), index=False, sep=';', encoding='utf-8-sig')
TT = T.copy()
TT.index.name = 'id_nil'
TT.round(2).to_csv(os.path.join(DOC, 'nil_indicatori.csv'), sep=';', encoding='utf-8-sig')
sal.head(300).to_csv(os.path.join(DOC, 'salti.csv'), index=False, sep=';', encoding='utf-8-sig')
# anche in out/ per il controllo
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'fermate_indicatori.csv'), index=False, sep=';', encoding='utf-8-sig')

riep = dict(generato=out['generato'], gtfs=linee_gtfs['gtfs'], voto=VOTO, n_linee=len(tutte), n_fermate=int(sum(L['n_fermate'] for L in tutte)),
            nil_toccati=len(tocc), soglie=dict(residenti_valori_di_quartiere=SOGLIA_RES, residenti_per_abitante=SOGLIA_RES_PC, voti_validi_minimi=SOGLIA_VOTI, tolleranza_bordo_m=TOL_M),
            indicatori={d['id']: dict(etichetta=d['lungo'], unita=d['unita'], livello=d['liv'], anno=d['anno'], fonte=d['fonte'], n_unita=d['n_unita'],
                                      mediana_citta=d['mediana'], min=d['min'], max=d['max'], soglie_colore=d['soglie']) for d in IND},
            linee={L['id']: dict(nome=L['nome'], fermate=L['n_fermate'], fuori_milano=L['n_fuori'], quartieri=L['n_nil'], zone_omi=L['n_omi'], trip_id=L['trip_id']) for L in tutte},
            salti_per_indicatore=[pack(s) for s in top_ind])
json.dump(riep, open(os.path.join(DOC, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
tot = sum(os.path.getsize(os.path.join(DOC, f)) for f in os.listdir(DOC))
print('dati pagina:', tot // 1024, 'KB')
for s in top_abs:
    print(testo_salto(s), 'perc', s['perc'])
for L in tutte:
    print(chr(10).join(L['d'][0]['testo']))
    print('  [ritorno] ' + L['d'][1]['testo'][2 if len(L['d'][1]['testo']) > 2 else 0])
