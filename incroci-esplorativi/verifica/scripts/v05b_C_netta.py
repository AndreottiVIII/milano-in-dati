"""C, seconda parte: affluenza senza elettori all'estero al denominatore."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
L = open(os.path.join(OUT, 'C2.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
n = pd.read_csv(os.path.join(OUT, 'nil_tabella_C.csv'))
K = ['aff_cam18', 'aff_cam22', 'aff_reg18_netta', 'aff_com21_netta', 'aff_reg23_netta', 'aff_eur24_netta']
n['aff_netta'] = sum((n[k] - n[k].mean()) / n[k].std() for k in K) / len(K)
AGE = ['ita_q18_34', 'ita_q35_49', 'ita_q65_79', 'ita_q80p']
rows = []
def riga(et, df, x, y, c):
    a = analisi(df, x, y, c, B=1500)
    rows.append(dict(prova=et, x=x, y=y, **a)); say(f'{et:62s} {x:12s} {y:18s} {fmt(a)}  top:{a["top5"]}')
x = 'aff_netta'
for y in ['smrTT|2012-2019', 'smrTT|2012-2015', 'smrTT|2016-2019', 'smrTT|2022-2024']:
    riga('base', n, x, y, CTRL)
for y in ['smrTT|2012-2019', 'smrTT|2022-2024']:
    riga('nessun controllo', n, x, y, None)
    riga('+ laureati', n, x, y, CTRL + ['laur_oggi'])
    riga('classi età italiani invece di età media', n, x, y, ['dist_duomo', 'reddito_2024', 'densita_ab_km2'] + AGE)
    riga('classi età + laureati', n, x, y, ['dist_duomo', 'reddito_2024', 'densita_ab_km2', 'laur_oggi'] + AGE)
    riga('+ anagrafe/censimento', n, x, y, CTRL + ['r_anag_cens2021'])
    riga('+ 85+', n, x, y, CTRL + ['ita_q85p'])
    riga('senza 10 NIL con più 85+', n[n.rapp85.rank(ascending=False) > 10], x, y, CTRL)
    riga('+ stranieri', n, x, y, CTRL + ['quota_stranieri'])
    riga('tutti (laureati, classi età, AIRE, anagrafe, 85+, stranieri)', n, x, y, ['dist_duomo', 'reddito_2024', 'densita_ab_km2', 'laur_oggi', 'q_aire', 'r_anag_cens2021', 'ita_q85p', 'quota_stranieri'] + AGE)
    riga('uomini', n, x, y.replace('smrTT', 'smrTM'), CTRL)
    riga('donne', n, x, y.replace('smrTT', 'smrTF'), CTRL)
    riga('italiani', n, x, y.replace('smrTT', 'smrITAT'), CTRL)
    riga('italiani + laureati + età', n, x, y.replace('smrTT', 'smrITAT'), ['dist_duomo', 'reddito_2024', 'densita_ab_km2', 'laur_oggi'] + AGE)
    riga('NIL>=10000', n[n.residenti >= 10000], x, y, CTRL)
    riga('NIL>=10000 + laureati', n[n.residenti >= 10000], x, y, CTRL + ['laur_oggi'])
# età come spiegazione: pendenza affluenza su età nei 70 NIL
say('Spearman aff_netta con: età media %.2f, 18-34 %.2f, 65-79 %.2f, 80+ %.2f, 85+ %.2f' % tuple(stats.spearmanr(n.aff_netta, n[c]).statistic for c in ['eta_media', 'ita_q18_34', 'ita_q65_79', 'ita_q80p', 'ita_q85p']))
say('Spearman SMR2012-19 con: età media %.2f, 80+ %.2f, 85+ %.2f, laureati %.2f, reddito %.2f, dist %.2f, stranieri %.2f' % tuple(stats.spearmanr(n['smrTT|2012-2019'], n[c]).statistic for c in ['eta_media', 'ita_q80p', 'ita_q85p', 'laur_oggi', 'reddito_2024', 'dist_duomo', 'quota_stranieri']))
say('Spearman aff_netta con: laureati %.2f, reddito %.2f, dist %.2f, stranieri %.2f, densità %.2f' % tuple(stats.spearmanr(n.aff_netta, n[c]).statistic for c in ['laur_oggi', 'reddito_2024', 'dist_duomo', 'quota_stranieri', 'densita_ab_km2']))
# confronto laureati vs affluenza come predittori dell'SMR
for y in ['smrTT|2012-2019', 'smrTT|2022-2024']:
    riga('LAUREATI a parità di affluenza netta', n, 'laur_oggi', y, CTRL + ['aff_netta'])
    riga('AFFLUENZA NETTA a parità di laureati', n, 'aff_netta', y, CTRL + ['laur_oggi'])
# prova di permutazione spaziale: quanto è facile avere r così dall'autocorrelazione spaziale?
from numpy.linalg import norm
XY = n[['cx', 'cy']].values
Dm = np.sqrt(((XY[:, None] - XY[None]) ** 2).sum(-1))
# NIL residuo su controlli, poi correlazione residua tra vicini (I di Moran)
def moran(v, soglia=2.0):
    v = v - v.mean(); W = (Dm < soglia) & (Dm > 0)
    return (W * np.outer(v, v)).sum() / W.sum() / (v ** 2).mean()
rx = n[CTRL].rank().values
for y in ['aff_netta', 'smrTT|2012-2019']:
    A = np.column_stack([np.ones(len(n)), rx]); r_ = n[y].rank().values
    e = r_ - A @ np.linalg.lstsq(A, r_, rcond=None)[0]
    say('Moran (entro 2 km) del residuo di', y, round(moran(e), 3))
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'C_prove_netta.csv'), index=False)
L.close()
