"""Fase 2, passi 5-8: punteggi per NIL, variante bordo, redditi per CAP, mappe, controlli.
Uso: python -I f2_aggrega.py <ABS strand>   (dopo f2_grafo.py e f2_punti.py)"""
import sys, glob, json, time
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import shape, Polygon, mapping
from shapely.ops import transform as shp_transform
from scipy.stats import spearmanr, pearsonr
from scipy.spatial import cKDTree
from scipy.sparse import load_npz
from scipy.sparse.csgraph import dijkstra
S = sys.argv[1]; R = S + '/raw/comune_milano/'; O = S + '/out/'
t0 = time.time(); CK = {}
TIPI = ['farmacie', 'medici', 'nidi', 'scuole', 'biblioteche', 'mercati', 'parchi', 'sport', 'poste', 'vicinato']
BORDO = ['farmacie', 'scuole', 'nidi', 'poste', 'vicinato']
ETI = {'farmacie': 'Farmacie', 'medici': 'Medici di base', 'nidi': 'Asili nido', 'scuole': 'Scuole (infanzia, primaria, sec. I)',
       'biblioteche': 'Biblioteche', 'mercati': 'Mercati', 'parchi': 'Parchi e giardini (>=5.000 m2)', 'sport': 'Impianti sportivi',
       'poste': 'Uffici postali', 'vicinato': 'Negozi alimentari di vicinato'}
SOGLIA = 15.0
c = pd.read_csv(O + 'civici_tempi.csv', dtype={'CAP': str})
NT = len(TIPI)
# ---- popolazione 2025 per NIL
p = pd.read_csv(glob.glob(R + 'pop_cittadinanza_quartiere/estratto/*.csv')[0], sep=';', usecols=['Anno', 'IdNil', 'Nil', 'Residenti'])
p = p[p.Anno == 2025].groupby(['IdNil', 'Nil'], as_index=False).Residenti.sum().rename(columns={'IdNil': 'ID_NIL', 'Nil': 'NIL_nome', 'Residenti': 'residenti_2025'})
CK['residenti_2025_totale'] = int(p.residenti_2025.sum()); CK['nil_con_residenti'] = len(p)
# ---- pesi: residenti del NIL distribuiti in parti uguali sui civici residenziali (RESIDENZIALE=1) del NIL
res = c[(c.RESIDENZIALE == 1) & c.ID_NIL.notna()].copy()
cnt = res.groupby('ID_NIL').size().rename('n_civici_res')
p = p.merge(cnt, left_on='ID_NIL', right_index=True, how='left')
CK['nil_con_residenti_ma_senza_civici_residenziali'] = p[p.n_civici_res.isna()][['ID_NIL', 'NIL_nome', 'residenti_2025']].to_dict('records')
res = res.merge(p[['ID_NIL', 'residenti_2025']], on='ID_NIL', how='left')
res['peso'] = res.residenti_2025 / res.ID_NIL.map(cnt)
res = res[res.peso.notna()].copy()
CK['residenti_distribuiti_sui_civici'] = round(float(res.peso.sum()))
CK['civici_residenziali_con_peso'] = len(res)
# ---- indicatori per civico
for t in TIPI: res['in_' + t] = (res['min_' + t] <= SOGLIA)
res['n15'] = res[['in_' + t for t in TIPI]].sum(axis=1)
res['n10'] = (res[['min_' + t for t in TIPI]] <= 10.0).sum(axis=1)
res['tutti'] = (res.n15 == NT)
res['min_medio'] = res[['min_' + t for t in TIPI]].clip(upper=30).fillna(30).mean(axis=1)
BCOL = [('minBordo_' + t) if t in BORDO else ('min_' + t) for t in TIPI]
res['n15_bordo'] = (res[BCOL] <= SOGLIA).sum(axis=1)
res['tutti_bordo'] = res.n15_bordo == NT
def wavg(g, col): return float((g[col].astype(float) * g.peso).sum() / g.peso.sum())
def agg(g):
    d = {'residenti_stimati': g.peso.sum(), 'civici_residenziali': len(g), 'punteggio_medio': wavg(g, 'n15'),
         'punteggio_medio_10min': wavg(g, 'n10'), 'quota_residenti_tutti_i_servizi': wavg(g, 'tutti'),
         'minuti_medi_30max': wavg(g, 'min_medio'), 'punteggio_medio_con_bordo': wavg(g, 'n15_bordo'),
         'quota_tutti_con_bordo': wavg(g, 'tutti_bordo')}
    for t in TIPI: d['quota_entro15_' + t] = wavg(g, 'in_' + t)
    return pd.Series(d)
nil = res.groupby('ID_NIL').apply(agg, include_groups=False).reset_index()
nil = nil.merge(p[['ID_NIL', 'NIL_nome', 'residenti_2025']], on='ID_NIL', how='left')
nil['differenza_bordo'] = nil.punteggio_medio_con_bordo - nil.punteggio_medio
nil['peggiore_servizio'] = nil[['quota_entro15_' + t for t in TIPI]].idxmin(axis=1).str.replace('quota_entro15_', '')
cols = ['ID_NIL', 'NIL_nome', 'residenti_2025', 'civici_residenziali', 'punteggio_medio', 'punteggio_medio_10min', 'quota_residenti_tutti_i_servizi', 'minuti_medi_30max',
        'punteggio_medio_con_bordo', 'differenza_bordo', 'quota_tutti_con_bordo', 'peggiore_servizio'] + ['quota_entro15_' + t for t in TIPI]
nil = nil[cols].sort_values('punteggio_medio', ascending=False)
nil.round(4).to_csv(O + 'nil_punteggi.csv', index=False, encoding='utf-8')
# ---- citta' intera
city = {'residenti_stimati': round(float(res.peso.sum())), 'punteggio_medio': round(wavg(res, 'n15'), 3), 'punteggio_medio_10min': round(wavg(res, 'n10'), 3),
        'quota_residenti_tutti': round(wavg(res, 'tutti'), 4), 'quota_residenti_tutti_con_bordo': round(wavg(res, 'tutti_bordo'), 4)}
city['distribuzione_punteggio_residenti'] = {int(k): round(float(v), 4) for k, v in (res.groupby('n15').peso.sum() / res.peso.sum()).items()}
city['quota_residenti_entro15_per_tipo'] = {t: round(wavg(res, 'in_' + t), 4) for t in TIPI}
city['minuti_mediani_pesati_per_tipo'] = {}
for t in TIPI:
    v = res['min_' + t].fillna(99).values; o = np.argsort(v); cw = np.cumsum(res.peso.values[o]); city['minuti_mediani_pesati_per_tipo'][t] = round(float(v[o][np.searchsorted(cw, cw[-1] / 2)]), 1)
# ---- top / bottom NIL (>= 1000 residenti)
big = nil[nil.residenti_2025 >= 1000].copy()
CK['nil_con_>=1000_residenti'] = len(big)
def mancano(r):
    out = [(ETI[t], r['quota_entro15_' + t]) for t in TIPI if r['quota_entro15_' + t] < 0.5]
    out.sort(key=lambda z: z[1]); return '; '.join(f'{a} ({b*100:.0f}% dei residenti entro 15 min)' for a, b in out) if out else 'nessuno sotto il 50%'
def peggio3(r):
    out = sorted([(ETI[t], r['quota_entro15_' + t]) for t in TIPI], key=lambda z: z[1])[:3]
    return '; '.join(f'{a} {b*100:.0f}%' for a, b in out)
tb = pd.concat([big.head(5).assign(gruppo='migliori 5'), big.tail(5).assign(gruppo='peggiori 5')])
tb['servizi_che_mancano_a_meta_dei_residenti'] = tb.apply(mancano, axis=1); tb['i_3_servizi_meno_raggiungibili'] = tb.apply(peggio3, axis=1)
tb[['gruppo', 'ID_NIL', 'NIL_nome', 'residenti_2025', 'punteggio_medio', 'quota_residenti_tutti_i_servizi', 'servizi_che_mancano_a_meta_dei_residenti', 'i_3_servizi_meno_raggiungibili']].round(3).to_csv(O + 'nil_top_bottom.csv', index=False, encoding='utf-8')
# ---- effetto bordo
nd_ = json.load(open(R + 'nil_vigenti/ds964_nil_wm.geojson', encoding='utf-8'))
tr = Transformer.from_crs(4326, 32632, always_xy=True)
conf = shape(json.load(open(glob.glob(R + 'confine_comune/*.geojson')[0], encoding='utf-8'))['features'][0]['geometry'])
confb = shp_transform(lambda x, y, z=None: tr.transform(x, y), conf).boundary
nilm = {int(f['properties']['ID_NIL']): shp_transform(lambda x, y, z=None: tr.transform(x, y), shape(f['geometry'])) for f in nd_['features']}
dist_b = {i: g.distance(confb) for i, g in nilm.items()}
nil['dist_confine_m'] = nil.ID_NIL.map(dist_b)
nil['NIL_di_bordo'] = nil.dist_confine_m <= 100
bd = nil[['ID_NIL', 'NIL_nome', 'residenti_2025', 'NIL_di_bordo', 'punteggio_medio', 'punteggio_medio_con_bordo', 'differenza_bordo', 'quota_residenti_tutti_i_servizi', 'quota_tutti_con_bordo']].sort_values('differenza_bordo', ascending=False)
bd.round(4).to_csv(O + 'bordo_effetto.csv', index=False, encoding='utf-8')
b = nil[nil.NIL_di_bordo]
CK['bordo'] = {'nil_di_bordo(<=100m dal confine)': int(len(b)), 'differenza_media_nil_bordo': round(float(b.differenza_bordo.mean()), 4), 'differenza_media_nil_interni': round(float(nil[~nil.NIL_di_bordo].differenza_bordo.mean()), 4),
               'differenza_massima': round(float(nil.differenza_bordo.max()), 3), 'nil_con_differenza>=0.05': int((nil.differenza_bordo >= 0.05).sum()),
               'nil_con_differenza>=0.1': int((nil.differenza_bordo >= 0.1).sum()),
               'prime5': bd.head(5)[['NIL_nome', 'differenza_bordo']].round(3).to_dict('records'),
               'citta_punteggio_senza_bordo': city['punteggio_medio'], 'citta_punteggio_con_bordo': round(wavg(res, 'n15_bordo'), 3),
               'civici_che_cambiano_punteggio': int((c.punteggio_bordo != c.punteggio).sum()), 'civici_che_guadagnano_tutti_i_tipi': int(((c.punteggio_bordo == NT) & (c.punteggio < NT)).sum())}
# ---- NIL poligoni con punteggi
feats = []
nm = nil.set_index('ID_NIL')
for f in nd_['features']:
    i = int(f['properties']['ID_NIL'])
    pr = {'ID_NIL': i, 'NIL': f['properties'].get('NIL')}
    if i in nm.index:
        r = nm.loc[i]; pr.update({'residenti': int(r.residenti_2025), 'punteggio': round(float(r.punteggio_medio), 2), 'punteggio_10min': round(float(r.punteggio_medio_10min), 2),
                                  'quota_tutti': round(float(r.quota_residenti_tutti_i_servizi), 3), 'punteggio_bordo': round(float(r.punteggio_medio_con_bordo), 2), 'peggiore': r.peggiore_servizio})
        for t in TIPI: pr['q_' + t] = round(float(r['quota_entro15_' + t]), 3)
    g = shape(f['geometry']).simplify(0.00003, preserve_topology=True)
    feats.append({'type': 'Feature', 'properties': pr, 'geometry': json.loads(json.dumps(mapping(g)))})
def rnd(o):
    if isinstance(o, float): return round(o, 5)
    if isinstance(o, (list, tuple)): return [rnd(x) for x in o]
    return o
for ft in feats: ft['geometry']['coordinates'] = rnd(ft['geometry']['coordinates'])
json.dump({'type': 'FeatureCollection', 'features': feats}, open(O + 'nil_poligoni_punteggi.geojson', 'w'), ensure_ascii=False, separators=(',', ':'))
# ---- esagoni da 100 m (piatto-piatto), punteggio medio dei civici (tutti gli applicati) dentro ciascuno
SZ = 100 / np.sqrt(3)          # raggio (centro-vertice) con 100 m tra lati opposti
x = c.x.values; y = c.y.values
q = (np.sqrt(3) / 3 * x - 1 / 3 * y) / SZ; r_ = (2 / 3 * y) / SZ
def hexround(q, r):
    cx = q; cz = r; cy = -cx - cz
    rx = np.round(cx); ry = np.round(cy); rz = np.round(cz)
    dx = abs(rx - cx); dy = abs(ry - cy); dz = abs(rz - cz)
    m1 = (dx > dy) & (dx > dz); m2 = (~m1) & (dy > dz)
    rx = np.where(m1, -ry - rz, rx); rz = np.where((~m1) & (~m2), -rx - ry, rz)
    return rx.astype(int), rz.astype(int)
hq, hr = hexround(q, r_)
c['hq'] = hq; c['hr'] = hr
c['n_civ'] = 1
for t in TIPI: c['in_' + t] = (c['min_' + t] <= SOGLIA).astype(float)
gh = c.groupby(['hq', 'hr'])
H = gh.agg(n=('n_civ', 'sum'), punteggio=('punteggio', 'mean'), **{('min_' + t): ('min_' + t, 'median') for t in TIPI}).reset_index()
H['id'] = np.arange(len(H))
hx = SZ * np.sqrt(3) * (H.hq + H.hr / 2); hy = SZ * 1.5 * H.hr
inv = Transformer.from_crs(32632, 4326, always_xy=True)
hf = []
ang = np.deg2rad(np.arange(6) * 60 + 30)
for k in range(len(H)):
    vx = hx.iloc[k] + SZ * np.cos(ang); vy = hy.iloc[k] + SZ * np.sin(ang)
    lo, la = inv.transform(vx, vy)
    ring = [[round(float(a), 5), round(float(b), 5)] for a, b in zip(lo, la)]; ring.append(ring[0])
    hf.append({'type': 'Feature', 'properties': {'id': int(H.id.iloc[k]), 'n': int(H.n.iloc[k]), 'p': round(float(H.punteggio.iloc[k]), 1)}, 'geometry': {'type': 'Polygon', 'coordinates': [ring]}})
json.dump({'type': 'FeatureCollection', 'features': hf}, open(O + 'hex100_citta.geojson', 'w'), separators=(',', ':'))
Ht = H[['id', 'n'] + ['min_' + t for t in TIPI]].copy()
for t in TIPI: Ht['min_' + t] = Ht['min_' + t].round(1)
Ht.to_csv(O + 'hex100_tempi_per_tipo.csv', index=False)
CK['hex'] = {'esagoni': len(H), 'dimensione_geojson_MB': round(len(open(O + 'hex100_citta.geojson', 'rb').read()) / 1e6, 2), 'dimensione_nil_geojson_MB': round(len(open(O + 'nil_poligoni_punteggi.geojson', 'rb').read()) / 1e6, 2)}
# ---- redditi per CAP
def carica_redditi():
    out = []
    for f in sorted(glob.glob(R + 'redditi_*/redditi_*.csv')):
        d = pd.read_csv(f, sep=';', dtype=str, encoding='utf-8-sig'); d.columns = ['anno', 'CAP', 'var', 'val']
        d['anno'] = pd.to_numeric(d.anno); d['val'] = pd.to_numeric(d.val, errors='coerce'); d['var'] = d['var'].str.strip()
        out.append(d)
    return pd.concat(out)
rd = carica_redditi(); pv = rd.pivot_table(index=['CAP', 'anno'], columns='var', values='val', aggfunc='first').reset_index()
pv['imponibile_per_contribuente'] = pv['Reddito imponibile - Ammontare in euro'] / pv['Numero contribuenti']
pv['complessivo_per_contribuente'] = pv['Reddito complessivo - Ammontare in euro'] / pv['Numero contribuenti']
pv['imponibile_per_frequenza'] = pv['Reddito imponibile - Ammontare in euro'] / pv['Reddito imponibile - Frequenza']
anni = sorted(pv.anno.unique()); ULT = max(anni)
CK['redditi_anni'] = [int(a) for a in anni]; CK['redditi_CAP'] = int(pv.CAP.nunique())
cap = res.groupby('CAP').apply(agg, include_groups=False).reset_index()
cap = cap[['CAP', 'residenti_stimati', 'civici_residenziali', 'punteggio_medio', 'punteggio_medio_10min', 'quota_residenti_tutti_i_servizi', 'minuti_medi_30max'] + ['quota_entro15_' + t for t in TIPI]]
wide = pv.pivot(index='CAP', columns='anno', values='imponibile_per_contribuente'); wide.columns = [f'imponibile_medio_{int(a)}' for a in wide.columns]
cap = cap.merge(wide.reset_index(), on='CAP', how='outer')
cap = cap.merge(pv[pv.anno == ULT][['CAP', 'Numero contribuenti', 'complessivo_per_contribuente', 'imponibile_per_frequenza']].rename(columns={'Numero contribuenti': f'contribuenti_{int(ULT)}'}), on='CAP', how='left')
# nome: NIL piu' frequente per CAP (dai civici)
dom = c.groupby(['CAP', 'NIL']).size().reset_index(name='n').sort_values('n', ascending=False).drop_duplicates('CAP')
cap = cap.merge(dom[['CAP', 'NIL']].rename(columns={'NIL': 'NIL_piu_frequente'}), on='CAP', how='left')
def sp_ci(a, b, nb=5000, seed=7):
    rho, pval = spearmanr(a, b); rng = np.random.default_rng(seed); n = len(a); bs = []
    for _ in range(nb):
        ix = rng.integers(0, n, n)
        if len(np.unique(a[ix])) < 2 or len(np.unique(b[ix])) < 2: continue
        bs.append(spearmanr(a[ix], b[ix])[0])
    return float(rho), float(pval), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
COR = {}
for metrica in ['punteggio_medio', 'punteggio_medio_10min', 'quota_residenti_tutti_i_servizi', 'minuti_medi_30max']:
    COR[metrica] = {}
    for a in anni:
        col = f'imponibile_medio_{int(a)}'; z = cap[[metrica, col]].dropna()
        rho, pval, lo_, hi_ = sp_ci(z[metrica].values, z[col].values)
        COR[metrica][int(a)] = {'spearman': round(rho, 3), 'p': round(pval, 4), 'ic95_bootstrap': [round(lo_, 3), round(hi_, 3)], 'n_CAP': int(len(z))}
for t in TIPI:
    z = cap[['quota_entro15_' + t, f'imponibile_medio_{int(ULT)}']].dropna()
    COR.setdefault('per_tipo_' + str(int(ULT)), {})[t] = round(float(spearmanr(z.iloc[:, 0], z.iloc[:, 1])[0]), 3)
inc = {int(a): cap[f'imponibile_medio_{int(a)}'].values for a in anni}
COR['stabilita_reddito_spearman_tra_anni'] = {f'{int(a)}-{int(b)}': round(float(spearmanr(inc[int(a)], inc[int(b)])[0]), 3) for a in anni for b in anni if a < b}
z = cap.dropna(subset=['punteggio_medio', f'imponibile_medio_{int(ULT)}']).copy()
z['log_reddito'] = np.log(z[f'imponibile_medio_{int(ULT)}'])
bcoef = np.polyfit(z.log_reddito, z.punteggio_medio, 1); z['previsto'] = np.polyval(bcoef, z.log_reddito); z['residuo'] = z.punteggio_medio - z.previsto
z['residuo_std'] = z.residuo / z.residuo.std(ddof=2)
COR['retta_punteggio_su_log_reddito'] = {'pendenza_per_log': round(float(bcoef[0]), 4), 'intercetta': round(float(bcoef[1]), 3), 'R2': round(float(pearsonr(z.log_reddito, z.punteggio_medio)[0] ** 2), 3), 'sd_residui': round(float(z.residuo.std(ddof=2)), 3)}
cap = cap.merge(z[['CAP', 'previsto', 'residuo', 'residuo_std']], on='CAP', how='left')
cap = cap.sort_values('CAP')
cap.round(4).to_csv(O + 'cap_redditi_servizi.csv', index=False, encoding='utf-8')
zz = z.sort_values('residuo')
COR['eccezioni_servite_meno_del_previsto'] = zz.head(5)[['CAP', 'NIL_piu_frequente', f'imponibile_medio_{int(ULT)}', 'punteggio_medio', 'previsto', 'residuo_std']].round(3).to_dict('records')
COR['eccezioni_servite_piu_del_previsto'] = zz.tail(5)[['CAP', 'NIL_piu_frequente', f'imponibile_medio_{int(ULT)}', 'punteggio_medio', 'previsto', 'residuo_std']].round(3).to_dict('records')
COR['CAP_reddito_basso_ben_serviti'] = z[(z[f'imponibile_medio_{int(ULT)}'] <= z[f'imponibile_medio_{int(ULT)}'].quantile(0.33)) & (z.punteggio_medio >= z.punteggio_medio.quantile(0.67))][['CAP', 'NIL_piu_frequente', f'imponibile_medio_{int(ULT)}', 'punteggio_medio']].round(2).to_dict('records')
COR['CAP_reddito_alto_serviti_poco'] = z[(z[f'imponibile_medio_{int(ULT)}'] >= z[f'imponibile_medio_{int(ULT)}'].quantile(0.67)) & (z.punteggio_medio <= z.punteggio_medio.quantile(0.33))][['CAP', 'NIL_piu_frequente', f'imponibile_medio_{int(ULT)}', 'punteggio_medio']].round(2).to_dict('records')
tz = cap.dropna(subset=['punteggio_medio', f'imponibile_medio_{int(ULT)}']).copy()
tz['terzile_reddito'] = pd.qcut(tz[f'imponibile_medio_{int(ULT)}'], 3, labels=['basso', 'medio', 'alto'])
COR['terzili_reddito_CAP_pesati_per_residenti'] = {str(k): {'CAP': int(len(g)), 'residenti_stimati': round(float(g.residenti_stimati.sum())),
    'punteggio_medio': round(float((g.punteggio_medio * g.residenti_stimati).sum() / g.residenti_stimati.sum()), 3),
    'quota_tutti': round(float((g.quota_residenti_tutti_i_servizi * g.residenti_stimati).sum() / g.residenti_stimati.sum()), 3),
    'minuti_medi_30max': round(float((g.minuti_medi_30max * g.residenti_stimati).sum() / g.residenti_stimati.sum()), 2),
    'reddito_imponibile_medio_min_max': [round(float(g[f'imponibile_medio_{int(ULT)}'].min())), round(float(g[f'imponibile_medio_{int(ULT)}'].max()))]} for k, g in tz.groupby('terzile_reddito', observed=True)}
# controllo: stessa correlazione ma con le quote per NIL assegnando a ogni NIL il suo CAP dominante non e' fatto (CAP e NIL non coincidono)
# ---- controlli: Dijkstra indipendente da singolo civico + luoghi noti
G = load_npz(O + 'grafo_pedonale_csr.npz'); sv = pd.read_csv(O + 'servizi_puliti.csv'); SPEED = 4.5 / 3.6
nd = np.load(O + 'grafo_pedonale_nodi.npz'); gtree = cKDTree(np.c_[nd['x'], nd['y']])
rng = np.random.default_rng(11); ix = rng.choice(len(c), 20, replace=False); diffs = []; violaz = 0
cx_, cy_ = c.x.values, c.y.values
for i in ix:
    nodo = gtree.query([cx_[i], cy_[i]])[1]; snapc = np.hypot(nd['x'][nodo] - cx_[i], nd['y'][nodo] - cy_[i])
    dd = dijkstra(G, directed=True, indices=nodo, limit=3300)
    for t in ['farmacie', 'poste', 'biblioteche', 'scuole']:
        s_ = sv[sv.tipo == t]; dm = (dd[s_.node.values] + s_.snap_m.values).min() + snapc
        m_ = c['min_' + t].values[i]; mt = dm / SPEED / 60
        if np.isfinite(mt) and not np.isnan(m_): diffs.append(abs(mt - m_))
        dl = np.hypot(s_.x.values - cx_[i], s_.y.values - cy_[i]).min()
        if np.isfinite(dm) and dm < dl - 1: violaz += 1
CK['controllo_20_civici_casuali'] = {'confronti': len(diffs), 'differenza_massima_minuti': round(float(max(diffs)), 3), 'differenza_media_minuti': round(float(np.mean(diffs)), 4), 'rete<linea_aria': violaz}
LUOGHI = {'Piazza Duomo': (45.46427, 9.18951), 'Stazione Centrale': (45.48609, 9.20493), 'Bicocca (Piazza della Scienza)': (45.51767, 9.21293),
          'Quarto Oggiaro (Via Amoretti)': (45.51160, 9.15110), 'Gratosoglio (Via Saponaro)': (45.40760, 9.17780), 'Lorenteggio (Piazza Frattini)': (45.44420, 9.12880),
          'Chiaravalle (Via S. Arialdo)': (45.42950, 9.23530), 'Baggio (Piazza Stovani)': (45.46000, 9.08190)}
Ltr = Transformer.from_crs(4326, 32632, always_xy=True); lu = {}
for nome, (la, lo) in LUOGHI.items():
    px, py = Ltr.transform(lo, la); dd_, k = cKDTree(np.c_[cx_, cy_]).query([px, py]); r = c.iloc[k]
    lu[nome] = {'civico': f"{r.DENOMINAZIONE} {r.NUMEROCOMPLETO}", 'distanza_dal_punto_m': round(float(dd_)), 'punteggio': int(r.punteggio), **{t: round(float(r['min_' + t]), 1) for t in TIPI}}
CK['luoghi_noti'] = lu
CK['citta'] = city
CK['correlazioni'] = COR
CK['secondi'] = round(time.time() - t0)
json.dump(CK, open(O + 'controlli_fase2.json', 'w'), indent=1, ensure_ascii=False, default=str)
print(json.dumps(CK, indent=1, ensure_ascii=False, default=str)[:14000])
