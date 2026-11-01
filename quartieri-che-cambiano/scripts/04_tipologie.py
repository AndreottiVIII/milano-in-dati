"""Passo 4 - tipologie (livello x cambiamento), prova di raggruppamento automatico, municipi, ampiezza, scarto dal livello.

Tipologie con regola semplice e dichiarata (terzili tra i NIL classificati):
  cambiamento = indice di base (terzile alto / medio / basso); livello = media z di reddito 2024, prezzo 2026, laureati 2023 (alto se >= +0,5, basso se <= -0,5).
  - "In salita rapida"           : cambiamento alto e livello non alto
  - "Alti e ancora in salita"    : cambiamento alto e livello alto
  - "Gia alti e stabili"         : cambiamento basso e livello alto
  - "Fermi su livelli bassi"     : cambiamento basso e livello basso
  - "Fermi su livelli medi"      : cambiamento basso e livello medio
  - "Nella media"                : cambiamento medio
Prova di raggruppamento automatico: k-means (k = 2..6) su (indice, livello) e sui tre blocchi + livello, con silhouette.
Uso: python -I -X utf8 04_tipologie.py <milano-in-dati> <quartieri-che-cambiano>
"""
import sys, os, json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

BASE, QC = sys.argv[1], sys.argv[2]
OUT = os.path.join(QC, 'out')
E = pd.read_csv(os.path.join(OUT, 'indice_nil.csv'), index_col=0)
D = pd.read_csv(os.path.join(OUT, 'indicatori_nil.csv'), index_col=0)
anag = pd.read_csv(os.path.join(BASE, 'popolazione', 'pulito', 'nil_anagrafica.csv')).set_index('id_nil')
E['municipio'] = anag.municipio_prevalente.reindex(E.index)
C = E.dropna(subset=['indice', 'livello']).copy()
res = {'n_classificati': int(len(C))}

q = lambda s, p: s.quantile(p)
c_lo, c_hi = q(C.indice, 1 / 3), q(C.indice, 2 / 3)
l_lo, l_hi = -0.5, 0.5   # livello: z medio di reddito 2024, prezzo 2026 e laureati 2023; soglie fisse +-0,5
res['soglie'] = {'indice_terzo_basso': round(float(c_lo), 3), 'indice_terzo_alto': round(float(c_hi), 3),
                 'livello_basso_fino_a': l_lo, 'livello_alto_da': l_hi}


def tipo(r):
    ch = 'alto' if r.indice >= c_hi else ('basso' if r.indice <= c_lo else 'medio')
    lv = 'alto' if r.livello >= l_hi else ('basso' if r.livello <= l_lo else 'medio')
    if ch == 'alto':
        return 'Alti e ancora in salita' if lv == 'alto' else 'In salita rapida'
    if ch == 'basso':
        return {'alto': 'Già alti e stabili', 'basso': 'Fermi su livelli bassi', 'medio': 'Fermi su livelli medi'}[lv]
    return 'Nella media'


C['tipologia'] = C.apply(tipo, axis=1)
# stabilita' della tipologia: quota di estrazioni con pesi casuali che lasciano il NIL nello stesso terzile di cambiamento
res['tipologie_conteggio'] = C.tipologia.value_counts().to_dict()

# tipologia robusta: stesso terzile di cambiamento in tutte le varianti? Si usa il rango min/max delle varianti
n = len(C)
C['terzile_cambiamento'] = np.where(C.indice >= c_hi, 'alto', np.where(C.indice <= c_lo, 'basso', 'medio'))
C['terzile_stabile'] = ((C.rango_max_varianti <= n / 3 + 3) & (C.terzile_cambiamento == 'alto')) | \
                       ((C.rango_min_varianti >= 2 * n / 3 - 3) & (C.terzile_cambiamento == 'basso'))

# ampiezza: numero di indicatori su 9 con z > 0,5 (segnali concordi)
zc = [c for c in E.columns if c.startswith('z_') and c[2:] in ['reddito_var', 'prezzo_var', 'affitto_var', 'costruzioni_100', 'airbnb_100', 'ristoranti_var', 'botteghe_var', 'giovani_var', 'laureati_var']]
C['n_segnali_alti'] = (C[zc] > 0.5).sum(axis=1)
C['n_segnali_bassi'] = (C[zc] < -0.5).sum(axis=1)

# scarto dal livello: indice meno quanto previsto dal livello (retta)
b = np.polyfit(C.livello, C.indice, 1)
C['scarto_dal_livello'] = C.indice - (b[0] * C.livello + b[1])
res['retta_indice_su_livello'] = {'pendenza': round(float(b[0]), 3), 'intercetta': round(float(b[1]), 3),
                                  'spearman': round(float(C[['indice', 'livello']].corr(method='spearman').iloc[0, 1]), 3)}

# raggruppamento automatico
sil = {}
for nome, cols in [('indice+livello', ['indice', 'livello']), ('tre_blocchi+livello', ['blocco_casa', 'blocco_negozi', 'blocco_persone', 'livello'])]:
    X = C[cols].dropna()
    X = (X - X.mean()) / X.std(ddof=0)
    sil[nome] = {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, n_init=20, random_state=20261101).fit(X)
        sil[nome][k] = round(float(silhouette_score(X, km.labels_)), 3)
res['silhouette_kmeans'] = sil

# municipi (media pesata con i residenti 2024)
w = lambda g, c: np.average(g[c].dropna(), weights=g.loc[g[c].notna(), 'residenti_2024'])
mun = C.groupby('municipio').apply(lambda g: pd.Series({'n_NIL': len(g), 'residenti_2024': g.residenti_2024.sum(), 'indice_medio_pesato': w(g, 'indice'),
                                                         'livello_medio_pesato': w(g, 'livello'), 'blocco_casa': w(g, 'blocco_casa'),
                                                         'blocco_negozi': w(g, 'blocco_negozi'), 'blocco_persone': w(g, 'blocco_persone')}), include_groups=False)
mun.round(3).to_csv(os.path.join(OUT, 'municipi.csv'))

# segnalazione: residenti cresciuti di oltre il 25% in 11 anni (probabile nuovo quartiere; il filone costruzioni non e' ancora disponibile)
C['residenti_oltre_25pct'] = C.pop_var > 25
keep = ['nil', 'municipio', 'pop_var', 'residenti_oltre_25pct', 'residenti_2024', 'n_indicatori', 'indice', 'rango', 'rango_min_varianti', 'rango_max_varianti', 'rango_mediano', 'rango_p5', 'rango_p95',
        'quota_top10_pesi_casuali', 'quota_bottom10_pesi_casuali', 'livello', 'rango_livello', 'blocco_casa', 'blocco_negozi', 'blocco_persone', 'tipologia',
        'terzile_cambiamento', 'terzile_stabile', 'n_segnali_alti', 'n_segnali_bassi', 'scarto_dal_livello']
C[keep].sort_values('rango').to_csv(os.path.join(OUT, 'tipologie_nil.csv'))
res['stabilita_terzile'] = {'alto_stabile': int(((C.terzile_cambiamento == 'alto') & C.terzile_stabile).sum()), 'alto': int((C.terzile_cambiamento == 'alto').sum()),
                            'basso_stabile': int(((C.terzile_cambiamento == 'basso') & C.terzile_stabile).sum()), 'basso': int((C.terzile_cambiamento == 'basso').sum())}
json.dump(res, open(os.path.join(OUT, 'tipologie_log.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
pd.set_option('display.width', 250)
print(json.dumps(res, ensure_ascii=False, indent=1))
print(mun.round(2).to_string())
for t, g in C.groupby('tipologia'):
    print('\n==', t, len(g))
    print(g.sort_values('rango')[['nil', 'rango', 'indice', 'livello', 'n_segnali_alti', 'terzile_stabile']].round(2).to_string())
print(C.sort_values('scarto_dal_livello')[['nil', 'rango', 'rango_livello', 'scarto_dal_livello']].round(2).iloc[[0, 1, 2, 3, -4, -3, -2, -1]].to_string())
