"""Ultime prove: G con Sinistra+Centro, O con prezzi, A/B riepilogo; Q limite superiore; scrive il riepilogo di fase 1."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
L = open(os.path.join(OUT, 'rifiniture.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
n = pd.read_csv(os.path.join(OUT, 'nil_tabella_finale.csv'))
say('== G: famiglie 2021 costanti; sinistra+centro; solo PD; destra')
for eid in ELEZ_POL:
    t = eid.split('-')[0]; e = elezione(eid).set_index('id_nil')
    n[f'q_sxce|{t}'] = n.id_nil.map(e.q_sx + e.q_ce.fillna(0)); n[f'q_ce|{t}'] = n.id_nil.map(e.q_ce); n[f'q_m5|{t}'] = n.id_nil.map(e.q_m5)
    say(f"{t:28s} sx {parz(n.fam_2021.values, n[f'q_sx|{t}'].values, n[CTRL].values):+.2f} | sx+centro {parz(n.fam_2021.values, n[f'q_sxce|{t}'].values, n[CTRL].values):+.2f} | dx {parz(n.fam_2021.values, n[f'q_dx|{t}'].values, n[CTRL].values):+.2f} | semplice sx {stats.spearmanr(n.fam_2021, n[f'q_sx|{t}']).statistic:+.2f} sx+c {stats.spearmanr(n.fam_2021, n[f'q_sxce|{t}']).statistic:+.2f}")
a = analisi(n, 'fam_2021', 'q_sxce|camera_2022', CTRL, B=800); say('sx+centro camera 2022:', fmt(a)); a = analisi(n, 'fam_2021', 'q_sxce|camera_2018', CTRL, B=800); say('sx+centro camera 2018:', fmt(a))
say('\n== O: Airbnb è specifico o è il prezzo?')
n['q014'] = n.q014_2014
for y in ['k_2019_2024', 'k_2014_2019']:
    d = n[n.air_picc != True]
    say(y, 'prezzo:', fmt(analisi(d, 'prezzo_2026_reale', y, CTRL + ['q014'], B=500)))
    say(y, 'Airbnb a parità di prezzo:', fmt(analisi(d, 'air100', y, CTRL + ['q014', 'prezzo_2026_reale'], B=500)))
    say(y, 'Airbnb a parità di stranieri:', fmt(analisi(d, 'air100', y, CTRL + ['q014', 'quota_stranieri'], B=500)))
    say(y, 'prezzo a parità di Airbnb:', fmt(analisi(d, 'prezzo_2026_reale', y, CTRL + ['q014', 'air100'], B=500)))
e = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv')); w = e[e.anno.isin([2019, 2024])].pivot_table(index='id_nil', columns='anno', values='n_0_14').sum()
say('bambini 0-14 città 2019, 2024', w.to_dict())
say('\n== Q: limite superiore della vera dispersione 2020')
from scipy.stats import chi2
X2 = 73.2; df = 69; phi_hi = X2 / chi2.ppf(.025, df); phi_lo = X2 / chi2.ppf(.975, df); say(f'phi tra {phi_lo:.2f} e {phi_hi:.2f}; dispersione vera SD massima circa {np.sqrt(max(phi_hi - 1, 0)) * .097:.3f}')
L.close()
