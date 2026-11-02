"""Sport: conteggi per NIL (ogni 10.000 abitanti) e accesso a piedi in 15 minuti (stesso metodo di citta-15-minuti, fase 3).
Uso: python -I -X utf8 analisi.py <ABS sport> <ABS citta-15-minuti>   (dopo build.py)
Scrive pulito/nil_sport.csv, pulito/citta_sport.json, pulito/sedi_olimpiche.csv.
Metodo di accesso (identico a citta-15-minuti/scripts/f4_tempi.py): rete pedonale OSM gia' costruita (citta-15-minuti/out/grafo_pedonale_*.npz, solo letta),
57.405 civici applicati come partenze, 4,5 km/h, tetto 3.200 m, luogo valido se a meno di 150 m dalla rete, soglia 15 minuti,
residenti del NIL (2025) distribuiti in parti uguali sui civici residenziali."""
import sys, json, glob
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse import load_npz, csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.stats import spearmanr
from pyproj import Transformer
S, C = sys.argv[1].rstrip('\\/'), sys.argv[2].rstrip('\\/')
O = C + '/out/'
SPEED = 4.5 / 3.6; LIM = 3200.0; MAXSNAP = 150.0; SOGLIA = 15.0
P = pd.read_csv(S + '/pulito/siti.csv', dtype={'ID_NIL': 'Int64'})
nil = pd.read_csv(O + 'nil_punteggi.csv')[['ID_NIL', 'NIL_nome', 'residenti_2025']]
nil['ID_NIL'] = nil.ID_NIL.astype(int)
# ------------------------------------------------------------- gruppi
imp = P.livello == 'impianto'
com = P.gestione.isin(['milanosport', 'comune_concessione', 'comune_da_verificare'])
GRP = {
    'tutti': imp,                                           # tutti gli impianti (esclusi i campi liberi)
    'piscine': imp & P.piscina,
    'palestre': imp & P.palestra,
    'campi': P.campo,                                       # impianti con campi + campi liberi (giardini, OSM)
    'comunali': imp & com,                                  # Milanosport + concessioni del Comune + da verificare
    'milanosport': P.gestione == 'milanosport',
    'campi_liberi_comune': P.gestione.eq('comune_libero') & P.campo,
    'scuole': imp & P.gestione.eq('scuola'),
    'altro': imp & P.gestione.eq('altro'),                  # non risulta comunale
    'piscine_comunali': imp & P.piscina & com,
    'tutto_con_campi_liberi': pd.Series(True, index=P.index),
}
# ------------------------------------------------------------- conteggi per NIL
cnt = pd.DataFrame({'ID_NIL': nil.ID_NIL})
for g, m in GRP.items():
    cnt[g] = cnt.ID_NIL.map(P[m & P.ID_NIL.notna()].groupby('ID_NIL').size()).fillna(0).astype(int)
# per fonte (controllo): elenco del Comune (ds34+ds2941+ds32), OSM, Regione 2016, scuole
def con_fonte(f): return P.fonti.str.contains(f) & imp
for nome, f in {'f_comune': 'ds34|ds2941|ds32', 'f_osm': r'(^|\|)osm(\||$)', 'f_regione': 'regione2016'}.items():
    m = P.fonti.str.contains(f, regex=True) & imp & P.ID_NIL.notna()
    cnt[nome] = cnt.ID_NIL.map(P[m].groupby('ID_NIL').size()).fillna(0).astype(int)
nl = nil.merge(cnt, on='ID_NIL')
for g in list(GRP) + ['f_comune', 'f_osm', 'f_regione']:
    nl['per10k_' + g] = np.where(nl.residenti_2025 > 0, nl[g] / nl.residenti_2025 * 1e4, np.nan)
# ------------------------------------------------------------- accesso a piedi
G = load_npz(O + 'grafo_pedonale_csr.npz'); nd = np.load(O + 'grafo_pedonale_nodi.npz'); N = G.shape[0]
tree = cKDTree(np.c_[nd['x'], nd['y']])
c = pd.read_csv(O + 'civici_tempi.csv', usecols=['IDMASTER', 'ID_NIL', 'RESIDENZIALE', 'x', 'y', 'snap_m', 'CAP', 'punteggio'])
c['node'] = tree.query(np.c_[c.x.values, c.y.values])[1]
dist, nodes = tree.query(np.c_[P.x.values, P.y.values]); P['node'] = nodes; P['snap_m'] = dist
indptr = G.indptr; ind = G.indices; dat = G.data
base_r = np.repeat(np.arange(N), np.diff(indptr))
def minutes(sub):
    sub = sub[sub.snap_m <= MAXSNAP]
    best = pd.DataFrame({'n': sub.node.values, 's': sub.snap_m.values}).groupby('n', as_index=False).s.min()
    A = csr_matrix((np.r_[dat, best.s.values + 0.01], (np.r_[base_r, np.full(len(best), N)], np.r_[ind, best.n.values])), shape=(N + 1, N + 1))
    dn = dijkstra(A, directed=True, indices=N, limit=LIM)[:N]
    dm = dn[c.node.values] + c.snap_m.values
    return np.round(np.where(dm > LIM + MAXSNAP, np.nan, dm / SPEED / 60.0), 2), len(sub)
res = c[(c.RESIDENZIALE == 1) & c.ID_NIL.notna()].copy()
res['ID_NIL'] = res.ID_NIL.astype(int)
pop = nil.set_index('ID_NIL').residenti_2025
res['peso'] = res.ID_NIL.map(pop) / res.ID_NIL.map(res.groupby('ID_NIL').size()); res = res[res.peso.notna()]
R = {'residenti_stimati': round(float(res.peso.sum())), 'luoghi_scartati_oltre_150m_dalla_rete': int((P.snap_m > MAXSNAP).sum()), 'gruppi': {}}
cmin = {}
for g, m in GRP.items():
    mm, n = minutes(P[m]); cmin[g] = pd.Series(mm, index=c.index)
    t = cmin[g].loc[res.index]; ok = (t <= SOGLIA).astype(float)
    res['in_' + g] = ok.values
    v = t.fillna(99).values; o = np.argsort(v); cw = np.cumsum(res.peso.values[o])
    R['gruppi'][g] = {'luoghi_usati': n, 'quota_residenti_entro15': round(float((ok.values * res.peso.values).sum() / res.peso.sum()), 4),
                      'minuti_mediani': round(float(v[o][np.searchsorted(cw, cw[-1] / 2)]), 1)}
for g in GRP:
    q = res.groupby('ID_NIL').apply(lambda d: float((d['in_' + g] * d.peso).sum() / d.peso.sum()), include_groups=False)
    nl['quota15_' + g] = nl.ID_NIL.map(q)
# minuti medi al piu' vicino, solo per 'tutti' e 'piscine'
for g in ['tutti', 'piscine', 'palestre']:
    t = cmin[g].loc[res.index].fillna(45).values
    mm = pd.Series(t * res.peso.values, index=res.index).groupby(res.ID_NIL).sum() / res.groupby('ID_NIL').peso.sum()
    nl['minuti_medi_' + g] = nl.ID_NIL.map(mm).round(1)
# ------------------------------------------------------------- citta'
ab = nl.residenti_2025.sum(); R['residenti_2025'] = int(ab)
R['per10k_citta'] = {g: round(float(nl[g].sum() / ab * 1e4), 2) for g in list(GRP) + ['f_comune', 'f_osm', 'f_regione']}
R['totali'] = {g: int(nl[g].sum()) for g in list(GRP) + ['f_comune', 'f_osm', 'f_regione']}
R['luoghi_totali_nel_comune_con_NIL'] = int(P.ID_NIL.notna().sum())
big = nl[nl.residenti_2025 >= 1000].copy(); R['nil_con_almeno_1000_residenti'] = len(big)
def top(col, n=5, asc=False): return big.sort_values(col, ascending=asc).head(n)[['NIL_nome', 'residenti_2025', col]].round(2).to_dict('records')
R['top_per10k_tutti'] = top('per10k_tutti'); R['bottom_per10k_tutti'] = top('per10k_tutti', asc=True)
R['top_per10k_piscine'] = top('per10k_piscine'); R['nil_senza_piscine_(>=1000_ab)'] = int((big.piscine == 0).sum())
R['bottom_quota15_piscine'] = top('quota15_piscine', asc=True); R['bottom_quota15_tutti'] = top('quota15_tutti', asc=True)
R['nil_senza_impianti_comunali_(>=1000_ab)'] = int((big.comunali == 0).sum())
R['nil_senza_impianti_comunali_elenco'] = big[big.comunali == 0].NIL_nome.tolist()
R['nil_senza_piscine_elenco'] = big[big.piscine == 0].NIL_nome.tolist()
R['nil_senza_nessun_impianto_(>=1000_ab)'] = big[big.tutti == 0].NIL_nome.tolist()
R['mediana_per10k_tutti_nil'] = round(float(big.per10k_tutti.median()), 2)
# robustezza tra fonti: correlazione di Spearman delle classifiche dei NIL (>=1000 ab)
rb = {}
for a, b in [('per10k_f_comune', 'per10k_f_osm'), ('per10k_f_comune', 'per10k_f_regione'), ('per10k_f_osm', 'per10k_f_regione')]:
    rb[a.replace('per10k_', '') + ' vs ' + b.replace('per10k_', '')] = round(float(spearmanr(big[a], big[b]).statistic), 2)
R['spearman_fonti_nil'] = rb
# concentrazione: quanta parte degli impianti sta nei 10 NIL piu' ricchi di impianti
R['quota_impianti_nei_10_nil_con_piu_impianti'] = round(float(nl.sort_values('tutti', ascending=False).head(10).tutti.sum() / nl.tutti.sum()), 3)
# reddito: tra CAP non si puo' (gli impianti sono per NIL): niente. Correlazione con punteggio 15 minuti della fase 2
pun = pd.read_csv(O + 'nil_punteggi.csv')[['ID_NIL', 'punteggio_medio']]
bb = big.merge(pun, on='ID_NIL'); R['spearman_per10k_tutti_vs_punteggio15min_fase2'] = round(float(spearmanr(bb.per10k_tutti, bb.punteggio_medio).statistic), 2)
# ------------------------------------------------------------- sedi olimpiche (contesto)
tr = Transformer.from_crs(4326, 32632, always_xy=True)
SEDI = [('Stadio San Siro (Meazza)', 'cerimonia di apertura', 'esistente', 9.12397, 45.47803, 'Milano'),
        ('Arena Santa Giulia (Milano Santagiulia Ice Hockey Arena; oggi Unipol Dome)', 'hockey su ghiaccio', 'nuova', 9.25517, 45.44138, 'Milano'),
        ('Villaggio olimpico di Porta Romana', 'alloggio atleti; poi studentato', 'nuovo', 9.20552, 45.44554, 'Milano'),
        ('Forum di Assago (Milano Ice Skating Arena)', 'pattinaggio di figura e short track', 'esistente', 9.1423, 45.40141, 'Assago (fuori Milano)')]
rows = []
npoly = json.load(open(C + '/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson', encoding='utf-8'))['features']
from shapely.geometry import shape, Point
from shapely.ops import transform
polys = [(f['properties']['ID_NIL'], f['properties']['NIL'], shape(f['geometry'])) for f in npoly]
for nome, gara, stato, lon, lat, dove in SEDI:
    idn = nn = None
    for i, n, pg in polys:
        if pg.contains(Point(lon, lat)): idn, nn = i, n
    r = nl[nl.ID_NIL == idn]
    rows.append(dict(sede=nome, evento=gara, stato=stato, comune=dove, lon=lon, lat=lat, ID_NIL=idn, NIL=nn,
                     residenti=int(r.residenti_2025.iloc[0]) if len(r) else None, impianti_nel_NIL=int(r.tutti.iloc[0]) if len(r) else None,
                     per10k_tutti=round(float(r.per10k_tutti.iloc[0]), 2) if len(r) else None, quota15_tutti=round(float(r.quota15_tutti.iloc[0]), 3) if len(r) else None,
                     quota15_piscine=round(float(r.quota15_piscine.iloc[0]), 3) if len(r) else None, quota15_comunali=round(float(r.quota15_comunali.iloc[0]), 3) if len(r) else None))
pd.DataFrame(rows).to_csv(S + '/pulito/sedi_olimpiche.csv', index=False, encoding='utf-8')
nl.round(4).to_csv(S + '/pulito/nil_sport.csv', index=False, encoding='utf-8')
P.drop(columns=['node']).round({'x': 1, 'y': 1, 'snap_m': 1, 'lon': 6, 'lat': 6}).to_csv(S + '/pulito/siti.csv', index=False, encoding='utf-8')   # aggiunge snap_m
json.dump(R, open(S + '/pulito/citta_sport.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1)); print(pd.DataFrame(rows).to_string())
