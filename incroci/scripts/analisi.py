"""Passo 3: aggancia gli incidenti agli incroci e alle vie, calcola classifiche, tendenze, zone 30, Area C.
Uso: python -I -X utf8 analisi.py <ABS cartella incroci>
Legge: pulito/incidenti_geo.csv.gz, pulito/incroci_osm.csv, pulito/nodi_incrocio_osm.csv.gz, pulito/ref_vie_km_filone7.csv,
       raw/comune_milano/*.csv|geojson, raw/lombardia/y7qm_milano.json
Scrive: pulito/*.csv e pulito/riepilogo.json"""
import sys, json, collections, re
import numpy as np, pandas as pd
import shapely
from shapely import STRtree
from scipy.spatial import cKDTree
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as sh_transform
S = sys.argv[1]
ANNI = list(range(2010, 2025))
df = pd.read_csv(S + '/pulito/incidenti_geo.csv.gz', keep_default_na=False)
df['via1_k'] = df.via1_k.astype(str); df['via2_k'] = df.via2_k.astype(str)
T = Transformer.from_crs(4326, 32632, always_xy=True)
BUONI = ['civico', 'civico_approx', 'incrocio', 'incrocio_approx']
df['buono'] = df.livello.isin(BUONI)
lon = pd.to_numeric(df.lon, errors='coerce').fillna(0).values; lat = pd.to_numeric(df.lat, errors='coerce').fillna(0).values
x, y = T.transform(lon, lat)
df['x'] = x; df['y'] = y
R = {}   # riepilogo

# ------------------------------------------------------------ 1. serie annuali e categorie
g = df.groupby('anno')
ser = pd.DataFrame({'incidenti': g.size(), 'feriti': g.feriti.sum(), 'morti': g.morti.sum(), 'ped_inc': g.ped.sum(), 'ped_feriti': g.ped_feriti.sum(), 'ped_morti': g.ped_morti.sum(),
                    'bici_inc': g.bici.sum(), 'moto_inc': g.moto.sum(), 'monop_inc': g.monop.sum(), 'auto_inc': g.auto.sum(),
                    'bici_morti': df[df.bici == 1].groupby('anno').morti.sum(), 'moto_morti': df[df.moto == 1].groupby('anno').morti.sum(),
                    'auto_morti': df[df.auto == 1].groupby('anno').morti.sum(),
                    'posizionati': df[df.buono].groupby('anno').size()}).fillna(0).astype(int).reset_index()
ser.to_csv(S + '/pulito/serie_annuale.csv', index=False)
R['serie'] = {c: ser[c].tolist() for c in ser.columns}
tot = {c: int(df[c].sum()) for c in ('feriti', 'morti', 'ped_feriti', 'ped_morti', 'ped', 'bici', 'moto', 'monop', 'auto')}; tot['righe'] = len(df); tot['posizionati'] = int(df.buono.sum())
R['totali'] = tot

# mesi
mm = df.groupby(['anno', 'mese']).size().unstack(fill_value=0)
R['mesi'] = {'media_2010_19': [round(float(mm.loc[2010:2019, m].mean()), 1) for m in range(1, 13)],
             'anno_2019': [int(mm.loc[2019, m]) for m in range(1, 13)], 'anno_2020': [int(mm.loc[2020, m]) for m in range(1, 13)],
             'anno_2021': [int(mm.loc[2021, m]) for m in range(1, 13)], 'anno_2024': [int(mm.loc[2024, m]) for m in range(1, 13)]}
c175 = pd.read_csv(S + '/raw/comune_milano/ds175_incidenti_mese.csv', sep=';')
c175['IncidentiMortali'] = c175.IncidentiMortali.fillna(0)     # celle vuote = nessun incidente mortale nel mese
c175['inc'] = c175.IncidentiMortali + c175.IncidentiSoliFeriti
ca = c175.groupby('Anno').agg(inc=('inc', 'sum'), morti=('Morti', 'sum'), feriti=('Feriti', 'sum')).reset_index()
R['comune_annuale'] = {'anno': ca.Anno.tolist(), 'inc': ca.inc.tolist(), 'morti': ca.morti.tolist(), 'feriti': ca.feriti.tolist()}
cm = c175[c175.Anno.isin([2019, 2020, 2021])].pivot(index='Mese', columns='Anno', values='inc')
R['comune_mesi_covid'] = {str(a): cm[a].tolist() for a in cm.columns}
R['comune_2025'] = {'inc': int(ca[ca.Anno == 2025].inc.iloc[0]), 'morti': int(ca[ca.Anno == 2025].morti.iloc[0]), 'feriti': int(ca[ca.Anno == 2025].feriti.iloc[0]),
                    'mesi': int(len(c175[c175.Anno == 2025]))}

# ------------------------------------------------------------ 2. quando: Lombardia 2000-2011 (comune, senza luogo)
yq = json.load(open(S + '/raw/lombardia/y7qm_milano.json', encoding='utf-8'))
Q = []
for r in sorted(yq, key=lambda r: r['anno_incidente']):
    n = float(r['tot_inc'])
    Q.append({'anno': int(r['anno_incidente']), 'inc': int(n), 'punta_7_9': int(r['ore_di_punta_07_09_inc']), 'punta_17_19': int(r['ore_di_punta_17_19_inc']),
              'notte': int(r['notte_inc']), 'giorno': int(r['giorno_inc']), 'weekend': int(r['weekend_inc']), 'feriali': int(r['feriali_inc']),
              'ped_infortunati': int(r['pedoni_infortunati']), 'ped_morti': int(r['pedoni_morti']), 'morti': int(r['tot_morti']),
              'morti_punta_17_19': int(r['ore_di_punta_17_19_morti']), 'morti_punta_7_9': int(r['ore_di_punta_07_09_morti']), 'morti_notte': int(r['notte_morti']), 'morti_weekend': int(r['weekend_morti']),
              'intersezione': int(r['intersezione_inc']), 'non_intersezione': int(r['non_intersezione_inc'])})
Q = pd.DataFrame(Q); Q.to_csv(S + '/pulito/quando_lombardia_2000_2011.csv', index=False)
q2 = Q[Q.anno.between(2007, 2011)]
R['quando'] = {'anni': Q.anno.tolist(), 'punta_17_19_pct': [round(100 * a / b, 1) for a, b in zip(Q.punta_17_19, Q.inc)], 'punta_7_9_pct': [round(100 * a / b, 1) for a, b in zip(Q.punta_7_9, Q.inc)],
               'notte_pct': [round(100 * a / b, 1) for a, b in zip(Q.notte, Q.inc)], 'weekend_pct': [round(100 * a / b, 1) for a, b in zip(Q.weekend, Q.inc)],
               'intersezione_pct': [round(100 * a / b, 1) for a, b in zip(Q.intersezione, Q.inc)],
               'sintesi_2007_2011': {'inc': int(q2.inc.sum()), 'punta_17_19': int(q2.punta_17_19.sum()), 'punta_7_9': int(q2.punta_7_9.sum()), 'notte': int(q2.notte.sum()), 'weekend': int(q2.weekend.sum()),
                                     'feriali': int(q2.feriali.sum()), 'morti': int(q2.morti.sum()), 'morti_notte': int(q2.morti_notte.sum()), 'morti_weekend': int(q2.morti_weekend.sum()),
                                     'morti_punta_17_19': int(q2.morti_punta_17_19.sum()), 'morti_punta_7_9': int(q2.morti_punta_7_9.sum())}}

# ------------------------------------------------------------ 3. incroci OSM e aggancio
inc = pd.read_csv(S + '/pulito/incroci_osm.csv'); nod = pd.read_csv(S + '/pulito/nodi_incrocio_osm.csv.gz')
nx_, ny_ = T.transform(nod.lon.values, nod.lat.values)
tree = cKDTree(np.c_[nx_, ny_]); cid = nod.incrocio.values
d, j = tree.query(np.c_[df.x.values, df.y.values])
df['dist'] = d; df['inc'] = cid[j]
dich = df.interse.between(1, 6)                         # la polizia ha scritto "intersezione"
lvl_inc = df.livello.isin(['incrocio', 'incrocio_approx'])
valido = (df.via1_k != df.via2_k) & (df.via2_k != '') & (df.via1_k != '') & (df.via2_k != 'None') & (df.via1_k != 'None')
snap_inc = lvl_inc & valido & (df.dist <= 60)
snap_civ = df.livello.isin(['civico', 'civico_approx']) & dich & (df.dist <= 40)
df['agganciato'] = snap_inc | snap_civ
df.loc[~df.agganciato, 'inc'] = -1
R['aggancio'] = {'incrocio_scritto': int(lvl_inc.sum()), 'agganciati_da_incrocio': int(snap_inc.sum()), 'scartati_stessa_via_o_senza_via': int((lvl_inc & ~valido).sum()),
                 'scartati_lontani': int((lvl_inc & valido & (df.dist > 60)).sum()), 'civico_dichiarato_incrocio': int((df.livello.isin(['civico', 'civico_approx']) & dich).sum()),
                 'agganciati_da_civico': int(snap_civ.sum()), 'totale_agganciati': int(df.agganciato.sum()), 'multi_tra_agganciati': int(df[df.agganciato].multi.sum()),
                 'distanza_mediana_m': round(float(df[snap_inc].dist.median()), 1), 'distanza_p90_m': round(float(df[snap_inc].dist.quantile(.9)), 1)}
A = df[df.agganciato].copy()
def etichetta(grp):
    c = collections.Counter()
    for a, b in zip(grp.via1, grp.via2):
        if a and b and a != b: c[tuple(sorted([a, b]))] += 1
    if not c: return ''
    (a, b), _ = c.most_common(1)[0]
    return a + ' / ' + b
lab = {i: etichetta(gp) for i, gp in A[A.livello.isin(['incrocio', 'incrocio_approx'])].groupby('inc')}
per = {'p1': (2010, 2014), 'p2': (2015, 2019), 'p3': (2020, 2024)}
def agg(gp):
    r = {'inc': len(gp), 'feriti': int(gp.feriti.sum()), 'morti': int(gp.morti.sum()), 'ped': int(gp.ped.sum()), 'ped_feriti': int(gp.ped_feriti.sum()), 'ped_morti': int(gp.ped_morti.sum()),
         'bici': int(gp.bici.sum()), 'moto': int(gp.moto.sum()), 'auto': int(gp.auto.sum()), 'monop': int(gp.monop.sum()),
         'bici_morti': int(gp[gp.bici == 1].morti.sum()), 'moto_morti': int(gp[gp.moto == 1].morti.sum()), 'semaforo': int((gp.interse == 4).sum()), 'rotatoria': int((gp.interse == 2).sum())}
    for k, (a, b) in per.items(): r[k] = int(gp.anno.between(a, b).sum())
    r['y'] = [int((gp.anno == a).sum()) for a in ANNI]
    r['ped_p3'] = int(((gp.ped == 1) & gp.anno.between(2020, 2024)).sum()); r['bici_p3'] = int(((gp.bici == 1) & gp.anno.between(2020, 2024)).sum())
    return r
rows = []
for i, gp in A.groupby('inc'):
    r = agg(gp); r['id'] = int(i); r['nome'] = lab.get(i, ''); rows.append(r)
IC = pd.DataFrame(rows).merge(inc[['id', 'lon', 'lat', 'nomi_osm', 'nodi', 'diam_m']], on='id')
IC['anni_con'] = IC.y.apply(lambda v: sum(1 for t in v if t > 0))
IC = IC.sort_values('inc', ascending=False).reset_index(drop=True)
IC.drop(columns=['y']).to_csv(S + '/pulito/incroci_classifica.csv', index=False)
# incroci dentro il confine del Comune (poligoni dei 88 NIL, semplificati): il ritaglio OSM arriva a circa 4 km oltre il confine
from shapely.ops import unary_union
Ng = json.load(open(S + '/raw/comune_milano/nil_confini_semplificati.geojson', encoding='utf-8'))
com = unary_union([shape(f['geometry']).buffer(0) for f in Ng['features']]).buffer(0.0004)   # circa 40 m di tolleranza (gradi)
dentro = shapely.contains(com, shapely.points(inc.lon.values, inc.lat.values))
inc['dentro'] = dentro
N_inc_osm = int(dentro.sum()); N_inc_con = int(len(IC))
R['incroci_osm'] = {'nodi_incrocio': int(len(nod)), 'incroci_ritaglio': int(len(inc)), 'incroci': N_inc_osm, 'con_incidenti': N_inc_con}
cs = np.sort(IC.inc.values)[::-1]; totA = cs.sum()
R['concentrazione'] = {'agganciati': int(totA), 'top10_pct': round(100 * cs[:10].sum() / totA, 1), 'top100_pct': round(100 * cs[:100].sum() / totA, 1), 'top1000_pct': round(100 * cs[:1000].sum() / totA, 1),
                       'incroci_con_almeno_1': N_inc_con, 'incroci_con_almeno_10': int((IC.inc >= 10).sum()), 'incroci_con_almeno_50': int((IC.inc >= 50).sum()),
                       'incidenti_in_incroci_con_almeno_50_pct': round(100 * IC[IC.inc >= 50].inc.sum() / totA, 1), 'pct_incroci_osm_con_almeno_1': round(100 * N_inc_con / N_inc_osm, 1),
                       'n_per_meta_incidenti': int(np.searchsorted(np.cumsum(cs), totA / 2) + 1)}
R['concentrazione']['pct_incroci_per_meta_incidenti'] = round(100 * R['concentrazione']['n_per_meta_incidenti'] / N_inc_osm, 2)
top1 = IC.sort_values('p1', ascending=False).head(20); top3 = IC.sort_values('p3', ascending=False).head(20)
R['persistenza'] = {'top20_2010_14_ancora_top20_2020_24': int(len(set(top1.id) & set(top3.id))),
                    'top20_2010_14_ancora_top100_2020_24': int(len(set(top1.id) & set(IC.sort_values('p3', ascending=False).head(100).id))),
                    'top20_2010_14_inc_p1': int(top1.p1.sum()), 'top20_2010_14_inc_p3': int(top1.p3.sum()),
                    'tutti_inc_p1': int(IC.p1.sum()), 'tutti_inc_p3': int(IC.p3.sum()),
                    'corr_p1_p3_spearman': round(float(IC[['p1', 'p3']].corr(method='spearman').iloc[0, 1]), 2),
                    'corr_p2_p3_spearman': round(float(IC[['p2', 'p3']].corr(method='spearman').iloc[0, 1]), 2)}

# ------------------------------------------------------------ 4. vie
vie = pd.read_csv(S + '/pulito/ref_vie_km_filone7.csv', sep=';', encoding='utf-8-sig')
vie['key'] = vie.key.astype(str)
K = df[df.livello != 'nessuna']
cnt = collections.defaultdict(collections.Counter)
def addrow(k, r):
    c = cnt[k]; c['inc'] += 1; c['feriti'] += r.feriti; c['morti'] += r.morti; c['ped'] += r.ped; c['ped_feriti'] += r.ped_feriti; c['ped_morti'] += r.ped_morti
    c['bici'] += r.bici; c['moto'] += r.moto
    if r.anno >= 2020: c['p3'] += 1
for r in K.itertuples():
    ks = {r.via1_k}
    if r.livello in ('incrocio', 'incrocio_approx', 'strada') and r.via2_k not in ('', 'None'): ks.add(r.via2_k)
    for k in ks:
        if k not in ('', 'None'): addrow(k, r)
V = pd.DataFrame([{'key': k, **c} for k, c in cnt.items()]).merge(vie[['key', 'nome', 'km', 'cl']], on='key')
for c in ('inc', 'feriti', 'morti', 'ped', 'ped_feriti', 'ped_morti', 'bici', 'moto', 'p3'): V[c] = V[c].fillna(0).astype(int)
V['inc_km_anno'] = V.inc / V.km / 15; V['p3_km_anno'] = V.p3 / V.km / 5; V['ped_km_anno'] = V.ped / V.km / 15
V = V.sort_values('inc', ascending=False)
V.drop(columns=['key']).to_csv(S + '/pulito/vie_classifica.csv', index=False)
R['vie'] = {'con_lunghezza': int(len(V)), 'km_totali': round(float(V.km.sum()), 0)}

# ------------------------------------------------------------ 5. mappa a celle di 100 m
P = df[df.buono]
cx = np.floor(P.x / 100).astype(int).values; cy = np.floor(P.y / 100).astype(int).values
cells = pd.DataFrame({'cx': cx, 'cy': cy, 'ped': P.ped.values, 'bici': P.bici.values, 'moto': P.moto.values, 'p3': (P.anno >= 2020).astype(int).values,
                      'morti': (P.morti > 0).astype(int).values}).groupby(['cx', 'cy']).agg(n=('ped', 'size'), ped=('ped', 'sum'), bici=('bici', 'sum'), moto=('moto', 'sum'),
                                                                                              p3=('p3', 'sum'), morti=('morti', 'sum')).reset_index()
Ti = Transformer.from_crs(32632, 4326, always_xy=True)
lo, la = Ti.transform((cells.cx.values + .5) * 100, (cells.cy.values + .5) * 100)
cells['lon'] = np.round(lo, 5); cells['lat'] = np.round(la, 5)
cells.to_csv(S + '/pulito/celle100m.csv', index=False)
R['celle'] = {'n': int(len(cells)), 'max': int(cells.n.max())}

# ------------------------------------------------------------ 6. zone a velocita' limitata (ds1438) prima/dopo
Zg = json.load(open(S + '/raw/comune_milano/aree_velim.geojson', encoding='utf-8'))
zp = []; zy = []
for f in Zg['features']:
    p = f['properties']
    if p.get('limite') not in ('30', '20', '15', '10'): continue
    gm = sh_transform(lambda xx, yy, z=None: T.transform(xx, yy), shape(f['geometry'])).buffer(15)
    zp.append(gm); zy.append(int(p['anno']))
zy = np.array(zy); st = STRtree(zp)
bmask = df.buono.values; bi = np.where(bmask)[0]
pts = shapely.points(df.x.values[bmask], df.y.values[bmask])
pi_, zi_ = st.query(pts, predicate='within')
first = np.full(len(df), 9999)
np.minimum.at(first, bi[pi_], zy[zi_])
df['coorte'] = first
B = df[df.buono]
ctrl = B[B.coorte == 9999]
wind = []
for Y in range(2013, 2022):
    zn = B[B.coorte == Y]
    f = lambda d, a, b: int(d.anno.between(a, b).sum())
    wind.append({'anno_zona': Y, 'punti_zona': int(len(zn)), 'zona_prima': f(zn, Y - 3, Y - 1), 'zona_dopo': f(zn, Y + 1, Y + 3), 'altrove_prima': f(ctrl, Y - 3, Y - 1), 'altrove_dopo': f(ctrl, Y + 1, Y + 3),
                 'zona_ped_prima': f(zn[zn.ped == 1], Y - 3, Y - 1), 'zona_ped_dopo': f(zn[zn.ped == 1], Y + 1, Y + 3),
                 'altrove_ped_prima': f(ctrl[ctrl.ped == 1], Y - 3, Y - 1), 'altrove_ped_dopo': f(ctrl[ctrl.ped == 1], Y + 1, Y + 3)})
W = pd.DataFrame(wind); W.to_csv(S + '/pulito/zone30_prima_dopo.csv', index=False)
def pooled(prefix=''):
    zb = W['zona_' + prefix + 'prima'].sum(); za = W['zona_' + prefix + 'dopo'].sum()
    exp = float((W['zona_' + prefix + 'prima'] * W['altrove_' + prefix + 'dopo'] / W['altrove_' + prefix + 'prima']).sum())
    return {'prima': int(zb), 'dopo': int(za), 'atteso_se_come_altrove': round(exp, 1), 'rapporto_dopo_prima_zona': round(za / zb, 3), 'rapporto_atteso': round(exp / zb, 3)}
R['zone30'] = {'tutti': pooled(''), 'pedoni': pooled('ped_'), 'zone_attive': len(zp), 'n_punti_in_zone': int((B.coorte < 9999).sum()), 'n_punti_posizionati': int(len(B)),
               'per_anno_zona': {int(a): int(n) for a, n in sorted(collections.Counter(zy.tolist()).items())}}

# ------------------------------------------------------------ 7. Area C e Area B
Ag = json.load(open(S + '/raw/comune_milano/disciplina_aree_areaB_areaC.geojson', encoding='utf-8'))
ar = {}
for f in Ag['features']:
    if f['properties']['tipo'] in ('AREA_C', 'AREA_B'):
        ar[f['properties']['tipo']] = sh_transform(lambda xx, yy, z=None: T.transform(xx, yy), shape(f['geometry']))
shapely.prepare(ar['AREA_C']); shapely.prepare(ar['AREA_B'])
inC = np.zeros(len(df), bool); inB = np.zeros(len(df), bool)
inC[bi] = shapely.contains(ar['AREA_C'], pts); inB[bi] = shapely.contains(ar['AREA_B'], pts)
df['areaC'] = inC; df['areaB'] = inB
def serie(mask): return [int(((df.anno == a) & df.buono & mask).sum()) for a in ANNI]
R['aree'] = {'dentro_areaC': serie(df.areaC), 'areaB_fuori_C': serie(df.areaB & ~df.areaC), 'fuori_areaB': serie(~df.areaB),
             'km2_areaC': round(ar['AREA_C'].area / 1e6, 2), 'km2_areaB': round(ar['AREA_B'].area / 1e6, 2)}
pd.DataFrame({'anno': ANNI, 'dentro_areaC': R['aree']['dentro_areaC'], 'areaB_fuori_C': R['aree']['areaB_fuori_C'], 'fuori_areaB': R['aree']['fuori_areaB']}).to_csv(S + '/pulito/aree_b_c.csv', index=False)

# ------------------------------------------------------------ 8. pedoni e morti: incrocio o no
ped = df[df.ped == 1]
R['pedoni_dove'] = {'incidenti_ped': int(len(ped)), 'in_incrocio_dichiarato_pct': round(100 * float(ped.interse.between(1, 6).mean()), 1), 'tutti_in_incrocio_dichiarato_pct': round(100 * float(df.interse.between(1, 6).mean()), 1),
                    'morti_ped_totali': int(ped.ped_morti.sum())}
dd = df[df.morti > 0]
R['morti_dove'] = {'incidenti_mortali': int(len(dd)), 'in_incrocio_dichiarato_pct': round(100 * float(dd.interse.between(1, 6).mean()), 1),
                   'rettilineo_pct': round(100 * float((dd.interse == 7).mean()), 1), 'morti_totali': int(df.morti.sum()), 'con_pedone_pct': round(100 * float((dd.ped == 1).mean()), 1)}
R['interse_tutti'] = {str(k): int(v) for k, v in df.interse.value_counts().sort_index().items()}
# ------------------------------------------------------------ 9. tratti di strada lontani dagli incroci (cella di 100 m, solo incidenti con "non intersezione")
NI = df[df.buono & df.interse.between(7, 12) & ~df.agganciato].copy()
NI['cx'] = np.floor(NI.x / 100).astype(int); NI['cy'] = np.floor(NI.y / 100).astype(int)
trat = []
for (a, b), gp in NI.groupby(['cx', 'cy']):
    if len(gp) < 8: continue
    nm = collections.Counter(gp.via1[gp.via1 != '']).most_common(1)
    trat.append({'via': nm[0][0] if nm else '', 'inc': len(gp), 'feriti': int(gp.feriti.sum()), 'morti': int(gp.morti.sum()), 'ped': int(gp.ped.sum()), 'moto': int(gp.moto.sum()), 'bici': int(gp.bici.sum()),
                 'p3': int((gp.anno >= 2020).sum()), 'lon': round(float(Ti.transform(gp.x.mean(), gp.y.mean())[0]), 5), 'lat': round(float(Ti.transform(gp.x.mean(), gp.y.mean())[1]), 5)})
TR = pd.DataFrame(trat).sort_values('inc', ascending=False).reset_index(drop=True)
TR.to_csv(S + '/pulito/tratti_lontani_da_incroci.csv', index=False)
R['tratti'] = {'celle_con_8_o_piu': int(len(TR)), 'non_intersezione_posizionati': int(len(NI))}
lv = df.livello.value_counts(); n = len(df)
R['qualita'] = {k: round(100 * float(lv.get(k, 0)) / n, 1) for k in ('civico', 'civico_approx', 'incrocio', 'incrocio_approx', 'strada', 'nessuna')}
R['qualita']['posizionati'] = round(100 * float(df.buono.mean()), 1)
IC.to_pickle(S + '/pulito/_IC.pkl'); V.to_pickle(S + '/pulito/_V.pkl')
json.dump(R, open(S + '/pulito/riepilogo.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({k: R[k] for k in ('aggancio', 'incroci_osm', 'concentrazione', 'persistenza', 'zone30', 'pedoni_dove', 'morti_dove', 'totali')}, ensure_ascii=False, indent=1))
print(IC.head(25)[['nome', 'inc', 'feriti', 'morti', 'ped', 'bici', 'moto', 'p1', 'p2', 'p3', 'nomi_osm']].to_string())
