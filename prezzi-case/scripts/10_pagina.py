r"""Prepara i dati leggeri per la pagina docs\prezzi-case (filone 12, prezzi delle case).
Entrata (sola lettura): <prezzi-case>\pulito\  (prezzi_zona_semestre_prevalente.csv, prezzi_citta_mediana_zone.csv,
    crescita_zone_2006_2013.csv, crescita_zone_2014_2026.csv, m4_confronto.csv, omi_milano_zone.csv,
    ntn_milano_trimestrale.csv)  e  <prezzi-case>\raw\geopoi\F205_<AAAAS>.json (perimetri dell'ultimo semestre).
Uscite (in <docs>\prezzi-case\data\, solo valori aggregati per zona, nessun dato per singola quotazione di stato):
    riepilogo.json            serie della citta' (abitazioni civili, negozi, eventuali uffici/capannoni), M4, compravendite, numeri della "sorpresa"
    zone.geojson              le zone dell'ultimo semestre con i valori da mostrare sulla mappa
    serie_zone.json           serie di ogni zona dell'ultimo semestre (dal 2014/2, o da quando esiste)
    serie_citta.csv, zone_ultimo_semestre.csv, serie_zone.csv, m4_confronto.csv, compravendite_milano.csv   (scaricabili)
Si puo' rilanciare tale e quale: se in pulito\ ci sono anche uffici (T) e capannoni (P) con abbastanza dati, la sezione
"uffici e capannoni" compare nel riepilogo (il campo "altre"); altrimenti il campo e' vuoto e la pagina non la mostra.
Quotazione di riferimento: Abitazioni civili (cod 20), stato prevalente, centro = (min+max)/2, euro 2025 (FOI senza tabacchi).
Uso: python -I 10_pagina.py <cartella prezzi-case> [cartella di uscita]
"""
import sys, os, json, re, math
from functools import reduce
import numpy as np
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely.validation import make_valid

BASE = sys.argv[1]
PUL = os.path.join(BASE, 'pulito')
GEO = os.path.join(BASE, 'raw', 'geopoi')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(BASE)), 'docs', 'prezzi-case', 'data')
os.makedirs(OUT, exist_ok=True)

SOGLIA_ALTRE_SEMESTRI = 8     # una tipologia (ufficio, capannone...) compare solo se ha almeno 8 semestri...
SOGLIA_ALTRE_ZONE = 10        # ... con almeno 10 zone con valori
SEM_BASE_CRESCITA = '2014-S2'
DATA_SCARICO = '30/10/2026'


def lab(s):            # '2026-S1' -> '2026/1'
    return s[:4] + '/' + s[-1]


def num(x, nd=4):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) or pd.isna(x):
        return None
    return round(float(x), nd)


def rifinisci(t):
    t = t.title().replace('`', "'")
    t = t.replace('Sanbabila', 'San Babila').replace('P.Ta', 'P.ta').replace('P.Le', 'P.le')
    t = t.replace('Universita', 'Universit\u00e0').replace('Xxii', 'XXII')
    t = re.sub(r",(?=\S)", ", ", t)
    t = re.sub(r"\b(Di|Del|Della|Da|Dei|Delle)\b", lambda m: m.group(1).lower(), t)
    return t


def nome_breve(n):
    """Nome corto leggibile: prime due voci, iniziale maiuscola."""
    n = re.sub(r'\s+-\s*$', '', str(n)).strip()
    n = re.sub(r'\s+-(?=\S)', ' - ', n)
    voci = [v.strip(' ,') for v in n.split(',') if v.strip(' ,')]
    return rifinisci(', '.join(voci[:2]))


def nome_pulito(n):
    n = re.sub(r'\s+-\s*$', '', str(n)).strip()
    n = re.sub(r'\s+-(?=\S)', ' - ', n)
    n = re.sub(r'\s+,', ',', n)
    n = re.sub(r',\s*,', ',', n)
    return rifinisci(n)


v = pd.read_csv(os.path.join(PUL, 'prezzi_zona_semestre_prevalente.csv'), dtype={'zona': str, 'link_zona': str})
zz = pd.read_csv(os.path.join(PUL, 'omi_milano_zone.csv'), dtype=str)
semestri = sorted(v.semestre.unique())
ULT = semestri[-1]
PRIMO = semestri[0]
r20 = v[v.cod_tip == 20].copy()
r20 = r20[r20.semestre.isin(semestri)]


# ---------------------------------------------------------------- serie della citta' (mediana NON pesata fra le zone)
def serie_citta(d):
    righe = []
    for s, g in d.groupby('semestre'):
        g = g.dropna(subset=['compr_centro'])
        if len(g) == 0:
            continue
        righe.append({
            's': lab(s), 'sem': s, 'n': int(len(g)),
            'nom': num(g.compr_centro.median(), 1), 'reale': num(g.compr_centro_reale_2025.median(), 1),
            'aff_nom': num(g.loc_centro.median(), 2), 'aff_reale': num(g.loc_centro_reale_2025.median(), 2),
            'resa': num(g.resa_lorda_annua.median(), 4), 'anni': num(g.anni_di_affitto_per_il_prezzo.median(), 2)})
    return righe


S_ABIT = serie_citta(r20)
S_NEG = serie_citta(v[v.cod_tip == 5])
ab = pd.DataFrame(S_ABIT).set_index('sem')

# controllo contro il file della pipeline (stessa mediana)
cm = pd.read_csv(os.path.join(PUL, 'prezzi_citta_mediana_zone.csv'))
cm = cm[cm.cod_tip == 20].set_index('semestre')
diff = (ab.reale - cm.compr_mediana_zone_reale_2025.reindex(ab.index)).abs().max()
assert diff < 0.2, 'la mediana ricalcolata non coincide con prezzi_citta_mediana_zone.csv: %s' % diff

# ---------------------------------------------------------------- uffici, capannoni (solo se ci sono davvero)
altre = []
for (cod, tip, cat), d in v[v.categoria.isin(['terziaria', 'produttiva'])].groupby(['cod_tip', 'tipologia', 'categoria']):
    s = serie_citta(d)
    buoni = [x for x in s if x['n'] >= SOGLIA_ALTRE_ZONE]
    if len(buoni) >= SOGLIA_ALTRE_SEMESTRI:
        altre.append({'cod': int(cod), 'tipologia': tip, 'categoria': cat, 'serie': s})

# ---------------------------------------------------------------- crescita per zona
g14 = pd.read_csv(os.path.join(PUL, 'crescita_zone_2014_2026.csv'), dtype={'k': str, 'zona_fine': str}).set_index('k')
g06 = pd.read_csv(os.path.join(PUL, 'crescita_zone_2006_2013.csv'), dtype={'k': str})


def var_stesse_zone(a, b):
    A = r20[r20.semestre == a].dropna(subset=['id_serie']).drop_duplicates('id_serie').set_index('id_serie')
    B = r20[r20.semestre == b].dropna(subset=['id_serie']).drop_duplicates('id_serie').set_index('id_serie')
    k = A.index.intersection(B.index)
    if len(k) == 0:
        return {'n': 0, 'reale': None, 'nom': None}
    return {'n': int(len(k)),
            'reale': num((B.loc[k].compr_centro_reale_2025 / A.loc[k].compr_centro_reale_2025 - 1).median()),
            'nom': num((B.loc[k].compr_centro / A.loc[k].compr_centro - 1).median())}


def var_mediana(a, b):
    return num(ab.loc[b, 'reale'] / ab.loc[a, 'reale'] - 1), num(ab.loc[b, 'nom'] / ab.loc[a, 'nom'] - 1)


# ---------------------------------------------------------------- zone dell'ultimo semestre
ult = r20[r20.semestre == ULT].dropna(subset=['compr_centro']).copy()
nomi = {z: d for s, z, d in zip(zz.semestre, zz.zona, zz.zona_descr) if s == ULT}
m4c = pd.read_csv(os.path.join(PUL, 'm4_confronto.csv'), dtype={'zona': str})
m4c['g'] = m4c.gruppo.str[0]
m4_per_zona = m4c[m4c.periodo.str.startswith('2')].set_index('zona').g.to_dict()

serie_zone = {}
righe_zone = []
for _, x in ult.sort_values('zona').iterrows():
    sid = x.id_serie
    sd = pd.DataFrame()
    if isinstance(sid, str):
        sd = r20[(r20.id_serie == sid) & (r20.semestre >= SEM_BASE_CRESCITA)].sort_values('semestre')
    serie_zone[x.zona] = {
        's': [lab(s) for s in sd.semestre], 'nom': [num(a, 1) for a in sd.compr_centro],
        'reale': [num(a, 1) for a in sd.compr_centro_reale_2025], 'aff_reale': [num(a, 2) for a in sd.loc_centro_reale_2025]}
    dal = sd.semestre.iloc[0] if len(sd) else ULT
    in_crescita = isinstance(sid, str) and sid in g14.index
    righe_zone.append({
        'zona': x.zona, 'id_serie': sid if isinstance(sid, str) else '', 'nome': nome_pulito(nomi.get(x.zona, '')),
        'nome_breve': nome_breve(nomi.get(x.zona, '')), 'fascia': x.fascia,
        'compr_min': num(x.compr_min, 0), 'compr_max': num(x.compr_max, 0), 'compr_centro': num(x.compr_centro, 0),
        'compr_centro_reale_2025': num(x.compr_centro_reale_2025, 0),
        'loc_min': num(x.loc_min, 2), 'loc_max': num(x.loc_max, 2), 'loc_centro': num(x.loc_centro, 2),
        'resa_lorda_annua': num(x.resa_lorda_annua, 4), 'anni_di_affitto': num(x.anni_di_affitto_per_il_prezzo, 1),
        'var_reale_2014_2_ultimo': num(g14.loc[sid, 'var_reale']) if in_crescita else None,
        'var_nominale_2014_2_ultimo': num(g14.loc[sid, 'var_nominale']) if in_crescita else None,
        'var_affitto_reale_2014_2_ultimo': num(g14.loc[sid, 'var_affitto_reale']) if in_crescita else None,
        'serie_dal': lab(dal), 'n_semestri_serie': int(len(sd)), 'gruppo_metro': m4_per_zona.get(x.zona, '')})
Z = pd.DataFrame(righe_zone)

# ---------------------------------------------------------------- perimetri (regola pari/dispari sugli anelli)
def pezzi(g):
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, MultiPolygon):
        return list(g.geoms)
    if hasattr(g, 'geoms'):
        return [p for h in g.geoms for p in pezzi(h)]
    return []


def arrotonda(c):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], 5), round(c[1], 5)]
    return [arrotonda(i) for i in c]


gpath = os.path.join(GEO, 'F205_%s.json' % ULT.replace('-S', ''))
dg = json.load(open(gpath, encoding='utf-8'))
geom = {}
for f in dg['dat']['features']:
    cod = f['properties']['zona']
    anelli = [make_valid(Polygon(r)) for r in f['geometry']['coordinates']]
    g = reduce(lambda p, q: p.symmetric_difference(q), anelli)
    geom[cod] = geom[cod].union(g) if cod in geom else g
feats = []
for _, z in Z.iterrows():
    g = geom.get(z.zona)
    if g is None:
        print('ATTENZIONE: nessun perimetro per la zona', z.zona)
        continue
    g = g.simplify(0.00004, preserve_topology=True)
    ps = [p for p in pezzi(g) if p.area > 0]
    gm = mapping(MultiPolygon(ps) if len(ps) > 1 else ps[0])
    gm = {'type': gm['type'], 'coordinates': arrotonda(gm['coordinates'])}
    pr = {k: (None if (isinstance(val, float) and math.isnan(val)) else val) for k, val in z.items()}
    feats.append({'type': 'Feature', 'properties': pr, 'geometry': gm})
senza = [z for z in geom if z not in set(Z.zona)]
if senza:
    print('Nota: perimetri senza quotazioni (non mostrati):', senza)
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(OUT, 'zone.geojson'), 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))
json.dump(serie_zone, open(os.path.join(OUT, 'serie_zone.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------------------------------------------------------------- M4
ETI = {'A': 'Zone con fermata M4', 'B': 'Zone con un’altra metro (aperta prima del 2022)', 'C': 'Zone senza metro'}
m4 = {'etichette': ETI, 'periodi': []}
for per, d in m4c.groupby('periodo'):
    gr = {}
    for g_, dd in d.groupby('g'):
        gr[g_] = {'n': int(len(dd)), 'var_reale': num(dd.var_reale.median()), 'var_affitto': num(dd.var_affitto.median()),
                  'fasce': {fg: {'n': int(len(x)), 'var_reale': num(x.var_reale.median())} for fg, x in dd.groupby('fascia_gr')}}
    m4['periodi'].append({'periodo': per, 'gruppi': gr})
m4['zone_M4'] = sorted(m4c[(m4c.g == 'A') & m4c.periodo.str.startswith('2')].zona.tolist())

# ---------------------------------------------------------------- compravendite (NTN)
nt = pd.read_csv(os.path.join(PUL, 'ntn_milano_trimestrale.csv'))
prio = {'definitiva_2011_2024': 0, 'provvisoria_2025_2026': 1, 'archivio_2004_2016': 2}
nt['p'] = nt.serie.map(prio)
nt = nt.sort_values(['anno', 'trimestre', 'p']).drop_duplicates(['anno', 'trimestre'])
ntn = [[int(a), int(t), num(n, 1), s] for a, t, n, s in zip(nt.anno, nt.trimestre, nt.ntn_capoluogo, nt.serie)]
cnt = nt.groupby('anno').trimestre.count()
annui = {int(a): num(g.ntn_capoluogo.sum(), 0) for a, g in nt.groupby('anno') if cnt[a] == 4}
nt[['anno', 'trimestre', 'ntn_capoluogo', 'serie']].rename(columns={'serie': 'serie_usata'}).to_csv(
    os.path.join(OUT, 'compravendite_milano.csv'), index=False)

# ---------------------------------------------------------------- numeri della "sorpresa" (tutti dai dati)
r06 = float(ab.loc[PRIMO, 'reale'])
sotto = [s for s in ab.index if ab.loc[s, 'reale'] < r06 and s > '2013-S2']
s_sotto = sotto[-1] if sotto else None
r_ult = float(ab.loc[ULT, 'reale'])
r_sotto = float(ab.loc[s_sotto, 'reale']) if s_sotto else None
b12 = Z[Z.zona == 'B12']
ordine = g14.sort_values('var_reale', ascending=False)
top = [{'zona': row.zona_fine, 'nome': nome_breve(row.nome_fine), 'var': num(row.var_reale)} for _, row in ordine.head(3).iterrows()]
j14 = var_mediana('2014-S1', '2014-S2')
j24 = var_mediana('2024-S1', '2024-S2')
sorpresa = {
    'primo': lab(PRIMO), 'ultimo': lab(ULT), 'sem_sotto': lab(s_sotto) if s_sotto else None,
    'reale_primo': num(r06, 0), 'reale_sotto': num(r_sotto, 0) if r_sotto else None, 'reale_ultimo': num(r_ult, 0),
    'var_sotto_ultimo': num(r_ult / r_sotto - 1) if r_sotto else None,
    'var_primo_ultimo': num(r_ult / r06 - 1),
    'nom_primo': num(ab.loc[PRIMO, 'nom'], 0), 'nom_ultimo': num(ab.loc[ULT, 'nom'], 0),
    'var_nom_primo_ultimo': num(ab.loc[ULT, 'nom'] / ab.loc[PRIMO, 'nom'] - 1),
    'mediana_var_2006_2013': num(g06.var_reale.median()), 'n_zone_2006_2013': int(len(g06)),
    'mediana_var_2014_ultimo': num(g14.var_reale.median()), 'n_zone_2014_ultimo': int(len(g14)),
    'stesse_zone_2014_2_2021_2': var_stesse_zone('2014-S2', '2021-S2'),
    'centro': {'zona': 'B12', 'nome': nome_breve(b12.nome.iloc[0]) if len(b12) else '', 'var': num(g14.loc['S075', 'var_reale']) if 'S075' in g14.index else None},
    'top': top,
    'salto_2014': {'mediana_reale': j14[0], 'mediana_nom': j14[1], 'stesse_zone': var_stesse_zone('2014-S1', '2014-S2')},
    'salto_2024': {'mediana_reale': j24[0], 'mediana_nom': j24[1], 'stesse_zone': var_stesse_zone('2024-S1', '2024-S2')},
    'base_crescita': lab(SEM_BASE_CRESCITA),
}
# la zona del centro: cerco il codice nei dati della crescita invece di scriverlo a mano
cz = g14[g14.zona_fine == 'B12']
if len(cz):
    sorpresa['centro']['var'] = num(cz.var_reale.iloc[0])

# zone per periodo (per segnare i cambi sul grafico)
nz = ab.n.to_dict()
cambi = []
prev = None
for s in ab.index:
    if prev is not None and nz[s] != nz[prev]:
        cambi.append({'sem': lab(s), 'da': int(nz[prev]), 'a': int(nz[s])})
    prev = s

riep = {
    'meta': {'data_scarico': DATA_SCARICO, 'primo': lab(PRIMO), 'ultimo': lab(ULT), 'n_semestri': int(len(ab)),
             'n_zone_ultimo': int(len(Z)), 'n_zone_confrontabili': int(len(g14)), 'cambi_zone': cambi,
             'base_crescita': lab(SEM_BASE_CRESCITA)},
    'abitazioni': S_ABIT, 'negozi': S_NEG, 'altre': altre, 'm4': m4, 'ntn': ntn, 'ntn_annui': annui, 'sorpresa': sorpresa}
json.dump(riep, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------------------------------------------------------------- CSV scaricabili
righe = []
for nome, s in [('Abitazioni civili', S_ABIT), ('Negozi', S_NEG)] + [(a['tipologia'], a['serie']) for a in altre]:
    for x in s:
        righe.append({'tipologia': nome, 'semestre': x['sem'], 'n_zone': x['n'], 'prezzo_mediano_nominale_eur_m2': x['nom'],
                      'prezzo_mediano_euro2025_m2': x['reale'], 'affitto_mediano_nominale_eur_m2_mese': x['aff_nom'],
                      'affitto_mediano_euro2025_m2_mese': x['aff_reale'], 'resa_lorda_annua_mediana': x['resa'],
                      'anni_di_affitto_per_il_prezzo_mediani': x['anni']})
pd.DataFrame(righe).to_csv(os.path.join(OUT, 'serie_citta.csv'), index=False)
Z.drop(columns=['nome_breve']).to_csv(os.path.join(OUT, 'zone_ultimo_semestre.csv'), index=False)
sz = []
for cod, d in serie_zone.items():
    for i, s in enumerate(d['s']):
        sz.append({'zona_ultimo_semestre': cod, 'semestre': s, 'prezzo_nominale_eur_m2': d['nom'][i],
                   'prezzo_euro2025_m2': d['reale'][i], 'affitto_euro2025_m2_mese': d['aff_reale'][i]})
pd.DataFrame(sz).to_csv(os.path.join(OUT, 'serie_zone.csv'), index=False)
m4c.drop(columns=['g']).to_csv(os.path.join(OUT, 'm4_confronto.csv'), index=False)

print('Scritto in', OUT)
print('Semestri %d (%s - %s); zone %s: %d; confrontabili %d; altre tipologie mostrate: %s' % (
    len(ab), lab(PRIMO), lab(ULT), lab(ULT), len(Z), len(g14), [a['tipologia'] for a in altre] or 'nessuna'))
print(json.dumps(sorpresa, ensure_ascii=False, indent=1))
