"""Fase 4 (servizi extra), passo 2: minuti a piedi per ogni civico fino a ciascun extra (stesso Dijkstra multi-sorgente, stessa velocita 4,5 km/h,
stesso tetto di 3.200 m e stessa distanza di aggancio della fase 2), poi aggregazione per NIL e per CAP (pesata sui residenti) e punteggio esteso 0-20.
Uso: python -I f4_tempi.py <ABS strand>   (dopo f2_grafo.py, f2_punti.py, f2_aggrega.py, f4_servizi.py). Non modifica nessun file della fase 2."""
import sys, json, time
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse import load_npz, csr_matrix
from scipy.sparse.csgraph import dijkstra
S = sys.argv[1]; O = S + '/out/'; t0 = time.time()
SPEED = 4.5 / 3.6; LIM = 3200.0; MAXSNAP = 150.0; SOGLIA = 15.0
TIPI = ['farmacie', 'medici', 'nidi', 'scuole', 'biblioteche', 'mercati', 'parchi', 'sport', 'poste', 'vicinato']
EX = ['cinema', 'teatri_musei', 'giochi', 'piscine', 'cani', 'metro', 'bikemi', 'supermercati', 'ospedali', 'librerie']
G = load_npz(O + 'grafo_pedonale_csr.npz'); nd = np.load(O + 'grafo_pedonale_nodi.npz'); N = G.shape[0]
tree = cKDTree(np.c_[nd['x'], nd['y']])
c = pd.read_csv(O + 'civici_tempi.csv', dtype={'CAP': str})
c['node'] = tree.query(np.c_[c.x.values, c.y.values])[1]
sv = pd.read_csv(O + 'extra_servizi_puliti.csv')
indptr = G.indptr; ind = G.indices; dat = G.data
def build_aug(nodes, snaps):
    best = pd.DataFrame({'n': nodes, 's': snaps}).groupby('n', as_index=False).s.min()
    r = np.r_[np.repeat(np.arange(N), np.diff(indptr)), np.full(len(best), N)]
    cc = np.r_[ind, best.n.values]; vv = np.r_[dat, best.s.values + 0.01]
    return csr_matrix((vv, (r, cc)), shape=(N + 1, N + 1))
def minutes(nodes, snaps):
    dn = dijkstra(build_aug(nodes, snaps), directed=True, indices=N, limit=LIM)[:N]
    dm = dn[c.node.values] + c.snap_m.values
    t = dm / SPEED / 60.0
    return np.round(np.where(dm > LIM + MAXSNAP, np.nan, t), 2)
out = c[['IDMASTER', 'ID_NIL', 'RESIDENZIALE', 'CAP']].copy()
for t in EX:
    s_ = sv[sv.tipo == t]; out['min_' + t] = minutes(s_.node.values, s_.snap_m.values)
s_ = sv[(sv.tipo == 'ospedali') & (sv['sub'] == 'con pronto soccorso')]; out['min_ospedali_ps'] = minutes(s_.node.values, s_.snap_m.values)
s_ = sv[(sv.tipo == 'teatri_musei') & (sv['sub'] == 'teatro')]; out['min_solo_teatri'] = minutes(s_.node.values, s_.snap_m.values)
s_ = sv[(sv.tipo == 'teatri_musei') & (sv['sub'] != 'teatro')]; out['min_solo_musei'] = minutes(s_.node.values, s_.snap_m.values)
out['punteggio'] = c.punteggio.values
out['punteggio_extra'] = (out[['min_' + t for t in EX]] <= SOGLIA).sum(axis=1)
out['punteggio_20'] = out.punteggio + out.punteggio_extra
out.to_csv(O + 'civici_tempi_extra.csv', index=False, encoding='utf-8')
# ---------------- controllo rete >= linea d'aria
chk = {}
for t in EX:
    s_ = sv[sv.tipo == t]; dl, _ = cKDTree(np.c_[s_.x.values, s_.y.values]).query(np.c_[c.x.values, c.y.values])
    mn = out['min_' + t].values * 60 * SPEED; okm = ~np.isnan(mn); far = okm & (dl > 100)
    chk[t] = {'violazioni': int((okm & (mn < dl - 1.0)).sum()), 'rapporto_mediano': round(float(np.median(mn[far] / dl[far])), 3), 'civici_con_tempo': int(okm.sum())}
# ---------------- popolazione e pesi (identici alla fase 2)
nil = pd.read_csv(O + 'nil_punteggi.csv')
pop = nil.set_index('ID_NIL').residenti_2025
res = out[(out.RESIDENZIALE == 1) & out.ID_NIL.notna()].copy()
cnt = res.groupby('ID_NIL').size()
res['peso'] = res.ID_NIL.map(pop) / res.ID_NIL.map(cnt); res = res[res.peso.notna()].copy()
for t in EX: res['in_' + t] = res['min_' + t] <= SOGLIA
res['in_ospedali_ps'] = res.min_ospedali_ps <= SOGLIA
res['in_solo_teatri'] = res.min_solo_teatri <= SOGLIA; res['in_solo_musei'] = res.min_solo_musei <= SOGLIA
res['tutti10'] = res.punteggio == 10; res['tutti_extra'] = res.punteggio_extra == 10; res['tutti20'] = res.punteggio_20 == 20
res['n10x'] = (res[['min_' + t for t in EX]] <= 10.0).sum(axis=1)
def wavg(g, col): return float((g[col].astype(float) * g.peso).sum() / g.peso.sum())
COLS = ['punteggio', 'punteggio_extra', 'punteggio_20', 'tutti10', 'tutti_extra', 'tutti20'] + ['in_' + t for t in EX] + ['in_ospedali_ps']
def agg(g): return pd.Series({c_: wavg(g, c_) for c_ in COLS} | {'residenti_stimati': g.peso.sum(), 'civici_residenziali': len(g)})
nl = res.groupby('ID_NIL').apply(agg, include_groups=False).reset_index().merge(nil[['ID_NIL', 'NIL_nome', 'residenti_2025']], on='ID_NIL')
nl = nl.rename(columns={'punteggio': 'punteggio_medio_10', 'punteggio_extra': 'punteggio_medio_extra', 'punteggio_20': 'punteggio_medio_20'})
nl.round(4).to_csv(O + 'nil_punteggi_extra.csv', index=False, encoding='utf-8')
cp = res.groupby('CAP').apply(agg, include_groups=False).reset_index().rename(columns={'punteggio': 'punteggio_medio_10', 'punteggio_extra': 'punteggio_medio_extra', 'punteggio_20': 'punteggio_medio_20'})
cp.round(4).to_csv(O + 'cap_punteggi_extra.csv', index=False, encoding='utf-8')
# ---------------- citta
R = {'residenti_stimati': round(float(res.peso.sum())), 'controllo_rete_vs_linea_aria': chk}
R['quota_residenti_entro15'] = {t: round(wavg(res, 'in_' + t), 4) for t in EX}
R['quota_residenti_entro15']['ospedali_con_pronto_soccorso'] = round(wavg(res, 'in_ospedali_ps'), 4)
R['quota_residenti_entro15']['solo_teatri'] = round(wavg(res, 'in_solo_teatri'), 4); R['quota_residenti_entro15']['solo_musei'] = round(wavg(res, 'in_solo_musei'), 4)
R['minuti_mediani_pesati'] = {}
for t in EX + ['ospedali_ps']:
    v = res['min_' + t].fillna(99).values; o = np.argsort(v); cw = np.cumsum(res.peso.values[o]); R['minuti_mediani_pesati'][t] = round(float(v[o][np.searchsorted(cw, cw[-1] / 2)]), 1)
R['punteggio_medio'] = {'essenziali_0_10': round(wavg(res, 'punteggio'), 3), 'extra_0_10': round(wavg(res, 'punteggio_extra'), 3), 'totale_0_20': round(wavg(res, 'punteggio_20'), 3)}
R['quota_con_tutti'] = {'10_essenziali': round(wavg(res, 'tutti10'), 4), '10_extra': round(wavg(res, 'tutti_extra'), 4), 'tutti_20': round(wavg(res, 'tutti20'), 4)}
R['distribuzione_punteggio_extra'] = {int(k): round(float(v), 4) for k, v in (res.groupby('punteggio_extra').peso.sum() / res.peso.sum()).items()}
R['distribuzione_punteggio_20'] = {int(k): round(float(v), 4) for k, v in (res.groupby('punteggio_20').peso.sum() / res.peso.sum()).items()}
R['spearman_civici_10_vs_extra'] = round(float(res[['punteggio', 'punteggio_extra']].corr(method='spearman').iloc[0, 1]), 3)
big = nl[nl.residenti_2025 >= 1000]
R['nil_migliori5_totale_20'] = big.sort_values('punteggio_medio_20', ascending=False).head(5)[['NIL_nome', 'punteggio_medio_20', 'punteggio_medio_10']].round(2).to_dict('records')
R['nil_peggiori5_totale_20'] = big.sort_values('punteggio_medio_20').head(5)[['NIL_nome', 'punteggio_medio_20', 'punteggio_medio_10']].round(2).to_dict('records')
R['nil_migliori5_solo_extra'] = big.sort_values('punteggio_medio_extra', ascending=False).head(5)[['NIL_nome', 'punteggio_medio_extra']].round(2).to_dict('records')
R['nil_peggiori5_solo_extra'] = big.sort_values('punteggio_medio_extra').head(5)[['NIL_nome', 'punteggio_medio_extra']].round(2).to_dict('records')
b1 = big.sort_values('punteggio_medio_10', ascending=False).reset_index(drop=True); b2 = big.sort_values('punteggio_medio_20', ascending=False).reset_index(drop=True)
r1 = {i: k for k, i in enumerate(b1.ID_NIL)}; r2 = {i: k for k, i in enumerate(b2.ID_NIL)}
mv = pd.DataFrame({'NIL': b1.NIL_nome, 'pos10': [r1[i] + 1 for i in b1.ID_NIL], 'pos20': [r2[i] + 1 for i in b1.ID_NIL]}); mv['salto'] = mv.pos10 - mv.pos20
R['nil_che_salgono_di_piu'] = mv.sort_values('salto', ascending=False).head(5).to_dict('records'); R['nil_che_scendono_di_piu'] = mv.sort_values('salto').head(5).to_dict('records')
R['spearman_classifica_NIL_10_vs_20'] = round(float(pd.Series(list(r1.values())).corr(pd.Series([r2[i] for i in r1]), method='spearman')), 3)
cap0 = pd.read_csv(O + 'cap_redditi_servizi.csv', dtype={'CAP': str})
cz = cp.merge(cap0[['CAP', 'imponibile_medio_2024', 'punteggio_medio']], on='CAP')
from scipy.stats import spearmanr
R['cap_spearman_reddito2024'] = {'essenziali': round(float(spearmanr(cz.punteggio_medio_10, cz.imponibile_medio_2024)[0]), 3), 'solo_extra': round(float(spearmanr(cz.punteggio_medio_extra, cz.imponibile_medio_2024)[0]), 3), 'totale_20': round(float(spearmanr(cz.punteggio_medio_20, cz.imponibile_medio_2024)[0]), 3), 'n_CAP': len(cz)}
R['cap_spearman_reddito2024_per_extra'] = {t: round(float(spearmanr(cz['in_' + t], cz.imponibile_medio_2024)[0]), 2) for t in EX}
# esagoni: gli stessi di f3_dati (ordine groupby hq, hr): mediana dei minuti per extra
SZ = 100 / np.sqrt(3); x = c.x.values; y = c.y.values
q = (np.sqrt(3) / 3 * x - 1 / 3 * y) / SZ; r_ = (2 / 3 * y) / SZ; cx_ = q; cz_ = r_; cy = -cx_ - cz_
rx = np.round(cx_); ry = np.round(cy); rz = np.round(cz_); dx = abs(rx - cx_); dy = abs(ry - cy); dz = abs(rz - cz_)
m1 = (dx > dy) & (dx > dz); m2 = (~m1) & (dy > dz); rx = np.where(m1, -ry - rz, rx); rz = np.where((~m1) & (~m2), -rx - ry, rz)
hx = pd.DataFrame({'hq': rx.astype(int), 'hr': rz.astype(int), 'p20': out.punteggio_20.values, 'pe': out.punteggio_extra.values})
for t in EX: hx['m_' + t] = out['min_' + t].fillna(99).values
Hh = hx.groupby(['hq', 'hr']).agg(**{'p20': ('p20', 'mean'), 'pe': ('pe', 'mean')}, **{('m_' + t): ('m_' + t, 'median') for t in EX}).reset_index()
Hh.round(3).to_csv(O + 'hex100_extra.csv', index=False)
R['esagoni'] = len(Hh); R['secondi'] = round(time.time() - t0)
json.dump(R, open(O + 'f4_risultati.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(json.dumps(R, indent=1, ensure_ascii=False))
