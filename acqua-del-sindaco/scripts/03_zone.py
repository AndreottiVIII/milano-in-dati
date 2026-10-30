"""Passo 3 - zone MM e tavola degli indirizzi.
Uso: python -I 03_zone.py <cartella_strand> <cartella_civici_comune>
  - legge raw/ds1827*/civici_zone_mm_no_dupl.csv (civico -> zona MM)
  - legge (SOLO LETTURA) il file civici del Comune in citta-15-minuti/raw/comune_milano/civici/estratto
  - legge (SOLO LETTURA) il confine comunale in citta-15-minuti/raw/comune_milano/confine_comune
Scrive in pulito/: civici_zone.csv, indirizzi_zona.csv, strade_zona.csv, nil_zone.csv,
                   zone_celle.csv, zone_approx.geojson, zone_riepilogo.csv, _controlli/zone_*.csv
"""
import sys, os, re, glob, json, unicodedata
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import box, shape, mapping, Polygon
from shapely.ops import unary_union, transform as shp_transform

BASE = sys.argv[1]
COMUNE = sys.argv[2]            # .../citta-15-minuti/raw/comune_milano
OUT = os.path.join(BASE, 'pulito')
CTL = os.path.join(OUT, '_controlli')
os.makedirs(CTL, exist_ok=True)
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


ZONE = {'milano nord ovest': ('NO', 'Nord-Ovest', 6), 'milano nord est': ('NE', 'Nord-Est', 18),
        'milano sud est': ('SE', 'Sud-Est', 16), 'milano sud ovest': ('SO', 'Sud-Ovest', 15)}


def senza_accenti(s):
    s = unicodedata.normalize('NFD', s)
    return ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')


def chiave_testo(s):
    s = senza_accenti(s).lower()
    s = re.sub(r"[^a-z0-9 ]", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


# ---------------------------------------------------------------- lettura
c = pd.read_csv(glob.glob(os.path.join(BASE, 'raw', 'ds1827*', 'civici_zone_mm_no_dupl.csv'))[0], sep=';', dtype=str, keep_default_na=False)
d = pd.read_csv(glob.glob(os.path.join(COMUNE, 'civici', 'estratto', '*.csv'))[0], sep=';', dtype=str, keep_default_na=False)
log('ds1827 civici->zona:', len(c), '| civici Comune (ds634):', len(d))

d = d.rename(columns={'LONG_WGS84': 'lon_d', 'LAT_WGS84': 'lat_d'})
dsel = d[['IDMASTER', 'lon_d', 'lat_d', 'NUMERO', 'LETTERA', 'BARRA', 'BARRA2', 'STATOCIVICO', 'RESIDENZIALE', 'TIPO', 'DESCRITTIVO',
          'DENOMINAZIONE', 'OPENSTREETMAP', 'MUNICIPIO', 'ID_NIL', 'NIL', 'NUMEROCOMPLETO']].copy()

m = c.merge(dsel, on='IDMASTER', how='left', suffixes=('', '_d'))
in634 = m['lon_d'].notna() & (m['lon_d'] != '')
log('civici di ds1827 trovati nel file del Comune (stesso IDMASTER):', int(in634.sum()), 'non trovati:', int((~in634).sum()))
m['lon'] = np.where(in634, m['lon_d'], m['LONG_WGS84']).astype(float)
m['lat'] = np.where(in634, m['lat_d'], m['LAT_WGS84']).astype(float)
m['coordinate_fonte'] = np.where(in634, 'ds634 (Comune, ott 2026)', 'ds1827')
m['zona_key'] = m['ZONA_MM'].str.lower().str.strip()
etichettato = m['zona_key'].isin(ZONE)
log('civici con zona valida in ds1827:', int(etichettato.sum()), '| zona vuota:', int((~etichettato).sum()))

# civici del Comune che NON sono in ds1827
nuovi = d[~d['IDMASTER'].isin(c['IDMASTER'])].copy()
nuovi['lon'] = nuovi['lon_d'].astype(float)
nuovi['lat'] = nuovi['lat_d'].astype(float)
log('civici del Comune senza zona in ds1827 (nuovi o non ancora attivi):', len(nuovi), nuovi.STATOCIVICO.value_counts().to_dict())

# ---------------------------------------------------------------- proiezione metrica
to_m = Transformer.from_crs(4326, 32632, always_xy=True)
to_ll = Transformer.from_crs(32632, 4326, always_xy=True)
m['x'], m['y'] = to_m.transform(m.lon.values, m.lat.values)
nuovi['x'], nuovi['y'] = to_m.transform(nuovi.lon.values, nuovi.lat.values)

lab = m[etichettato].reset_index(drop=True)
cod = lab['zona_key'].map(lambda z: ZONE[z][0]).values
codici = ['NE', 'NO', 'SE', 'SO']
cod_i = np.array([codici.index(z) for z in cod])
tree = cKDTree(np.c_[lab.x.values, lab.y.values])

# ---------------------------------------------------------------- coerenza: leave-one-out kNN
K = 7
dist, idx = tree.query(np.c_[lab.x.values, lab.y.values], k=K + 1)
vot = np.zeros((len(lab), 4))
for j in range(1, K + 1):
    np.add.at(vot, (np.arange(len(lab)), cod_i[idx[:, j]]), 1)
pred = vot.argmax(1)
acc = (pred == cod_i).mean()
log('coerenza spaziale (leave-one-out, %d vicini piu prossimi): %.2f%% dei civici ha la stessa zona della maggioranza dei vicini' % (K, 100 * acc))
lab['coerente'] = (pred == cod_i)
lab['dist_vicino_m'] = dist[:, 1]
# civici con zona diversa dal vicino piu prossimo
diff1 = (cod_i[idx[:, 1]] != cod_i).mean()
log('quota civici con zona diversa dal vicino piu vicino: %.2f%%' % (100 * diff1))
# per distanza dal vicino piu vicino (civici isolati)
lab[~lab.coerente][['IDMASTER', 'TIPO', 'DESCRITTIVO', 'NUMEROCOMPLETO', 'ZONA_MM', 'MUNICIPIO', 'NIL', 'lon', 'lat']].to_csv(
    os.path.join(CTL, 'zone_civici_incoerenti_con_i_vicini.csv'), sep=';', index=False)

# ---------------------------------------------------------------- zona stimata per i civici senza etichetta
senza = pd.concat([m[~etichettato].assign(origine='ds1827_zona_vuota'), nuovi.assign(origine='solo_file_Comune')], ignore_index=True, sort=False)
if len(senza):
    dd, ii = tree.query(np.c_[senza.x.values, senza.y.values], k=K)
    v2 = np.zeros((len(senza), 4))
    w = 1.0 / (dd + 10.0)
    for j in range(K):
        np.add.at(v2, (np.arange(len(senza)), cod_i[ii[:, j]]), w[:, j])
    share = v2.max(1) / v2.sum(1)
    senza['zona_codice'] = [codici[k] for k in v2.argmax(1)]
    senza['confidenza'] = share.round(2)
    senza['dist_vicino_m'] = dd[:, 0].round(0)
    log('zona stimata per', len(senza), 'civici; confidenza >= 0.9 per', int((share >= 0.9).sum()), '; < 0.7 per', int((share < 0.7).sum()),
        '; vicino piu prossimo oltre 200 m per', int((dd[:, 0] > 200).sum()))

# ---------------------------------------------------------------- tavola civici -> zona
inv = {v[0]: v for v in ZONE.values()}


lab_out = lab.copy()
lab_out['zona_codice'] = cod
lab_out['fonte_zona'] = 'ds1827 (MM, ufficiale)'
lab_out['confidenza'] = 1.0
se_out = senza.copy()
se_out['fonte_zona'] = 'stimata dai vicini (' + senza['origine'] + ')'
tutto = pd.concat([lab_out, se_out], ignore_index=True, sort=False)
tutto['zona_nome'] = tutto.zona_codice.map(lambda z: inv[z][1])
tutto['zona_id'] = tutto.zona_codice.map(lambda z: inv[z][2])
tutto['zona_mm_originale'] = tutto.get('ZONA_MM')
tutto['numero_base'] = tutto['NUMERO'].where(tutto['NUMERO'].notna() & (tutto['NUMERO'] != ''), tutto['NUMEROCOMPLETO'].str.extract(r'^(\d+)')[0])
tutto['lettera'] = tutto['LETTERA'].fillna('')
tutto['barra'] = tutto['BARRA'].fillna('') + tutto['BARRA2'].fillna('').map(lambda s: ('/' + s) if s else '')
tutto['chiave_via'] = (tutto['TIPO'].fillna('') + ' ' + tutto['DESCRITTIVO'].fillna('')).map(chiave_testo)
STOP = {'di', 'del', 'della', 'dei', 'delle', 'degli', 'dello', 'da', 'de', 'dal', 'dalla', 'd', 'l', 'la', 'le', 'il', 'lo', 'i', 'gli', 'al', 'alla', 'ai', 'e'}


def token_via(tipo, via):
    t = [w for w in chiave_testo(via).split() if w not in STOP]
    return chiave_testo(tipo) + ' ' + ' '.join(sorted(set(t)))


tutto['chiave_via_token'] = [token_via(a, b) for a, b in zip(tutto['TIPO'].fillna(''), tutto['DESCRITTIVO'].fillna(''))]
tutto['chiave_civico'] = tutto['numero_base'].fillna('').astype(str) + tutto['lettera'].str.lower()
res = tutto.rename(columns={'IDMASTER': 'idmaster', 'TIPO': 'tipo_via', 'DESCRITTIVO': 'via', 'NUMEROCOMPLETO': 'civico_completo',
                            'MUNICIPIO': 'municipio', 'ID_NIL': 'id_nil', 'NIL': 'nil', 'DENOMINAZIONE': 'denominazione_via',
                            'STATOCIVICO': 'stato_civico'})
# se mancano tipo/via/nil perche' vengono da ds1827 non trovato nel Comune, prendi quelli di ds1827 (gia' nelle colonne originali)
cols = ['idmaster', 'tipo_via', 'via', 'civico_completo', 'numero_base', 'lettera', 'barra', 'chiave_via', 'chiave_via_token', 'chiave_civico',
        'zona_codice', 'zona_nome', 'zona_id', 'fonte_zona', 'confidenza', 'municipio', 'id_nil', 'nil', 'lon', 'lat', 'coordinate_fonte',
        'stato_civico', 'zona_mm_originale']
res['coordinate_fonte'] = res['coordinate_fonte'].fillna('ds634 (Comune, ott 2026)')
res['stato_civico'] = res['stato_civico'].fillna('')
res = res[cols]
res['lon'] = res.lon.round(6)
res['lat'] = res.lat.round(6)
res.to_csv(os.path.join(OUT, 'civici_zone.csv'), sep=';', index=False, encoding='utf-8')
log('civici_zone.csv', res.shape, res.fonte_zona.value_counts().to_dict())
log(res.zona_nome.value_counts().to_dict())
log('civici senza numero_base:', int((res.numero_base.isna() | (res.numero_base == '')).sum()))

# --- indirizzi_zona.csv: un record per (via, numero base + lettera), zona = maggioranza dei civici (barre incluse)
res['zc'] = res.zona_codice
g = res.groupby(['tipo_via', 'via', 'chiave_via', 'chiave_via_token', 'chiave_civico', 'municipio']).agg(
    n_civici=('idmaster', 'size'), zone_distinte=('zc', 'nunique'),
    zona_codice=('zc', lambda s: s.value_counts().index[0]),
    quota_zona=('zc', lambda s: s.value_counts().iloc[0] / len(s)),
    nil=('nil', 'first'),
    lon=('lon', 'mean'), lat=('lat', 'mean'),
    da_ds1827=('fonte_zona', lambda s: int(s.str.startswith('ds1827').any()))).reset_index()
g['zona_nome'] = g.zona_codice.map(lambda z: inv[z][1])
g['lon'] = g.lon.round(6)
g['lat'] = g.lat.round(6)
g['quota_zona'] = g.quota_zona.round(2)
amb = g.groupby(['chiave_via', 'chiave_civico']).size()
log('indirizzi (via+civico) presenti in piu municipi, quindi ambigui senza municipio/CAP:', int((amb > 1).sum()), 'su', len(amb))
g.to_csv(os.path.join(OUT, 'indirizzi_zona.csv'), sep=';', index=False, encoding='utf-8')
log('indirizzi_zona.csv (via + numero base/lettera):', g.shape, '| indirizzi con civici in piu zone:', int((g.zone_distinte > 1).sum()))

# --- strade_zona.csv: quote per zona di ogni via
s = res.groupby(['tipo_via', 'via', 'chiave_via']).agg(n_civici=('idmaster', 'size'), zone_distinte=('zc', 'nunique')).reset_index()
pz = res.pivot_table(index=['tipo_via', 'via', 'chiave_via'], columns='zc', values='idmaster', aggfunc='size', fill_value=0).reset_index()
s = s.merge(pz, on=['tipo_via', 'via', 'chiave_via'])
for z in codici:
    if z not in s.columns:
        s[z] = 0
s.to_csv(os.path.join(OUT, 'strade_zona.csv'), sep=';', index=False, encoding='utf-8')
log('strade_zona.csv:', s.shape, '| vie in piu zone:', int((s.zone_distinte > 1).sum()), 'su', len(s))
dupv = res.groupby('chiave_via').agg(t=('tipo_via', 'nunique'), v=('via', 'nunique'), mun=('municipio', 'nunique'))
log('chiave_via con piu denominazioni diverse:', int((dupv.v > 1).sum()), '| vie omonime in piu municipi:', int((dupv.mun > 1).sum()))

# --- NIL x zona
nz = res[res.nil.notna() & (res.nil != '')].pivot_table(index=['id_nil', 'nil'], columns='zc', values='idmaster', aggfunc='size', fill_value=0).reset_index()
for z in codici:
    if z not in nz.columns:
        nz[z] = 0
nz['totale'] = nz[codici].sum(1)
nz['zona_prevalente'] = nz[codici].idxmax(1)
nz['quota_prevalente'] = (nz[codici].max(1) / nz.totale).round(3)
nz.to_csv(os.path.join(OUT, 'nil_zone.csv'), sep=';', index=False, encoding='utf-8')
log('NIL con una sola zona:', int((nz.quota_prevalente == 1).sum()), 'su', len(nz), '| NIL con prevalente < 90%:', int((nz.quota_prevalente < 0.9).sum()))
log(nz[nz.quota_prevalente < 0.9][['id_nil', 'nil'] + codici + ['quota_prevalente']].to_string())
mz = res.pivot_table(index='municipio', columns='zc', values='idmaster', aggfunc='size', fill_value=0)
log('Municipio x zona (civici):\n' + mz.to_string())

# ---------------------------------------------------------------- zone approssimate (griglia 100 m)
conf = json.load(open(glob.glob(os.path.join(COMUNE, 'confine_comune', '*.geojson'))[0], encoding='utf-8'))
poly = shape(conf['features'][0]['geometry'])
poly_m = shp_transform(lambda x, y, z=None: to_m.transform(x, y), poly)
minx, miny, maxx, maxy = poly_m.bounds
CELL = 100.0
xs = np.arange(np.floor(minx / CELL) * CELL, maxx + CELL, CELL)
ys = np.arange(np.floor(miny / CELL) * CELL, maxy + CELL, CELL)
gx, gy = np.meshgrid(xs + CELL / 2, ys + CELL / 2)
pts = np.c_[gx.ravel(), gy.ravel()]
from shapely import contains_xy
dentro = contains_xy(poly_m, pts[:, 0], pts[:, 1])
# tengo anche le celle che toccano il confine
from shapely import intersects, box as sbox
cand = np.where(~dentro)[0]
ok = dentro.copy()
for i in cand:
    cx, cy = pts[i]
    if poly_m.intersects(box(cx - CELL / 2, cy - CELL / 2, cx + CELL / 2, cy + CELL / 2)):
        ok[i] = True
P = pts[ok]
KC = 15
dd, ii = tree.query(P, k=KC)
v = np.zeros((len(P), 4))
w = 1.0 / (dd + 25.0)
for j in range(KC):
    np.add.at(v, (np.arange(len(P)), cod_i[ii[:, j]]), w[:, j])
lab_cell = v.argmax(1)
conf_cell = (v.max(1) / v.sum(1))
# filtro di maggioranza 3x3 (una sola passata) per togliere celle isolate
G = -np.ones(gx.shape, dtype=int)
flat = G.ravel()
flat[np.where(ok)[0]] = lab_cell
G = flat.reshape(gx.shape)
G2 = G.copy()
for r in range(1, G.shape[0] - 1):
    for q in range(1, G.shape[1] - 1):
        if G[r, q] < 0:
            continue
        win = G[r - 1:r + 2, q - 1:q + 2].ravel()
        win = win[win >= 0]
        cnt = np.bincount(win, minlength=4)
        k = cnt.argmax()
        if cnt[k] >= 5 and k != G[r, q]:
            G2[r, q] = k
camb = int((G2 != G).sum())
log('celle 100 m dentro il Comune:', len(P), '| celle cambiate dal filtro di maggioranza:', camb)
lab_cell2 = G2.ravel()[np.where(ok)[0]]
cells = pd.DataFrame({'x': P[:, 0], 'y': P[:, 1], 'zona_codice': [codici[k] for k in lab_cell2], 'confidenza': conf_cell.round(2),
                      'dist_civico_m': dd[:, 0].round(0)})
cells['lon'], cells['lat'] = to_ll.transform(cells.x.values, cells.y.values)
cells['lon'] = cells.lon.round(6)
cells['lat'] = cells.lat.round(6)
cells[['lon', 'lat', 'zona_codice', 'confidenza', 'dist_civico_m']].to_csv(os.path.join(OUT, 'zone_celle.csv'), sep=';', index=False)
feats = []
riep = []
for z in codici:
    sel = cells[cells.zona_codice == z]
    boxes = [box(x - CELL / 2, y - CELL / 2, x + CELL / 2, y + CELL / 2) for x, y in zip(sel.x, sel.y)]
    u = unary_union(boxes).intersection(poly_m)
    u = u.buffer(60).buffer(-60).simplify(20).intersection(poly_m)       # leviga i gradini di 100 m
    area = u.area / 1e6
    ug = shp_transform(lambda x, y, zz=None: to_ll.transform(x, y), u)
    zz = inv[z]
    feats.append({'type': 'Feature', 'geometry': mapping(ug),
                  'properties': {'zona_codice': z, 'zona_nome': zz[1], 'zona_id': zz[2], 'area_km2': round(area, 2),
                                 'nota': 'zona APPROSSIMATA da punti civici (ds1827); non e un confine ufficiale'}})
    riep.append(dict(zona_codice=z, zona_nome=zz[1], zona_id=zz[2], civici_ds1827=int((cod == z).sum()), celle_100m=len(sel), area_km2=round(area, 2),
                     quota_area=None))
json.dump({'type': 'FeatureCollection', 'crs': {'type': 'name', 'properties': {'name': 'EPSG:4326'}}, 'features': feats},
          open(os.path.join(OUT, 'zone_approx.geojson'), 'w', encoding='utf-8'), ensure_ascii=False)
riep = pd.DataFrame(riep)
riep['quota_area'] = (riep.area_km2 / riep.area_km2.sum()).round(3)
riep['quota_civici'] = (riep.civici_ds1827 / riep.civici_ds1827.sum()).round(3)
riep.to_csv(os.path.join(OUT, 'zone_riepilogo.csv'), sep=';', index=False)
log(riep.to_string())
log('area comune (km2) dal confine:', round(poly_m.area / 1e6, 1), '| somma aree zone:', round(riep.area_km2.sum(), 1))
# confidenza bassa: celle di confine
log('celle con confidenza < 0.7 (area di confine tra zone):', int((cells.confidenza < 0.7).sum()), 'su', len(cells))
log('celle a oltre 500 m dal civico piu vicino (zone non edificate, zona assegnata per prossimita):', int((cells.dist_civico_m > 500).sum()))
open(os.path.join(OUT, '_log_zone.txt'), 'w', encoding='utf-8').write('\n'.join(LOG))
