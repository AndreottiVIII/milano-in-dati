"""Stessa domanda a livello di NIL (quartieri): prezzo OMI per NIL da sovrapposizione di aree con le zone OMI 2026/1.
Uso: python -I -X utf8 05_nil.py <ABS milano-in-dati> <ABS case-servizi-reddito>
Entrate (sola lettura): citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson (NIL, EPSG:4326, campi ID_NIL, NIL),
  out/zone_geom_utm.geojson, out/zone_tabella.csv, out/civici_zone.csv, citta-15-minuti/out/nil_punteggi.csv.
Uscite: out/nil_tabella.csv, out/nil_risultati.json
Due modi di dare un prezzo al NIL (tutti e due usano lo STESSO prezzo OMI di zona, che e' una STIMA dell'Agenzia delle Entrate):
  - per area: media dei prezzi delle zone pesata con l'area di sovrapposizione (esclusa la zona rurale R2, senza prezzo);
  - per residenti: media dei prezzi della zona di ogni civico residenziale, pesata con i residenti stimati.
Unita' di analisi: NIL con almeno 30 civici e 1.000 residenti (come la classifica del filone 9), senza Cascina Merlata (dati dei civici incompleti).
Attenzione: i NIL non sono 88 osservazioni indipendenti. I prezzi vengono da 42 zone: NIL nella stessa zona hanno lo stesso prezzo.
Gli intervalli sono quindi un bootstrap a grappoli: si ricampionano le zone OMI (zona dominante del NIL), non i singoli NIL.
"""
import sys, json
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
from scipy import stats

def P(a): return a.replace(chr(92), '/').rstrip('/')
R, O = P(sys.argv[1]), P(sys.argv[2])
LOG = {}
tr = Transformer.from_crs(4326, 32632, always_xy=True)
DUOMO = tr.transform(9.19192, 45.46427)

nj = json.load(open(R + '/citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson', encoding='utf-8'))
nil = {}
for f in nj['features']:
    g = transform(tr.transform, shape(f['geometry']))
    if not g.is_valid:
        g = g.buffer(0)
    nil[int(f['properties']['ID_NIL'])] = (f['properties']['NIL'], g)
zj = json.load(open(O + '/out/zone_geom_utm.geojson'))
zone = {f['properties']['zona']: shape(f['geometry']) for f in zj['features']}
zt = pd.read_csv(O + '/out/zone_tabella.csv').set_index('zona')
price = zt.prezzo_eur_m2.to_dict()
LOG['n_nil'] = len(nil)
LOG['area_nil_km2'] = round(sum(g.area for _, g in nil.values()) / 1e6, 2)

rows = []
for i, (nome, g) in nil.items():
    tot = 0.0; num = 0.0; num_r = 0.0; area_p = 0.0; ov = {}
    for z, zg in zone.items():
        a = g.intersection(zg).area
        if a <= 0:
            continue
        ov[z] = a
        tot += a
        if not np.isnan(price.get(z, np.nan)):
            num += a * price[z]
            num_r += a * zt.loc[z, 'affitto_eur_m2_mese']
            area_p += a
    dom = max(ov, key=ov.get)
    cen = g.centroid
    rows.append(dict(ID_NIL=i, NIL=nome, area_km2=g.area / 1e6, prezzo_per_area=num / area_p if area_p else np.nan,
                     quota_area_con_prezzo=area_p / g.area, zona_dominante=dom, quota_zona_dominante=ov[dom] / tot,
                     n_zone_toccate_ge10pct=sum(1 for v in ov.values() if v / tot >= 0.10),
                     dist_duomo_centroide_m=float(np.hypot(cen.x - DUOMO[0], cen.y - DUOMO[1]))))
N = pd.DataFrame(rows)

c = pd.read_csv(O + '/out/civici_zone.csv')
c['prezzo'] = c.zona.map(price)
def wavg(g, col):
    m = g[col].notna() & (g.peso > 0)
    return float((g.loc[m, col] * g.loc[m, 'peso']).sum() / g.loc[m, 'peso'].sum()) if m.any() else np.nan
cr = []
for i, g in c.groupby('ID_NIL'):
    cr.append(dict(ID_NIL=int(i), n_civici=len(g), n_civici_res=int((g.RESIDENZIALE == 1).sum()), residenti=float(g.peso.sum()),
                   S10=wavg(g, 'punteggio'), S20=wavg(g, 'punteggio_20'), SX=wavg(g, 'punteggio_extra'),
                   prezzo_per_residenti=wavg(g, 'prezzo'), reddito=wavg(g, 'imponibile_medio_2024'),
                   quota_res_in_R2=float(g.loc[g.zona == 'R2', 'peso'].sum() / g.peso.sum()) if g.peso.sum() > 0 else np.nan))
N = N.merge(pd.DataFrame(cr), on='ID_NIL', how='left')
N['ammesso'] = (N.n_civici >= 30) & (N.residenti >= 1000) & (N.NIL.str.upper() != 'CASCINA MERLATA') & N.prezzo_per_area.notna() & N.prezzo_per_residenti.notna()
N.to_csv(O + '/out/nil_tabella.csv', index=False, float_format='%.4f')
A = N[N.ammesso].copy()
LOG['nil_ammessi'] = len(A)
LOG['nil_esclusi'] = N[~N.ammesso][['ID_NIL', 'NIL', 'n_civici', 'residenti']].round(0).to_dict('records')
LOG['quota_nil_con_zona_dominante_ge80pct'] = round(float((A.quota_zona_dominante >= 0.8).mean()), 3)
LOG['quota_nil_che_toccano_2_o_piu_zone_ge10pct'] = round(float((A.n_zone_toccate_ge10pct >= 2).mean()), 3)
LOG['zone_OMI_distinte_come_dominanti'] = int(A.zona_dominante.nunique())
LOG['spearman_prezzo_area_vs_residenti'] = round(float(stats.spearmanr(A.prezzo_per_area, A.prezzo_per_residenti).statistic), 3)
LOG['scarto_relativo_mediano_area_vs_residenti'] = round(float(((A.prezzo_per_area - A.prezzo_per_residenti).abs() / A.prezzo_per_residenti).median()), 3)
LOG['scarto_relativo_max_area_vs_residenti'] = round(float(((A.prezzo_per_area - A.prezzo_per_residenti).abs() / A.prezzo_per_residenti).max()), 3)

SEED, NB = 20261101, 4000
A['lnD'] = np.log(A.dist_duomo_centroide_m / 1000)
A['lnY'] = np.log(A.reddito)

def ols(y, X):
    X1 = np.column_stack([np.ones(len(y)), X])
    b = np.linalg.lstsq(X1, y, rcond=None)[0]
    e = y - X1 @ b
    return b, 1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum()

def cluster_boot(d, cols, pcol, nb=NB):
    """bootstrap a grappoli: ricampiona le zone OMI dominanti"""
    rng = np.random.default_rng(SEED)
    cl = {k: v for k, v in d.groupby('zona_dominante')}
    keys = list(cl)
    out = []
    for _ in range(nb):
        pick = rng.integers(0, len(keys), len(keys))
        dd = pd.concat([cl[keys[j]] for j in pick])
        if dd.S20.nunique() < 3:
            continue
        b, _ = ols(np.log(dd[pcol].values), dd[cols].values)
        out.append(b[1])
    return np.percentile(out, [2.5, 97.5])

def spear_boot(d, a, b_, nb=NB):
    rng = np.random.default_rng(SEED)
    cl = {k: v for k, v in d.groupby('zona_dominante')}
    keys = list(cl)
    out = []
    for _ in range(nb):
        pick = rng.integers(0, len(keys), len(keys))
        dd = pd.concat([cl[keys[j]] for j in pick])
        v = stats.spearmanr(dd[a], dd[b_]).statistic
        if np.isfinite(v):
            out.append(v)
    return np.percentile(out, [2.5, 97.5])

res = {}
for lab, pc in [('prezzo per residenti', 'prezzo_per_residenti'), ('prezzo per area', 'prezzo_per_area')]:
    r = {}
    for nm, a_, b_ in [('prezzo-servizi20', pc, 'S20'), ('prezzo-servizi10', pc, 'S10'), ('prezzo-reddito', pc, 'reddito'),
                       ('prezzo-distanza', pc, 'dist_duomo_centroide_m')]:
        e = stats.spearmanr(A[a_], A[b_]).statistic
        lo, hi = spear_boot(A, a_, b_)
        r['spearman_' + nm] = [round(float(e), 3), round(float(lo), 3), round(float(hi), 3)]
    for nm, cols in [('S20 solo', ['S20']), ('S20 + distanza + reddito', ['S20', 'lnD', 'lnY'])]:
        b, r2 = ols(np.log(A[pc].values), A[cols].values)
        lo, hi = cluster_boot(A, cols, pc)
        r['reg ' + nm] = dict(pct_per_servizio=round(100 * (np.exp(b[1]) - 1), 2), ic95_grappoli_pct=[round(100 * (np.exp(lo) - 1), 2), round(100 * (np.exp(hi) - 1), 2)], r2=round(r2, 3))
    # Spearman parziale
    rk = A[[pc, 'S20', 'dist_duomo_centroide_m', 'reddito']].rank().values
    C = np.column_stack([np.ones(len(A)), rk[:, 2:]])
    rx = rk[:, 1] - C @ np.linalg.lstsq(C, rk[:, 1], rcond=None)[0]
    ry = rk[:, 0] - C @ np.linalg.lstsq(C, rk[:, 0], rcond=None)[0]
    r['spearman_parziale_S20_dist_reddito'] = round(float(np.corrcoef(rx, ry)[0, 1]), 3)
    res[lab] = r
LOG['risultati'] = res
# solo NIL con zona dominante >= 80% (piu' "puliti")
Ap = A[A.quota_zona_dominante >= 0.8]
LOG['n_nil_puliti_ge80pct'] = len(Ap)
b, r2 = ols(np.log(Ap.prezzo_per_residenti.values), Ap[['S20', 'lnD', 'lnY']].values)
lo, hi = cluster_boot(Ap, ['S20', 'lnD', 'lnY'], 'prezzo_per_residenti')
LOG['reg_nil_puliti_prezzo_residenti'] = dict(pct_per_servizio=round(100 * (np.exp(b[1]) - 1), 2), ic95_grappoli_pct=[round(100 * (np.exp(lo) - 1), 2), round(100 * (np.exp(hi) - 1), 2)])
# confronto con le 41 zone: stessa regressione con 'zona' come unita'
json.dump(LOG, open(O + '/out/nil_risultati.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(json.dumps(LOG, indent=1, ensure_ascii=False, default=float))
