"""Fase 2, passi 2-4: civici + servizi puliti + aggancio al grafo + tempi a piedi (Dijkstra multi-sorgente).
Uso: python -I f2_punti.py <ABS strand>
Scrive in out/: servizi_puliti.csv, civici_tempi.csv, f2_punti_log.json. Spiegazioni in NOTE.md "Fase 2"."""
import sys, glob, json, time, re
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import unary_union, transform as shp_transform
from shapely import STRtree, contains_xy
import shapely
from scipy.spatial import cKDTree
from scipy.sparse import load_npz, csr_matrix
from scipy.sparse.csgraph import dijkstra
S = sys.argv[1]; R = S + '/raw/comune_milano/'; O = S + '/out/'
t0 = time.time(); LOG = {}
SPEED = 4.5 / 3.6          # m/s  (4,5 km/h)
MAXSNAP = 150.0            # m, oltre si scarta
LIM = 3200.0               # m, il Dijkstra si ferma qui (circa 43 minuti)
PARK_MIN_M2 = 5000.0
tr = Transformer.from_crs(4326, 32632, always_xy=True)
def xy(lon, lat):
    a, b = tr.transform(np.asarray(lon, float), np.asarray(lat, float)); return np.asarray(a), np.asarray(b)
def rd(pat, sep=';', **k): return pd.read_csv(glob.glob(R + pat)[0], sep=sep, dtype=str, **k)
def fl(s): return pd.to_numeric(pd.Series(s).astype(str).str.replace(',', '.'), errors='coerce')

# ---- grafo
G = load_npz(O + 'grafo_pedonale_csr.npz'); nd = np.load(O + 'grafo_pedonale_nodi.npz')
gx, gy = nd['x'], nd['y']; N = G.shape[0]; tree = cKDTree(np.c_[gx, gy])
# ---- confine del Comune (m)
conf = shape(json.load(open(glob.glob(R + 'confine_comune/*.geojson')[0], encoding='utf-8'))['features'][0]['geometry'])
confm = shp_transform(lambda x, y, z=None: tr.transform(x, y), conf)
LOG['area_comune_km2'] = round(confm.area / 1e6, 2)
conf_buf = confm.buffer(200)       # tolleranza 200 m per le coordinate al bordo
def inside(x, y): return contains_xy(conf_buf, x, y)
def snap(x, y):
    d, i = tree.query(np.c_[x, y]); return i, d

# ---- civici
c = pd.read_csv(glob.glob(R + 'civici/estratto/*.csv')[0], sep=';', dtype=str,
                usecols=['IDMASTER', 'CODICE_VIA', 'NUMEROCOMPLETO', 'RESIDENZIALE', 'STATOCIVICO', 'DENOMINAZIONE', 'LIVELLO', 'ID_NIL', 'NIL', 'LONG_WGS84', 'LAT_WGS84'])
LOG['civici_righe'] = len(c)
c = c[c.STATOCIVICO == 'Applicato'].copy(); LOG['civici_applicati'] = len(c)
c['lon'] = fl(c.LONG_WGS84).values; c['lat'] = fl(c.LAT_WGS84).values
c = c.dropna(subset=['lon', 'lat'])
c['k'] = c.lon.round(6).astype(str) + '_' + c.lat.round(6).astype(str)
n0 = len(c); c = c.drop_duplicates('k'); LOG['civici_dopo_dedup_coordinate'] = len(c); LOG['civici_duplicati_coordinate_scartati'] = n0 - len(c)
c['x'], c['y'] = xy(c.lon, c.lat)
m = inside(c.x.values, c.y.values); LOG['civici_fuori_confine_scartati'] = int((~m).sum()); c = c[m].copy()
i, d = snap(c.x.values, c.y.values); c['node'] = i; c['snap_m'] = d
LOG['civici_snap_mediana_m'] = round(float(np.median(d)), 1); LOG['civici_snap_p95_m'] = round(float(np.percentile(d, 95)), 1)
LOG['civici_snap_max_m'] = round(float(d.max()), 1); LOG['civici_snap_oltre150m'] = int((d > MAXSNAP).sum())
c['flag_snap150'] = (d > MAXSNAP).astype(int)
c['ID_NIL'] = pd.to_numeric(c.ID_NIL, errors='coerce'); c['RESIDENZIALE'] = pd.to_numeric(c.RESIDENZIALE, errors='coerce')
c = c.reset_index(drop=True)

# ---- servizi
SV = []
def add(tipo, df, lon, lat, nome=None, sub='', anno='', dedup=True):
    t = pd.DataFrame({'tipo': tipo, 'sub': sub, 'nome': (df[nome].values if nome is not None else ''),
                      'lon': fl(df[lon]).values, 'lat': fl(df[lat]).values, 'anno': anno})
    n_in = len(t); t = t.dropna(subset=['lon', 'lat']); n_nocoord = n_in - len(t)
    t = t[(t.lon > 0) & (t.lat > 0)]
    if dedup:
        t['k'] = t.lon.round(6).astype(str) + '_' + t.lat.round(6).astype(str); t = t.drop_duplicates(['tipo', 'k']).drop(columns='k')
    LOG.setdefault('servizi_ingressi', {})[tipo + (':' + sub if sub else '')] = {'righe_in': n_in, 'senza_coordinate': n_nocoord, 'punti_distinti': len(t)}
    SV.append(t)
add('farmacie', rd('farmacie/*.csv'), 'LONGITUDINE', 'LATITUDINE', 'DESCRIZIONE_FARMACIA', anno='elenco regionale 15/10/2026')
mm = rd('mmg/*.csv'); LOG['mmg_tipi'] = mm.tipoMedico.value_counts().to_dict()
add('medici', mm[mm.attivo == '1'], 'LONG_X_4326', 'LAT_Y_4326', None, anno='29/10/2026, solo attivo=1, un punto per ambulatorio')
# nidi: ultimo anno 2018/19; coordinate mancanti riempite con quelle dello stesso nido in altri anni, poi dall'indirizzo
nd_ = rd('nidi/*.csv'); a19 = nd_[nd_.CODANNOSCOLASTICO == '1819'].copy()
a19['lon'] = fl(a19.LONG_WGS84).values; a19['lat'] = fl(a19.LAT_WGS84).values
alt = nd_[nd_.CODANNOSCOLASTICO != '1819'].copy(); alt['lon'] = fl(alt.LONG_WGS84).values; alt['lat'] = fl(alt.LAT_WGS84).values
alt = alt.dropna(subset=['lon']).drop_duplicates('NOME_LUNGO').set_index('NOME_LUNGO')[['lon', 'lat']]
nmiss0 = int(a19.lon.isna().sum()); filled = 0
for ix in a19.index[a19.lon.isna()]:
    k = a19.at[ix, 'NOME_LUNGO']
    if k in alt.index:
        a19.at[ix, 'lon'] = alt.at[k, 'lon']; a19.at[ix, 'lat'] = alt.at[k, 'lat']; filled += 1
LOG['nidi_2018_19_righe'] = len(a19); LOG['nidi_senza_coordinate_prima'] = nmiss0; LOG['nidi_riempite_da_altri_anni'] = filled
def norm(s): return re.sub(r'[^A-Z0-9]', '', str(s).upper())
cv_idx = {}
for r_ in c[['DENOMINAZIONE', 'NUMEROCOMPLETO', 'lon', 'lat']].itertuples(index=False):
    cv_idx.setdefault((norm(r_.DENOMINAZIONE), norm(r_.NUMEROCOMPLETO)), (r_.lon, r_.lat))
geo = 0
for ix in a19.index[a19.lon.isna()]:
    s_ = norm(a19.at[ix, 'INDIRIZZO']); n_ = norm(a19.at[ix, 'NUMEROCIVICO'])
    if (s_, n_) in cv_idx:
        a19.at[ix, 'lon'], a19.at[ix, 'lat'] = cv_idx[(s_, n_)]; geo += 1
LOG['nidi_riempite_da_indirizzo_civici'] = geo; LOG['nidi_ancora_senza_coordinate'] = int(a19.lon.isna().sum())
add('nidi', a19, 'lon', 'lat', 'NOMINATIVO', anno='a.s. 2018/19 (ultimo disponibile)')
# scuole (infanzia + primaria + secondaria I) ultimo anno 2025/26
for key, pat in [('infanzia', 'scuole_infanzia_2025/*.csv'), ('primaria', 'scuole_primarie/*.csv'), ('sec1', 'scuole_sec1_2025/*.csv')]:
    s = rd(pat); s = s[s.ANNOSCOL == '2025/2026']
    add('scuole', s, 'LONG_X_4326', 'LAT_Y_4326', 'DENOMINAZIONE', sub=key, anno='a.s. 2025/26', dedup=False)
add('sec2_info', rd('scuole_sec2/*.csv'), 'LONG_X_4326', 'LAT_Y_4326', 'DENOMINAZ', anno='anno non dichiarato (solo informativo)')
add('biblioteche', rd('biblioteche_sistema/*.csv'), 'long', 'lat', 'Biblioteche - Sede', anno='Sistema bibliotecario, caricato 10/7/2026')
mc = rd('mercati_coperti/*.csv'); mc = mc[mc.attivo.str.upper() == 'SI']
add('mercati', mc, 'LONG_X_4326', 'LAT_Y_4326', 'MCC', sub='coperto', anno='maggio 2024', dedup=False)
add('mercati', rd('mercati_settimanali/*.csv'), 'LONG_X_4326', 'LAT_Y_4326', 'MERCATO', sub='settimanale', anno='maggio 2024', dedup=False)
add('mercati', rd('mercati_agricoltori/*.csv', sep=','), 'LONG_WGS84', 'LAT_WGS84', 'NOME_MERCATO', sub='agricoltori', anno='anno non dichiarato', dedup=False)
add('sport', rd('sport_ds34/*.csv'), 'LONG_X_4326', 'LAT_Y_4326', 'Nome', anno='anno non dichiarato (ds34)')
add('poste', rd('poste/*.csv'), 'LONG_X_4326', 'LAT_Y_4326', 'Sportello', anno='anno non dichiarato')
vi = rd('vicinato/*.csv'); st = vi.settore_merceologico.fillna('').str.lower()
food = st.str.contains(r'(?<!non )alimentare', regex=True)
LOG['vicinato_righe'] = len(vi); LOG['vicinato_righe_alimentari'] = int(food.sum())
add('vicinato', vi[food], 'LONG_X_4326', 'LAT_Y_4326', 'insegna', anno='caricato 31/8/2026 (negozi alimentari)')
sv = pd.concat(SV, ignore_index=True)
sv['k'] = sv.lon.round(6).astype(str) + '_' + sv.lat.round(6).astype(str)
sv = sv.sort_values(['tipo', 'sub']).drop_duplicates(['tipo', 'k']).drop(columns='k').reset_index(drop=True)
sv['x'], sv['y'] = xy(sv.lon, sv.lat)
ok = inside(sv.x.values, sv.y.values)
LOG['servizi_fuori_confine_scartati'] = sv[~ok].groupby('tipo').size().to_dict(); sv = sv[ok].reset_index(drop=True)
i, d = snap(sv.x.values, sv.y.values); sv['node'] = i; sv['snap_m'] = d
LOG['servizi_snap_oltre150m_scartati'] = sv[sv.snap_m > MAXSNAP].groupby('tipo').size().to_dict()
sv = sv[sv.snap_m <= MAXSNAP].reset_index(drop=True)
LOG['servizi_snap_mediana_m'] = sv.groupby('tipo').snap_m.median().round(1).to_dict()
LOG['servizi_finali'] = sv.groupby('tipo').size().to_dict()

# ---- parchi: unione dei poligoni, soglia di area, ingressi lungo il bordo
pk = json.load(open(R + 'parchi/parchi.geojson', encoding='utf-8'))['features']
polys = [shp_transform(lambda x, y, z=None: tr.transform(x, y), shape(f['geometry'])).buffer(0) for f in pk]
U = unary_union(polys); parts = list(U.geoms) if hasattr(U, 'geoms') else [U]
big = [p for p in parts if p.area >= PARK_MIN_M2]
LOG['parchi_poligoni_originali'] = len(polys); LOG['parchi_dopo_unione'] = len(parts); LOG['parchi_>=5000m2'] = len(big)
LOG['parchi_area_totale_>=5000_ha'] = round(sum(p.area for p in big) / 1e4, 1); LOG['parchi_area_totale_tutti_ha'] = round(sum(p.area for p in parts) / 1e4, 1)
ent = []
for pid, p in enumerate(big):
    ring = p.exterior; L = ring.length; n = max(4, int(L // 50))
    for q in shapely.line_interpolate_point(ring, np.linspace(0, L, n, endpoint=False)): ent.append((pid, q.x, q.y))
ent = pd.DataFrame(ent, columns=['pid', 'x', 'y'])
i, d = snap(ent.x.values, ent.y.values); ent['node'] = i; ent['snap_m'] = d
LOG['parchi_ingressi_totali'] = len(ent); ent = ent[ent.snap_m <= MAXSNAP].copy(); LOG['parchi_ingressi_validi'] = len(ent)
LOG['parchi_senza_ingressi_validi'] = int(len(big) - ent.pid.nunique())
pk_sv = pd.DataFrame({'tipo': 'parchi', 'sub': ent.pid.values, 'nome': '', 'lon': 0.0, 'lat': 0.0, 'anno': 'parchi >=5000 m2, ingressi ogni 50 m sul bordo', 'x': ent.x.values, 'y': ent.y.values, 'node': ent.node.values, 'snap_m': ent.snap_m.values})
lo, la = Transformer.from_crs(32632, 4326, always_xy=True).transform(pk_sv.x.values, pk_sv.y.values); pk_sv['lon'] = lo; pk_sv['lat'] = la
svall = pd.concat([sv, pk_sv], ignore_index=True)
svall.to_csv(O + 'servizi_puliti.csv', index=False, encoding='utf-8')
pd.DataFrame({'pid': range(len(big)), 'area_m2': [round(p.area) for p in big]}).to_csv(O + 'parchi_grandi_aree.csv', index=False)

# ---- OSM fuori confine (variante bordo)
po = pd.read_csv(S + '/raw/osm_poi/osm_poi_milano_estratto.csv', dtype=str)
po = po[po.fascia == 'fuori_entro_1500m'].copy(); po['lon'] = fl(po.lon).values; po['lat'] = fl(po.lat).values
po['x'], po['y'] = xy(po.lon, po.lat)
MAPOSM = {'farmacie': ['pharmacy'], 'scuole': ['school', 'kindergarten'], 'nidi': ['kindergarten', 'childcare'],
          'poste': ['post_office'], 'vicinato': ['supermarket', 'bakery', 'butcher', 'greengrocer', 'convenience']}
osm_pts = {}
for tipo, tags in MAPOSM.items():
    q = po[po.tag.isin(tags)].copy()
    if tipo == 'poste':
        q = q[~q.operator.fillna('').str.contains('DHL|GLS|Nexive|Mail Boxes|Posta Express|SDA|BRT|UPS|FedEx', case=False, regex=True)]
    i, d = snap(q.x.values, q.y.values); q['node'] = i; q['snap_m'] = d; q = q[q.snap_m <= MAXSNAP]
    osm_pts[tipo] = q; LOG.setdefault('osm_fuori_punti', {})[tipo] = len(q)

# ---- Dijkstra multi-sorgente con super-sorgente (la distanza di aggancio del servizio e' contata)
indptr = G.indptr; ind = G.indices; dat = G.data
def build_aug(nodes, snaps):
    best = pd.DataFrame({'n': nodes, 's': snaps}).groupby('n', as_index=False).s.min()
    r = np.r_[np.repeat(np.arange(N), np.diff(indptr)), np.full(len(best), N)]
    cc = np.r_[ind, best.n.values]; vv = np.r_[dat, best.s.values + 0.01]
    return csr_matrix((vv, (r, cc)), shape=(N + 1, N + 1))
def times(nodes, snaps):
    return dijkstra(build_aug(nodes, snaps), directed=True, indices=N, limit=LIM)[:N]
TIPI = ['farmacie', 'medici', 'nidi', 'scuole', 'biblioteche', 'mercati', 'parchi', 'sport', 'poste', 'vicinato']
EXTRA = ['sec2_info']
def minutes(dist_nodes):
    dm = dist_nodes[c.node.values] + c.snap_m.values
    t = dm / SPEED / 60.0
    t = np.where(dm > LIM + MAXSNAP, np.nan, t)
    return np.round(t, 2)
out = c[['IDMASTER', 'CODICE_VIA', 'NUMEROCOMPLETO', 'DENOMINAZIONE', 'RESIDENZIALE', 'ID_NIL', 'NIL', 'lon', 'lat', 'snap_m', 'flag_snap150']].copy()
for tipo in TIPI + EXTRA + ['mercato_coperto']:
    if tipo == 'mercato_coperto': s_ = svall[(svall.tipo == 'mercati') & (svall['sub'] == 'coperto')]
    else: s_ = svall[svall.tipo == tipo]
    out['min_' + tipo] = minutes(times(s_.node.values, s_.snap_m.values))
inpark = np.zeros(len(c), bool)
for p in big: inpark |= contains_xy(p, c.x.values, c.y.values)
LOG['civici_dentro_un_parco_>=5000m2'] = int(inpark.sum()); out.loc[inpark, 'min_parchi'] = 0.0
for tipo in MAPOSM:
    s_ = svall[svall.tipo == tipo]; q = osm_pts[tipo]
    out['minBordo_' + tipo] = minutes(times(np.r_[s_.node.values, q.node.values], np.r_[s_.snap_m.values, q.snap_m.values]))
# CAP stimato: CAP del punto con CAP noto piu vicino (vicinato, farmacie, poste, mmg)
kn = []
for pat, lo_, la_ in [('vicinato/*.csv', 'LONG_X_4326', 'LAT_Y_4326'), ('farmacie/*.csv', 'LONGITUDINE', 'LATITUDINE'), ('poste/*.csv', 'LONG_X_4326', 'LAT_Y_4326'), ('mmg/*.csv', 'LONG_X_4326', 'LAT_Y_4326')]:
    z = rd(pat); z = pd.DataFrame({'lon': fl(z[lo_]).values, 'lat': fl(z[la_]).values, 'cap': z.CAP.values}).dropna(); kn.append(z[(z.lon > 0) & (z.cap.str.len() == 5)])
kn = pd.concat(kn).drop_duplicates(['lon', 'lat']); kx, ky = xy(kn.lon, kn.lat)
dd, ii = cKDTree(np.c_[kx, ky]).query(np.c_[c.x.values, c.y.values])
out['CAP'] = kn.cap.values[ii]; out['CAP_dist_m'] = np.round(dd, 1)
LOG['cap_stimato_dist_mediana_m'] = round(float(np.median(dd)), 1); LOG['cap_stimato_dist_p95_m'] = round(float(np.percentile(dd, 95)), 1)
out['x'] = np.round(c.x.values, 1); out['y'] = np.round(c.y.values, 1)
out['punteggio'] = (out[['min_' + t for t in TIPI]] <= 15.0).sum(axis=1)
out['punteggio_bordo'] = (out[[('minBordo_' + t) if t in MAPOSM else ('min_' + t) for t in TIPI]] <= 15.0).sum(axis=1)
out.to_csv(O + 'civici_tempi.csv', index=False, encoding='utf-8')
# ---- controllo: distanza in rete >= distanza in linea d'aria (tutti i civici, tutti i tipi puntuali)
chk = {}
for tipo in [t for t in TIPI if t != 'parchi']:
    s_ = svall[svall.tipo == tipo]; dl, _ = cKDTree(np.c_[s_.x.values, s_.y.values]).query(np.c_[c.x.values, c.y.values])
    mn = out['min_' + tipo].values * 60 * SPEED; okm = ~np.isnan(mn)
    viol = okm & (mn < dl - 1.0)
    far = okm & (dl > 100)
    chk[tipo] = {'civici_con_tempo': int(okm.sum()), 'violazioni_rete<linea_aria': int(viol.sum()),
                 'rapporto_rete_su_linea_aria_mediano': round(float(np.median(mn[far] / dl[far])), 3)}
LOG['controllo_rete_vs_linea_aria'] = chk
LOG['secondi'] = round(time.time() - t0)
json.dump(LOG, open(O + 'f2_punti_log.json', 'w'), indent=1, ensure_ascii=False, default=str)
print(json.dumps(LOG, indent=1, ensure_ascii=False, default=str))
