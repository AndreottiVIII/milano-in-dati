import sys, os
sys.path.insert(0, sys.argv[1])
from vc import *
n = pd.read_csv(os.path.join(OUT, 'nil_tabella_finale.csv'))
e = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv'))
print('colonne', [c for c in e.columns if c.startswith('n_') or c.startswith('q_') or c == 'residenti'])
def piv(col): return e.pivot_table(index='id_nil', columns='anno', values=col)
R, K = piv('residenti'), piv('n_0_14')
A = R - K
for a_, b_ in [(2014, 2019), (2019, 2024)]:
    t = f'{a_}_{b_}'
    n['dR' + t] = n.id_nil.map((R[b_] / R[a_] - 1) * 100)
    n['dK' + t] = n.id_nil.map((K[b_] / K[a_] - 1) * 100)
    n['dA' + t] = n.id_nil.map((A[b_] / A[a_] - 1) * 100)
    n['dQ' + t] = n.id_nil.map((K[b_] / R[b_] - K[a_] / R[a_]) * 100)
n['q014'] = n.q014_2014 if 'q014_2014' in n else n.id_nil.map(e[e.anno == 2014].set_index('id_nil').q_0_14 * 100)
d = n[n.air_picc != True]
cc = CTRL + ['q014']
nomi = dict(dK='bambini 0-14', dR='tutti i residenti', dA='residenti senza i bambini', dQ='quota di bambini (punti)')
for t in ['2014_2019', '2019_2024']:
    for k, lab in nomi.items():
        print(t, f'{lab:28s}', 'sempl %+.2f' % stats.spearmanr(d.air100, d[k + t], nan_policy='omit').statistic, fmt(analisi(d, 'air100', k + t, cc, B=1000)))
d = d.assign(terzo=pd.qcut(d.air100, 3, labels=['pochi', 'medi', 'molti']))
r2 = d.id_nil.map(R[2019]); r4 = d.id_nil.map(R[2024]); k2 = d.id_nil.map(K[2019]); k4 = d.id_nil.map(K[2024])
for g in ['pochi', 'medi', 'molti']:
    m = d.terzo == g
    print(g, 'bambini %+.1f%%' % ((k4[m].sum() / k2[m].sum() - 1) * 100), 'residenti %+.1f%%' % ((r4[m].sum() / r2[m].sum() - 1) * 100), 'quartieri', int(m.sum()))
print('citta bambini %+.1f%% residenti %+.1f%%' % ((K[2024].sum() / K[2019].sum() - 1) * 100, (R[2024].sum() / R[2019].sum() - 1) * 100))
