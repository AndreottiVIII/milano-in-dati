"""Permettersi Milano - costruisce i dati della pagina docs/permettersi/ (affitto OMI / reddito, regola del 30%).

Uso:  python -I -X utf8 pagina.py <C:\\...\\milano-in-dati\\permettersi> <C:\\...\\milano-in-dati>
Si puo' rilanciare: le zone OMI di ogni civico per semestre sono in cache (permettersi/out/cache_zone_civici.csv.gz);
per ricalcolarle, cancellare la cache.

Entrate (tutte gia' su disco):
  quartieri-che-cambiano/out/civici_collegamenti.csv      civici residenziali con NIL, CAP, lon/lat (derivato dai civici del Comune, CC BY)
  quartieri-che-cambiano/out/collegamento_cap_nil.csv     quota di civici di ogni NIL in ogni CAP
  quartieri-che-cambiano/out/collegamento_omi_nil.csv     quota di civici di ogni NIL in ogni zona OMI (2026/1)
  prezzi-case/raw/geopoi/F205_<anno><sem>.json            perimetri zone OMI per semestre
  prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv  quotazioni OMI (stato prevalente) per zona e semestre
  redditi/pulito/mef_cap_2011_2024.csv, mef_comuni_2000_2024.csv    redditi MEF per CAP e per comune (classi)
  prezzi-case/pulito/foi_annuale.csv                      indice dei prezzi ISTAT (FOI)
  affitti-brevi/pulito/confronto_affitto_notti_zone.csv   notti Airbnb per eguagliare l'affitto OMI di 60 mq, per zona
  docs/alberi/data/nil.geojson                            confini dei quartieri (semplificati) e residenti 2024
Uscite: docs/permettersi/data/ (dati.json, nil.geojson, riepilogo.json, csv) e permettersi/out/.
"""
import sys, os, json, gzip
from functools import reduce
import numpy as np
import pandas as pd

PERM = sys.argv[1]
BASE = sys.argv[2]
OUT = os.path.join(PERM, 'out')
DOCS = os.path.join(BASE, 'docs', 'permettersi', 'data')
os.makedirs(OUT, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)
LOG = {}

ANNI_ALL = list(range(2011, 2025))                     # affitti OMI
ANNI_CAP = [2011, 2015, 2019, 2020, 2021, 2022, 2023, 2024]   # redditi per CAP (MEF: solo questi anni)
SOGLIA = 0.30
MQ = [40, 60, 80]


def P(*a):
    return os.path.join(BASE, *a)


# ---------------------------------------------------------------- 1. zone OMI di ogni civico, per semestre
civ = pd.read_csv(P('quartieri-che-cambiano', 'out', 'civici_collegamenti.csv'),
                  usecols=['IDMASTER', 'RESIDENZIALE', 'ID_NIL', 'lon', 'lat', 'CAP'])
civ = civ[(civ.RESIDENZIALE == 1) & civ.ID_NIL.notna()].reset_index(drop=True)
LOG['civici_residenziali'] = int(len(civ))
SEMS = [(a, s) for a in ANNI_ALL for s in (1, 2)]
cache = os.path.join(OUT, 'cache_zone_civici.csv.gz')
if os.path.exists(cache):
    zc = pd.read_csv(cache, dtype=str)
    assert len(zc) == len(civ)
else:
    from pyproj import Transformer
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree
    from shapely.validation import make_valid
    import shapely
    TR = Transformer.from_crs(4326, 32632, always_xy=True)
    x, y = TR.transform(civ.lon.values, civ.lat.values)
    pts = shapely.points(x, y)

    def geom_feature(feat):
        ps = []
        for ring in feat['geometry']['coordinates']:
            a = np.array(ring, dtype=float)
            xx, yy = TR.transform(a[:, 0], a[:, 1])
            ps.append(make_valid(Polygon(np.column_stack([xx, yy]))))
        return reduce(lambda p, q: p.symmetric_difference(q), ps)   # regola pari/dispari degli anelli

    zc = pd.DataFrame({'IDMASTER': civ.IDMASTER.astype(str)})
    for a, s in SEMS:
        d = json.load(open(P('prezzi-case', 'raw', 'geopoi', 'F205_%d%d.json' % (a, s)), encoding='utf-8'))
        z = {}
        for f in d['dat']['features']:
            cod = f['properties']['zona']
            g = geom_feature(f)
            z[cod] = z[cod].union(g) if cod in z else g
        codici = list(z.keys())
        tree = STRtree([z[c] for c in codici])
        pi, gi = tree.query(pts, predicate='within')
        res = np.full(len(pts), None, dtype=object)
        for p_, g_ in zip(pi, gi):
            if res[p_] is None:
                res[p_] = codici[g_]
        zc['%d-S%d' % (a, s)] = res
        print('zone', a, s, 'senza zona:', int(pd.isna(res).sum()), flush=True)
    zc.to_csv(cache, index=False, compression='gzip')

# ---------------------------------------------------------------- 2. affitti OMI per civico, anno, NIL
q = pd.read_csv(P('prezzi-case', 'pulito', 'prezzi_zona_semestre_prevalente.csv'))
q = q[q.prevalente == True]
TIP = {'civ': 'Abitazioni civili', 'eco': 'Abitazioni di tipo economico'}
CAMPI = {'c': 'loc_centro', 'lo': 'loc_min', 'hi': 'loc_max'}
aff = {}      # (tip, campo) -> DataFrame NIL x anno
nil_ids = sorted(civ.ID_NIL.astype(int).unique())
for tk, tn in TIP.items():
    qq = q[q.tipologia == tn]
    assert qq.groupby(['semestre', 'zona']).size().max() == 1
    for ck, cn in CAMPI.items():
        per_sem = {}
        for a, s in SEMS:
            sem = '%d-S%d' % (a, s)
            ser = qq[qq.semestre == sem].set_index('zona')[cn]
            per_sem[sem] = zc[sem].map(ser).astype(float).values
        cols = {}
        for a in ANNI_ALL:
            v = np.nanmean(np.vstack([per_sem['%d-S1' % a], per_sem['%d-S2' % a]]), axis=0)
            cols[a] = v
        df = pd.DataFrame(cols)
        df['ID_NIL'] = civ.ID_NIL.astype(int).values
        aff[(tk, ck)] = df.groupby('ID_NIL').mean()
        # civici senza valore
        LOG['civici_senza_valore_%s_%s' % (tk, ck)] = int(df[ANNI_ALL].isna().all(axis=1).sum())
# copertura
LOG['nil_con_affitto_civ'] = int(aff[('civ', 'c')].notna().all(axis=1).sum())

# ---------------------------------------------------------------- 3. redditi: percentili da classi
EDGES = [0, 10000, 15000, 26000, 55000, 75000, 120000]   # estremi inferiori delle classi 1..7 (la classe <=0 e' unita alla 1)
NAMES = ['cl1_0_10k', 'cl2_10_15k', 'cl3_15_26k', 'cl4_26_55k', 'cl5_55_75k', 'cl6_75_120k', 'cl7_oltre120k']
TOP = 120000.0


def quantili(n, e, qs):
    """n, e: conteggi e importi delle 7 classi (la classe <=0 e' gia' sommata alla prima).
    Dentro ogni classe la densita' e' lineare e ha la media che risulta da importo/conteggio
    (se la media e' fuori dai limiti possibili la densita' si riduce a un trapezio al limite).
    Ritorna i quantili richiesti (euro) e la quota di contribuenti per classe."""
    n = np.asarray(n, float)
    tot = n.sum()
    cum = np.concatenate([[0], np.cumsum(n)]) / tot
    out = []
    for qv in qs:
        k = int(np.searchsorted(cum, qv, side='right') - 1)
        k = min(max(k, 0), 6)
        if k == 6:
            raise ValueError('quantile nella classe aperta')
        x0, x1 = EDGES[k], EDGES[k + 1]
        w = x1 - x0
        m = e[k] / n[k] if (n[k] > 0 and not np.isnan(e[k])) else (x0 + x1) / 2
        tm = (m - x0) / w
        c = float(np.clip(12 * (tm - .5), -1.98, 1.98))
        r = (qv - cum[k]) / (cum[k + 1] - cum[k])        # frazione di massa della classe
        if abs(c) < 1e-9:
            t = r
        else:
            t = (-(1 - c / 2) + np.sqrt((1 - c / 2) ** 2 + 2 * c * r)) / c
        out.append(x0 + t * w)
    return out


def classi_da_riga(row):
    ns, es = [], []
    for j, nm in enumerate(NAMES):
        nn = row[nm + '_n']
        ee = row[nm + '_eur']
        ns.append(nn)
        es.append(ee)
    n0 = row['cl0_le0_n'] if not pd.isna(row['cl0_le0_n']) else 0
    e0 = row['cl0_le0_eur'] if not pd.isna(row['cl0_le0_eur']) else 0
    ns[0] = ns[0] + n0
    es[0] = es[0] + e0
    # classe oltre 120k mancante (CAP 2023-24): conteggio = reddito_complessivo_n - somma delle altre classi
    if pd.isna(ns[6]):
        rc = row.get('reddito_complessivo_n')
        if pd.isna(rc):
            ns[6] = 0.0
        else:
            ns[6] = max(0.0, rc - sum(ns[:6]))
        es[6] = np.nan
    return ns, es


com = pd.read_csv(P('redditi', 'pulito', 'mef_comuni_2000_2024.csv'), low_memory=False, dtype={'istat': str, 'catastale': str})
com = com[com.catastale == 'F205'].set_index('anno')
city = {}
for a in ANNI_ALL:
    ns, es = classi_da_riga(com.loc[a])
    p10, p25, p50, p75 = quantili(ns, es, [.10, .25, .50, .75])
    city[a] = {'p10': p10, 'p25': p25, 'p50': p50, 'p75': p75, 'contribuenti_con_classe': float(sum(ns)),
               'contribuenti': float(com.loc[a, 'contribuenti'])}
# confronto con il valore usato dalla pagina costo-vita (interpolazione uniforme)
cv = pd.read_csv(P('costo-vita', 'pulito', 'affitto_vs_reddito.csv'), sep=';').set_index('anno')
LOG['mediana_citta_questo_lavoro_vs_costo_vita'] = {str(a): [round(city[a]['p50']), round(float(cv.loc[a, 'reddito_complessivo_mediano_mese_interpolato']) * 12)] for a in (2011, 2015, 2019, 2024)}

# reddito per NIL: miscela delle distribuzioni dei CAP, con pesi = quota dei civici del NIL in ogni CAP
cap = pd.read_csv(P('redditi', 'pulito', 'mef_cap_2011_2024.csv'), low_memory=False, dtype={'cap': str, 'catastale': str})
cap = cap[cap.catastale == 'F205']
cn = pd.read_csv(P('quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv'), dtype={'CAP': str})
cn['ID_NIL'] = cn.ID_NIL.astype(int)
capd = {}      # (anno, cap) -> (quote per classe, importo medio per classe)
for _, r in cap.iterrows():
    ns, es = classi_da_riga(r)
    capd[(int(r.anno), r.cap)] = (np.array(ns, float), np.array(es, float))
red = {}
cap_mancanti = set()
for a in ANNI_CAP:
    for nid, g in cn.groupby('ID_NIL'):
        wsum = 0.0
        sh = np.zeros(7)
        em = np.zeros(7)     # importo per contribuente (somma pesata) per classe
        for _, r in g.iterrows():
            k = (a, r.CAP)
            if k not in capd:
                cap_mancanti.add(r.CAP)
                continue
            ns, es = capd[k]
            s = ns / ns.sum()
            sh += r.quota_nil * s
            # importo medio di classe; se manca (oltre 120k) niente
            with np.errstate(invalid='ignore', divide='ignore'):
                mm = np.where(ns > 0, es / ns, np.nan)
            em += r.quota_nil * s * np.nan_to_num(mm, nan=0.0)
            wsum += r.quota_nil
        if wsum < 0.5:
            continue
        sh /= sh.sum()
        # n_ = quota di contribuenti per classe; e_ = importo per classe (stesse unita': e_/n_ = importo medio di classe)
        n_ = sh
        e_ = np.where(em > 0, em, np.nan)
        p25, p50 = quantili(n_ * 1e6, e_ * 1e6, [.25, .50])
        red[(nid, a)] = {'p25': p25, 'p50': p50, 'quota_sotto_15k': float(sh[0] + sh[1]), 'wsum': wsum}
LOG['cap_non_trovati'] = sorted(cap_mancanti)

# ---------------------------------------------------------------- 4. FOI


# ---------------------------------------------------------------- 5. funzione di ripartizione dei contribuenti (citta')
def cdf_citta(a, x):
    """Quota di contribuenti (con reddito in classe) di Milano nell'anno a con reddito complessivo <= x (euro/anno)."""
    ns, es = CLS[a]
    ns = np.asarray(ns, float)
    tot = ns.sum()
    cum = np.concatenate([[0], np.cumsum(ns)]) / tot
    if x <= 0:
        return 0.0
    if x >= TOP:
        m7 = es[6] / ns[6]
        al = m7 / (m7 - TOP)               # coda di Pareto con la media della classe oltre 120k
        return float(cum[6] + (1 - cum[6]) * (1 - (TOP / x) ** al))
    k = max(i for i in range(7) if EDGES[i] <= x)
    x0, x1 = EDGES[k], EDGES[k + 1]
    w = x1 - x0
    m = es[k] / ns[k]
    c = float(np.clip(12 * ((m - x0) / w - .5), -1.98, 1.98))
    t = (x - x0) / w
    F = t + c * (t * t / 2 - t / 2)
    return float(cum[k] + (cum[k + 1] - cum[k]) * F)


CLS = {}
for a in ANNI_ALL:
    CLS[a] = classi_da_riga(com.loc[a])

# ---------------------------------------------------------------- 6. nomi, residenti, Airbnb, CAP instabili
g = json.load(open(P('docs', 'alberi', 'data', 'nil.geojson'), encoding='utf-8'))
info = {f['properties']['i']: {'n': f['properties']['n'], 'ab': f['properties']['ab']} for f in g['features']}
feat_out = [{'type': 'Feature', 'properties': {'i': f['properties']['i'], 'n': f['properties']['n']}, 'geometry': f['geometry']} for f in g['features']]
json.dump({'type': 'FeatureCollection', 'features': feat_out}, open(os.path.join(DOCS, 'nil.geojson'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

instab = cn[cn.CAP.isin(['20121', '20122'])].groupby('ID_NIL').quota_nil.sum()
cap_dom = cn.sort_values('quota_nil', ascending=False).groupby('ID_NIL').head(1).set_index('ID_NIL')

az = pd.read_csv(P('affitti-brevi', 'pulito', 'confronto_affitto_notti_zone.csv')).set_index('zona')
zn = pd.read_csv(P('quartieri-che-cambiano', 'out', 'collegamento_omi_nil.csv'))
zn['ID_NIL'] = zn.ID_NIL.astype(int)
zn['notti'] = zn.zona_2026_1.map(az.notti_al_mese_per_affitto_60mq)
notti = {}
for nid_, d_ in zn.dropna(subset=['notti']).groupby('ID_NIL'):
    notti[int(nid_)] = float((d_.notti * d_.quota_nil).sum() / d_.quota_nil.sum())

foi = pd.read_csv(P('prezzi-case', 'pulito', 'foi_annuale.csv')).set_index('anno').indice_raccordato_2025_100
FOI = {a: float(foi[a]) for a in ANNI_ALL}

# ---------------------------------------------------------------- 7. tabelle
SOGLIA_AB = 2000      # quartieri con almeno 2.000 residenti (2024) entrano nei conteggi
rows = []
nil_list = []
for nid in nil_ids:
    ai = info[nid]
    c_ = aff[('civ', 'c')].loc[nid]
    lo_ = aff[('civ', 'lo')].loc[nid]
    hi_ = aff[('civ', 'hi')].loc[nid]
    e_ = aff[('eco', 'c')].loc[nid]
    ok = {}
    for mq in MQ:
        arr = []
        for a in ANNI_ALL:
            v = c_[a]
            if pd.isna(v):
                arr.append(None)
                continue
            need = v * mq * 12 / SOGLIA
            arr.append(round(100 * (1 - cdf_citta(a, need)), 1))
        ok[str(mq)] = arr
    d = {
        'i': int(nid), 'n': ai['n'], 'ab': int(ai['ab']),
        'aff': [None if pd.isna(c_[a]) else round(float(c_[a]), 2) for a in ANNI_ALL],
        'lo': [None if pd.isna(lo_[a]) else round(float(lo_[a]), 2) for a in ANNI_ALL],
        'hi': [None if pd.isna(hi_[a]) else round(float(hi_[a]), 2) for a in ANNI_ALL],
        'eco': [None if pd.isna(e_[a]) else round(float(e_[a]), 2) for a in ANNI_ALL],
        'p50': [round(red[(nid, a)]['p50']) if (nid, a) in red else None for a in ANNI_CAP],
        'p25': [round(red[(nid, a)]['p25']) if (nid, a) in red else None for a in ANNI_CAP],
        'cap': cap_dom.loc[nid, 'CAP'], 'cap_q': round(float(cap_dom.loc[nid, 'quota_nil']), 2),
        'instab': bool(instab.get(nid, 0) >= 0.5),
        'notti': None if nid not in notti else round(notti[nid], 1),
        'ok': ok,
    }
    nil_list.append(d)
    for ia, a in enumerate(ANNI_ALL):
        r = {'id_nil': nid, 'nil': ai['n'], 'residenti_2024': ai['ab'], 'anno': a,
             'affitto_civili_eur_mq_mese': d['aff'][ia], 'affitto_min': d['lo'][ia], 'affitto_max': d['hi'][ia],
             'affitto_economiche_eur_mq_mese': d['eco'][ia]}
        if a in ANNI_CAP:
            j = ANNI_CAP.index(a)
            r['reddito_mediano_contribuente_nil_eur'] = d['p50'][j]
            r['reddito_p25_contribuente_nil_eur'] = d['p25'][j]
        for mq in MQ:
            if d['aff'][ia] is not None:
                rent = d['aff'][ia] * mq
                r['affitto_%dmq_mese_eur' % mq] = round(rent)
                r['quota_su_mediana_citta_%dmq' % mq] = round(rent * 12 / city[a]['p50'], 3)
                r['quota_su_p25_citta_%dmq' % mq] = round(rent * 12 / city[a]['p25'], 3)
                if a in ANNI_CAP and d['p50'][ANNI_CAP.index(a)]:
                    r['quota_su_mediana_nil_%dmq' % mq] = round(rent * 12 / d['p50'][ANNI_CAP.index(a)], 3)
                r['contribuenti_che_stanno_nel_30pct_%dmq_pct' % mq] = d['ok'][str(mq)][ia]
        rows.append(r)
tab = pd.DataFrame(rows)
tab.to_csv(os.path.join(DOCS, 'nil_affitti_redditi.csv'), index=False, encoding='utf-8')

# ---------------------------------------------------------------- 8. citta'
cit = []
affciv = aff[('civ', 'c')].reindex(civ.ID_NIL.astype(int).values)
for a in ANNI_ALL:
    ca = float(affciv[a].mean())          # media su tutti i civici residenziali (pesa i quartieri per le case)
    cit.append({'anno': a, 'p25': round(city[a]['p25']), 'p50': round(city[a]['p50']), 'p75': round(city[a]['p75']),
                'affitto_mq_media_civici': round(ca, 2),
                'quota_p50_40': round(ca * 40 * 12 / city[a]['p50'], 3), 'quota_p50_60': round(ca * 60 * 12 / city[a]['p50'], 3),
                'quota_p50_80': round(ca * 80 * 12 / city[a]['p50'], 3),
                'quota_p25_40': round(ca * 40 * 12 / city[a]['p25'], 3), 'quota_p25_60': round(ca * 60 * 12 / city[a]['p25'], 3),
                'foi': round(FOI[a], 3)})
citd = pd.DataFrame(cit)
citd.to_csv(os.path.join(DOCS, 'citta_percentili_affitto.csv'), index=False)

# ---------------------------------------------------------------- 9. sintesi (numeri del testo)
byid = {n['i']: n for n in nil_list}
ab_ok = {n['i'] for n in nil_list if n['ab'] >= SOGLIA_AB and n['aff'][ANNI_ALL.index(2015)] is not None}
LOG['nil_nei_conteggi'] = len(ab_ok)
IX = {a: ANNI_ALL.index(a) for a in ANNI_ALL}


def conta(ids, f):
    return [i for i in ids if f(byid[i])]


def quota(n, a, mq, inc):
    return n['aff'][IX[a]] * mq * 12 / inc


S = {'soglia_residenti': SOGLIA_AB, 'n_nil': len(ab_ok), 'persona': {}, 'locale': {}}
for pk in ('p25', 'p50', 'p75'):
    S['persona'][pk] = {}
    for mq in MQ:
        o = {}
        for a in (2011, 2015, 2019, 2022, 2024):
            ids = conta(ab_ok, lambda n: n['aff'][IX[a]] is not None and quota(n, a, mq, city[a][pk]) <= SOGLIA)
            o[str(a)] = len(ids)
        in15 = set(conta(ab_ok, lambda n: quota(n, 2015, mq, city[2015][pk]) <= SOGLIA))
        in24 = set(conta(ab_ok, lambda n: quota(n, 2024, mq, city[2024][pk]) <= SOGLIA))
        o['usciti_2015_2024'] = sorted(byid[i]['n'] for i in in15 - in24)
        o['entrati_2015_2024'] = sorted(byid[i]['n'] for i in in24 - in15)
        o['restano_2024'] = sorted(byid[i]['n'] for i in in24)
        o['reddito_eur'] = {str(a): round(city[a][pk]) for a in (2015, 2024)}
        S['persona'][pk][str(mq)] = o
ok_loc = {i for i in ab_ok if not byid[i]['instab']}
S['locale']['n_nil'] = len(ok_loc)
for mq in MQ:
    o = {}
    for a in ANNI_CAP:
        j = ANNI_CAP.index(a)
        o[str(a)] = len(conta(ok_loc, lambda n: quota(n, a, mq, n['p50'][j]) <= SOGLIA))
    in15 = set(conta(ok_loc, lambda n: quota(n, 2015, mq, n['p50'][1]) <= SOGLIA))
    in24 = set(conta(ok_loc, lambda n: quota(n, 2024, mq, n['p50'][7]) <= SOGLIA))
    o['usciti_2015_2024'] = sorted(byid[i]['n'] for i in in15 - in24)
    o['restano_2024'] = sorted(byid[i]['n'] for i in in24)
    S['locale'][str(mq)] = o
nec = {}
for a in (2015, 2024):
    arr = [(byid[i]['n'], byid[i]['aff'][IX[a]] * 60 * 12 / SOGLIA) for i in ab_ok]
    arr.sort(key=lambda t: t[1])
    med = float(np.median([t[1] for t in arr]))
    nec[str(a)] = {'min': [arr[0][0], round(arr[0][1])], 'max': [arr[-1][0], round(arr[-1][1])], 'mediana': round(med),
                   'quota_contribuenti_sopra_mediana_nil': round(100 * (1 - cdf_citta(a, med)), 1)}
S['reddito_necessario_60mq'] = nec
S['citta'] = {str(r['anno']): r for r in cit if r['anno'] in (2011, 2015, 2019, 2022, 2024)}
S['rent_growth_nil_2015_2024_pct'] = {
    'mediana': round(float(np.median([100 * (byid[i]['aff'][-1] / byid[i]['aff'][IX[2015]] - 1) for i in ab_ok])), 1)}
S['reddito_mediano_crescita_2015_2024_pct'] = round(100 * (city[2024]['p50'] / city[2015]['p50'] - 1), 1)
S['reddito_p25_crescita_2015_2024_pct'] = round(100 * (city[2024]['p25'] / city[2015]['p25'] - 1), 1)
S['affitto_civici_crescita_2015_2022_pct'] = round(100 * (cit[IX[2022]]['affitto_mq_media_civici'] / cit[IX[2015]]['affitto_mq_media_civici'] - 1), 1)
S['affitto_civici_crescita_2022_2024_pct'] = round(100 * (cit[-1]['affitto_mq_media_civici'] / cit[IX[2022]]['affitto_mq_media_civici'] - 1), 1)
S['affitto_civici_crescita_2015_2024_pct'] = round(100 * (cit[-1]['affitto_mq_media_civici'] / cit[IX[2015]]['affitto_mq_media_civici'] - 1), 1)
S['foi_crescita_2015_2024_pct'] = round(100 * (FOI[2024] / FOI[2015] - 1), 1)
S['nil_instabili'] = sorted(byid[i]['n'] for i in byid if byid[i]['instab'])

cls_out = {}
for a in ANNI_ALL:
    ns_, es_ = CLS[a]
    tot_ = float(sum(ns_))
    cls_out[str(a)] = {'sh': [round(float(n_) / tot_, 5) for n_ in ns_], 'm': [round(float(e_ / n_)) for n_, e_ in zip(ns_, es_)]}
nil_json = [{k: v for k, v in n.items() if k != 'ok'} for n in nil_list]
# stipendi tabellari ufficiali (ARAN, testi definitivi dei CCNL 2022-2024): euro per 12 mensilita', si aggiunge la 13a
ARAN_SAN = 'https://www.aranagenzia.it/wp-content/uploads/2025/10/2025.10.27-CCNL-comparto-definitivo-3.pdf'
ARAN_IR = 'https://www.aranagenzia.it/wp-content/uploads/2025/12/2025_12_23_COMP-IR_2022-2024.pdf'
PROF_RAW = [
    ('inf', 'Infermiere/a, Area dei professionisti della salute e dei funzionari', 24918.93, 'CCNL Comparto Sanità 2022-2024 (firmato il 27/10/2025), Tabella 2a «Nuova retribuzione tabellare annua, dal 1.1.2024», pagina 106 del testo (107 del PDF)', ARAN_SAN),
    ('dp0', 'Docente scuola primaria, 0-8 anni di servizio', 22420.48, 'CCNL Istruzione e Ricerca 2022-2024 (firmato il 23/12/2025), Tabella A2 Scuola «segue», pagina 49 del testo (51 del PDF)', ARAN_IR),
    ('dp15', 'Docente scuola primaria, 15-20 anni di servizio', 26873.83, 'stessa tabella (Tabella A2 Scuola, pagina 49)', ARAN_IR),
    ('ds0', 'Docente laureato scuola secondaria di II grado, 0-8 anni', 24268.28, 'stessa tabella (Tabella A2 Scuola, pagina 49)', ARAN_IR),
    ('ds15', 'Docente laureato scuola secondaria di II grado, 15-20 anni', 30341.15, 'stessa tabella (Tabella A2 Scuola, pagina 49)', ARAN_IR),
]
IND_SPEC_INF = 80.73      # Tabella 3 del CCNL Sanita': indennita' di specificita' infermieristica, euro/mese per 12 mesi, dal 1/1/2024
prof = []
for k_, nome_, t12, fonte_, url_ in PROF_RAW:
    lordo = round(t12 * 13 / 12, 2)
    o_ = {'k': k_, 'nome': nome_, 'tabellare_12': t12, 'lordo': lordo, 'fonte': fonte_, 'url': url_}
    cnt = {}
    for mq in MQ:
        cnt[str(mq)] = len([i for i in ab_ok if byid[i]['aff'][IX[2024]] is not None and byid[i]['aff'][IX[2024]] * mq * 12 / lordo <= SOGLIA])
    o_['nil_dentro_30_2024'] = cnt
    prof.append(o_)
S['professioni'] = {'elenco': prof, 'indennita_specificita_infermieristica_mese': IND_SPEC_INF}

dati = {'anni': ANNI_ALL, 'anni_cap': ANNI_CAP, 'mq': MQ, 'soglia': SOGLIA, 'foi': {str(a): round(FOI[a], 3) for a in ANNI_ALL},
        'citta': cit, 'professioni': prof, 'cls': cls_out, 'edges': EDGES, 'nil': nil_json, 'soglia_residenti': SOGLIA_AB}
json.dump(dati, open(os.path.join(DOCS, 'dati.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
S['log'] = LOG
json.dump(S, open(os.path.join(DOCS, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(S, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', os.path.getsize(os.path.join(DOCS, 'dati.json')))
