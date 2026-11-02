"""B, seconda parte: il segno del 1991 è curvatura, età dei laureati o altro?  A: differenza appaiata al livello CAP."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
L = open(os.path.join(OUT, 'B2.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
n = pd.read_csv(os.path.join(OUT, 'nil_tabella_AB.csv'))
e = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv'))
e23 = e[e.anno == 2023].set_index('id_nil')
n['q2534'] = n.id_nil.map(e23.n_25_34 / e23.residenti * 100); n['q2034'] = n.id_nil.map(e23.n_20_34 / e23.residenti * 100)
c = pd.read_csv(p('censimenti', 'pulito', 'indicatori_NIL.csv'))
n['q65_91'] = n.id_nil.map(c[c.anno == 1991].set_index('nil').quota_65p)
n['eta_91'] = n.id_nil.map(c[c.anno == 1991].set_index('nil').eta_media_classi)
n['var_pop'] = n.pop_2023 / n.pop_1991
n['rl'] = n.laur_oggi.rank(); n['rl2'] = (n.rl - n.rl.mean()) ** 2
n['rd2'] = (n.dist_duomo.rank() - 35) ** 2
n['delta'] = n.laur_oggi - n.laur_1991
ys = ['q_sx|camera_2018', 'q_dx|camera_2018', 'q_sx|comunali_consiglio_2021', 'q_dx|comunali_consiglio_2021', 'q_sx|camera_2022', 'q_dx|camera_2022', 'q_sx|europee_2024', 'q_dx|europee_2024']
C = CTRL + ['laur_oggi']
TEST = {'base': (n, C), 'curva laureati oggi': (n, C + ['rl2']), 'curva distanza': (n, C + ['rd2']), '+25-34 anni': (n, C + ['q2534']), '+età 1991': (n, C + ['eta_91']), '+var pop 1991-2023': (n, C + ['var_pop']),
        '+stranieri': (n, C + ['quota_stranieri']), 'senza Municipio 1': (n[n.municipio != 1], C), 'senza 10 NIL più laureati 1991': (n[n.laur_1991.rank(ascending=False) > 10], C), 'NIL>=10000': (n[n.residenti >= 10000], C),
        '+curva+25-34+stranieri': (n, C + ['rl2', 'q2534', 'quota_stranieri']), 'reddito 2019-22': (n, ['dist_duomo', 'reddito_2019_22_euro2025', 'eta_media', 'densita_ab_km2', 'laur_oggi'])}
rows = []
for k, (d, cc) in TEST.items():
    for y in ys:
        a = analisi(d, 'laur_1991', y, cc, B=500)
        rows.append(dict(prova=k, y=y, **a))
T = pd.DataFrame(rows); T.to_csv(os.path.join(OUT, 'B2_prove.csv'), index=False)
for k in TEST:
    t = T[T.prova == k]
    say(f"{k:34s} n={t.n.iloc[0]} " + ' '.join(f"{a.split('|')[0][2:]}{a.split('|')[1][:3]}{a[-2:]}:{r:+.2f}" for a, r in zip(t.y, t.r)))
say('\nDettaglio base per elezioni:')
say(T[T.prova == 'base'][['y', 'n', 'r', 'lo', 'hi', 'r_senza5', 'r_senza5_avverso', 'top5']].to_string())
# famiglie
fam_rows = []
for t in ['camera_2018', 'europee_2019', 'camera_2022', 'europee_2024', 'comunali_consiglio_2021']:
    for v in ['q_pd', 'q_csx_sx', 'q_cdx', 'q_lega', 'q_dest', 'q_m5', 'q_ce']:
        y = f'{v}|{t}'
        if y in n and n[y].notna().sum() > 50 and n[y].std() > 0:
            a = analisi(n, 'laur_1991', y, C, B=300); fam_rows.append(dict(y=y, r=a['r'], lo=a['lo'], hi=a['hi'], s5=a['r_senza5']))
say(pd.DataFrame(fam_rows).to_string())
# Quartieri che spingono
y = 'q_sx|comunali_consiglio_2021'
n['res_1991'] = 0.0
rz = np.column_stack([n[k].rank().values for k in C]); A = np.column_stack([np.ones(len(n)), rz])
n['res_1991'] = n.laur_1991.rank().values - A @ np.linalg.lstsq(A, n.laur_1991.rank().values, rcond=None)[0]
n['res_y'] = n[y].rank().values - A @ np.linalg.lstsq(A, n[y].rank().values, rcond=None)[0]
s = n.sort_values('res_1991')
say('NIL con 1991 BASSO rispetto a oggi:', s.head(10)[['nil', 'laur_1991', 'laur_oggi', y]].round(1).values.tolist())
say('NIL con 1991 ALTO rispetto a oggi:', s.tail(10)[['nil', 'laur_1991', 'laur_oggi', y]].round(1).values.tolist())
# Diff appaiata al CAP
Cc = pd.read_csv(os.path.join(OUT, 'A_livello_CAP.csv'))
say(Cc[(Cc['var'] == '38cap')][['el', 'voto', 'n', 'r_laur', 'l_lo', 'l_hi', 'r_redd', 'r_lo', 'r_hi']].to_string())
L.close()
