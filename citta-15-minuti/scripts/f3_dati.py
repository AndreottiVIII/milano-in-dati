"""Fase 3: dati per la pagina del sito (docs/citta-15-minuti/data/).
Uso: python -I f3_dati.py <ABS strand citta-15-minuti> <ABS docs/citta-15-minuti>
Regole decise dal coordinatore:
 - Cascina Merlata (ID_NIL 73): dato non affidabile -> grigio sulle mappe, fuori da classifiche e dal confronto con i redditi (CAP ricalcolati senza i suoi civici).
 - NIL con meno di 30 civici o meno di 1.000 residenti: mostrati, ma non in classifica.
Non pubblica niente dei medici di base: solo tempi a piedi aggregati in esagoni da 100 m."""
import sys, json, os, shutil
import numpy as np, pandas as pd
from scipy.stats import spearmanr, pearsonr
S = sys.argv[1]; D = sys.argv[2]; O = S + '/out/'; DD = D + '/data/'
os.makedirs(DD, exist_ok=True)
TIPI = ['farmacie', 'medici', 'nidi', 'scuole', 'biblioteche', 'mercati', 'parchi', 'sport', 'poste', 'vicinato']
ETI = {'farmacie': 'Farmacie', 'medici': 'Medici di base', 'nidi': 'Asili nido', 'scuole': 'Scuole (infanzia, primarie, medie)',
       'biblioteche': 'Biblioteche', 'mercati': 'Mercati', 'parchi': 'Parchi e giardini (almeno 5.000 m²)', 'sport': 'Impianti sportivi',
       'poste': 'Uffici postali', 'vicinato': 'Negozi alimentari di vicinato'}
CM = 73; SOGLIA = 15.0
c = pd.read_csv(O + 'civici_tempi.csv', dtype={'CAP': str})
nilcsv = pd.read_csv(O + 'nil_punteggi.csv')
CK = json.load(open(O + 'controlli_fase2.json', encoding='utf-8'))
SENS = json.load(open(O + 'sensibilita_fase2.json', encoding='utf-8'))

def titolo(s):
    """Nome del NIL come scritto nel file dei residenti (corretto di qualche difetto); se e' tutto maiuscolo cerca il nome nel file dei residenti."""
    s = str(s).replace('�', "'").strip()
    k = s.upper().replace('’', "'")
    s = NOMI.get(k, s)
    s = s.replace("Citta' studi", 'Città Studi').replace("in citta'", 'in città').replace("Citta'", 'Città')
    return s
NOMI = {}
for _n in pd.read_csv(O + 'nil_punteggi.csv').NIL_nome:
    _n = str(_n).replace('�', "'"); NOMI[_n.upper().replace('’', "'")] = _n

# ------------------------------------------------------------------ NIL
civ_tot = c.groupby('ID_NIL').size()
nilcsv = nilcsv.merge(civ_tot.rename('civici_totali'), left_on='ID_NIL', right_index=True, how='left')
nm = nilcsv.set_index('ID_NIL')
g = json.load(open(O + 'nil_poligoni_punteggi.geojson', encoding='utf-8'))
def stato(i):
    if i == CM: return 'nonaff'
    r = nm.loc[i]
    if r.civici_totali < 30 or r.residenti_2025 < 1000: return 'pochi'
    return 'ok'
feats = []; rows = []
for f in g['features']:
    p = f['properties']; i = int(p['ID_NIL'])
    if i in nm.index:
        r = nm.loc[i]; st = stato(i)
        pr = {'i': i, 'n': titolo(r.NIL_nome), 'c': int(r.civici_totali), 's': st, 'r': int(r.residenti_2025)}
        if st != 'nonaff':
            pr.update({'p': round(float(r.punteggio_medio), 2), 'p10': round(float(r.punteggio_medio_10min), 2), 't': round(float(r.quota_residenti_tutti_i_servizi), 3),
                       'q': [round(float(r['quota_entro15_' + t]), 3) for t in TIPI]})
        rows.append({'ID_NIL': i, 'NIL': pr['n'], 'residenti_2025': pr['r'], 'civici_totali': pr['c'], 'stato': {'ok': 'in classifica', 'pochi': 'non in classifica (meno di 30 civici o di 1.000 residenti)', 'nonaff': 'dato non affidabile'}[st],
                     **({} if st == 'nonaff' else {'punteggio_su_10': round(float(r.punteggio_medio), 2), 'punteggio_entro_10_minuti': round(float(r.punteggio_medio_10min), 2),
                          'quota_residenti_con_tutti_i_10_servizi': round(float(r.quota_residenti_tutti_i_servizi), 3),
                          **{'quota_entro15_' + t: round(float(r['quota_entro15_' + t]), 3) for t in TIPI}})})
    else:
        pr = {'i': i, 'n': str(p.get('NIL', '')).title(), 's': 'senza', 'r': 0, 'c': int(civ_tot.get(i, 0))}
    feats.append({'type': 'Feature', 'properties': pr, 'geometry': f['geometry']})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(DD + 'nil.geojson', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
pd.DataFrame(rows).sort_values('ID_NIL').to_csv(DD + 'nil_punteggi.csv', index=False, encoding='utf-8')

# top / bottom 5 tra i NIL in classifica
ok = nilcsv[[stato(int(i)) == 'ok' for i in nilcsv.ID_NIL]].sort_values('punteggio_medio', ascending=False)
def scheda(r):
    qs = sorted([(t, float(r['quota_entro15_' + t])) for t in TIPI], key=lambda z: z[1])
    return {'i': int(r.ID_NIL), 'n': titolo(r.NIL_nome), 'r': int(r.residenti_2025), 'p': round(float(r.punteggio_medio), 2), 't': round(float(r.quota_residenti_tutti_i_servizi), 3),
            'meta': [[t, round(q, 2)] for t, q in qs if q < 0.5], 'peggio3': [[t, round(q, 2)] for t, q in qs[:3]]}
top = [scheda(r) for _, r in ok.head(5).iterrows()]; bot = [scheda(r) for _, r in ok.tail(5).iloc[::-1].iterrows()]
rank_pos = {int(r.ID_NIL): k + 1 for k, (_, r) in enumerate(ok.iterrows())}
duomo = nilcsv[nilcsv.ID_NIL == 1].iloc[0]

# ------------------------------------------------------------------ esagoni
SZ = 100 / np.sqrt(3); x = c.x.values; y = c.y.values
q = (np.sqrt(3) / 3 * x - 1 / 3 * y) / SZ; r_ = (2 / 3 * y) / SZ
cx_ = q; cz = r_; cy = -cx_ - cz
rx = np.round(cx_); ry = np.round(cy); rz = np.round(cz)
dx = abs(rx - cx_); dy = abs(ry - cy); dz = abs(rz - cz)
m1 = (dx > dy) & (dx > dz); m2 = (~m1) & (dy > dz)
rx = np.where(m1, -ry - rz, rx); rz = np.where((~m1) & (~m2), -rx - ry, rz)
c['hq'] = rx.astype(int); c['hr'] = rz.astype(int)
c['n_civ'] = 1
for t in TIPI: c['m_' + t] = c['min_' + t].fillna(99)
H = c.groupby(['hq', 'hr']).agg(n=('n_civ', 'sum'), p=('punteggio', 'mean'), lon=('lon', 'mean'), lat=('lat', 'mean'), **{('m_' + t): ('m_' + t, 'median') for t in TIPI}).reset_index()
H['id'] = np.arange(len(H))
# controllo: stessi esagoni del geojson di fase 2
hg = json.load(open(O + 'hex100_citta.geojson', encoding='utf-8'))['features']
assert len(hg) == len(H) and all(int(f['properties']['n']) == int(n) for f, n in zip(hg[:500], H.n[:500])), 'esagoni diversi da fase 2'
cen = np.array([np.mean(np.array(f['geometry']['coordinates'][0][:6]), axis=0) for f in hg])
# NIL dell'esagono: quello della maggioranza dei civici
mode = c.dropna(subset=['ID_NIL']).groupby(['hq', 'hr']).ID_NIL.agg(lambda s: s.mode().iloc[0]).rename('nil')
H = H.merge(mode, left_on=['hq', 'hr'], right_index=True, how='left')
H['nil'] = H.nil.fillna(-1).astype(int)
hexj = {'x': [int(round(v * 1e5)) for v in cen[:, 0]], 'y': [int(round(v * 1e5)) for v in cen[:, 1]], 'n': [int(v) for v in H.n],
        'p': [int(round(v * 10)) for v in H.p], 'nil': [int(v) for v in H.nil],
        't': {t: [(-1 if v >= 99 else int(round(v * 10))) for v in H['m_' + t]] for t in TIPI}}
json.dump(hexj, open(DD + 'esagoni.json', 'w'), separators=(',', ':'))

# ------------------------------------------------------------------ riepilogo città
city = CK['citta']
qt = city['quota_residenti_entro15_per_tipo']; med = city['minuti_mediani_pesati_per_tipo']
tipi_tab = sorted([{'t': t, 'nome': ETI[t], 'q': qt[t], 'med': med[t]} for t in TIPI], key=lambda z: -z['q'])

# ------------------------------------------------------------------ CAP (senza Cascina Merlata)
cap0 = pd.read_csv(O + 'cap_redditi_servizi.csv', dtype={'CAP': str})
pop = nilcsv.set_index('ID_NIL').residenti_2025
res = c[(c.RESIDENZIALE == 1) & c.ID_NIL.notna()].copy()
cnt = res.groupby('ID_NIL').size()
res['peso'] = res.ID_NIL.map(pop) / res.ID_NIL.map(cnt)
res = res[res.peso.notna()]
n_cm = int(((res.ID_NIL == CM)).sum()); peso_cm = float(res[res.ID_NIL == CM].peso.sum()); cap_cm = res[res.ID_NIL == CM].CAP.unique().tolist()
res = res[res.ID_NIL != CM].copy()
for t in TIPI: res['in_' + t] = (res['min_' + t] <= SOGLIA)
res['n15'] = res[['in_' + t for t in TIPI]].sum(axis=1)
res['tutti'] = res.n15 == 10
def wavg(gr, col): return float((gr[col].astype(float) * gr.peso).sum() / gr.peso.sum())
rr = []
for k, gr in res.groupby('CAP'):
    d = {'CAP': k, 'residenti': float(gr.peso.sum()), 'punteggio': wavg(gr, 'n15'), 'tutti': wavg(gr, 'tutti')}
    for t in TIPI: d['q_' + t] = wavg(gr, 'in_' + t)
    rr.append(d)
cap = pd.DataFrame(rr)
inc = cap0[['CAP'] + [f'imponibile_medio_{a}' for a in range(2019, 2025)] + ['contribuenti_2024', 'NIL_piu_frequente']]
cap = cap.merge(inc, on='CAP', how='inner')
ULT = 'imponibile_medio_2024'
def sp_ci(a, b, nb=5000, seed=7):
    rho, pval = spearmanr(a, b); rng = np.random.default_rng(seed); n = len(a); bs = []
    for _ in range(nb):
        ix = rng.integers(0, n, n)
        if len(np.unique(a[ix])) < 2 or len(np.unique(b[ix])) < 2: continue
        bs.append(spearmanr(a[ix], b[ix])[0])
    return float(rho), float(pval), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
rho, pv, lo, hi = sp_ci(cap.punteggio.values, cap[ULT].values)
rho_t, _, lo_t, hi_t = sp_ci(cap.tutti.values, cap[ULT].values)
cor_tipo = {t: round(float(spearmanr(cap['q_' + t], cap[ULT])[0]), 2) for t in TIPI}
cap['lr'] = np.log(cap[ULT])
b = np.polyfit(cap.lr, cap.punteggio, 1); cap['previsto'] = np.polyval(b, cap.lr); cap['residuo'] = cap.punteggio - cap.previsto
cap['zres'] = cap.residuo / cap.residuo.std(ddof=2)
R2 = float(pearsonr(cap.lr, cap.punteggio)[0] ** 2)
cap['terzo'] = pd.qcut(cap[ULT], 3, labels=['basso', 'medio', 'alto'])
terzi = {}
for k, gr in cap.groupby('terzo', observed=True):
    terzi[str(k)] = {'cap': int(len(gr)), 'residenti': round(float(gr.residenti.sum())), 'punteggio': round(float((gr.punteggio * gr.residenti).sum() / gr.residenti.sum()), 2),
                     'quota_biblio': round(float((gr.q_biblioteche * gr.residenti).sum() / gr.residenti.sum()), 3),
                     'red_min': round(float(gr[ULT].min())), 'red_max': round(float(gr[ULT].max()))}
q33 = cap[ULT].quantile(1 / 3); q67 = cap[ULT].quantile(2 / 3); s33 = cap.punteggio.quantile(1 / 3); s67 = cap.punteggio.quantile(2 / 3)
povero_servito = cap[(cap[ULT] <= q33) & (cap.punteggio >= s67)]
ricco_poco = cap[(cap[ULT] >= q67) & (cap.punteggio <= s33)]
def capj(r): return {'cap': r.CAP, 'zona': titolo(r.NIL_piu_frequente), 'red': round(float(r[ULT])), 'p': round(float(r.punteggio), 2), 'prev': round(float(r.previsto), 2), 'z': round(float(r.zres), 1), 'res': round(float(r.residenti))}
zs = cap.sort_values('zres')
capj_all = [capj(r) for _, r in cap.sort_values('CAP').iterrows()]
capj_all = [dict(a, **{'q': [round(float(cap.loc[cap.CAP == a['cap'], 'q_' + t].iloc[0]), 3) for t in TIPI]}) for a in capj_all]
cap_out = cap.drop(columns=['lr', 'terzo']).copy()
cap_out = cap_out.rename(columns={'residenti': 'residenti_stimati', 'punteggio': 'punteggio_su_10', 'tutti': 'quota_residenti_con_tutti_i_10_servizi', 'NIL_piu_frequente': 'zona_prevalente'})
cap_out['zona_prevalente'] = cap_out.zona_prevalente.map(titolo)
cap_out.round(4).to_csv(DD + 'cap_redditi_servizi.csv', index=False, encoding='utf-8')

# ------------------------------------------------------------------ riepilogo json
meta = {
    'citta': {'residenti': CK['residenti_2025_totale'], 'p': city['punteggio_medio'], 'p10': city['punteggio_medio_10min'], 'tutti': city['quota_residenti_tutti'],
              'distribuzione': city['distribuzione_punteggio_residenti'], 'biblio_osm': SENS.get('biblioteche_con_OSM')},
    'tipi': tipi_tab, 'etichette': ETI, 'ordine': TIPI,
    'top': top, 'bottom': bot, 'rank_n': int(len(ok)),
    'duomo': {'pos': rank_pos.get(1), 'p': round(float(duomo.punteggio_medio), 2), 'biblio': round(float(duomo.quota_entro15_biblioteche), 2)},
    'cap': {'lista': capj_all, 'n': int(len(cap)), 'rho': round(rho, 2), 'ic': [round(lo, 2), round(hi, 2)], 'rho_tutti': round(rho_t, 2), 'ic_tutti': [round(lo_t, 2), round(hi_t, 2)],
            'cor_tipo': cor_tipo, 'R2': round(R2, 2), 'retta': [round(float(b[0]), 4), round(float(b[1]), 3)], 'terzi': terzi,
            'meno_del_previsto': [capj(r) for _, r in zs.head(5).iterrows()], 'piu_del_previsto': [capj(r) for _, r in zs.tail(5).iloc[::-1].iterrows()],
            'poveri_serviti': [capj(r) for _, r in povero_servito.iterrows()], 'ricchi_poco': [capj(r) for _, r in ricco_poco.iterrows()],
            'cm': {'civici_res': n_cm, 'residenti': round(peso_cm), 'cap': cap_cm},
            'sd_res': round(float(cap.residuo.std(ddof=2)), 3)},
}
json.dump(meta, open(DD + 'riepilogo.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps({k: meta[k] for k in ['citta', 'top', 'bottom', 'duomo']}, ensure_ascii=False, indent=1)[:3500])
print(json.dumps({k: v for k, v in meta['cap'].items() if k != 'lista'}, ensure_ascii=False, indent=1))
for f in sorted(os.listdir(DD)): print(f, os.path.getsize(DD + f))
