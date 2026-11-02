"""Fase 2, misura dell'effetto degli errori trovati."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
from shapely.geometry import shape
L = open(os.path.join(OUT, 'fase2b.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 30)
g = json.load(open(p('docs', 'quartiere', 'data', 'nil.geojson'), encoding='utf8'))
REF = {f['properties']['i']: f['properties']['n'] for f in g['features']}; POL = {f['properties']['i']: shape(f['geometry']).buffer(0) for f in g['features']}
n = pd.read_csv(os.path.join(OUT, 'nil_tabella_finale.csv')); A_ids = list(n.id_nil); nomi = set(REF.values())
say('Nomi scritti a mano in 07:', {k: (k in nomi) for k in ['Morivione', 'Muggiano', 'San Siro', 'Duomo', 'Brera', 'Guastalla', 'Porta Vigentina - Porta Lodovica']})
say('Nomi diversi tra quartiere/geojson e popolazione nei 70:', [(i, REF[i], m) for i, m in zip(n.id_nil, n.nil) if REF[i] != m][:15])
# flussi
fl = pd.read_csv(p('popolazione', 'pulito', 'flussi_nil_riepilogo.csv'))
piv = {c: fl[fl.id_nil.isin(A_ids)].pivot(index='id_nil', columns='periodo', values=c) for c in ['saldo_italia_x1000_anno', 'saldo_estero_x1000_anno']}
for c, t in piv.items():
    say(c); say(t.corr(method='spearman').round(2).to_string())
    n['_a'] = n.id_nil.map(t['2004-2019']); n['_b'] = n.id_nil.map(t['2012-2019']); n['_c'] = n.id_nil.map(t['2022-2024']); n['_d'] = n.id_nil.map(t['2020-2024'])
    for y in ['smrTT|2012-2019', 'aff_netta', 'reddito_2024', 'quota_stranieri', 'laur_oggi']:
        say(f'  {y:18s} scritto come 12_19 (in realtà 2004-19) {stats.spearmanr(n._a, n[y]).statistic:+.2f} | vero 2012-19 {stats.spearmanr(n._b, n[y]).statistic:+.2f} || scritto come 20_24 (in realtà 2022-24) {stats.spearmanr(n._c, n[y]).statistic:+.2f} | vero 2020-24 {stats.spearmanr(n._d, n[y]).statistic:+.2f}')
# wiki
tl = pd.read_csv(p('luoghi-cercati', 'pulito', 'totali_luogo.csv'), sep=';', low_memory=False)
t = tl[tl.id_nil.notna()].copy(); t['id_nil'] = t.id_nil.astype(int)
say('\nLetture con id_nil per tipo (milioni):', (t.groupby('tipo').views_totali.sum() / 1e6).round(1).to_dict())
say('Prime voci non luogo con NIL:', t[t.tipo != 'luogo'].sort_values('views_totali', ascending=False)[['nome', 'tipo', 'nil', 'views_totali']].head(10).values.tolist())
tutto = t.groupby('id_nil').agg(v=('views_totali', 'sum'), it=('views_it', 'sum'), k=('qid', 'size')); solo = t[t.tipo == 'luogo'].groupby('id_nil').agg(v=('views_totali', 'sum'), it=('views_it', 'sum'), k=('qid', 'size'))
are = n.set_index('id_nil').area_km2
a1 = (tutto.v / are).reindex(A_ids); a2 = (solo.v / are).reindex(A_ids)
q1 = ((1 - tutto.it / tutto.v).where(tutto.k >= 5) * 100).reindex(A_ids); q2 = ((1 - solo.it / solo.v).where(solo.k >= 5) * 100).reindex(A_ids)
say('Spearman letture/km2 tutte contro solo luoghi', round(stats.spearmanr(a1, a2, nan_policy='omit').statistic, 3), ' quota estero', round(stats.spearmanr(q1, q2, nan_policy='omit').statistic, 3))
say('Quota sul NIL di voci non luogo: mediana', round(((tutto.v - solo.v.reindex(tutto.index).fillna(0)) / tutto.v).reindex(A_ids).median(), 3), 'massimo', ((tutto.v - solo.v.reindex(tutto.index).fillna(0)) / tutto.v).reindex(A_ids).sort_values().tail(4).round(2).to_dict())
for nm, s_ in [('tutte', q1), ('solo luoghi', q2)]:
    n['_q'] = s_.values
    say('quota estero', nm, 'con reddito parziale', fmt(analisi(n, '_q', 'laur_oggi', ['dist_duomo', 'eta_media', 'densita_ab_km2'], B=200)))
# Wm, vicini veri
ids = sorted(POL); righe = [(a, b) for a in ids for b in ids if a < b and POL[a].buffer(0.0003).intersects(POL[b])]
pos = {i: k for k, i in enumerate(A_ids)}; W = np.zeros((len(A_ids), len(A_ids)))
for a, b in righe:
    if a in pos and b in pos:
        W[pos[a], pos[b]] = W[pos[b], pos[a]] = 1
n_ = len(A_ids); H = np.eye(n_) - 1 / n_; lam, U = np.linalg.eigh(H @ W @ H); U2 = U[:, np.abs(U.T @ np.ones(n_)) < 1e-6]
say('msr con la contiguità reale: colonne', U2.shape[1], 'su', n_, 'autovalori quasi nulli', int((np.abs(lam) < 1e-8).sum()), 'grado min', W.sum(1).min())
L.close()
