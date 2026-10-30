"""Fase 4 (servizi extra), passo 1: pulizia dei 10 servizi extra. Uso: python -I f4_servizi.py <ABS strand>
Scrive out/extra_servizi_puliti.csv e out/f4_servizi_log.json. Stesso confine (Comune + 200 m) e stesso aggancio alla rete (max 150 m) dei servizi essenziali."""
import sys, glob, json, re, datetime
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as shp_transform
from shapely import contains_xy
from scipy.spatial import cKDTree
S = sys.argv[1]; R = S + '/raw/comune_milano/'; O = S + '/out/'; ROOT = S + '/..'
LOG = {}; MAXSNAP = 150.0
tr = Transformer.from_crs(4326, 32632, always_xy=True)
def xy(lon, lat):
    a, b = tr.transform(np.asarray(lon, float), np.asarray(lat, float)); return np.asarray(a), np.asarray(b)
conf = shape(json.load(open(glob.glob(R + 'confine_comune/*.geojson')[0], encoding='utf-8'))['features'][0]['geometry'])
cbuf = shp_transform(lambda x, y, z=None: tr.transform(x, y), conf).buffer(200)
nd = np.load(O + 'grafo_pedonale_nodi.npz'); gtree = cKDTree(np.c_[nd['x'], nd['y']])
def fl(s): return pd.to_numeric(pd.Series(s).astype(str).str.replace(',', '.'), errors='coerce').values
def norm(s): return re.sub(r'[^a-z0-9]', '', str(s).lower())
STOP = ['teatro', 'cinema', 'museo', 'libreria', 'supermercato', 'piscina', 'ospedale', 'il', 'la', 'lo', 'di', 'del', 'della', 'dei']
def nkey(s):
    s = str(s).lower()
    for w in STOP: s = re.sub(r'\b' + w + r'\b', ' ', s)
    return norm(s)
def dedupe(df, R_, same_name=True):
    """greedy: scarta un punto se entro R_ metri di uno gia tenuto con lo stesso nome (o con nome vuoto da una parte)."""
    df = df.reset_index(drop=True); keep = []; kx = []; ky = []; kn = []
    for i, r in df.iterrows():
        k = nkey(r['nome']); dup = False
        for j in range(len(keep)):
            if np.hypot(kx[j] - r.x, ky[j] - r.y) < R_:
                if (not same_name) or k == '' or kn[j] == '' or k == kn[j] or k in kn[j] or kn[j] in k: dup = True; break
        if not dup: keep.append(i); kx.append(r.x); ky.append(r.y); kn.append(k)
    return df.loc[keep].reset_index(drop=True)
OUT = []; SUMM = {}
def finish(tipo, df, fonte, anno, righe_in, note='', dedup_m=0, same_name=True):
    """df con colonne nome, lon, lat, sub. Applica: coordinate valide, dentro il confine+200 m, dedupe, aggancio <=150 m."""
    L = {'righe_in': righe_in}
    df = df.copy(); df['lon'] = pd.to_numeric(df.lon, errors='coerce'); df['lat'] = pd.to_numeric(df.lat, errors='coerce')
    n0 = len(df); df = df.dropna(subset=['lon', 'lat']); L['senza_coordinate'] = n0 - len(df)
    df['x'], df['y'] = xy(df.lon.values, df.lat.values)
    ok = contains_xy(cbuf, df.x.values, df.y.values); L['fuori_confine_scartati'] = int((~ok).sum()); L['fuori_confine_esempi'] = df[~ok].nome.head(6).tolist(); df = df[ok]
    k = df.lon.round(6).astype(str) + '_' + df.lat.round(6).astype(str); n1 = len(df)
    df = df[~k.duplicated()]; L['duplicati_stesse_coordinate'] = n1 - len(df)
    if dedup_m:
        n2 = len(df); df = dedupe(df, dedup_m, same_name); L['duplicati_stesso_nome_vicini'] = n2 - len(df)
    d, i = gtree.query(np.c_[df.x.values, df.y.values]); df['node'] = i; df['snap_m'] = np.round(d, 1)
    L['oltre150m_dalla_rete_scartati'] = int((d > MAXSNAP).sum()); df = df[d <= MAXSNAP]
    L['finali'] = len(df); L['snap_mediana_m'] = round(float(np.median(df.snap_m)), 1) if len(df) else None
    L.update({'fonte': fonte, 'anno': anno, 'note': note}); SUMM[tipo] = L
    df['tipo'] = tipo; df['anno'] = anno; OUT.append(df[['tipo', 'sub', 'nome', 'lon', 'lat', 'x', 'y', 'node', 'snap_m', 'anno']])
    return df
OSMX = json.load(open(S + '/raw/osm_extra/overpass_extra_milano.json', encoding='utf-8'))
OSMT = OSMX['osm3s']['timestamp_osm_base']
def osm_rows(elems):
    rr = []
    for e in elems:
        t = e.get('tags', {}); lon = e.get('lon', e.get('center', {}).get('lon')); lat = e.get('lat', e.get('center', {}).get('lat'))
        rr.append(dict(osm='%s%d' % (e['type'][0], e['id']), nome=t.get('name', ''), lon=lon, lat=lat, t=t))
    return pd.DataFrame(rr)
O_ = osm_rows(OSMX['elements']); T_ = O_.t
def tag(k): return T_.map(lambda t: t.get(k))
def bad(t): return any(k in t for k in ['disused', 'abandoned', 'disused:tourism', 'was:tourism', 'disused:shop']) or t.get('access') in ('private', 'no')
LOG['osm_extra_timestamp'] = OSMT
# -------- cinema (filiera 14, sola lettura)
cn = pd.read_csv(ROOT + '/cinema-spariti/pulito/cinema.csv', dtype=str, encoding='utf-8-sig')
LOG['cinema_stato_2026'] = cn.stato_2026.value_counts().to_dict()
ca = cn[cn.stato_2026.str.startswith('attivo')]
d = finish('cinema', pd.DataFrame({'nome': ca.nome.values, 'lon': ca.lon.values, 'lat': ca.lat.values, 'sub': ''}), 'filiera 14 (cinema-spariti), cinema.csv, solo stato_2026 = attivo', 'OSM 29/10/2026', len(ca), 'solo i cinema aperti; esclusi 168 chiusi, 4 da verificare, 2 disused; sono 29, non 28', dedup_m=40, same_name=False)
# -------- teatri e musei
th = O_[(tag('amenity') == 'theatre').values].copy(); th['sub'] = 'teatro'
mu = O_[(tag('tourism') == 'museum').values].copy(); mu['sub'] = 'museo OSM'
LOG['osm_teatri_righe'] = len(th); LOG['osm_musei_righe'] = len(mu)
th = th[~th.t.map(bad)]; mu = mu[~mu.t.map(bad)]
LOG['osm_teatri_dopo_filtro_disused_private'] = len(th); LOG['osm_musei_dopo_filtro_disused_private'] = len(mu)
mc = pd.read_csv(glob.glob(S + '/raw/extra_comune/musei_card/*.csv')[0], sep=';', dtype=str, encoding='utf-8-sig')
mcd = pd.DataFrame({'nome': mc['nome museo'].str.strip().values, 'lon': fl(mc['LONG_X_4326']), 'lat': fl(mc['LAT_Y_4326']), 'sub': 'museo (Milano Musei Card)'})
bc = pd.read_csv(ROOT + '/beni-culturali/pulito/beni_milano.csv', dtype=str)
bc = bc[bc.ubicazione_precisione.isin(['sito', 'indirizzo']) & (bc.coord_in_comune == '1')]
pat = r'museo|pinacoteca|castello sforzesco|villa necchi|palazzo reale|galleria|casa museo|acquario|planetario'
bc = bc[(bc.luogo_attuale.fillna('') + ' ' + bc.istituzione.fillna('')).str.contains(pat, case=False, regex=True)]
bcg = bc.groupby(['luogo_attuale', 'lat', 'long']).size().reset_index(name='n')
bcd = pd.DataFrame({'nome': bcg.luogo_attuale.str.replace('�', "'").values, 'lon': fl(bcg['long']), 'lat': fl(bcg['lat']), 'sub': 'museo (beni culturali, filiera 3)'})
allm = pd.concat([th[['nome', 'lon', 'lat', 'sub']], mu[['nome', 'lon', 'lat', 'sub']], mcd, bcd], ignore_index=True)  # bcd: valutati e poi scartati (vedi sotto)
allm['x'], allm['y'] = xy(allm.lon.values, allm.lat.values)
allm = allm[contains_xy(cbuf, allm.x.values, allm.y.values)].reset_index(drop=True)
allm = dedupe(allm, 150, True)
isbc = allm['sub'].eq('museo (beni culturali, filiera 3)').values
LOG['beni_culturali_musei_candidati_dopo_dedupe_per_nome'] = int(isbc.sum())
tr_ = cKDTree(np.c_[allm.x.values[~isbc], allm.y.values[~isbc]])
dd, _ = tr_.query(np.c_[allm.x.values[isbc], allm.y.values[isbc]]); drop = np.where(isbc)[0][dd < 120]
LOG['beni_culturali_gia_coperti_entro_120m'] = int(len(drop))
allm = allm.drop(index=allm.index[drop]).reset_index(drop=True)
LOG['beni_culturali_scartati_perche_non_sono_musei_veri'] = allm[allm['sub'] == 'museo (beni culturali, filiera 3)'].nome.tolist()
allm = allm[allm['sub'] != 'museo (beni culturali, filiera 3)'].reset_index(drop=True)   # solo galleria commerciale, Palazzo Marino (sede del Comune) e Palazzo Reale con coordinate dubbie: non aggiungono nulla
d = finish('teatri_musei', allm[['nome', 'lon', 'lat', 'sub']], 'OpenStreetMap amenity=theatre + tourism=museum (Overpass, base 30/10/2026); Comune ds2727 Milano Musei Card (15 musei civici); filiera 3 (beni culturali): sedi non gia presenti', 'OSM 30/10/2026; Musei Card file 15/4/2024', len(th) + len(mu) + len(mcd), 'sedi dalla filiera 3 (beni culturali) valutate e scartate: i 4 candidati non coperti non sono musei veri; esclusi tag disused/abandoned/access=private; teatri e musei contano come un solo tipo')
SUMM['teatri_musei']['teatri'] = int((d['sub'] == 'teatro').sum()); SUMM['teatri_musei']['musei'] = int(d['sub'].str.startswith('museo').sum())
SUMM['teatri_musei']['musei_da_OSM'] = int((d['sub'] == 'museo OSM').sum()); SUMM['teatri_musei']['musei_da_Musei_Card_non_in_OSM'] = int((d['sub'] == 'museo (Milano Musei Card)').sum()); # -------- aree gioco (Comune ds724)
ag = pd.read_csv(glob.glob(S + '/raw/extra_comune/aree_gioco/*.csv')[0], sep=';', dtype=str)
LOG['aree_gioco_righe'] = len(ag); LOG['aree_gioco_obj_id_duplicati'] = int(ag.obj_id.duplicated().sum()); LOG['aree_gioco_codici'] = ag.descrizione_codice.value_counts().to_dict()
d = finish('giochi', pd.DataFrame({'nome': ag['località'].values, 'lon': fl(ag.LONG_X_4326), 'lat': fl(ag.LAT_Y_4326), 'sub': ''}), 'Comune di Milano ds724 aree gioco (CC BY)', 'file del 25/11/2024 (aree con data di inizio dal 2003 al 2024)', len(ag), 'una riga = un\'area gioco; dedupe solo per coordinate identiche')
pg = O_[(tag('leisure') == 'playground').values].copy(); pg['x'], pg['y'] = xy(pg.lon.values, pg.lat.values); pg = pg[contains_xy(cbuf, pg.x.values, pg.y.values)]
dd, _ = cKDTree(np.c_[d.x.values, d.y.values]).query(np.c_[pg.x.values, pg.y.values]); SUMM['giochi']['osm_playground_dentro_confine_per_confronto'] = len(pg); SUMM['giochi']['osm_playground_a_piu_di_100m_da_un_gioco_del_Comune'] = int((dd > 100).sum())
# -------- aree cani (Comune ds52 + OSM dog_park non gia presenti)
ac = pd.read_csv(glob.glob(S + '/raw/extra_comune/aree_cani/*.csv')[0], sep=';', dtype=str)
LOG['aree_cani_righe'] = len(ac)
dp = O_[(tag('leisure') == 'dog_park').values].copy(); dp = dp[~dp.t.map(lambda t: t.get('access') in ('private', 'no'))]
dpx, dpy = xy(dp.lon.values, dp.lat.values); acx, acy = xy(fl(ac.LONG_X_4326), fl(ac.LAT_Y_4326))
dd, _ = cKDTree(np.c_[acx[~np.isnan(acx)], acy[~np.isnan(acx)]]).query(np.c_[dpx, dpy]); new = dd > 100
d = finish('cani', pd.concat([pd.DataFrame({'nome': ac['località'].values, 'lon': fl(ac.LONG_X_4326), 'lat': fl(ac.LAT_Y_4326), 'sub': 'Comune'}),
                              pd.DataFrame({'nome': dp.nome.values[new], 'lon': dp.lon.values[new], 'lat': dp.lat.values[new], 'sub': 'OSM'})], ignore_index=True),
           'Comune di Milano ds52 aree fruizione cani (CC BY) + OpenStreetMap leisure=dog_park a piu di 100 m da un\'area del Comune', 'Comune: file del 21/11/2024; OSM 30/10/2026', len(ac) + int(new.sum()), 'OSM dog_park gia presenti nel dato del Comune (entro 100 m) non contati due volte')
SUMM['cani']['osm_dog_park_totali_nell_area'] = len(dp); SUMM['cani']['osm_aggiunti'] = int((d['sub'] == 'OSM').sum())
# -------- piscine (Comune ds32 + OSM)
cb = pd.read_csv(glob.glob(S + '/raw/extra_comune/centri_balneari/*.csv')[0], sep=';', dtype=str)
LOG['centri_balneari_tipologie'] = cb.TIPOLOGIA.value_counts().to_dict()
cbd = pd.DataFrame({'nome': cb.DENOMINAZIONE.values, 'lon': fl(cb.x), 'lat': fl(cb.y), 'sub': 'Comune'})
pool = O_[(tag('leisure') == 'swimming_pool').values | ((tag('leisure') == 'sports_centre').values & tag('sport').map(lambda s: 'swimming' in str(s)).values)].copy()
LOG['osm_piscine_righe_grezze'] = len(pool)
def okpool(r):
    t = r.t; a = t.get('access')
    if a in ('private', 'no'): return False
    if t.get('location') == 'rooftop' or t.get('building') in ('apartments', 'residential'): return False
    sw = 'swimming' in str(t.get('sport', '')) or re.search(r'piscin|nuoto|pool|natator|aquatic|acqua|balnear', r.nome, re.I)
    return bool(r.nome) and bool(sw)
pool = pool[pool.apply(okpool, axis=1)].copy(); pool['sub'] = 'OSM'
LOG['osm_piscine_pubbliche_con_nome_e_sport'] = len(pool)
pa = pd.concat([cbd, pool[['nome', 'lon', 'lat', 'sub']]], ignore_index=True)
d = finish('piscine', pa[['nome', 'lon', 'lat', 'sub']], 'Comune di Milano ds32 centri balneari / piscine (CC BY) + OpenStreetMap leisure=swimming_pool o sports_centre sport=swimming, con nome e senza access=private/no', 'Comune: file del 2019-2020 (vecchio); OSM 30/10/2026', len(cbd) + len(pool), 'un impianto con piu vasche conta una volta (stessa sede entro 200 m); il dato del Comune prevale su OSM', dedup_m=200, same_name=False)
SUMM['piscine']['da_Comune'] = int((d['sub'] == 'Comune').sum()); SUMM['piscine']['da_OSM'] = int((d['sub'] == 'OSM').sum())
# -------- metro
mt = pd.read_csv(ROOT + '/prezzi-case/pulito/fermate_metro.csv', dtype=str)
oggi = datetime.date(2026, 10, 30).isoformat(); mt['aperta'] = mt.data_apertura <= oggi
LOG['metro_righe'] = len(mt); LOG['metro_non_ancora_aperte'] = int((~mt.aperta).sum()); LOG['metro_data_apertura_max'] = mt.data_apertura.max()
mt = mt[mt.aperta]
d = finish('metro', pd.DataFrame({'nome': (mt.fermata + ' ' + mt.linea).values, 'lon': mt.lon.values, 'lat': mt.lat.values, 'sub': mt.linea.values}), 'filiera 5 (prezzi-case), fermate_metro.csv (Wikipedia; date di apertura), solo fermate aperte oggi', 'aperture 1964-2024', len(mt), 'una riga per fermata e linea; le stazioni di interscambio hanno un punto per linea')
cl = d.copy(); cl['nome'] = cl.nome.str.replace(r' M\d$', '', regex=True)
SUMM['metro']['stazioni_distinte_stesso_nome_entro_300m'] = int(len(dedupe(cl, 300, True)))
SUMM['metro']['per_linea'] = d['sub'].value_counts().to_dict()
# -------- BikeMi
bk = pd.read_csv(ROOT + '/bici-auto-mezzi/raw/bikemi/bikemi_stazioni.csv', sep=';', dtype=str)
LOG['bikemi_stati'] = bk.stato.value_counts().to_dict(); bk = bk[bk.stato == 'attiva']
d = finish('bikemi', pd.DataFrame({'nome': bk.nome.values, 'lon': fl(bk.LONG_X_4326), 'lat': fl(bk.LAT_Y_4326), 'sub': ''}), 'filiera 7 (bici-auto-mezzi), Comune ds65 stazioni BikeMi (file del 2022)', '2022 (installazioni 2008-2021): puo non coincidere con le stazioni di oggi', len(bk), 'file vecchio: la rete BikeMi cambia')
# -------- supermercati (OSM)
sm = O_[(tag('shop') == 'supermarket').values].copy(); LOG['osm_supermercati_righe'] = len(sm)
sm = sm[~sm.t.map(bad)]; sm['sub'] = ''
d = finish('supermercati', sm[['nome', 'lon', 'lat', 'sub']], 'OpenStreetMap shop=supermarket (Overpass, base 30/10/2026)', 'OSM 30/10/2026', len(sm), 'nodi e poligoni dello stesso negozio contati una volta (stessa insegna entro 60 m; senza insegna entro 60 m da altro); OSM puo mancare di qualche negozio', dedup_m=60)
# -------- ospedali
reg = pd.read_csv(glob.glob(S + '/raw/extra_regione/*.csv')[0], dtype=str)
reg = reg[reg.localita.str.upper().str.contains('MILANO')].copy()
reg['lat'] = pd.to_numeric(reg.coordinata_geografica_x); reg['lon'] = pd.to_numeric(reg.coordinata_geografica_y)   # TRAPPOLA: x e y scambiate (x = latitudine)
h6 = pd.read_csv(glob.glob(S + '/raw/extra_comune/ospedali_posti_letto/*.csv')[0], sep=';', dtype=str, encoding='utf-8-sig')
LOG['ospedali_ds683_anni'] = sorted(h6.Anno.unique()); h6 = h6[h6.Anno == h6.Anno.max()]
h6 = h6.groupby(['Codice struttura', 'Denominazione Struttura/Stabilimento', 'Descrizione tipo struttura', 'LONG_X_4326', 'LAT_Y_4326']).size().reset_index()
h6['code'] = h6['Codice struttura'].astype(int); reg['code'] = reg.codice_struttura_di_ricovero.str[:6].astype(int)
base = pd.DataFrame({'nome': h6['Denominazione Struttura/Stabilimento'].values, 'tipo683': h6['Descrizione tipo struttura'].values, 'lon': fl(h6.LONG_X_4326), 'lat': fl(h6.LAT_Y_4326), 'src': 'Comune ds683 (2023)', 'code': h6.code.values})
add = reg[~reg.code.isin(h6.code)]
reg_only = pd.DataFrame({'nome': add.descrizione_struttura_di.values, 'tipo683': '', 'lon': add.lon.values, 'lat': add.lat.values, 'src': 'Regione 6n7g-5p5e (2018)', 'code': add.code.values})
hs = pd.concat([base, reg_only], ignore_index=True)
LOG['ospedali_ds683_strutture_sede'] = len(base); LOG['ospedali_regione_milano_righe'] = len(reg); LOG['ospedali_regione_solo_non_in_ds683'] = len(reg_only)
LOG['ospedali_regione_trappole'] = ['colonne coordinata_geografica_x/y scambiate (x = latitudine)', 'IRCCS Ospedale Capitanio (030936-03) con coordinate 45,28 / 9,87 (fuori Milano)', "Istituto Ortopedico Galeazzi di via Galeazzi 4 (030946-00) e chiuso: l'ospedale e ora in via Belgioioso 173 (ds683 2023 e OSM)", 'Istituto Europeo di Oncologia (030941-00) a 9,1988/45,4441, sbagliato: in ds683 e OSM e a 9,206/45,414']
O_['x'], O_['y'] = xy(O_.lon.values, O_.lat.values)
ps = O_[T_.map(lambda t: (t.get('emergency') in ('yes', 'emergency_ward_entrance') or 'pronto soccorso' in str(t.get('name', '')).lower()) and (t.get('amenity') in ('hospital', 'clinic') or t.get('healthcare') in ('hospital', 'clinic')))]
hs['x'], hs['y'] = xy(hs.lon.values, hs.lat.values); okc = contains_xy(cbuf, hs.x.values, hs.y.values)
dps, _ = cKDTree(np.c_[ps.x.values, ps.y.values]).query(np.c_[hs.x.values, hs.y.values])
hs['ps'] = (dps < 300) & okc; hs['ps100'] = (dps < 100) & okc
EXC = r'CASA DI CURA|STOMATOLOG|NEMO|POLO CHIRURGICO|^SAN CARLO - MILANO'
hs['esc_nome'] = hs.nome.str.contains(EXC, case=False, regex=True)
hs['ospedale'] = ~hs.esc_nome & ((hs.tipo683 != 'Casa di cura privata accreditata') | hs.ps100)   # casa di cura accreditata contata solo se ha un pronto soccorso proprio in OSM (a meno di 100 m)
LOG['ospedali_escluse_come_case_di_cura_senza_PS'] = hs[~hs.ospedale].nome.tolist()
LOG['ospedali_lista_strutture'] = hs[['nome', 'src', 'ospedale', 'ps']].values.tolist()
hk = hs[hs.ospedale].copy(); hk['sub'] = np.where(hk.ps, 'con pronto soccorso', 'senza pronto soccorso (OSM)')
d = finish('ospedali', hk[['nome', 'lon', 'lat', 'sub']], 'Comune di Milano ds683 posti letto strutture ospedaliere (dato Regione, 2023, sedi con coordinate) + Regione Lombardia dati.lombardia.it 6n7g-5p5e georeferenziazione strutture (CC0, ultimo aggiornamento 2018) per le sedi mancanti; pronto soccorso da OpenStreetMap (emergency=yes)', 'ds683: dati al 2023 (file 1/9/2025); Regione: 2018; OSM 30/10/2026', len(hs), 'escluse case di cura private e centri specialistici senza pronto soccorso in OSM; sedi nello stesso edificio (entro 150 m) contano una volta; il punto e il centro del campus', dedup_m=150, same_name=False)
SUMM['ospedali']['con_pronto_soccorso'] = int(d['sub'].eq('con pronto soccorso').sum()); SUMM['ospedali']['escluse_case_di_cura'] = int((~hs.ospedale).sum())
# -------- librerie (OSM shop=books)
lb = json.load(open(S + '/raw/osm_extra/overpass_librerie_milano.json', encoding='utf-8'))
LOG['librerie_osm_timestamp'] = lb['osm3s']['timestamp_osm_base']
L_ = osm_rows(lb['elements']); n_all = len(L_)
L_ = L_[L_.t.map(lambda t: t.get('shop') == 'books')]; LOG['librerie_stationery_con_tag_books_esclusi'] = n_all - len(L_)
L_ = L_[~L_.t.map(bad)]
L_['sub'] = L_.t.map(lambda t: 'usati' if t.get('second_hand') in ('yes', 'only') else 'libri')
d = finish('librerie', L_[['nome', 'lon', 'lat', 'sub']], 'OpenStreetMap shop=books (Overpass, base 30/10/2026), anche usati', 'OSM 30/10/2026', len(L_), 'esclusi shop=stationery; stesse insegne entro 30 m o negozi senza nome entro 30 m contati una volta; OSM puo mancare di librerie', dedup_m=30)
SUMM['librerie']['usati'] = int((d['sub'] == 'usati').sum()); SUMM['librerie']['senza_nome'] = int((d.nome == '').sum()); SUMM['librerie']['nome_edicola_cartoleria'] = int(d.nome.str.contains('edicola|cartoleria', case=False).sum())
ALL = pd.concat(OUT, ignore_index=True)
ALL.to_csv(O + 'extra_servizi_puliti.csv', index=False, encoding='utf-8')
LOG['servizi'] = SUMM
json.dump(LOG, open(O + 'f4_servizi_log.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
for k, v in SUMM.items(): print(k, {a: b for a, b in v.items() if a not in ('fonte', 'note', 'anno')})
