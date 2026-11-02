"""C: affluenza e mortalità standardizzata. Prova le spiegazioni meccaniche una per una."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 300)
L = open(os.path.join(OUT, 'C.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()

b = base()
red = pd.read_csv(p('voto-reddito', 'out', 'nil_reddito.csv'), encoding='utf-8-sig')
b = b.merge(red[['id_nil', 'reddito_2019_22_euro2025']], on='id_nil', how='left')
b['laur_oggi'] = b[['laur_2021', 'laur_2023']].mean(axis=1)
smr = pd.read_csv(os.path.join(OUT, 'smr_propri.csv'))
for wn in smr.finestra.unique():
    for po in ['T', 'ITA']:
        for s in ['T', 'M', 'F']:
            x = smr[(smr.finestra == wn) & (smr['pop'] == po) & (smr.sesso == s)].set_index('id_nil')
            b[f'smr{po}{s}|{wn}'] = b.id_nil.map(x.smr)
            if po == 'T' and s == 'T':
                b[f'O|{wn}'] = b.id_nil.map(x.O); b[f'E|{wn}'] = b.id_nil.map(x.E)
se = pd.read_csv(os.path.join(OUT, 'nil_affluenza_sezioni.csv'))
AFFS = {'com16': 'comunali_consiglio_2016-06-05', 'cam18': 'camera_2018-03-04', 'reg18': 'regionali_consiglio_2018-03-04', 'eur19': 'europee_2019-05-26', 'com21': 'comunali_consiglio_2021-10-03', 'cam22': 'camera_2022-09-25', 'reg23': 'regionali_consiglio_2023-02-12', 'eur24': 'europee_2024-06-08',
        'ref16': 'referendum_2016-12-04_ds1370', 'ref20': 'referendum_2020-09-20_ds1461', 'ref22': 'referendum_2022-06-12_ds1889', 'ref25': 'referendum_2025-06-08_ds2930', 'ref26': 'referendum_2026-03-22_ds2975', 'sen18': 'senato_2018-03-04'}
for k, eid in AFFS.items():
    x = se[se.eid == eid].set_index('id_nil')
    b['aff_' + k] = b.id_nil.map(x.aff_reg); b['e_' + k] = b.id_nil.map(x.e_reg); b['v_' + k] = b.id_nil.map(x.v_reg)
    b['affprev_' + k] = b.id_nil.map(x.aff_prev)
MAIN = ['com16', 'cam18', 'reg18', 'eur19', 'com21', 'cam22', 'reg23', 'eur24']
n0 = nil3000(b)
zs = pd.DataFrame({k: (b['aff_' + k] - n0['aff_' + k].mean()) / n0['aff_' + k].std() for k in MAIN})
b['aff_media'] = zs.mean(axis=1)
say('Affluenza città (somma sezioni regolari):')
for k in AFFS:
    x = b.dropna(subset=['e_' + k]); say(' ', k, round(x['v_' + k].sum() / x['e_' + k].sum() * 100, 1), 'elettori', round(x['e_' + k].sum()))

# ---- AIRE ed elettori giovani dal confronto nello stesso giorno, 4 marzo 2018
b['aire18'] = (b.e_reg18 - b.e_cam18)
b['q_aire'] = b.aire18 / b.e_reg18 * 100
b['q_giov_el'] = (b.e_cam18 - b.e_sen18) / b.e_cam18 * 100
b['aff_25p'] = b.v_sen18 / b.e_sen18 * 100
b['aff_18_24'] = (b.v_cam18 - b.v_sen18) / (b.e_cam18 - b.e_sen18) * 100
b['aff_reg18_netta'] = b.v_reg18 / b.e_cam18 * 100
# proxy AIRE per il 2021 (elettori comunali 2021 meno camera 2022)
b['q_aire21'] = (b.e_com21 - b.e_cam22) / b.e_com21 * 100
b['aff_com21_netta'] = b.v_com21 / b.e_cam22 * 100
b['aff_reg23_netta'] = b.v_reg23 / b.e_cam22 * 100
b['aff_eur24_netta'] = b.v_eur24 / b.e_cam22 * 100
# ---- età degli italiani (ds27)
ei = pd.read_csv(os.path.join(OUT, 'ds27_eta_ita.csv'))
def quote(an, solo_ita=True):
    x = ei[(ei.anno == an) & (ei.ita == True)] if solo_ita else ei[ei.anno == an]
    x = x[x.eta >= 18]
    w = x.pivot_table(index='id_nil', values='res', aggfunc='sum')
    o = pd.DataFrame({'adulti': w.res})
    for nm, (a, c) in {'18_34': (18, 34), '35_49': (35, 49), '50_64': (50, 64), '65_79': (65, 79), '80p': (80, 200), '85p': (85, 200), '90p': (90, 200)}.items():
        o['q' + nm] = x[(x.eta >= a) & (x.eta <= c)].groupby('id_nil').res.sum() / w.res * 100
    return o
qi = quote(2019)
for c in qi.columns:
    b['ita_' + c] = b.id_nil.map(qi[c])
ad17 = quote(2017)
b['ita_ad17'] = b.id_nil.map(ad17.adulti)
ad21 = quote(2021); b['ita_ad21'] = b.id_nil.map(ad21.adulti)
b['r_el_ita'] = b.e_cam18 / b.ita_ad17    # elettori residenti in Italia / italiani adulti anagrafe
b['r_el_ita_loc'] = b.e_reg18 / b.ita_ad17
# ---- residenti solo sulla carta: anagrafe contro censimento
c = pd.read_csv(p('censimenti', 'pulito', 'indicatori_NIL.csv'))
e = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv'))
for an in [2011, 2021, 2023]:
    b[f'r_anag_cens{an}'] = b.id_nil.map(e[e.anno == an].set_index('id_nil').residenti) / b.id_nil.map(c[c.anno == an].set_index('nil')['pop'])
sv = pd.read_csv(p('speranza-vita', 'pulito', 'nil_bandiere_residenze.csv'))
b['rapp85'] = b.id_nil.map(sv.set_index('id_nil').rapporto_85piu_2024)
info = pd.read_csv(p('elezioni', 'pulito', 'nil_info.csv'))
b['q_condivisi'] = b.id_nil.map(info.set_index('nil').quota_civici_condivisi)
b['fem_vs_masc'] = b['smrTF|2012-2019'] / b['smrTM|2012-2019']
n = nil3000(b)
n.to_csv(os.path.join(OUT, 'nil_tabella_C.csv'), index=False)
say('\nCittà: AIRE18 stimato', round(n.aire18.sum()), 'quota mediana', round(n.q_aire.median(), 2), 'min/max', round(n.q_aire.min(), 2), round(n.q_aire.max(), 2))
say('Top AIRE:', n.sort_values('q_aire', ascending=False)[['nil', 'q_aire', 'reddito_2024', 'r_el_ita']].head(8).round(2).values.tolist())
say('Coerenza q_aire 2018 vs q_aire21 Spearman', round(stats.spearmanr(n.q_aire, n.q_aire21).statistic, 3))
say('Rapporto elettori/italiani adulti: mediana', round(n.r_el_ita.median(), 3), 'min/max', round(n.r_el_ita.min(), 3), round(n.r_el_ita.max(), 3))
say('Rapporto anagrafe/censimento 2021 mediana', round(n.r_anag_cens2021.median(), 3), 'min/max', round(n.r_anag_cens2021.min(), 3), round(n.r_anag_cens2021.max(), 3), ' 2023', round(n.r_anag_cens2023.median(), 3))
say(' peggiori:', n.sort_values('r_anag_cens2021', ascending=False)[['nil', 'r_anag_cens2021']].head(6).round(3).values.tolist())
say('Spearman: q_aire~reddito %.2f, q_aire~dist %.2f, r_anag~reddito %.2f, r_anag~dist %.2f, r_anag~stranieri %.2f' % (
    stats.spearmanr(n.q_aire, n.reddito_2024).statistic, stats.spearmanr(n.q_aire, n.dist_duomo).statistic, stats.spearmanr(n.r_anag_cens2021, n.reddito_2024).statistic, stats.spearmanr(n.r_anag_cens2021, n.dist_duomo).statistic, stats.spearmanr(n.r_anag_cens2021, n.quota_stranieri).statistic))
s = 'smrTT|'
say('SMR~q_aire %.2f; SMR~r_anag %.2f; aff_cam18~q_aire %.2f; aff_reg18~q_aire %.2f; aff_com21~q_aire21 %.2f; aff_cam22~q_aire21 %.2f' % (
    stats.spearmanr(n[s + '2012-2019'], n.q_aire).statistic, stats.spearmanr(n[s + '2012-2019'], n.r_anag_cens2021).statistic, stats.spearmanr(n.aff_cam18, n.q_aire).statistic, stats.spearmanr(n.aff_reg18, n.q_aire).statistic, stats.spearmanr(n.aff_com21, n.q_aire21).statistic, stats.spearmanr(n.aff_cam22, n.q_aire21).statistic))
say('Correlazioni tra elezioni (Spearman):'); say(n[['aff_' + k for k in MAIN]].corr(method='spearman').round(2).to_string())

# ---- Base: griglia elezione x finestra
rows = []
WIN = ['2012-2015', '2016-2019', '2012-2019', '2020', '2021', '2022-2024']
for k in list(AFFS):
    for wn in WIN:
        y = f'smrTT|{wn}'
        rows.append(dict(el=k, fin=wn, sempl=round(stats.spearmanr(n['aff_' + k], n[y], nan_policy='omit').statistic, 3), parz=round(parz(n['aff_' + k].values, n[y].values, n[CTRL].values), 3)))
G = pd.DataFrame(rows); G.to_csv(os.path.join(OUT, 'C_griglia.csv'), index=False)
say('\nGriglia correlazione parziale (righe elezioni, colonne finestre)'); say(G.pivot(index='el', columns='fin', values='parz').loc[list(AFFS), WIN].to_string())
say('Griglia correlazione semplice'); say(G.pivot(index='el', columns='fin', values='sempl').loc[list(AFFS), WIN].to_string())

# ---- Analisi complete
AGE = ['ita_q18_34', 'ita_q35_49', 'ita_q65_79', 'ita_q80p']
y0 = 'smrTT|2012-2019'
rows = []
def riga(et, df, x, y, c):
    a = analisi(df, x, y, c, B=1500)
    rows.append(dict(prova=et, x=x, y=y, **a)); say(f'{et:62s} {x:16s} {y:18s} {fmt(a)}')
for x in ['aff_media', 'aff_cam18', 'aff_com21', 'aff_cam22', 'aff_eur24']:
    for y in ['smrTT|2012-2019', 'smrTT|2022-2024']:
        riga('base (distanza,reddito,età,densità)', n, x, y, CTRL)
say('')
x = 'aff_media'
for y in ['smrTT|2012-2019', 'smrTT|2022-2024']:
    riga('nessun controllo', n, x, y, None)
    riga('solo reddito', n, x, y, ['reddito_2024'])
    riga('solo età', n, x, y, ['eta_media'])
    riga('reddito 2019-22 invece di 2024', n, x, y, ['dist_duomo', 'reddito_2019_22_euro2025', 'eta_media', 'densita_ab_km2'])
    riga('GRANA: + laureati (grana fine)', n, x, y, CTRL + ['laur_oggi'])
    riga('GRANA: + laureati + prezzo casa', n, x, y, CTRL + ['laur_oggi', 'prezzo_2026_reale'])
    riga('GRANA: solo NIL con civici condivisi <50%', n[n.q_condivisi < .5], x, y, CTRL)
    riga('ETA: classi di età degli italiani adulti', n, x, y, ['dist_duomo', 'reddito_2024', 'densita_ab_km2'] + AGE)
    riga('ETA: base + quota elettori 18-24 (2018)', n, x, y, CTRL + ['q_giov_el'])
    riga('REGISTRO: + quota AIRE', n, x, y, CTRL + ['q_aire'])
    riga('REGISTRO: + anagrafe/censimento 2021', n, x, y, CTRL + ['r_anag_cens2021'])
    riga('REGISTRO: + AIRE + anagrafe/censimento', n, x, y, CTRL + ['q_aire', 'r_anag_cens2021'])
    riga('RSA: + quota 85+ tra gli italiani', n, x, y, CTRL + ['ita_q85p'])
    riga('RSA: + quota 90+', n, x, y, CTRL + ['ita_q90p'])
    riga('RSA: senza 10 NIL con più 85+', n[n.rapp85.rank(ascending=False) > 10], x, y, CTRL)
    riga('RSA: senza 5 NIL con eccesso femminile più alto', n[n.fem_vs_masc.rank(ascending=False) > 5], x, y, CTRL)
    riga('RSA: senza Morivione', n[n.nil != 'Morivione'], x, y, CTRL)
    riga('STRANIERI (controllo): + quota stranieri', n, x, y, CTRL + ['quota_stranieri'])
    riga('TUTTI: laureati, classi età, AIRE, anagrafe, 85+, stranieri', n, x, y, ['dist_duomo', 'reddito_2024', 'densita_ab_km2', 'laur_oggi', 'q_aire', 'r_anag_cens2021', 'ita_q85p', 'quota_stranieri'] + AGE)
    riga('POP: solo uomini', n, x, y.replace('smrTT', 'smrTM'), CTRL)
    riga('POP: solo donne', n, x, y.replace('smrTT', 'smrTF'), CTRL)
    riga('POP: solo italiani (morti e residenti)', n, x, y.replace('smrTT', 'smrITAT'), CTRL)
    riga('NIL>=5000', n[n.residenti >= 5000], x, y, CTRL)
    riga('NIL>=10000', n[n.residenti >= 10000], x, y, CTRL)
say('')
# AIRE: stessa giornata
for x in ['aff_cam18', 'aff_reg18', 'aff_reg18_netta', 'aff_25p', 'aff_18_24']:
    riga('STESSO GIORNO 2018', n, x, y0, CTRL)
for x in ['aff_com21', 'aff_com21_netta', 'aff_reg23', 'aff_reg23_netta', 'aff_eur24', 'aff_eur24_netta']:
    riga('NETTO AIRE', n, x, 'smrTT|2022-2024', CTRL)
    riga('NETTO AIRE', n, x, y0, CTRL)
riga('GIOVANI a parità di 25+', n, 'aff_18_24', y0, CTRL + ['aff_25p'])
riga('25+ a parità di GIOVANI', n, 'aff_25p', y0, CTRL + ['aff_18_24'])
# SMR corretto per residenti sulla carta
n = n.copy()
n['smr_cens'] = n['smrTT|2022-2024'] * n.r_anag_cens2023
riga('SMR 2022-24 con attesi riportati al censimento 2023', n, 'aff_media', 'smr_cens', CTRL)
# Covid e placebo in avanti/indietro
for wn in ['2012-2015', '2016-2019', '2020', '2021', '2022-2024']:
    riga('finestra', n, 'aff_media', f'smrTT|{wn}', CTRL)
    riga('finestra, referendum 2016 solo', n, 'aff_ref16', f'smrTT|{wn}', CTRL)
# Ciò che le prove meccaniche possono fare: prevalente invece di proporzionale
riga('sezione al NIL prevalente', n, 'affprev_cam22', y0, CTRL)
riga('confronto proporzionale', n, 'aff_cam22', y0, CTRL)
# Livello CAP (stessa grana del reddito)
sc = pd.read_csv(p('voto-reddito', 'out', 'sezione_cap.csv'), encoding='utf-8-sig')
rs = pd.read_csv(p('elezioni', 'pulito', 'risultati_sezione.csv'), low_memory=False, usecols=['elezione_id', 'sezione', 'elettori', 'votanti'])
capred = pd.read_csv(p('voto-reddito', 'out', 'cap_reddito.csv'), encoding='utf-8-sig')
cc = pd.read_csv(p('quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv')).dropna(subset=['ID_NIL'])
cc['id_nil'] = cc.ID_NIL.astype(int)
cc = cc.merge(b[['id_nil', 'residenti', 'O|2012-2019', 'E|2012-2019', 'eta_media', 'dist_duomo', 'laur_oggi']], on='id_nil')
cc['w'] = cc.quota_nil; cc['pes'] = cc.w * cc.residenti
cap = cc.groupby('CAP').apply(lambda g: pd.Series({'O': (g['O|2012-2019'] * g.w).sum(), 'E': (g['E|2012-2019'] * g.w).sum(), 'eta_media': np.average(g.eta_media, weights=g.pes), 'dist_duomo': np.average(g.dist_duomo, weights=g.pes), 'laur': np.average(g.laur_oggi, weights=g.pes)}), include_groups=False).reset_index().rename(columns={'CAP': 'cap'})
cap['smr'] = cap.O / cap.E
for k in ['cam18', 'com21', 'cam22', 'eur24']:
    x = rs[rs.elezione_id == AFFS[k]]; x = x[(x.elettori > 0) & (x.votanti <= x.elettori)].merge(sc, on='sezione')
    g = x.assign(e=x.elettori * x.peso, v=x.votanti * x.peso).groupby('cap')[['e', 'v']].sum()
    cap['aff_' + k] = cap.cap.map(g.v / g.e * 100)
cap = cap.merge(capred[['cap', 'reddito_2019_22_euro2025', 'reddito_2024_euro2025']], on='cap'); cap['nil'] = cap.cap
for k in ['cam18', 'com21', 'cam22', 'eur24']:
    riga('LIVELLO CAP (età, distanza, reddito)', cap, 'aff_' + k, 'smr', ['dist_duomo', 'reddito_2019_22_euro2025', 'eta_media'])
    riga('LIVELLO CAP senza controlli', cap, 'aff_' + k, 'smr', None)
# Dentro il CAP dominante
dom = cc.sort_values('quota_nil').groupby('id_nil').tail(1)[['id_nil', 'CAP']].rename(columns={'CAP': 'cap_dom'})
n3 = n.merge(dom, on='id_nil'); g = n3[n3.groupby('cap_dom').cap_dom.transform('size') >= 2]
for wn in ['2012-2019', '2022-2024']:
    ex = g.aff_media - g.groupby('cap_dom').aff_media.transform('mean'); ey = g[f'smrTT|{wn}'] - g.groupby('cap_dom')[f'smrTT|{wn}'].transform('mean')
    say(f'Dentro lo stesso CAP dominante {wn}: n={len(g)} Pearson {np.corrcoef(ex, ey)[0, 1]:+.3f} Spearman {stats.spearmanr(ex, ey).statistic:+.3f}')
# Quanto rumore Poisson ha l'SMR: attenuazione
for wn in ['2012-2019', '2022-2024']:
    var_noise = (n[f'smrTT|{wn}'] / n[f'E|{wn}']).mean(); var_tot = n[f'smrTT|{wn}'].var(); say(wn, 'affidabilità SMR', round(1 - var_noise / var_tot, 3))
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'C_prove.csv'), index=False)
L.close()
