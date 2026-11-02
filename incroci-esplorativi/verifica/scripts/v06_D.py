"""D: indice senza reddito; quartieri dove il reddito per CAP descrive male."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 300)
L = open(os.path.join(OUT, 'D.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
n = pd.read_csv(os.path.join(OUT, 'nil_tabella_C.csv'))
K = ['aff_cam18', 'aff_cam22', 'aff_reg18_netta', 'aff_com21_netta', 'aff_reg23_netta', 'aff_eur24_netta']
n['aff_netta'] = sum((n[k] - n[k].mean()) / n[k].std() for k in K) / len(K)
lav = pd.read_csv(p('docs', 'lavoro', 'data', 'nil_lavoro.csv'))
n['occ_2023'] = n.id_nil.map(lav[lav.anno == 2023].set_index('nil').tasso_occ)
n['occ_2011'] = n.id_nil.map(lav[lav.anno == 2011].set_index('nil').tasso_occ)
n['disocc_2011'] = n.id_nil.map(lav[lav.anno == 2011].set_index('nil').tasso_disocc)
# censimento 2011: superficie per persona, proprietà
s = pd.read_csv(p('censimenti', 'pulito', 'sezioni_2011.csv'), low_memory=False)
keyc = [c for c in s.columns if c.upper().startswith('SEZ')][0]
s['sez'] = s[keyc].astype(str).str.replace(r'\.0$', '', regex=True).str[-7:].astype(int)
sa = pd.read_csv(p('censimenti', 'pulito', 'sezioni_armonizzate.csv'), usecols=['sez', 'anno', 'nil'], low_memory=False)
s = s.merge(sa[sa.anno == 2011], on='sez', how='inner')
g = s.groupby('nil')[['A44', 'A46', 'A47', 'A48', 'P1']].sum()
n['mq_persona_2011'] = n.id_nil.map(g.A44 / g.P1)
n['q_proprieta_2011'] = n.id_nil.map(g.A47 / (g.A46 + g.A47 + g.A48) * 100)
cp = pd.read_csv(p('docs', 'case-popolari', 'data', 'nil.csv'), sep=';')
n['aler'] = n.id_nil.map(cp.set_index('id_nil').canone_ALER_2016_per_abitazione_euro)
# Indicatori: nome, verso
IND = {'laur_oggi': 1, 'occ_2011': 1, 'disocc_2011': -1, 'prezzo_2026_reale': 1, 'mq_persona_2011': 1, 'q_proprieta_2011': 1, 'aler': -1}
say('Disponibilità:'); say(n[list(IND)].notna().sum().to_string())
say('Spearman tra indicatori e reddito:'); say(n[list(IND) + ['reddito_2024']].corr(method='spearman').round(2).to_string())
d = n.dropna(subset=list(IND)).copy()
say('NIL con tutti gli indicatori', len(d))
R_ = pd.DataFrame({k: v * d[k].rank().values for k, v in IND.items()}, index=d.index)
Z = (R_ - R_.mean()) / R_.std()
d['indice'] = Z.mean(axis=1)
d['r_ind'] = d.indice.rank(); d['r_red'] = d.reddito_2024.rank(); d['gap'] = d.r_ind - d.r_red
say('Spearman indice-reddito', round(stats.spearmanr(d.indice, d.reddito_2024).statistic, 3), 'indice-reddito 2019-22', round(stats.spearmanr(d.indice, d.reddito_2019_22_euro2025).statistic, 3))
PCA = np.linalg.svd(Z.values - Z.values.mean(0), full_matrices=False)
say('Prima componente: quota varianza', round((PCA[1] ** 2 / (PCA[1] ** 2).sum())[0], 3), 'pesi', dict(zip(IND, PCA[2][0].round(2))))
# pesi casuali
rng = np.random.default_rng(SEED)
W = rng.dirichlet(np.ones(len(IND)), 5000)
ind_mc = Z.values @ W.T
ranks_mc = pd.DataFrame(ind_mc).rank(axis=0).values
gaps = ranks_mc - d.r_red.values[:, None]
d['gap_p5'] = np.percentile(gaps, 5, axis=1); d['gap_p95'] = np.percentile(gaps, 95, axis=1)
absrank = pd.DataFrame(np.abs(gaps)).rank(axis=0, ascending=False).values
d['freq_top10'] = (absrank <= 10).mean(axis=1)
d['sempre_stesso_segno'] = (np.sign(d.gap_p5) == np.sign(d.gap_p95))
# togliendo un indicatore e varianti
var = {}
for k in IND:
    var['senza ' + k] = Z.drop(columns=[k]).mean(axis=1)
var['senza OMI e proprietà'] = Z.drop(columns=['prezzo_2026_reale', 'q_proprieta_2011']).mean(axis=1)
var['solo censimento (laureati, occ, disocc)'] = Z[['laur_oggi', 'occ_2011', 'disocc_2011']].mean(axis=1)
var['pca1'] = pd.Series(np.sign(PCA[2][0].sum()) * (Z.values @ PCA[2][0]), index=Z.index)
for k, v in var.items():
    gp = v.rank() - d.r_red
    d['gap ' + k] = gp
    say(f"variante {k:40s} Spearman con indice base {stats.spearmanr(v, d.indice).statistic:.3f}; Spearman dei gap {stats.spearmanr(gp, d.gap).statistic:.3f}; top10 in comune {len(set(gp.abs().nlargest(10).index) & set(d.gap.abs().nlargest(10).index))}")
gr = d[[c for c in d.columns if c.startswith('gap ')]]
d['gap_min'] = gr.min(axis=1); d['gap_max'] = gr.max(axis=1)
d['gap_red1922'] = d.r_ind - d.reddito_2019_22_euro2025.rank()
cap = pd.read_csv(p('quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv')).dropna(subset=['ID_NIL']); cap['id_nil'] = cap.ID_NIL.astype(int)
dom = cap.sort_values('quota_nil').groupby('id_nil').tail(1).set_index('id_nil')
d['cap_dom'] = d.id_nil.map(dom.CAP); d['q_cap_dom'] = d.id_nil.map(dom.quota_nil)
cols = ['nil', 'reddito_2024', 'r_red', 'r_ind', 'gap', 'gap_p5', 'gap_p95', 'freq_top10', 'gap_min', 'gap_max', 'gap_red1922', 'cap_dom', 'q_cap_dom', 'laur_oggi', 'prezzo_2026_reale']
o = d.sort_values('gap')[cols].round(2)
o.to_csv(os.path.join(OUT, 'D_divergenze.csv'), index=False)
say('\nReddito sovrastima (il reddito è più alto degli indicatori):'); say(o.head(12).to_string())
say('\nReddito sottostima:'); say(o.tail(12).iloc[::-1].to_string())
say('\nI più stabili (top10 con pesi casuali in >=80% delle estrazioni):')
say(d[d.freq_top10 >= .8].sort_values('gap')[['nil', 'gap', 'gap_p5', 'gap_p95', 'freq_top10', 'gap_min', 'gap_max']].round(2).to_string())
# Il problema è la grana?
say('\nSpearman |gap| con quota del CAP dominante', round(stats.spearmanr(d.gap.abs(), d.q_cap_dom).statistic, 3))
say('Spearman gap con stranieri', round(stats.spearmanr(d.gap, d.quota_stranieri).statistic, 3), ' con distanza', round(stats.spearmanr(d.gap, d.dist_duomo).statistic, 3), 'età', round(stats.spearmanr(d.gap, d.eta_media).statistic, 3), 'q_aire', round(stats.spearmanr(d.gap, d.q_aire).statistic, 3))
cc = d[d.groupby('cap_dom').cap_dom.transform('size') >= 2]
say('Quota della varianza del gap dentro lo stesso CAP dominante', round(1 - (cc.groupby('cap_dom').gap.transform('mean').var() / cc.gap.var()), 3), 'n', len(cc))
# Prove separate: mortalità e affluenza
rows = []
for y in ['smrTT|2012-2019', 'smrTT|2022-2024', 'smrTM|2012-2019', 'aff_netta', 'aff_cam22', 'aff_com21']:
    c0 = ['dist_duomo', 'eta_media', 'densita_ab_km2']
    a = analisi(d, 'indice', y, c0 + ['reddito_2024'], B=1500); bb = analisi(d, 'reddito_2024', y, c0 + ['indice'], B=1500)
    g_ = analisi(d, 'gap', y, c0, B=1500)
    # indice senza laureati, per non ripetere il filone A
    d['indice_nl'] = Z.drop(columns=['laur_oggi']).mean(axis=1)
    a2 = analisi(d, 'indice_nl', y, c0 + ['reddito_2024'], B=800)
    say(f"{y:18s} indice|reddito {fmt(a)} ; reddito|indice {fmt(bb)} ; gap {fmt(g_)} ; indice senza laureati|reddito {fmt(a2)}")
    rows.append(dict(y=y, **{'ind_' + k: v for k, v in a.items()}, **{'red_' + k: v for k, v in bb.items()}))
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'D_prove.csv'), index=False)
# SMR dei gruppi: stesso reddito, indice diverso
d['grp'] = pd.cut(d.gap, [-99, -12, 12, 99], labels=['reddito alto rispetto a indice', 'in linea', 'indice alto rispetto a reddito'])
t = d.groupby('grp', observed=True).agg(n=('gap', 'size'), red=('reddito_2024', 'median'), laur=('laur_oggi', 'median'), smr=('smrTT|2012-2019', 'median'), aff=('aff_netta', 'median'), O=('O|2012-2019', 'sum'), E=('E|2012-2019', 'sum'))
t['smr_pop'] = t.O / t.E
say(t.round(2).to_string())
d.to_csv(os.path.join(OUT, 'nil_tabella_D.csv'), index=False)
L.close()
