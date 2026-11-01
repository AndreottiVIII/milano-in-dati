"""Passo 3 - indice dei quartieri che cambiano: standardizzazione, indice, varianti, robustezza.

Indice di base: media semplice (pesi uguali) dei punteggi z di 9 indicatori di nucleo, sui NIL idonei (almeno 2.000
residenti nel 2024). z = (x - media) / scarto, tagliato a +-3. Servono almeno 6 indicatori su 9. Verso: piu alto = piu
"salita" (reddito, prezzi, affitti, affitti brevi, locali, giovani adulti, laureati).
Non e' una misura di cio' che succede alle persone: e' una sintesi di sette segnali, NIL contro NIL.
Uscite (out/): indice_nil.csv, robustezza_varianti.csv, robustezza_loo.csv, robustezza_pesi_casuali.csv,
               correlazioni_indicatori.csv, pca_indicatori.json, livello_nil.csv
Uso: python -I -X utf8 03_indice.py <milano-in-dati> <quartieri-che-cambiano>
"""
import sys, os, json
import numpy as np
import pandas as pd

BASE, QC = sys.argv[1], sys.argv[2]
OUT = os.path.join(QC, 'out')
D = pd.read_csv(os.path.join(OUT, 'indicatori_nil.csv')).set_index('id_nil')
civ = pd.read_csv(os.path.join(OUT, 'civici_collegamenti.csv'))
capd = pd.read_csv(os.path.join(OUT, 'cap_reddito_variazione.csv')).set_index('cap')

CORE = ['reddito_var', 'prezzo_var', 'affitto_var', 'costruzioni_100', 'airbnb_100', 'ristoranti_var', 'botteghe_var', 'giovani_var', 'laureati_var']
CORE7 = ['reddito_var', 'prezzo_var', 'affitto_var', 'airbnb_100', 'ristoranti_var', 'giovani_var', 'laureati_var']   # indice della prima versione
BLOCCO = {'reddito_var': 'casa', 'prezzo_var': 'casa', 'affitto_var': 'casa', 'costruzioni_100': 'casa', 'airbnb_100': 'commercio',
          'ristoranti_var': 'commercio', 'botteghe_var': 'commercio', 'giovani_var': 'persone', 'laureati_var': 'persone'}
K = len(CORE)
KMIN = 6
CLIP = 3.0
rng = np.random.default_rng(20261101)
E = D[D.idoneo].copy()     # NIL idonei


def zscore(x, clip=CLIP):
    z = (x - x.mean()) / x.std(ddof=0)
    return z.clip(-clip, clip) if clip else z


def pct_rank(x):
    return x.rank(pct=True) * 100


def indice(df, cols, w=None, tipo='z', kmin=KMIN, clip=CLIP):
    """Media pesata degli indicatori standardizzati disponibili (pesi rinormalizzati sui disponibili)."""
    w = pd.Series(1.0, index=cols) if w is None else pd.Series(w, index=cols, dtype=float)
    S = pd.DataFrame({c: (zscore(df[c], clip) if tipo == 'z' else pct_rank(df[c])) for c in cols})
    ok = S.notna()
    num = (S.fillna(0) * w).sum(axis=1)
    den = (ok * w).sum(axis=1)
    idx = (num / den).where(ok.sum(axis=1) >= kmin)
    return idx, S


# ------------------------------------------------------------ base
E['indice'], S = indice(E, CORE)
for c in CORE:
    E['z_' + c] = S[c]
E['n_indicatori'] = S.notna().sum(axis=1)
E['rango'] = E.indice.rank(ascending=False, method='min')
n_ranked = int(E.indice.notna().sum())

# ------------------------------------------------------------ correlazioni e PCA
cor = E[CORE].corr(method='spearman')
cor.to_csv(os.path.join(OUT, 'correlazioni_indicatori.csv'))
Zc = S.dropna()
k = len(CORE)
# con le botteghe (solo 23 NIL) pochi NIL hanno tutti i segnali: autovalori e alfa dalla matrice di correlazione a coppie (Spearman)
ev = np.linalg.eigvalsh(cor.values)[::-1]
rbar = float(cor.values[np.triu_indices(k, 1)].mean())
alpha = k * rbar / (1 + (k - 1) * rbar)     # alfa standardizzato
pca = {'n_NIL_con_tutti_i_9': int(len(Zc)), 'autovalori_correlazione_a_coppie': [round(float(v), 3) for v in ev],
       'quota_prima_componente': round(float(ev[0] / ev.sum()), 3), 'alfa_cronbach': round(float(alpha), 3),
       'correlazione_media_a_coppie_spearman': round(rbar, 3)}
json.dump(pca, open(os.path.join(OUT, 'pca_indicatori.json'), 'w', encoding='utf-8'), indent=1)

# ------------------------------------------------------------ varianti
V = {}   # nome -> serie indice
V['base'] = E.indice
V['percentili'] = indice(E, CORE, tipo='rank')[0]
V['senza_taglio_z'] = indice(E, CORE, clip=None)[0]
nb = pd.Series(BLOCCO).value_counts()
V['pesi_a_blocchi_3'] = indice(E, CORE, w=[1 / (3 * nb[BLOCCO[c]]) for c in CORE])[0]
for bk, nmv in [('casa', 'pesi_casa_x2'), ('commercio', 'pesi_negozi_x2'), ('persone', 'pesi_persone_x2')]:
    V[nmv] = indice(E, CORE, w=[2 if BLOCCO[c] == bk else 1 for c in CORE])[0]
V['solo_i_sette_indicatori_di_prima'] = indice(E, CORE7, kmin=5)[0]
# varianti di dato
E2 = E.copy()
E2['reddito_var'] = E2['reddito_var_con_cap_instabili']
V['reddito_con_CAP_instabili'] = indice(E2, CORE)[0]
E2 = E.copy()
E2['airbnb_100'] = E2['airbnb_cresc_100']
V['airbnb_crescita_invece_livello'] = indice(E2, CORE)[0]
E2 = E.copy()
E2['ristoranti_var'] = E2['ristoranti_var_codici']
V['locali_conteggio_codici'] = indice(E2, CORE)[0]
# geografia: tutti i civici (anche non residenziali) invece dei soli residenziali
cv = civ.copy()
cv['reddito_var_cap'] = cv.CAP.map(capd.reddito_var.where(~capd.instabile))
ga = cv.groupby('ID_NIL')
alt = pd.DataFrame({'reddito_var': ga.reddito_var_cap.mean(), 'prezzo_var': ga.crescita_prezzo.mean() * 100,
                    'affitto_var': ga.crescita_affitto.mean() * 100})
quota_inst = ga.apply(lambda g: g.CAP.map(capd.instabile).mean())
alt.loc[quota_inst > 0.5, 'reddito_var'] = np.nan
E2 = E.copy()
for c in alt.columns:
    E2[c] = alt[c].reindex(E2.index)
V['civici_tutti'] = indice(E2, CORE)[0]
# OMI con altre date: 2016/2 -> 2025/2 (stesse zone del 2014/2 fino al 2019/2 e stesse del 2026/1 dal 2024/2: si usano i codici gia assegnati)
pz = pd.read_csv(os.path.join(BASE, 'prezzi-case', 'pulito', 'prezzi_zona_semestre_prevalente.csv'))
pz = pz[(pz.tipologia == 'Abitazioni civili') & (pz.prevalente == True)]
rs = civ[civ.RESIDENZIALE == 1].copy()
def zv(sem, col, zc):
    return rs[zc].map(pz[pz.semestre == sem].set_index('zona')[col])
rs['cp'] = zv('2025-S2', 'compr_centro_reale_2025', 'zona_2026_1') / zv('2016-S2', 'compr_centro_reale_2025', 'zona_2014_2') - 1
rs['ca'] = zv('2025-S2', 'loc_centro_reale_2025', 'zona_2026_1') / zv('2016-S2', 'loc_centro_reale_2025', 'zona_2014_2') - 1
gg = rs.groupby('ID_NIL')
E2 = E.copy()
E2['prezzo_var'] = (gg.cp.mean() * 100).reindex(E2.index).where(E2.copertura_omi >= 0.7)
E2['affitto_var'] = (gg.ca.mean() * 100).reindex(E2.index).where(E2.copertura_omi >= 0.7)
V['OMI_2016-2_2025-2'] = indice(E2, CORE)[0]
# soglia di idoneita' diversa (confronto sui NIL in comune)
SOGLIE = {}
for soglia in (1000, 5000):
    Ex = D[D.residenti_2024 >= soglia].copy()
    SOGLIE[soglia] = indice(Ex, CORE)[0]
# leave-one-out
LOO = {}
for c in CORE:
    cols = [x for x in CORE if x != c]
    LOO[c] = indice(E, cols, kmin=5)[0]

rk = lambda s: s.rank(ascending=False, method='min')
base_r = rk(V['base'])
top = lambda s, n=10: set(s.nsmallest(n).index)


def conf(name, s):
    r = rk(s)
    both = pd.concat([V['base'], s], axis=1).dropna()
    rho = both.corr(method='spearman').iloc[0, 1]
    ta, tb = top(base_r), top(r)
    ba = set(base_r.nlargest(10).index)
    bb = set(r.nlargest(10).index)
    return dict(variante=name, n_NIL=int(s.notna().sum()), spearman_con_base=round(float(rho), 3),
                top10_in_comune=len(ta & tb), bottom10_in_comune=len(ba & bb))


rows = [conf(n, s) for n, s in V.items() if n != 'base']
for soglia, sx in SOGLIE.items():
    both = pd.concat([V['base'], sx], axis=1, join='inner').dropna()
    rows.append(dict(variante=f'soglia_residenti_{soglia}', n_NIL=int(sx.notna().sum()), spearman_con_base=round(float(both.corr(method='spearman').iloc[0, 1]), 3),
                     top10_in_comune=np.nan, bottom10_in_comune=np.nan))
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'robustezza_varianti.csv'), index=False)
pd.DataFrame([dict(escluso=c, **{k: v for k, v in conf('loo', s).items() if k != 'variante'}) for c, s in LOO.items()]).to_csv(
    os.path.join(OUT, 'robustezza_loo.csv'), index=False)

# pesi casuali (Dirichlet(1,..,1))
N = 5000
R = []
Zm = S[CORE]
for _ in range(N):
    w = rng.dirichlet(np.ones(len(CORE)))
    idx = indice(E, CORE, w=w)[0]
    R.append(rk(idx).reindex(E.index).values)
R = np.array(R)
rr = pd.DataFrame(R.T, index=E.index)
t10 = (rr <= 10).mean(axis=1)
b10 = (rr.apply(lambda c: c >= (c.notna().sum() - 9))).mean(axis=1)   # ultimi 10 di ciascuna estrazione
pc = pd.DataFrame({'rango_mediano': rr.median(axis=1), 'rango_p5': rr.quantile(0.05, axis=1), 'rango_p95': rr.quantile(0.95, axis=1),
                   'quota_estrazioni_top10': t10, 'quota_estrazioni_bottom10': b10})
pc.to_csv(os.path.join(OUT, 'robustezza_pesi_casuali.csv'))
# intervallo di rango tra tutte le varianti (non casuali) + LOO
allr = pd.DataFrame({n: rk(s) for n, s in list(V.items()) + [('loo_' + c, s) for c, s in LOO.items()]})
E['rango_min_varianti'] = allr.min(axis=1)
E['rango_max_varianti'] = allr.max(axis=1)
E = E.join(pc)
E['quota_top10_pesi_casuali'] = E['quota_estrazioni_top10']
E['quota_bottom10_pesi_casuali'] = E['quota_estrazioni_bottom10']

# ------------------------------------------------------------ livello (ricchezza di partenza/di arrivo)
LIV = ['reddito_2024', 'prezzo_2026_reale', 'laureati_2023']
E['livello'], SL = indice(E, LIV, kmin=2)
for c in LIV:
    E['z_' + c] = SL[c]
E['rango_livello'] = E.livello.rank(ascending=False, method='min')
# blocchi dell'indice (per leggere da dove viene)
for bk, nmc in [('casa', 'blocco_casa'), ('commercio', 'blocco_negozi'), ('persone', 'blocco_persone')]:
    E[nmc] = E[['z_' + c for c in CORE if BLOCCO[c] == bk]].mean(axis=1)

cols = (['nil', 'residenti_2024', 'n_indicatori', 'indice', 'rango', 'rango_min_varianti', 'rango_max_varianti', 'rango_mediano', 'rango_p5',
         'rango_p95', 'quota_top10_pesi_casuali', 'quota_bottom10_pesi_casuali', 'livello', 'rango_livello', 'blocco_casa', 'blocco_negozi', 'blocco_persone']
        + ['z_' + c for c in CORE] + CORE + ['reddito_2024', 'prezzo_2026_reale', 'affitto_2026_reale', 'laureati_2023', 'giovani_2025', 'stranieri_2025',
                                             'pop_var', 'stranieri_var', 'eta_media_var', 'scuole_var', 'airbnb_cresc_100', 'quota_civici_cap_instabili', 'copertura_omi', 'botteghe_albo_2017', 'botteghe_chiuse', 'nuove_abitazioni_2014_2024'])
E[cols].sort_values('rango').to_csv(os.path.join(OUT, 'indice_nil.csv'), index=True)
D.loc[~D.idoneo, ['nil', 'residenti_2024'] + CORE].to_csv(os.path.join(OUT, 'nil_non_in_classifica.csv'))

pd.set_option('display.width', 250)
print(pca)
print(pd.DataFrame(rows).to_string())
print(pd.read_csv(os.path.join(OUT, 'robustezza_loo.csv')).to_string())
T = E.sort_values('rango')
print(T[['nil', 'n_indicatori', 'indice', 'rango', 'rango_min_varianti', 'rango_max_varianti', 'rango_mediano', 'quota_top10_pesi_casuali', 'livello']].head(15).round(2).to_string())
print(T[['nil', 'n_indicatori', 'indice', 'rango', 'rango_min_varianti', 'rango_max_varianti', 'rango_mediano', 'quota_bottom10_pesi_casuali', 'livello']].dropna(subset=['indice']).tail(15).round(2).to_string())
print('classificati', n_ranked)
