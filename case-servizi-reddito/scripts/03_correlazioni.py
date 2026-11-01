"""Prezzo OMI vs servizi vs reddito, per zona OMI (2026/1, abitazioni civili): Spearman, correlazione parziale, regressione sui logaritmi.
Uso: python -I -X utf8 03_correlazioni.py <ABS case-servizi-reddito>
Entrata: out/zone_tabella.csv (da 02). Uscite: out/correlazioni_spearman.csv, out/spearman_parziale.csv, out/modelli.csv, out/robustezza.csv,
         out/risultati_03.json, out/grafico_scatter.png
I prezzi OMI sono STIME dell'Agenzia delle Entrate, non prezzi di vendita reali.
Campione principale: zone con prezzo, senza D39 (Cascina Merlata: nel registro dei civici ha 105 indirizzi e il punteggio e falsato,
vedi citta-15-minuti/NOTE.md). Intervalli di confidenza: bootstrap sulle zone (5000 ripetizioni, seme 20261101) ed errori robusti HC3.
Con circa 41 zone gli intervalli sono ampi.
"""
import sys, json
import numpy as np, pandas as pd
from scipy import stats

O = sys.argv[1].replace(chr(92), '/').rstrip('/')
SEED, NB = 20261101, 5000
t = pd.read_csv(O + '/out/zone_tabella.csv')
t = t[t.prezzo_eur_m2.notna()].copy()
t['lnP'] = np.log(t.prezzo_eur_m2)
t['lnR'] = np.log(t.affitto_eur_m2_mese)
t['lnY'] = np.log(t.reddito_imponibile_medio_2024_pesato)
t['d_km'] = t.dist_duomo_centroide_m / 1000
t['lnD'] = np.log(t.d_km)
t['dm_km'] = t.dist_duomo_media_civici_m / 1000
t['lnDm'] = np.log(t.dm_km)
t['S10'] = t.servizi10_pesato
t['S20'] = t.servizi20_pesato
t['SX'] = t.servizi_extra_pesato
t['fascia'] = t.zona.str[0]
for f in 'CDE':
    t['F_' + f] = (t.fascia == f).astype(float)   # B = riferimento
RES = {}


def sample(df, escludi=('D39',), minres=0, solo_normale=False):
    d = df[~df.zona.isin(escludi)]
    if minres:
        d = d[d.n_civici_residenziali >= minres]
    if solo_normale:
        d = d[d.stato_prevalente == 'NORMALE']
    return d


def ols(y, X, names):
    X1 = np.column_stack([np.ones(len(y)), X])
    n, k = X1.shape
    XtXi = np.linalg.inv(X1.T @ X1)
    b = XtXi @ X1.T @ y
    e = y - X1 @ b
    h = np.einsum('ij,jk,ik->i', X1, XtXi, X1)
    meat = X1.T @ (X1 * ((e / (1 - h)) ** 2)[:, None])      # HC3
    V = XtXi @ meat @ XtXi
    se = np.sqrt(np.diag(V))
    r2 = 1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum()
    adj = 1 - (1 - r2) * (n - 1) / (n - k)
    return dict(b=dict(zip(['const'] + names, b)), se=dict(zip(['const'] + names, se)), r2=r2, r2adj=adj, n=n)


def boot_ci(df, ycol, xcols, target, nb=NB, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(df)
    out = []
    Y = df[ycol].values
    X = df[xcols].values
    for _ in range(nb):
        i = rng.integers(0, n, n)
        X1 = np.column_stack([np.ones(n), X[i]])
        b = np.linalg.lstsq(X1, Y[i], rcond=None)[0]
        out.append(b[1 + xcols.index(target)])
    return np.percentile(out, [2.5, 97.5])


def partial_spearman(df, x, y, ctrl, nb=NB, seed=SEED):
    def pr(d):
        r = d[[x, y] + ctrl].rank().values
        C = np.column_stack([np.ones(len(d)), r[:, 2:]]) if ctrl else np.ones((len(d), 1))
        rx = r[:, 0] - C @ np.linalg.lstsq(C, r[:, 0], rcond=None)[0]
        ry = r[:, 1] - C @ np.linalg.lstsq(C, r[:, 1], rcond=None)[0]
        return np.corrcoef(rx, ry)[0, 1]
    est = pr(df)
    rng = np.random.default_rng(seed)
    n = len(df)
    bs = []
    for _ in range(nb):
        i = rng.integers(0, n, n)
        d = df.iloc[i]
        if d[x].nunique() < 3 or d[y].nunique() < 3:
            continue
        v = pr(d)
        if np.isfinite(v):
            bs.append(v)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return est, lo, hi


def spearman_ci(df, a, b, nb=NB, seed=SEED):
    est = stats.spearmanr(df[a], df[b]).statistic
    rng = np.random.default_rng(seed)
    n = len(df)
    bs = []
    for _ in range(nb):
        i = rng.integers(0, n, n)
        d = df.iloc[i]
        v = stats.spearmanr(d[a], d[b]).statistic
        if np.isfinite(v):
            bs.append(v)
    return est, *np.percentile(bs, [2.5, 97.5])


main = sample(t)
RES['n_zone_principale'] = len(main)
RES['zone_escluse_dal_principale'] = ['R2 (nessun prezzo OMI)', 'D39 (punteggio servizi falsato)']
RES['n_zone_con_prezzo'] = len(t)

# ---- 1. Spearman a due a due
vars_ = [('prezzo_eur_m2', 'S10', 'prezzo vs servizi su 10'), ('prezzo_eur_m2', 'S20', 'prezzo vs servizi su 20'),
         ('prezzo_eur_m2', 'SX', 'prezzo vs servizi extra (10)'),
         ('prezzo_eur_m2', 'quota_premium_pesata', 'prezzo vs quota premium 20/20'),
         ('prezzo_eur_m2', 'reddito_imponibile_medio_2024_pesato', 'prezzo vs reddito medio (per CAP)'),
         ('prezzo_eur_m2', 'dist_duomo_centroide_m', 'prezzo vs distanza dal Duomo (centroide)'),
         ('prezzo_eur_m2', 'dist_duomo_media_civici_m', 'prezzo vs distanza dal Duomo (media civici)'),
         ('S20', 'reddito_imponibile_medio_2024_pesato', 'servizi 20 vs reddito'),
         ('S20', 'dist_duomo_centroide_m', 'servizi 20 vs distanza'),
         ('S10', 'dist_duomo_centroide_m', 'servizi 10 vs distanza'),
         ('reddito_imponibile_medio_2024_pesato', 'dist_duomo_centroide_m', 'reddito vs distanza'),
         ('affitto_eur_m2_mese', 'S20', 'affitto vs servizi 20')]
rows = []
for a, b, lab in vars_:
    e, lo, hi = spearman_ci(main, a, b)
    rows.append(dict(coppia=lab, var_a=a, var_b=b, n=len(main), spearman=e, ic95_basso=lo, ic95_alto=hi))
pd.DataFrame(rows).to_csv(O + '/out/correlazioni_spearman.csv', index=False, float_format='%.4f')
RES['spearman'] = {r['coppia']: [round(r['spearman'], 3), round(r['ic95_basso'], 3), round(r['ic95_alto'], 3)] for r in rows}

# ---- 2. Spearman parziale
par = []
for sv in ['S10', 'S20', 'SX']:
    for lab, ctrl in [('nessun controllo', []), ('controllo distanza', ['dist_duomo_centroide_m']),
                      ('controllo reddito', ['reddito_imponibile_medio_2024_pesato']),
                      ('controllo distanza + reddito', ['dist_duomo_centroide_m', 'reddito_imponibile_medio_2024_pesato'])]:
        e, lo, hi = partial_spearman(main, sv, 'prezzo_eur_m2', ctrl)
        par.append(dict(servizi=sv, controlli=lab, n=len(main), spearman_parziale=e, ic95_basso=lo, ic95_alto=hi))
pd.DataFrame(par).to_csv(O + '/out/spearman_parziale.csv', index=False, float_format='%.4f')
RES['spearman_parziale'] = [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()} for r in par]


# ---- 3. Regressioni sui logaritmi: ln(prezzo) ~ servizi + ln(distanza) + ln(reddito)
def modello(df, nome, xs, y='lnP', target=None):
    m = ols(df[y].values, df[xs].values, xs)
    r = dict(modello=nome, y=y, n=m['n'], r2=m['r2'], r2_corretto=m['r2adj'])
    for k in xs:
        r['b_' + k] = m['b'][k]
        r['se_' + k] = m['se'][k]
    tg = target or xs[0]
    lo, hi = boot_ci(df, y, xs, tg)
    r['target'] = tg
    r['b_target'] = m['b'][tg]
    r['ic95_boot_basso'] = lo
    r['ic95_boot_alto'] = hi
    r['ic95_hc3_basso'] = m['b'][tg] - 1.96 * m['se'][tg]
    r['ic95_hc3_alto'] = m['b'][tg] + 1.96 * m['se'][tg]
    return r


mods = []
for sv in ['S20', 'S10']:
    mods += [modello(main, f'{sv} solo', [sv]),
             modello(main, f'{sv} + distanza', [sv, 'lnD']),
             modello(main, f'{sv} + reddito', [sv, 'lnY']),
             modello(main, f'{sv} + distanza + reddito', [sv, 'lnD', 'lnY']),
             modello(main, f'{sv} + distanza + reddito + fascia OMI', [sv, 'lnD', 'lnY', 'F_C', 'F_D', 'F_E'])]
mods += [modello(main, 'senza servizi: distanza + reddito', ['lnD', 'lnY'], target='lnD'),
         modello(main, 'essenziali(10) + extra + distanza + reddito [effetto essenziali]', ['S10', 'SX', 'lnD', 'lnY'], target='S10'),
         modello(main, 'essenziali(10) + extra + distanza + reddito [effetto extra]', ['SX', 'S10', 'lnD', 'lnY'], target='SX')]
M = pd.DataFrame(mods)
M.to_csv(O + '/out/modelli.csv', index=False, float_format='%.5f')

base = ols(main.lnP.values, main[['lnD', 'lnY']].values, ['lnD', 'lnY'])['r2']
full = ols(main.lnP.values, main[['S20', 'lnD', 'lnY']].values, ['S20', 'lnD', 'lnY'])['r2']
only = ols(main.lnP.values, main[['S20']].values, ['S20'])['r2']
RES['r2'] = dict(solo_servizi20=round(only, 3), distanza_reddito=round(base, 3), distanza_reddito_servizi20=round(full, 3),
                 aumento_dai_servizi=round(full - base, 3))
m_full = [r for r in mods if r['modello'] == 'S20 + distanza + reddito'][0]
m_solo = [r for r in mods if r['modello'] == 'S20 solo'][0]
pct = lambda x: round(100 * (np.exp(x) - 1), 1)
RES['coef_S20_solo_pct_per_servizio'] = pct(m_solo['b_S20'])
RES['coef_S20_solo_ic_boot_pct'] = [pct(m_solo['ic95_boot_basso']), pct(m_solo['ic95_boot_alto'])]
RES['coef_S20_controllato_pct_per_servizio'] = pct(m_full['b_S20'])
RES['coef_S20_controllato_ic_boot_pct'] = [pct(m_full['ic95_boot_basso']), pct(m_full['ic95_boot_alto'])]
RES['coef_S20_controllato_ic_hc3_pct'] = [pct(m_full['ic95_hc3_basso']), pct(m_full['ic95_hc3_alto'])]
RES['quota_coefficiente_che_sopravvive_S20'] = round(m_full['b_S20'] / m_solo['b_S20'], 3)
pm = float(main.prezzo_eur_m2.median())
RES['prezzo_mediano_zone_principale_eur_m2'] = pm
b, lo, hi = m_full['b_S20'], m_full['ic95_boot_basso'], m_full['ic95_boot_alto']
RES['un_servizio_in_piu_eur_m2'] = [round(pm * (np.exp(x) - 1)) for x in (b, lo, hi)]
RES['un_servizio_in_piu_eur_appartamento_70m2'] = [round(70 * pm * (np.exp(x) - 1)) for x in (b, lo, hi)]
RES['sd_S20_zone'] = round(float(main.S20.std()), 3)
RES['range_S20_zone'] = [round(float(main.S20.min()), 2), round(float(main.S20.max()), 2)]
RES['un_sd_di_servizi_pct_controllato'] = pct(b * main.S20.std())

# ---- 4. Robustezza
rob = []


def rob_row(nome, df, xs=('S20', 'lnD', 'lnY'), y='lnP'):
    r = modello(df, nome, list(xs), y=y)
    rob.append(dict(variante=nome, n=r['n'], b_servizi=r['b_target'], pct_per_servizio=100 * (np.exp(r['b_target']) - 1),
                    ic95_boot_basso_pct=100 * (np.exp(r['ic95_boot_basso']) - 1),
                    ic95_boot_alto_pct=100 * (np.exp(r['ic95_boot_alto']) - 1), r2=r['r2']))


rob_row('principale (41 zone, senza D39)', main)
rob_row('tutte le 42 zone con prezzo (D39 incluso)', sample(t, escludi=()))
rob_row('senza zone con meno di 100 civici residenziali (C13, C14, D34, D39)', sample(t, minres=100))
rob_row('solo zone con stato prevalente NORMALE', sample(t, solo_normale=True))
rob_row('distanza = media dei civici (non centroide)', main.assign(lnD=main.lnDm))
rob_row('distanza lineare (km) invece di logaritmo', main.assign(lnD=main.d_km))
rob_row('distanza e distanza al quadrato', main.assign(D2=main.d_km ** 2), xs=('S20', 'lnD', 'lnY', 'D2'))
rob_row('con fascia OMI B/C/D/E', main, xs=('S20', 'lnD', 'lnY', 'F_C', 'F_D', 'F_E'))
rob_row('senza reddito (solo distanza)', main, xs=('S20', 'lnD'))
rob_row('affitto invece del prezzo', main, y='lnR')
rob_row('servizi su 10 (non su 20)', main, xs=('S10', 'lnD', 'lnY'))
rob_row('servizi extra (10) soli', main, xs=('SX', 'lnD', 'lnY'))
loo = []
for z in main.zona:
    d = main[main.zona != z]
    m = ols(d.lnP.values, d[['S20', 'lnD', 'lnY']].values, ['S20', 'lnD', 'lnY'])
    loo.append((z, m['b']['S20']))
lb = np.array([v for _, v in loo])
rob.append(dict(variante='togliendo una zona alla volta: minimo', n=len(main) - 1, b_servizi=lb.min(),
                pct_per_servizio=100 * (np.exp(lb.min()) - 1), r2=np.nan))
rob.append(dict(variante='togliendo una zona alla volta: massimo', n=len(main) - 1, b_servizi=lb.max(),
                pct_per_servizio=100 * (np.exp(lb.max()) - 1), r2=np.nan))
RES['loo'] = {'min': [loo[int(lb.argmin())][0], pct(lb.min())], 'max': [loo[int(lb.argmax())][0], pct(lb.max())]}
R_ = pd.DataFrame(rob)
R_.to_csv(O + '/out/robustezza.csv', index=False, float_format='%.4f')
RES['robustezza'] = [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()} for r in rob]
RES['correlazioni_tra_spiegatori_pearson_log'] = main[['S20', 'lnD', 'lnY']].corr().round(3).to_dict()
RES['VIF'] = {}
for k in ['S20', 'lnD', 'lnY']:
    o = [x for x in ['S20', 'lnD', 'lnY'] if x != k]
    r2 = ols(main[k].values, main[o].values, o)['r2']
    RES['VIF'][k] = round(1 / (1 - r2), 2)
json.dump(RES, open(O + '/out/risultati_03.json', 'w'), indent=1, ensure_ascii=False, default=float)
pd.set_option('display.width', 250)
pd.set_option('display.max_colwidth', 80)
print(json.dumps({k: v for k, v in RES.items() if k not in ('robustezza', 'spearman_parziale')}, indent=1, ensure_ascii=False, default=float))
print(pd.DataFrame(par).round(3).to_string())
print(M[['modello', 'n', 'r2', 'target', 'b_target', 'ic95_boot_basso', 'ic95_boot_alto', 'ic95_hc3_basso', 'ic95_hc3_alto']].round(3).to_string())
print(R_.round(2).to_string())

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
for a, (xc, xl) in zip(ax, [('S20', 'servizi su 20'), ('dist_duomo_centroide_m', 'distanza dal Duomo (m)'),
                            ('reddito_imponibile_medio_2024_pesato', 'reddito medio (CAP)')]):
    a.scatter(main[xc], main.prezzo_eur_m2, s=18)
    a.set_xlabel(xl)
    a.set_ylabel('prezzo OMI, euro/m2 (stima)')
    for _, r in main.iterrows():
        a.annotate(r.zona, (r[xc], r.prezzo_eur_m2), fontsize=6)
plt.tight_layout()
plt.savefig(O + '/out/grafico_scatter.png', dpi=110)
